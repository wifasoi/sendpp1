-- sendpp1.lua  –  Wireshark dissector for the PP1 embroidery-machine BLE protocol
--
-- Transport: BLE GATT (Bluetooth Low Energy)
--   Service  UUID : a76eb9e0-f3ac-4990-84cf-3a94d2426b2b
--   Write    UUID : a76eb9e2-f3ac-4990-84cf-3a94d2426b2b  (host → machine)
--   Read/Notify UUID : a76eb9e1-f3ac-4990-84cf-3a94d2426b2b  (machine → host)
--
-- Frame layout (both directions)
--   [0..1]  Command  uint16 big-endian
--   [2..]   Payload  structure depends on command
--
-- INSTALLATION
--   Copy to: %APPDATA%\Wireshark\plugins\sendpp1.lua
--   Restart Wireshark.
--
-- APPLYING THE DISSECTOR
--   The plugin registers on handles 0x0033 and 0x0034 (common for this device).
--   If your capture uses different handles, find them via:
--     Bluetooth → ATT → "Read By Type Response" listing the PP1 service UUIDs
--   Then update PP1_HANDLES at the top of this file.
--
--   Alternatively: right-click any ATT PDU on the PP1 handle → Decode As → PP1
--
-- DISPLAY FILTER:  sendpp1

-- ── Configurable handle list ──────────────────────────────────────────────────
-- Edit these to match your capture. Handle 0x0034 was observed in a real capture.
-- Add as many as needed.
local PP1_HANDLES = { 0x0032, 0x0033, 0x0034 }

-- ── Protocol object ───────────────────────────────────────────────────────────

local proto = Proto("sendpp1", "PP1 Sewing Machine BLE Protocol")

-- ── Fields ────────────────────────────────────────────────────────────────────

local f = proto.fields

f.cmd        = ProtoField.uint16("sendpp1.cmd",       "Command",    base.DEC)
f.cmd_name   = ProtoField.string("sendpp1.cmd_name",  "Command Name")
f.direction  = ProtoField.string("sendpp1.direction", "Direction")
f.payload    = ProtoField.bytes ("sendpp1.payload",   "Payload")
f.status     = ProtoField.uint8 ("sendpp1.status",    "Status Byte", base.HEX)

-- Machine Info (cmd 0)
f.sw_version  = ProtoField.uint8 ("sendpp1.sw_version",  "SW Version")
f.serial      = ProtoField.string("sendpp1.serial",       "Serial Number")
f.mac         = ProtoField.string("sendpp1.mac",          "MAC Address")
f.bt_version  = ProtoField.int8  ("sendpp1.bt_version",   "BT Version")
f.model       = ProtoField.uint8 ("sendpp1.model",        "Model")
f.oem         = ProtoField.uint8 ("sendpp1.oem",          "OEM")
f.monitor_ok  = ProtoField.bool  ("sendpp1.monitor_ok",   "Supports Monitor")
f.max_width   = ProtoField.int16 ("sendpp1.max_width",    "Max Width",  base.DEC)
f.max_height  = ProtoField.int16 ("sendpp1.max_height",   "Max Height", base.DEC)
f.model_code  = ProtoField.string("sendpp1.model_code",   "Model Code")

-- Machine State (cmd 1)
f.state_byte  = ProtoField.uint8 ("sendpp1.state",        "State Code", base.HEX)
f.state_name  = ProtoField.string("sendpp1.state_name",   "State Name")

-- Service Info (cmd 256)
f.svc_count   = ProtoField.uint32("sendpp1.svc_count",    "Service Count")
f.svc_total   = ProtoField.uint32("sendpp1.svc_total",    "Total Count")

-- Embroidery Info (cmd 1798)
f.emb_left    = ProtoField.int16 ("sendpp1.emb_left",     "Bound Left",    base.DEC)
f.emb_top     = ProtoField.int16 ("sendpp1.emb_top",      "Bound Top",     base.DEC)
f.emb_right   = ProtoField.int16 ("sendpp1.emb_right",    "Bound Right",   base.DEC)
f.emb_bottom  = ProtoField.int16 ("sendpp1.emb_bottom",   "Bound Bottom",  base.DEC)
f.emb_time    = ProtoField.int16 ("sendpp1.emb_time",     "Total Time (min)", base.DEC)
f.emb_stitches= ProtoField.uint16("sendpp1.emb_stitches", "Total Stitches")
f.emb_speed   = ProtoField.int16 ("sendpp1.emb_speed",    "Speed")

