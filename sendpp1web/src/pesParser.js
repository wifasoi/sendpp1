/**
 * PES / PEC file parser → PP1 stitch format encoder.
 *
 * Port of pyembroidery's PecReader + sendpp1's pp1Writer.
 * Parses .pes files, decodes PEC stitch data into absolute (x, y, cmd),
 * then encodes into the PP1 4-byte-per-stitch binary format.
 *
 * PP1 stitch format (4 bytes per command):
 *   x_raw = (x << 3) | section_flag    (int16 LE)
 *   y_raw = (y << 3) | operation_flag   (int16 LE)
 *   section:  0=normal, 3=color_change/stop, 5=end
 *   operation: 0=stitch, 1=feed, 2=cut/trim, 3=jump
 */

// ── PEC constants ───────────────────────────────────────────────────────────
const FLAG_LONG  = 0x80;
const JUMP_CODE  = 0x10;
const TRIM_CODE  = 0x20;

// pyembroidery command IDs (must match EmbConstant)
const CMD_STITCH       = 0;
const CMD_MOVE         = 1;  // JUMP / move
const CMD_TRIM         = 2;
const CMD_STOP         = 3;
const CMD_END          = 4;
const CMD_COLOR_CHANGE = 5;

// ── Helpers ─────────────────────────────────────────────────────────────────

function signed12(v) {
  v &= 0xFFF;
  return v > 0x7FF ? v - 0x1000 : v;
}

function signed7(v) {
  return v > 63 ? v - 128 : v;
}

function readUint8(data, pos) {
  return pos < data.length ? data[pos] : null;
}

function readInt24LE(data, pos) {
  if (pos + 2 >= data.length) return 0;
  return data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16);
}

// ── PES Parser ──────────────────────────────────────────────────────────────

/**
 * Parse a PES file and return stitches + color count.
 * @param {ArrayBuffer} buffer
 * @returns {{ stitches: Array<{x: number, y: number, cmd: number}>, colorCount: number }}
 */
export function parsePES(buffer) {
  const data = new Uint8Array(buffer);
  const dv = new DataView(buffer);

  const magic = String.fromCharCode(...data.slice(0, 4));
  if (magic !== "#PES" && magic !== "#PEC") {
    throw new Error(`Not a PES/PEC file (magic: "${magic}")`);
  }

  if (magic === "#PEC") {
    // Standalone PEC file — PEC header starts at byte 8
    return readPEC(data, 8);
  }

  // PES: PEC block offset at byte 8
  const pecOffset = dv.getUint32(8, true);
  if (pecOffset === 0 || pecOffset >= data.length) {
    throw new Error(`Invalid PEC offset: ${pecOffset}`);
  }

  return readPEC(data, pecOffset);
}

/**
 * Parse the PEC block following pyembroidery's PecReader.read_pec exactly.
 */
function readPEC(data, pecStart) {
  // Match pyembroidery's PecReader.read_pec offset calculations:
  // f.seek(3, 1)                   → skip "LA:"
  // read_string_8(f, 16)           → label (16 bytes)
  // f.seek(0xF, 1)                 → 15 bytes
  // read_int_8(f)                  → pec_graphic_byte_stride (1 byte)
  // read_int_8(f)                  → pec_graphic_icon_height (1 byte)
  // f.seek(0xC, 1)                 → 12 bytes
  // read_int_8(f)                  → color_changes (1 byte)
  // f.read(color_changes + 1)      → color bytes
  // f.seek(0x1D0 - color_changes, 1)
  // read_int_24le(f)               → stitch block end (3 bytes)
  // f.seek(0x0B, 1)                → 11 bytes → STITCH DATA START

  let off = pecStart;
  off += 3;             // "LA:"
  off += 16;            // label
  off += 0x0F;          // padding/metadata
  off += 1;             // pec_graphic_byte_stride
  off += 1;             // pec_graphic_icon_height
  off += 0x0C;          // more metadata

  const colorChanges = data[off] ?? 0;
  const colorCount = colorChanges + 1;
  off += 1;
  off += colorCount;    // color index bytes

  off += (0x1D0 - colorChanges);   // skip to stitch block header

  // read_int_24le for stitch_block_end (we don't need it for parsing, but
  // consume the 3 bytes to keep offset aligned)
  off += 3;

  // f.seek(0x0B, 1) — skip 11 bytes of stitch block header
  off += 0x0B;

  if (off >= data.length) {
    throw new Error(`PEC stitch data offset ${off} beyond file (${data.length} bytes)`);
  }

  const stitches = decodePECStitches(data, off);
  return { stitches, colorCount };
}

/**
 * Decode PEC stitch data — faithful port of pyembroidery's read_pec_stitches.
 * Returns absolute coordinates.
 */
