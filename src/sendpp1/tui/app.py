"""sendpp1 TUI — Textual-based interface for the Brother Skitch PP1.

Usage:
    sendpp1-tui <embroidery_file> [--device <MAC>]

If --device is omitted the app scans for PP1 machines and lets you pick one.
"""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from typing import Callable

import click
from loguru import logger
from textual import on, work

# Remove loguru's default stderr sink so it doesn't paint over the TUI.
logger.remove()

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static, SelectionList
from textual.worker import Worker, WorkerState

from bleak import BleakClient, BleakScanner

from sendpp1.core.machine import (
    EmbroideryMachine,
    EmbroideryLayout,
    EmbroideryBoundingBox,
    SewingMachineStatus,
)
from sendpp1.tui.widgets import ThreadList, MachineStatus, LogView

import pyembroidery
from sendpp1.pyembroidery import write_pp1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ACTIVE_SEWING = {
    SewingMachineStatus.Sewing,
    SewingMachineStatus.SewingDataReceive,
}

_READY_STATES = {
    SewingMachineStatus.SewingWait,
}

_PAUSED_STATES = {
    SewingMachineStatus.Pause,
    SewingMachineStatus.SewingInterruption,
    SewingMachineStatus.ThreadChange,
}


def _build_color_change_map(pattern: pyembroidery.EmbPattern) -> list[tuple[int, int]]:
    """Return a list of (stitch_index, thread_index) breakpoints."""
    breakpoints: list[tuple[int, int]] = []
    thread_idx = 0
    stitch_count = 0
    for _, _, cmd in pattern.stitches:
        if cmd == pyembroidery.COLOR_CHANGE:
            thread_idx += 1
            breakpoints.append((stitch_count, thread_idx))
        elif cmd == pyembroidery.STITCH:
            stitch_count += 1
    return breakpoints


def _thread_for_stitch(breakpoints: list[tuple[int, int]], current: int) -> int:
    """Given a stitch count, return the thread index that is active."""
    thread_idx = 0
    for stitch_at, tidx in breakpoints:
        if current >= stitch_at:
            thread_idx = tidx
        else:
            break
    return thread_idx


# ---------------------------------------------------------------------------
# Device scan screen
# ---------------------------------------------------------------------------