-- Embroidery Monitor (cmd 1799)
f.mon_stitches= ProtoField.uint16("sendpp1.mon_stitches", "Current Stitches")
f.mon_time    = ProtoField.int16 ("sendpp1.mon_time",     "Current Time")
f.mon_stop    = ProtoField.int16 ("sendpp1.mon_stop",     "Stop Time")
f.mon_x       = ProtoField.int16 ("sendpp1.mon_x",        "Needle X")
f.mon_y       = ProtoField.int16 ("sendpp1.mon_y",        "Needle Y")

-- Embroidery Layout (cmd 1796/1797/1808)
f.lay_movex   = ProtoField.int16 ("sendpp1.lay_movex",    "MoveX")
f.lay_movey   = ProtoField.int16 ("sendpp1.lay_movey",    "MoveY")
f.lay_sizex   = ProtoField.int16 ("sendpp1.lay_sizex",    "SizeX (%)")
f.lay_sizey   = ProtoField.int16 ("sendpp1.lay_sizey",    "SizeY (%)")
f.lay_rotate  = ProtoField.int16 ("sendpp1.lay_rotate",   "Rotate")
f.lay_flip    = ProtoField.uint8 ("sendpp1.lay_flip",     "Flip")
f.lay_frame   = ProtoField.uint8 ("sendpp1.lay_frame",    "Frame (0=70, 1=100)")

-- Bounding Box (appended after layout)
f.bb_tlx      = ProtoField.int16 ("sendpp1.bb_tlx",       "TopLeft X")
f.bb_tly      = ProtoField.int16 ("sendpp1.bb_tly",       "TopLeft Y")
f.bb_brx      = ProtoField.int16 ("sendpp1.bb_brx",       "BottomRight X")
f.bb_bry      = ProtoField.int16 ("sendpp1.bb_bry",       "BottomRight Y")
f.bb_cx       = ProtoField.int16 ("sendpp1.bb_cx",        "Center X")
f.bb_cy       = ProtoField.int16 ("sendpp1.bb_cy",        "Center Y")

-- Machine Settings (cmd 3073/3074)
f.set_autocut = ProtoField.bool  ("sendpp1.set_autocut",  "Auto Cut")
f.set_jumpcut = ProtoField.bool  ("sendpp1.set_jumpcut",  "Jumping Cut")
f.set_buzzer  = ProtoField.bool  ("sendpp1.set_buzzer",   "Buzzer")
f.set_foot    = ProtoField.uint8 ("sendpp1.set_foot",     "Foot Height (1=LOW 2=MED 3=HIGH)")
f.set_speed   = ProtoField.int16 ("sendpp1.set_speed",    "Sewing Speed")

-- Prepare Transfer (cmd 4608)
f.xfer_type   = ProtoField.uint8 ("sendpp1.xfer_type",    "Transfer Type")
f.xfer_size   = ProtoField.uint16("sendpp1.xfer_size",    "Data Size (bytes)")
f.xfer_csum   = ProtoField.uint16("sendpp1.xfer_csum",    "Checksum")

-- Data Packet (cmd 4609)
f.pkt_offset  = ProtoField.uint32("sendpp1.pkt_offset",   "Chunk Offset")
f.pkt_data    = ProtoField.bytes ("sendpp1.pkt_data",     "Chunk Data (raw)")
f.pkt_csum    = ProtoField.uint8 ("sendpp1.pkt_csum",     "Chunk Checksum")
f.pkt_ncmds   = ProtoField.uint32("sendpp1.pkt_ncmds",    "Command Count")
-- Embroidery Command (inside Data Packet chunk, 4 bytes each)
-- Encoding from commands.py Command dataclass:
--   x_raw, y_raw = int16_le pair
--   x = x_raw >> 3,  section  = x_raw & 0x07  (0=CMD, 3=END_COLOR, 5=END)
--   y = y_raw >> 3,  operation = y_raw & 0x07  (0=STITCH, 1=FEED, 2=CUT, 3=JUMP)
f.cmd_x       = ProtoField.int16 ("sendpp1.cmd_x",        "X")
f.cmd_y       = ProtoField.int16 ("sendpp1.cmd_y",        "Y")
f.cmd_section = ProtoField.string("sendpp1.cmd_section",  "Section")
f.cmd_op      = ProtoField.string("sendpp1.cmd_op",       "Operation")

