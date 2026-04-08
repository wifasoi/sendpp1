/**
 * PP1 Sewing Machine BLE Protocol — Web Bluetooth implementation.
 *
 * Direct port of sendpp1/core/machine.py.
 * All protocol logic runs client-side, no server required.
 */

// ── BLE UUIDs ────────────────────────────────────────────────────────────────
const MAIN_SERVICE_UUID   = "a76eb9e0-f3ac-4990-84cf-3a94d2426b2b";
const WRITE_CHAR_UUID     = "a76eb9e2-f3ac-4990-84cf-3a94d2426b2b";
const READ_CHAR_UUID      = "a76eb9e1-f3ac-4990-84cf-3a94d2426b2b";

// ── Machine Commands (big-endian uint16, matching MachineCommand enum) ───────
export const CMD = {
  MACHINE_INFO:       0x0000,   // 0
  MACHINE_STATE:      0x0001,   // 1
  SERVICE_COUNT:      0x0100,   // 256
  REGULAR_INSPECTION: 0x0103,   // 259
  PATTERN_UUID:       0x0702,   // 1794
  LAYOUT_DATA:        0x0705,   // 1797
  EMBROIDERY_INFO:    0x0706,   // 1798
  EMBROIDERY_MONITOR: 0x0707,   // 1799
  DELETE_EMBROIDERY:  0x0708,   // 1800
  SET_NEEDLE_MODE:    0x0709,   // 1801
  SEND_UUID:          0x070A,   // 1802
  RESUME_FLAG:        0x070B,   // 1803
  RESUME_EMBROIDERY:  0x070C,   // 1804
  START_SEWING:       0x070E,   // 1806
  HOOP_AVOIDANCE:     0x070F,   // 1807
  ORIGIN_POINT:       0x0800,   // 2048
  RESET_SETTINGS:     0x0C00,   // 3072
  SEND_HOST_SETTINGS: 0x0C01,   // 3073
  MACHINE_SETTINGS:   0x0C02,   // 3074
  PREPARE_TRANSFER:   0x1200,   // 4608
  DATA_PACKET:        0x1201,   // 4609
  CLEAR_ERROR:        0x1300,   // 4864
  ERROR_LOG:          0x1301,   // 4865
};

// ── Machine Status codes (from SewingMachineStatus enum) ────────────────────
export const MachineStatus = {
  0x00: "Initial",
  0x01: "LowerThread",
  0x10: "SewingWaitNoData",
  0x11: "SewingWait",
  0x12: "SewingDataReceive",
  0x20: "MaskTraceLockWait",
  0x21: "MaskTracing",
  0x22: "MaskTraceFinish",
  0x30: "Sewing",
  0x31: "SewingFinish",
  0x32: "SewingInterruption",
  0x40: "ThreadChange",
  0x41: "Pause",
  0x42: "Stop",
  0x50: "HoopAvoidance",
  0x51: "HoopAvoidancing",
  0x60: "RLReceiving",
  0x61: "RLReceived",
  0xDD: "None",
  0xFF: "TryConnecting",
};

// ── Transfer status codes ────────────────────────────────────────────────────
const STATUS_COMPLETE = 0;
const STATUS_CONTINUE = 2;

// ── Packet overhead: cmd(2) + offset(4) + checksum(1) = 7 ───────────────────
const PACKET_OVERHEAD = 7;

// ── Conservative default chunk size (BLE 4.0 minimum ATT payload) ───────────
// Web Bluetooth doesn't expose the negotiated MTU, so we default to a safe
// value.  512 - 3 (ATT header) - 7 (protocol overhead) = 502 is likely fine
// on modern hardware, but 20 is the guaranteed minimum.  We use 505 as a
// reasonable default matching the Python client's observed MTU.
const DEFAULT_CHUNK_SIZE = 505;

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Encode a command code as a 2-byte big-endian Uint8Array. */
function cmdBytes(cmd) {
  return new Uint8Array([(cmd >> 8) & 0xFF, cmd & 0xFF]);
}