function decodePECStitches(data, startOffset) {
  const stitches = [];
  let absX = 0;
  let absY = 0;
  let i = startOffset;
  let afterColorChange = false;

  while (i < data.length - 1) {
    let val1 = data[i++];
    let val2 = data[i++];

    // END: 0xFF 0x00
    if ((val1 === 0xFF && val2 === 0x00) || val2 === undefined) {
      break;
    }

    // COLOR_CHANGE: 0xFE 0xB0 + skip 1 byte
    if (val1 === 0xFE && val2 === 0xB0) {
      i += 1;  // skip 1 byte (matches pyembroidery f.seek(1, 1))
      stitches.push({ x: absX, y: absY, cmd: CMD_COLOR_CHANGE });
      afterColorChange = true;
      continue;
    }

    let jump = false;
    let trim = false;
    let x, y;

    // Decode X
    if (val1 & FLAG_LONG) {
      if (val1 & TRIM_CODE) trim = true;
      if (val1 & JUMP_CODE) jump = true;
      const code = (val1 << 8) | val2;
      x = signed12(code);
      // Read NEW val2 for Y processing
      val2 = readUint8(data, i++);
      if (val2 === null) break;
    } else {
      x = signed7(val1);
    }

    // Decode Y
    if (val2 & FLAG_LONG) {
      if (val2 & TRIM_CODE) trim = true;
      if (val2 & JUMP_CODE) jump = true;
      const val3 = readUint8(data, i++);
      if (val3 === null) break;
      const code = (val2 << 8) | val3;
      y = signed12(code);
    } else {
      y = signed7(val2);
    }

    // After COLOR_CHANGE: the next movement is ALWAYS a repositioning jump,
    // regardless of PEC flags. Different digitizers encode this differently —
    // some use TRIM+JUMP flags, some use plain short bytes. Either way, the
    // machine must not stitch here. We also suppress TRIM since the color
    // change already implies a thread cut.
    if (afterColorChange) {
      absX += x;
      absY += y;
      stitches.push({ x: absX, y: absY, cmd: CMD_MOVE });
      afterColorChange = false;
    } else if (trim) {
      // Intra-color trim: cut at CURRENT position, then jump to new one
      stitches.push({ x: absX, y: absY, cmd: CMD_TRIM });
      absX += x;
      absY += y;
      stitches.push({ x: absX, y: absY, cmd: CMD_MOVE });
    } else {
      absX += x;
      absY += y;
      if (jump) {
        stitches.push({ x: absX, y: absY, cmd: CMD_MOVE });
      } else {
        stitches.push({ x: absX, y: absY, cmd: CMD_STITCH });
      }
    }
  }

  // out.end()
  stitches.push({ x: absX, y: absY, cmd: CMD_END });

  return stitches;
}

// ── PP1 Encoder ─────────────────────────────────────────────────────────────

/**
 * Encode stitches into PP1 binary format.
 * Each stitch = 4 bytes:  x_raw(int16 LE) + y_raw(int16 LE)
 *
 * @param {Array<{x: number, y: number, cmd: number}>} stitches
 * @returns {Uint8Array}
 */
export function encodePP1(stitches) {
  const buf = new ArrayBuffer(stitches.length * 4);
  const dv = new DataView(buf);
  let off = 0;

  for (let idx = 0; idx < stitches.length; idx++) {
    const { x, y, cmd } = stitches[idx];
    let blockFlag = 0;   // section flag (x low 3 bits)
    let stitchFlag = 0;  // operation flag (y low 3 bits)

    // PP1 quirk: drop TRIM when the next command is a JUMP/MOVE.
    // A trim before a jump is redundant — the machine lifts the needle
    // for jumps anyway. The Python PP1 writer silently drops these,
    // and keeping them causes phantom thread cuts.
    if (cmd === CMD_TRIM) {
      const next = stitches[idx + 1];
      if (next && (next.cmd === CMD_MOVE || next.cmd === CMD_COLOR_CHANGE)) {
        continue;  // skip this TRIM
      }
    }

    switch (cmd) {
      case CMD_STITCH:
        blockFlag = 0; stitchFlag = 0;
        break;
      case CMD_MOVE:  // JUMP
        blockFlag = 0; stitchFlag = 3;
        break;
      case CMD_TRIM:
        blockFlag = 0; stitchFlag = 2;
        break;
      case CMD_COLOR_CHANGE:
      case CMD_STOP:
        blockFlag = 3; stitchFlag = 0;
        break;
      case CMD_END:
        blockFlag = 5; stitchFlag = 0;
        break;
      default:
        continue;
    }

    const xRaw = (x << 3) | (blockFlag & 0x07);
    const yRaw = (y << 3) | (stitchFlag & 0x07);

    dv.setInt16(off, xRaw, true);
    dv.setInt16(off + 2, yRaw, true);
    off += 4;
  }

  return new Uint8Array(buf, 0, off);
}

/**
 * Convenience: parse a PES file and return PP1-encoded binary.
 * @param {ArrayBuffer} pesBuffer
 * @returns {{ pp1Data: Uint8Array, stitchCount: number, colorCount: number }}
 */
export function pesToPP1(pesBuffer) {
  const { stitches, colorCount } = parsePES(pesBuffer);
  const stitchCount = stitches.filter(s => s.cmd === CMD_STITCH).length;
  const pp1Data = encodePP1(stitches);
  return { pp1Data, stitchCount, colorCount };
}