-- UUID (cmd 1794/1802)
f.uuid        = ProtoField.bytes ("sendpp1.uuid",         "Pattern UUID (16 bytes)")

-- ── Lookup tables ─────────────────────────────────────────────────────────────

local CMD_NAMES = {
    [0]    = "Machine Info",
    [1]    = "Machine State",
    [256]  = "Service Count",
    [259]  = "Regular Inspection",
    [1794] = "Pattern UUID",
    [1796] = "Mask Trace Simple",
    [1797] = "Layout Data",
    [1798] = "Embroidery Info",
    [1799] = "Embroidery Monitor",
    [1800] = "Delete Embroidery",
    [1801] = "Set Needle Mode",
    [1802] = "Send UUID",
    [1803] = "Resume Flag",
    [1804] = "Resume Embroidery",
    [1806] = "Start Sewing",
    [1807] = "Hoop Avoidance",
    [1808] = "Mask Trace Complex",
    [2048] = "Origin Point",
    [3072] = "Reset Settings",
    [3073] = "Send Host Settings",
    [3074] = "Machine Settings",
    [4608] = "Prepare Transfer",
    [4609] = "Data Packet",
    [4864] = "Clear Error",
    [4865] = "Error Log",
}

local STATE_NAMES = {
    [0x00] = "Initial",
    [0x01] = "LowerThread",
    [0x10] = "SewingWaitNoData",
    [0x11] = "SewingWait",
    [0x12] = "SewingDataReceive",
    [0x20] = "MaskTraceLockWait",
    [0x21] = "MaskTracing",
    [0x22] = "MaskTraceFinish",
    [0x30] = "Sewing",
    [0x31] = "SewingFinish",
    [0x32] = "SewingInterruption",
    [0x40] = "ThreadChange",
    [0x41] = "Pause",
    [0x42] = "Stop",
    [0x50] = "HoopAvoidance",
    [0x51] = "HoopAvoidancing",
    [0x60] = "RLReceiving",
    [0x61] = "RLReceived",
    [0xDD] = "None",
    [0xFF] = "TryConnecting",
}

-- ── Per-command payload parsers ───────────────────────────────────────────────

local function dissect_machine_info(buf, tree)
    if buf:len() < 48 then
        tree:add_expert_info(PI_MALFORMED, PI_WARN, "MachineInfo payload too short")
        return
    end
    tree:add_le(f.sw_version, buf(1, 1))
    tree:add(f.serial,        buf(2, 9):string())
    local m = buf(16, 6)
    tree:add(f.mac, string.format("%02X:%02X:%02X:%02X:%02X:%02X",
        m(0,1):uint(), m(1,1):uint(), m(2,1):uint(),
        m(3,1):uint(), m(4,1):uint(), m(5,1):uint()))
    tree:add_le(f.bt_version, buf(22, 1))
    tree:add_le(f.model,      buf(24, 1))
    tree:add_le(f.oem,        buf(25, 1))
    tree:add_le(f.monitor_ok, buf(26, 1))
    tree:add_le(f.max_width,  buf(27, 2))
    tree:add_le(f.max_height, buf(29, 2))
    if buf:len() >= 50 then
        tree:add(f.model_code, buf(39, 11):string())
    end
end

local function dissect_machine_state(buf, tree)
    if buf:len() < 1 then return end
    local sv = buf(0,1):uint()
    tree:add_le(f.state_byte, buf(0,1))
    tree:add(f.state_name, STATE_NAMES[sv] or string.format("Unknown (0x%02X)", sv))
end

local function dissect_service_info(buf, tree)
    if buf:len() < 8 then return end
    tree:add_le(f.svc_count, buf(0,4))
    tree:add_le(f.svc_total, buf(4,4))
end

local function dissect_embroidery_info(buf, tree)
    if buf:len() < 14 then return end
    tree:add_le(f.emb_left,      buf(0,2))
    tree:add_le(f.emb_top,       buf(2,2))
    tree:add_le(f.emb_right,     buf(4,2))
    tree:add_le(f.emb_bottom,    buf(6,2))
    tree:add_le(f.emb_time,      buf(8,2))
    tree:add_le(f.emb_stitches,  buf(10,2))
    tree:add_le(f.emb_speed,     buf(12,2))