/** Concatenate multiple Uint8Array / ArrayBuffer into one Uint8Array. */
function concat(...parts) {
  const bufs = parts.map(p => p instanceof ArrayBuffer ? new Uint8Array(p) : p);
  const len  = bufs.reduce((s, b) => s + b.length, 0);
  const out  = new Uint8Array(len);
  let off = 0;
  for (const b of bufs) { out.set(b, off); off += b.length; }
  return out;
}

/** Pack a number as little-endian bytes. */
function packLE(value, bytes) {
  const buf = new Uint8Array(bytes);
  for (let i = 0; i < bytes; i++) {
    buf[i] = (value >> (8 * i)) & 0xFF;
  }
  return buf;
}

/** Read a little-endian uint from a Uint8Array slice. */
function readLE(buf, offset, bytes) {
  let v = 0;
  for (let i = 0; i < bytes; i++) v |= buf[offset + i] << (8 * i);
  return v >>> 0;   // unsigned
}

/** Checksum: sum of bytes, masked. */
function checksum(data, mask) {
  let s = 0;
  for (let i = 0; i < data.length; i++) s += data[i];
  return s & mask;
}

// ── PP1Machine class ─────────────────────────────────────────────────────────

export class PP1Machine {
  /** @type {BluetoothDevice|null} */
  device = null;
  /** @type {BluetoothRemoteGATTCharacteristic|null} */
  writeCh = null;
  /** @type {BluetoothRemoteGATTCharacteristic|null} */
  readCh  = null;

  chunkSize = DEFAULT_CHUNK_SIZE;

  /** Callbacks — override these to hook into the UI. */
  onLog       = (msg) => console.log(`[PP1] ${msg}`);
  onProgress  = (sent, total) => {};

  /** GATT operation mutex — Web Bluetooth can only do one op at a time. */
  #gattQueue = Promise.resolve();

