# sendpp1

An open-source replacement for the Android app that controls the **Brother Skitch PP1** embroidery machine over Bluetooth Low Energy.

Includes a terminal UI for sending embroidery files and monitoring sewing progress, a core BLE protocol library, a Wireshark dissector for the PP1 protocol, and a custom pyembroidery writer for the PP1 stitch format.

## Quick start

```bash
# With Nix (recommended)
nix develop              # enter dev shell
sendpp1-tui design.pes   # run the TUI

# Or install directly
nix run .#tui -- design.pes

# Without Nix
pip install -e .
sendpp1-tui design.pes --device AA:BB:CC:DD:EE:FF
```

## Project structure

```
src/sendpp1/
  core/
    machine.py          BLE protocol abstraction (connect, transfer, sew)
    commands.py         PP1 command definitions
    main.py             CLI utility for quick tests
  tui/
    app.py              Textual-based terminal UI
    widgets/            Status panel, thread list, log view
  gui/                  Qt GUI (experimental, requires PySide6)
  pyembroidery/
    pp1Writer.py        Custom writer: converts EmbPattern -> PP1 binary
wireshark/
    sendpp1.lua         Wireshark Lua dissector for the PP1 BLE protocol
```

## Terminal UI

The TUI is the primary interface. It accepts any embroidery format that pyembroidery can read (PES, DST, JEF, EXP, etc.), converts it to the PP1 binary format, and transfers it over BLE.

```
sendpp1-tui <file> [--device <MAC>] [--log <logfile>]
```

Features:

- BLE device scanning and connection
- Automatic format conversion via pyembroidery
- Real-time machine state polling (keeps the 3s timeout alive)
- Thread color list with active-thread highlighting
- Sewing progress: stitch count, time, speed, needle position
- Start, pause, resume, delete controls
- Full debug logging to file with `--log`

Keybindings: **s** Send, **g** Start, **p** Pause, **r** Resume, **d** Delete, **q** Quit.

## BLE protocol

The PP1 exposes a single GATT service (`A76EB9E0-...`) with two characteristics acting as a serial link:

| UUID (suffix) | Direction | Role |
|---|---|---|
| `A76EB9E2` | Host -> Machine | Write channel |
| `A76EB9E1` | Machine -> Host | Read channel |

Every packet is: `command (2 bytes, big-endian) + payload`. The host writes a command, then reads the response. All writes use ATT Write Request (with BLE-level ACK), never Write Command. The machine disconnects after ~3 seconds of silence.

### Transfer sequence

Sending a design follows this order:

1. **Delete** old data (cmd `0x0708`)
2. **Prepare transfer** (cmd `0x1200`): announce size and checksum
3. **Data packets** (cmd `0x1201`): chunked stitch data, each with offset and per-chunk checksum
4. **Layout** (cmd `0x0705`): position, scale, rotation, bounding box
5. **UUID** (cmd `0x070A`): assign a pattern identifier
6. **Start** (cmd `0x070E`): begin sewing

### Prepare transfer format

```
type(1) = 0x03 | size(4, uint32 LE) | checksum(2, uint16 LE)
```

Total file checksum is `sum(all_bytes) & 0xFFFF`.

### Data packet format

```
offset(4, uint32 LE) | stitch_data(N) | checksum(1, uint8)
```

Per-chunk checksum is `sum(chunk_bytes) & 0xFF`. The machine has a fixed receive buffer of ~27 bytes regardless of negotiated BLE MTU, so the maximum stitch data per chunk is 20 bytes (5 stitch commands). Must be 4-byte aligned.

### Command table

| Cmd | Name | Description |
|-----|------|-------------|
| 0 | Machine Info | Serial, firmware, model, max dimensions |
| 1 | Machine State | Current status byte (see states below) |
| 256 | Service Count | Lifetime service/stitch counters |
| 1797 | Layout Data | Position, scale, rotation, bounding box |
| 1798 | Embroidery Info | Total stitches, time, speed after transfer |
| 1799 | Monitor | Live stitch count, time, needle position |
| 1800 | Delete Embroidery | Clear stored pattern |
| 1802 | Send UUID | Assign pattern identifier |
| 1803 | Resume Flag | Check if sewing can be resumed |
| 1806 | Start Sewing | Begin sewing the loaded pattern |
| 4608 | Prepare Transfer | Announce data size and checksum |
| 4609 | Data Packet | Chunked stitch data |

### Machine states

| Code | State |
|------|-------|
| `0x10` | SewingWaitNoData — connected, no pattern loaded |
| `0x11` | SewingWait — pattern loaded, ready to start |
| `0x30` | Sewing — actively sewing |
| `0x31` | SewingFinish — pattern complete |
| `0x40` | ThreadChange — waiting for thread swap |
| `0x41` | Pause |
| `0x32` | SewingInterruption |

## PP1 stitch format

Each stitch command is 4 bytes (two int16 LE values):

```
x_raw (int16 LE) | y_raw (int16 LE)

x = x_raw >> 3        (absolute coordinate)
section = x_raw & 0x7 (0=normal, 3=color change, 5=end)

y = y_raw >> 3        (absolute coordinate)
operation = y_raw & 0x7 (0=stitch, 1=feed, 2=cut, 3=jump)
```

## Wireshark dissector

The `wireshark/sendpp1.lua` plugin decodes the PP1 protocol in Wireshark. It registers on ATT handles and parses all known commands with field-level detail.

Install it:

```bash
# Nix
nix build .#wireshark-plugin
ls result/lib/wireshark/plugins/sendpp1.lua

# Manual
cp wireshark/sendpp1.lua ~/.local/lib/wireshark/plugins/
```

Or use the dev shell where `WIRESHARK_PLUGIN_DIR` is set automatically.

## Nix flake

```bash
nix build            # build sendpp1-tui
nix build .#tui      # same
nix build .#wireshark-plugin  # Wireshark dissector
nix develop          # dev shell: python, uv, ruff, tshark
```

The dev shell includes Python 3.12 with all dependencies, uv for fast package management, ruff for linting, and wireshark-cli for pcap analysis.

## License

See [LICENSE](LICENSE).