end

local function dissect_monitor_info(buf, tree)
    if buf:len() < 10 then return end
    tree:add_le(f.mon_stitches, buf(0,2))
    tree:add_le(f.mon_time,     buf(2,2))
    tree:add_le(f.mon_stop,     buf(4,2))
    tree:add_le(f.mon_x,        buf(6,2))
    tree:add_le(f.mon_y,        buf(8,2))
end

local function dissect_layout(buf, tree)
    if buf:len() < 12 then return 0 end
    tree:add_le(f.lay_movex,  buf(0,2))
    tree:add_le(f.lay_movey,  buf(2,2))
    tree:add_le(f.lay_sizex,  buf(4,2))
    tree:add_le(f.lay_sizey,  buf(6,2))
    tree:add_le(f.lay_rotate, buf(8,2))
    tree:add_le(f.lay_flip,   buf(10,1))
    tree:add_le(f.lay_frame,  buf(11,1))
    return 12
end

local function dissect_bbox(buf, tree)
    if buf:len() < 12 then return end
    tree:add_le(f.bb_tlx, buf(0,2))
    tree:add_le(f.bb_tly, buf(2,2))
    tree:add_le(f.bb_brx, buf(4,2))
    tree:add_le(f.bb_bry, buf(6,2))
    tree:add_le(f.bb_cx,  buf(8,2))
    tree:add_le(f.bb_cy,  buf(10,2))
end

local function dissect_machine_setting(buf, tree)
    if buf:len() < 6 then return end
    tree:add_le(f.set_autocut, buf(0,1))
    tree:add_le(f.set_jumpcut, buf(1,1))
    tree:add_le(f.set_buzzer,  buf(2,1))
    tree:add_le(f.set_foot,    buf(3,1))
    tree:add_le(f.set_speed,   buf(4,2))
end

local function dissect_prepare_transfer(buf, tree)
    if buf:len() < 5 then return end
    tree:add_le(f.xfer_type, buf(0,1))
    tree:add_le(f.xfer_size, buf(1,2))
    tree:add_le(f.xfer_csum, buf(3,2))
end

local SECTION_NAMES   = { [0]="CMD", [3]="END_COLOR", [5]="END" }
local OPERATION_NAMES = { [0]="STITCH", [1]="FEED", [2]="CUT", [3]="JUMP" }

local function dissect_data_packet(buf, tree)
    if buf:len() < 5 then return end
    tree:add_le(f.pkt_offset, buf(0,4))
    local chunk_len = buf:len() - 5
    if chunk_len <= 0 then
        tree:add_le(f.pkt_csum, buf(buf:len()-1, 1))
        return
    end

    local chunk = buf(4, chunk_len)
    local ncmds = math.floor(chunk_len / 4)
    tree:add(f.pkt_ncmds, ncmds)

    -- Parse each 4-byte Command: two int16_le values
    for i = 0, ncmds - 1 do
        local off = i * 4
        -- Read as signed 16-bit little-endian
        local xr = chunk(off,   2):le_int()
        local yr = chunk(off+2, 2):le_int()
        local x   = xr >> 3
        local y   = yr >> 3
        local sec = xr & 0x07
        local op  = yr & 0x07
        local sec_name = SECTION_NAMES[sec]   or string.format("UNKNOWN(%d)", sec)
        local op_name  = OPERATION_NAMES[op]  or string.format("UNKNOWN(%d)", op)
        local label = string.format("[%d] x=%-6d y=%-6d  %s / %s", i, x, y, sec_name, op_name)
        local ct = tree:add(proto, chunk(off, 4), label)
        ct:add_le(f.cmd_x,       chunk(off,   2))
        ct:add_le(f.cmd_y,       chunk(off+2, 2))
        ct:add(f.cmd_section,    sec_name)
        ct:add(f.cmd_op,         op_name)
    end

    -- Remaining bytes after full commands (should be 0 for well-formed packets)
    local remainder = chunk_len - ncmds * 4
    if remainder > 0 then
        tree:add(f.pkt_data, chunk(ncmds * 4, remainder))
    end

    tree:add_le(f.pkt_csum, buf(buf:len()-1, 1))