class DeviceScanScreen(ModalScreen[str | None]):
    """Modal that scans for BLE devices and lets the user pick one."""

    DEFAULT_CSS = """
    DeviceScanScreen {
        align: center middle;
    }
    DeviceScanScreen > Vertical {
        width: 60;
        height: auto;
        max-height: 24;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    DeviceScanScreen > Vertical > Horizontal {
        height: auto;
        align: center middle;
    }
    DeviceScanScreen > Vertical > Horizontal > Button {
        margin: 1 1 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Scanning for PP1 devices...", id="scan-label")
            yield SelectionList(id="device-list")
            with Horizontal():
                yield Button("Connect", variant="primary", id="btn-connect", disabled=True)
                yield Button("Rescan", id="btn-rescan")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_mount(self) -> None:
        self._scan()

    @work(exclusive=True)
    async def _scan(self) -> None:
        label = self.query_one("#scan-label", Static)
        sel = self.query_one("#device-list", SelectionList)
        btn = self.query_one("#btn-connect", Button)

        label.update("Scanning...")
        btn.disabled = True
        sel.clear_options()

        pp1_service = "a76eb9e0-f3ac-4990-84cf-3a94d2426b2b"
        candidates: list = []

        def _detection_callback(device, adv_data):
            svc_uuids = [str(u).lower() for u in (adv_data.service_uuids or [])]
            name = (device.name or "").lower()
            addr = device.address.lower()
            if (
                pp1_service in svc_uuids
                or "1a:4b:e8" in addr
                or ("brother" in name and "pp1" in name)
            ):
                candidates.append(device)

        scanner = BleakScanner(detection_callback=_detection_callback)
        await scanner.start()
        await asyncio.sleep(5.0)
        await scanner.stop()

        seen: set[str] = set()
        unique = []
        for d in candidates:
            if d.address not in seen:
                seen.add(d.address)
                unique.append(d)

        if unique:
            for d in unique:
                name = d.name or "Unknown"
                sel.add_option((f"{name}  [{d.address}]", d.address))
            label.update(f"Found {len(unique)} device(s)")
            btn.disabled = False
        else:
            label.update("No PP1 devices found. Try Rescan.")

    @on(Button.Pressed, "#btn-connect")
    def _connect(self) -> None:
        sel = self.query_one("#device-list", SelectionList)
        selected = sel.selected
        if selected:
            self.dismiss(selected[0])
        else:
            self.notify("Select a device first", severity="warning")

    @on(Button.Pressed, "#btn-rescan")
    def _rescan(self) -> None:
        self._scan()

    @on(Button.Pressed, "#btn-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class SendPP1App(App):
    """TUI for loading embroidery files and sending them to the PP1.

    Architecture: ONE single worker (_ble_loop) owns the BLE connection.
    It alternates between:
      - polling machine_state every ~1 s (keeping the connection alive)
      - executing queued commands (transfer, start, resume, delete)
    """

    TITLE = "sendpp1"
    SUB_TITLE = "Brother Skitch PP1 Controller"

    CSS = """
    /* ── Overall layout ─────────────────────────────────── */
    Screen {
        layout: vertical;
    }

    #body {
        height: 1fr;
    }

    #left-col {
        width: 30;
        min-width: 26;
    }
    #right-col {
        width: 1fr;
    }

    /* ── File info card ─────────────────────────────────── */
    #file-info {
        height: auto;
        max-height: 7;
        border: round $accent;
        padding: 0 1;
        color: $text;
    }

    /* ── Log ────────────────────────────────────────────── */
    #bottom-log {
        height: 12;
        min-height: 6;
    }

    /* ── Button bar ─────────────────────────────────────── */
    #button-bar {
        height: auto;
        min-height: 3;
        max-height: 3;
        padding: 0 1;
        background: $surface;
    }
    #button-bar Button {
        margin: 0 1;
        min-width: 12;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "send_file", "Send", show=True),
        Binding("g", "start_sewing", "Start", show=True),
        Binding("p", "pause", "Pause", show=True),
        Binding("r", "resume", "Resume", show=True),
        Binding("d", "delete", "Delete", show=True),
    ]

    def __init__(self, file_path: str | None = None, device: str | None = None) -> None:
        super().__init__()
        self._file_path = file_path
        self._device_addr = device
        self._pattern: pyembroidery.EmbPattern | None = None
        self._pp1_data: bytes | None = None
        self._color_map: list[tuple[int, int]] = []
        self._machine: EmbroideryMachine | None = None
        self._client: BleakClient | None = None
        self._running = False
        self._transferring = False  # guard against double-send
        self._cmd_queue: asyncio.Queue[Callable] = asyncio.Queue()

    # ── Compose ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="left-col"):
                yield Static("No file loaded", id="file-info")
                yield ThreadList()
            with Vertical(id="right-col"):
                yield MachineStatus()
                yield LogView(id="bottom-log")
        with Horizontal(id="button-bar"):
            yield Button("Connect", variant="primary", id="btn-connect")
            yield Button("Send", variant="success", id="btn-send", disabled=True)
            yield Button("Start", variant="warning", id="btn-start", disabled=True)
            yield Button("Pause", id="btn-pause", disabled=True)
            yield Button("Resume", id="btn-resume", disabled=True)
            yield Button("Delete", variant="error", id="btn-delete", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        if self._file_path:
            self._load_file(self._file_path)
        if self._device_addr:
            self._connect_device(self._device_addr)

    # ── File loading ─────────────────────────────────────────────────────

    def _load_file(self, path: str) -> None:
        log = self.query_one(LogView)
        try:
            self._pattern = pyembroidery.read(path)
        except Exception as exc:
            log.log(f"Failed to read file: {exc}", "error")
            return

        if not self._pattern or not self._pattern.stitches:
            log.log("File contains no stitch data", "error")
            return

        buf = BytesIO()
        write_pp1(self._pattern, buf)
        self._pp1_data = buf.getvalue()
        self._color_map = _build_color_change_map(self._pattern)

        n_stitches = sum(1 for _, _, c in self._pattern.stitches if c == pyembroidery.STITCH)
        n_colors = len(self._pattern.threadlist)
        bounds = self._pattern.bounds()
        w = (bounds[2] - bounds[0]) / 10
        h = (bounds[3] - bounds[1]) / 10
        fname = Path(path).name

        self.query_one("#file-info", Static).update(
            f"File: {fname}\n"
            f"Stitches: {n_stitches:,}\n"
            f"Colors: {n_colors}\n"
            f"Size: {w:.1f} x {h:.1f} mm"
        )

        self.query_one(ThreadList).set_threads(self._pattern.threadlist)
        if n_colors > 0:
            self.query_one(ThreadList).active_thread = 0

        log.log(f"Loaded {fname} ({n_stitches:,} stitches, {n_colors} colors)", "success")
        self._refresh_buttons()

    # ── BLE connection ───────────────────────────────────────────────────

    def action_quit(self) -> None:
        self._running = False
        self.exit()

    @on(Button.Pressed, "#btn-connect")
    def _on_connect_pressed(self) -> None:
        if self._device_addr:
            self._connect_device(self._device_addr)
        else:
            self.push_screen(DeviceScanScreen(), callback=self._on_device_selected)

    def _on_device_selected(self, address: str | None) -> None:
        if address:
            self._device_addr = address
            self._connect_device(address)

    @work(exclusive=True, group="ble")
    async def _connect_device(self, address: str) -> None:
        log = self.query_one(LogView)
        status = self.query_one(MachineStatus)
        log.log(f"Connecting to {address}...")

        try:
            self._client = BleakClient(address)
            await self._client.connect()
            self._machine = EmbroideryMachine(self._client)
            status.connected = True
            log.log(f"Connected to {address}", "success")

            info = await self._machine.machine_info
            if info:
                log.log(
                    f"Machine: {info.ModelCode}  S/N: {info.SerialNumber}  "
                    f"FW: {info.SoftwareVersion}  Max: {info.MaxWidth}x{info.MaxHeight}",
                    "info",
                )

            self.query_one("#btn-connect", Button).label = "Reconnect"
            self._refresh_buttons()

            self._running = True
            self._ble_loop()

        except Exception as exc:
            log.log(f"Connection failed: {exc}", "error")
            status.connected = False

    # ── BLE loop — single owner of the BLE connection ────────────────────

    @work(exclusive=True, group="ble-loop")
    async def _ble_loop(self) -> None:
        log = self.query_one(LogView)
        status_widget = self.query_one(MachineStatus)
        thread_list = self.query_one(ThreadList)
        prev_status: SewingMachineStatus | None = None

        while self._running and self._machine:
            # 1. Drain and execute queued commands
            while not self._cmd_queue.empty():
                try:
                    cmd_coro = self._cmd_queue.get_nowait()
                    await cmd_coro(self._machine, log)
                except Exception as exc:
                    log.log(f"Command error: {exc}", "error")

            # 2. Poll machine state
            try:
                state = await self._machine.machine_state
                if state is None:
                    await asyncio.sleep(1)
                    continue

                status_widget.status = state

                if state != prev_status:
                    log.log(f"State -> {state.name}")
                    prev_status = state
                    self._refresh_buttons()

                # 3. Monitor while sewing / thread change
                if state in _ACTIVE_SEWING or state == SewingMachineStatus.ThreadChange:
                    try:
                        mon = await self._machine.monitor_info
                        if mon:
                            status_widget.apply_monitor(mon)
                            tidx = _thread_for_stitch(self._color_map, mon.current_stitches)
                            thread_list.active_thread = tidx
                            if state == SewingMachineStatus.ThreadChange:
                                log.log(f"Thread change -> #{tidx + 1}", "warning")
                    except Exception:
                        pass

            except Exception as exc:
                log.log(f"Poll error: {exc}", "error")
                status_widget.connected = False
                await asyncio.sleep(3)
                try:
                    if self._client:
                        await self._client.connect()
                        status_widget.connected = True
                        log.log("Reconnected", "success")
                except Exception:
                    pass

            await asyncio.sleep(1)

    # ── Button state management ──────────────────────────────────────────

    def _refresh_buttons(self) -> None:
        """Update all button enabled/disabled states based on current context."""
        connected = self._machine is not None
        has_data = self._pp1_data is not None
        status = self.query_one(MachineStatus).status

        # Send: need connection + file loaded + not already transferring
        self.query_one("#btn-send", Button).disabled = not (
            connected and has_data and not self._transferring
        )
        # Start: machine must be in SewingWait
        self.query_one("#btn-start", Button).disabled = status not in _READY_STATES
        # Pause: only while actively sewing
        self.query_one("#btn-pause", Button).disabled = status not in _ACTIVE_SEWING
        # Resume: only when paused / thread change / interruption
        self.query_one("#btn-resume", Button).disabled = status not in _PAUSED_STATES
        # Delete: need connection
        self.query_one("#btn-delete", Button).disabled = not connected

    # ── Command factories — push async callables onto the queue ──────────

    @on(Button.Pressed, "#btn-send")
    def _on_send_pressed(self) -> None:
        self.action_send_file()

    def action_send_file(self) -> None:
        if not self._pp1_data or not self._machine or self._transferring:
            return
        self._transferring = True
        self._refresh_buttons()

        pp1_data = bytearray(self._pp1_data)
        status_widget = self.query_one(MachineStatus)

        async def _transfer(machine: EmbroideryMachine, log: LogView) -> None:
            try:
                log.log("Deleting old embroidery data...")
                await machine.delete_emboridery()
                log.log("Old data cleared", "success")

                log.log(f"Transferring {len(pp1_data):,} bytes...")
                ok = await machine.transfer(pp1_data)
                if not ok:
                    log.log("Transfer FAILED — machine rejected data", "error")
                    return
                log.log("Transfer complete", "success")

                layout = EmbroideryLayout()
                bbox = EmbroideryBoundingBox()
                await machine.send_layout(layout, bbox)
                log.log("Layout sent", "success")

                pattern_uuid = uuid4()
                await machine.set_pattern_uuid(pattern_uuid)
                log.log(f"Pattern UUID set", "info")

                try:
                    emb_info = await machine.embroidery_info
                    if emb_info:
                        status_widget.apply_emb_info(emb_info)
                        log.log(
                            f"Machine reports {emb_info.total_stitches} stitches, "
                            f"~{emb_info.total_time} min",
                            "info",
                        )
                except Exception:
                    pass
            finally:
                self._transferring = False
                self._refresh_buttons()

        self._cmd_queue.put_nowait(_transfer)

    @on(Button.Pressed, "#btn-start")
    def _on_start_pressed(self) -> None:
        self.action_start_sewing()

    def action_start_sewing(self) -> None:
        if not self._machine:
            return

        async def _start(machine: EmbroideryMachine, log: LogView) -> None:
            await machine.start_emboridery()
            log.log("Sewing started", "success")

        self._cmd_queue.put_nowait(_start)

    @on(Button.Pressed, "#btn-pause")
    def _on_pause_pressed(self) -> None:
        self.action_pause()

    def action_pause(self) -> None:
        log = self.query_one(LogView)
        log.log("Pause: use the physical button on the machine", "warning")

    @on(Button.Pressed, "#btn-resume")
    def _on_resume_pressed(self) -> None:
        self.action_resume()

    def action_resume(self) -> None:
        if not self._machine:
            return

        async def _resume(machine: EmbroideryMachine, log: LogView) -> None:
            can = await machine.can_resume
            if can:
                await machine.resume_emboridery()
                log.log("Resumed sewing", "success")
            else:
                log.log("Machine says: cannot resume", "warning")

        self._cmd_queue.put_nowait(_resume)

    @on(Button.Pressed, "#btn-delete")
    def _on_delete_pressed(self) -> None:
        self.action_delete()

    def action_delete(self) -> None:
        if not self._machine:
            return

        async def _delete(machine: EmbroideryMachine, log: LogView) -> None:
            await machine.delete_emboridery()
            log.log("Embroidery data deleted from machine", "success")

        self._cmd_queue.put_nowait(_delete)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.command()
@click.argument("file", required=False, type=click.Path(exists=True))
@click.option("--device", "-d", default=None, help="BLE MAC address (skip scan)")
@click.option(
    "--log", "-l",
    default=None,
    type=click.Path(),
    help="Write a full debug log to this file (e.g. --log session.log)",
)
def main(file: str | None, device: str | None, log: str | None) -> None:
    """sendpp1 TUI — send embroidery files to the Brother Skitch PP1."""
    if log:
        logger.add(
            log,
            level="TRACE",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
            rotation="5 MB",
            encoding="utf-8",
        )
        logger.info("Logging to {}", log)
    app = SendPP1App(file_path=file, device=device)
    app.run()


if __name__ == "__main__":
    main()