  /** Wrap a GATT operation so it waits for the previous one to finish. */
  #gattMutex(fn) {
    const next = this.#gattQueue.then(fn, fn);  // run even if prev rejected
    this.#gattQueue = next.catch(() => {});      // swallow so chain continues
    return next;
  }

  // ── Connection ───────────────────────────────────────────────────────────

  async connect() {
    this.device = await navigator.bluetooth.requestDevice({
      filters: [{ services: [MAIN_SERVICE_UUID] }],
    });

    this.onLog(`Paired with ${this.device.name ?? this.device.id}`);

    const server  = await this.device.gatt.connect();
    const service = await server.getPrimaryService(MAIN_SERVICE_UUID);
    this.writeCh  = await service.getCharacteristic(WRITE_CHAR_UUID);
    this.readCh   = await service.getCharacteristic(READ_CHAR_UUID);

    this.onLog("GATT connected, characteristics ready");
  }

  disconnect() {
    if (this.device?.gatt?.connected) {
      this.device.gatt.disconnect();
    }
    this.writeCh = null;
    this.readCh  = null;
    this.onLog("Disconnected");
  }

  get connected() {
    return !!this.device?.gatt?.connected;
  }

  // ── Low-level BLE I/O ────────────────────────────────────────────────────

  /** Build the wire frame: cmd(2) + data. */
  #buildCmd(cmd, data = new Uint8Array(0)) {
    return concat(cmdBytes(cmd), data);
  }

  async #send(cmd, data = new Uint8Array(0)) {
    const frame = this.#buildCmd(cmd, data);
    await this.writeCh.writeValueWithResponse(frame);
  }

  async #receive() {
    const dv = await this.readCh.readValue();
    return new Uint8Array(dv.buffer);
  }

  /**
   * Send a command and read the response.
   * Serialized through the GATT mutex so overlapping BLE ops never happen.
   * Returns the payload AFTER the 2-byte command echo, or null on mismatch.
   */
  async #request(cmd, data = new Uint8Array(0)) {
    return this.#gattMutex(async () => {
      await this.#send(cmd, data);
      const resp = await this.#receive();
      if (resp.length < 2) return null;
      const echoed = (resp[0] << 8) | resp[1];
      if (echoed !== cmd) {
        this.onLog(`Command echo mismatch: expected 0x${cmd.toString(16)} got 0x${echoed.toString(16)}`);
        return null;
      }
      return resp.slice(2);
    });
  }

  // ── Machine queries ──────────────────────────────────────────────────────

  async getMachineState() {
    const resp = await this.#request(CMD.MACHINE_STATE);
    return resp ? resp[0] : null;
  }

  async getMachineInfo() {
    return await this.#request(CMD.MACHINE_INFO);
  }

  /**
   * Get embroidery info (dimensions, stitch count, speed, etc.)
   * @returns {{ sizeLeft, sizeTop, sizeRight, sizeBottom, totalTime, totalStitches, speed } | null}
   */
  async getEmbroideryInfo() {
    const resp = await this.#request(CMD.EMBROIDERY_INFO);
    if (!resp || resp.length < 14) return null;
    const dv = new DataView(resp.buffer, resp.byteOffset, resp.byteLength);
    return {
      sizeLeft:       dv.getInt16(0, true),
      sizeTop:        dv.getInt16(2, true),
      sizeRight:      dv.getInt16(4, true),
      sizeBottom:     dv.getInt16(6, true),
      totalTime:      dv.getInt16(8, true),
      totalStitches:  dv.getUint16(10, true),
      speed:          dv.getInt16(12, true),
    };
  }

  /**
   * Get real-time embroidery monitor info (progress during sewing).
   * @returns {{ currentStitches, currentTime, stopTime, currentX, currentY } | null}
   */
  async getMonitorInfo() {
    const resp = await this.#request(CMD.EMBROIDERY_MONITOR);
    if (!resp || resp.length < 10) return null;
    const dv = new DataView(resp.buffer, resp.byteOffset, resp.byteLength);
    return {
      currentStitches: dv.getUint16(0, true),
      currentTime:     dv.getInt16(2, true),
      stopTime:        dv.getInt16(4, true),
      currentX:        dv.getInt16(6, true),
      currentY:        dv.getInt16(8, true),
    };
  }

  /**
   * Check if the machine can resume a previous embroidery.
   */
  async getResumeFlag() {
    const resp = await this.#request(CMD.RESUME_FLAG);
    return resp && resp[0] === 1;
  }

  /**
   * Resume a previously interrupted embroidery.
   */
  async resumeEmbroidery() {
    const resp = await this.#request(CMD.RESUME_EMBROIDERY);
    if (resp && resp[0] !== 0) {
      this.onLog(`Resume embroidery failed, status=${resp[0]}`);
      return false;
    }
    this.onLog("Resume embroidery OK");
    return true;
  }

  /**
   * Tell the machine to start sewing.
   */
  async startSewing() {
    await this.#request(CMD.START_SEWING);
    this.onLog("Start sewing command sent");
  }

  /**
   * Clear an error from the machine.
   * @param {number} errorCode  single-byte error code to clear
   */
  async clearError(errorCode = 0) {
    await this.#request(CMD.CLEAR_ERROR, new Uint8Array([errorCode]));
    this.onLog("Error cleared");
  }

  // ── Transfer protocol ────────────────────────────────────────────────────

  async deleteEmbroidery() {
    const resp = await this.#request(CMD.DELETE_EMBROIDERY);
    if (resp && resp[0] !== 0) {
      this.onLog(`Delete embroidery failed, status=${resp[0]}`);
      return false;
    }
    this.onLog("Embroidery deleted");
    return true;
  }

  async #prepareTransfer(size, csum) {
    // Payload: type(1)=0x03 | size(4, uint32 LE) | checksum(2, uint16 LE)
    const payload = concat(
      new Uint8Array([0x03]),
      packLE(size, 4),
      packLE(csum, 2),
    );
    const resp = await this.#request(CMD.PREPARE_TRANSFER, payload);
    if (!resp || resp[0] !== 0) {
      this.onLog(`Prepare transfer rejected, status=${resp?.[0]}`);
      return false;
    }
    this.onLog(`Prepare transfer OK — ${size} bytes, checksum 0x${csum.toString(16).toUpperCase()}`);
    return true;
  }

  /**
   * Transfer stitch data to the machine.
   * @param {Uint8Array} data  raw stitch bytes
   * @returns {Promise<boolean>} true on success
   */
  async transfer(data) {
    const transferSize = this.chunkSize;
    const totalChecksum = checksum(data, 0xFFFF);
    const totalChunks = Math.ceil(data.length / transferSize);

    this.onLog(`Starting transfer: ${data.length} bytes, checksum=0x${totalChecksum.toString(16).toUpperCase()}, chunks=${totalChunks}`);

    if (!(await this.#prepareTransfer(data.length, totalChecksum))) {
      return false;
    }

    // Small delay for the machine to allocate its receive buffer
    await new Promise(r => setTimeout(r, 100));

    let bytesSent = 0;
    for (let i = 0; i < totalChunks; i++) {
      const start = i * transferSize;
      const end   = Math.min(start + transferSize, data.length);
      const chunk = data.slice(start, end);
      const chunkCsum = checksum(chunk, 0xFF);

      // Format: offset(4,LE) + chunk + checksum(1)
      const payload = concat(
        packLE(bytesSent, 4),
        chunk,
        new Uint8Array([chunkCsum]),
      );

      const resp = await this.#request(CMD.DATA_PACKET, payload);
      if (!resp || resp.length === 0) {
        this.onLog(`DATA_PACKET ${i + 1}/${totalChunks} — no response`);
        return false;
      }

      const status = resp[0];

      if (status === STATUS_COMPLETE) {
        bytesSent += chunk.length;
        this.onLog(`Transfer complete — ${bytesSent} bytes`);
        this.onProgress(bytesSent, data.length);
        return true;
      } else if (status === STATUS_CONTINUE) {
        bytesSent += chunk.length;
        this.onProgress(bytesSent, data.length);
      } else {
        const extra = resp.length >= 5 ? readLE(resp, 1, 4) : -1;
        this.onLog(`DATA_PACKET ${i + 1}/${totalChunks} REJECTED status=${status} extra=${extra}`);
        return false;
      }
    }

    this.onLog(`All ${totalChunks} chunks sent (${bytesSent} bytes)`);
    return true;
  }

  async sendLayout(layout = null) {
    // Default layout: no move, 100% scale, no rotation, frame=1 (100mm)
    const payload = layout ?? concat(
      packLE(0, 2),     // moveX
      packLE(0, 2),     // moveY
      packLE(100, 2),   // sizeX %
      packLE(100, 2),   // sizeY %
      packLE(0, 2),     // rotate
      new Uint8Array([0x00]),  // flip
      new Uint8Array([0x01]),  // frame (1 = 100mm)
      // Bounding box (12 bytes of zeros = no constraint)
      new Uint8Array(12),
    );
    await this.#request(CMD.LAYOUT_DATA, payload);
    this.onLog("Layout sent");
  }

  async sendPatternUUID(uuidBytes) {
    const resp = await this.#request(CMD.SEND_UUID, uuidBytes);
    this.onLog("Pattern UUID sent");
  }

  /**
   * Full transfer flow: delete old → transfer data → send layout → send UUID.
   * @param {Uint8Array} stitchData  encoded stitch commands
   */
  async fullTransfer(stitchData) {
    await this.deleteEmbroidery();
    const ok = await this.transfer(stitchData);
    if (!ok) return false;
    await this.sendLayout();
    // Generate a random UUID for the pattern
    const uuid = crypto.getRandomValues(new Uint8Array(16));
    await this.sendPatternUUID(uuid);
    return true;
  }
}