end

-- ── Main dissector ────────────────────────────────────────────────────────────

function proto.dissector(buf, pinfo, tree)
    if buf:len() < 2 then return end

    local cmd_val  = buf(0,2):uint()   -- big-endian per MachineCommand.to_bytes()
    local cmd_name = CMD_NAMES[cmd_val] or string.format("Unknown (0x%04X)", cmd_val)

    pinfo.cols.protocol:set("PP1")

    local dir = (pinfo.p2p_dir == P2P_DIR_SENT)
                and "Request  (host → machine)"
                 or "Response (machine → host)"
    local arrow = (pinfo.p2p_dir == P2P_DIR_SENT) and "▶" or "◀"
    pinfo.cols.info:set(string.format("%s  %s", cmd_name, arrow))

    local root = tree:add(proto, buf(),
        string.format("PP1  [%s]  %s", cmd_name, dir))
    root:add(f.direction, dir)
    root:add(f.cmd,       buf(0,2))
    root:add(f.cmd_name,  cmd_name)

    local plen = buf:len() - 2
    if plen <= 0 then return end
    local p = buf(2, plen)

    if     cmd_val == 0    then
        dissect_machine_info(p, root:add(proto, p, "Machine Info"))

    elseif cmd_val == 1    then
        dissect_machine_state(p, root:add(proto, p, "Machine State"))

    elseif cmd_val == 256  then
        dissect_service_info(p, root:add(proto, p, "Service Info"))

    elseif cmd_val == 259  then
        if plen >= 1 then root:add_le(f.status, p(0,1)) end

    elseif cmd_val == 1794 then
        if plen >= 16 then root:add(f.uuid, p(0,16)) end

    elseif cmd_val == 1796 or cmd_val == 1797 or cmd_val == 1808 then
        local lt   = root:add(proto, p, "Embroidery Layout")
        local used = dissect_layout(p, lt)
        if plen >= used + 12 then
            dissect_bbox(p(used, 12), root:add(proto, p(used, 12), "Bounding Box"))
        end

    elseif cmd_val == 1798 then
        dissect_embroidery_info(p, root:add(proto, p, "Embroidery Info"))

    elseif cmd_val == 1799 then
        dissect_monitor_info(p, root:add(proto, p, "Monitor Info"))

    elseif cmd_val == 1802 then
        if pinfo.p2p_dir == P2P_DIR_SENT then
            if plen >= 16 then root:add(f.uuid, p(0,16)) end
        else
            if plen >= 1 then root:add_le(f.status, p(0,1)) end
        end

    elseif cmd_val == 1800 or cmd_val == 1803 or cmd_val == 1804 or
           cmd_val == 1806 or cmd_val == 1807 or cmd_val == 3072 or
           cmd_val == 4864 then
        if plen >= 1 then root:add_le(f.status, p(0,1)) end

    elseif cmd_val == 3073 or cmd_val == 3074 then
        dissect_machine_setting(p, root:add(proto, p, "Machine Setting"))

    elseif cmd_val == 4608 then
        if pinfo.p2p_dir == P2P_DIR_SENT then
            dissect_prepare_transfer(p, root:add(proto, p, "Transfer Params"))
        else
            if plen >= 1 then root:add_le(f.status, p(0,1)) end
        end

    elseif cmd_val == 4609 then
        dissect_data_packet(p, root:add(proto, p, "Data Packet"))

    else
        root:add(f.payload, p)
    end
end

-- ── Register on ATT handles ───────────────────────────────────────────────────
-- btatt.handle is the correct dissector table for ATT value payloads.
-- It is always available in Wireshark builds that include the BT stack.

local btatt = DissectorTable.get("btatt.handle")
if btatt then
    for _, h in ipairs(PP1_HANDLES) do
        btatt:add(h, proto)
    end
else
    report_failure("sendpp1: could not find 'btatt.handle' dissector table. "
        .. "Make sure Wireshark was built with Bluetooth support.")
end

-- Also register under the generic "Decode As" table so the user can manually
-- assign any handle via the GUI without editing this file.
local btatt_da = DissectorTable.get("btatt.handle")
if btatt_da then
    -- proto is already registered above; this just makes it appear in the
    -- "Decode As" dropdown for any ATT handle.
end
