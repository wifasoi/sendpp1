"""Machine status widget — shows connection state, sewing progress, and live monitor data."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, ProgressBar
from rich.text import Text

from sendpp1.core.machine import SewingMachineStatus, EmbroideryMonitorInfo, EmbroideryInfo


_SEWING_STATES = {
    SewingMachineStatus.Sewing,
    SewingMachineStatus.SewingDataReceive,
}

_STATE_LABELS: dict[SewingMachineStatus, tuple[str, str]] = {
    SewingMachineStatus.Initial:            ("Initial",           "dim"),
    SewingMachineStatus.LowerThread:        ("Lower Thread",      "yellow"),
    SewingMachineStatus.SewingWaitNoData:   ("Waiting (no data)", "yellow"),
    SewingMachineStatus.SewingWait:         ("Ready",             "bright_green"),
    SewingMachineStatus.SewingDataReceive:  ("Receiving Data",    "cyan"),
    SewingMachineStatus.MaskTraceLockWait:  ("Mask Trace Lock",   "yellow"),
    SewingMachineStatus.MaskTraceing:       ("Mask Tracing",      "cyan"),
    SewingMachineStatus.MaskTraceFinish:    ("Mask Trace Done",   "green"),
    SewingMachineStatus.Sewing:             ("Sewing",            "bold bright_green"),
    SewingMachineStatus.SewingFinish:       ("Finished!",         "bold green"),
    SewingMachineStatus.SewingInterruption: ("Interrupted",       "bold red"),
    SewingMachineStatus.ThreadChange:       ("Thread Change",     "bold magenta"),
    SewingMachineStatus.Pause:              ("Paused",            "yellow"),
    SewingMachineStatus.Stop:               ("Stopped",           "red"),
    SewingMachineStatus.HoopAvoidance:      ("Hoop Avoidance",    "yellow"),
    SewingMachineStatus.RLReceived:         ("RL Received",       "dim"),
    SewingMachineStatus.RLReceiving:        ("RL Receiving",      "dim"),
    SewingMachineStatus.HoopAvoidanceing:   ("Avoiding Hoop",     "yellow"),
    SewingMachineStatus.none:               ("Unknown",           "dim"),
    SewingMachineStatus.TryConnecting:      ("Connecting...",     "cyan"),
}


def _fmt_time(minutes: int) -> str:
    if minutes < 0:
        return "--:--"
    h, m = divmod(minutes, 60)
    return f"{h}:{m:02d}" if h else f"{m} min"


class MachineStatus(Widget):
    """Right-hand pane: connection indicator, state, progress bar, monitor info."""

    DEFAULT_CSS = """
    MachineStatus {
        width: 1fr;
        height: 1fr;
        border: round $accent;
        padding: 0 1;
    }
    MachineStatus > #status-header {
        height: 1;
        text-style: bold;
        color: $text-muted;
    }
    MachineStatus > .stat-row {
        height: 1;
    }
    MachineStatus > #progress-row {
        height: 1;
        margin: 1 0;
    }
    MachineStatus ProgressBar {
        width: 1fr;
    }
    """

    connected: reactive[bool] = reactive(False)
    status: reactive[SewingMachineStatus | None] = reactive(None)
    total_stitches: reactive[int] = reactive(0)
    current_stitches: reactive[int] = reactive(0)
    current_time: reactive[int] = reactive(0)
    total_time: reactive[int] = reactive(0)
    speed: reactive[int] = reactive(0)
    stitch_x: reactive[int] = reactive(0)
    stitch_y: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        yield Static("Machine", id="status-header")
        yield Static("", id="conn-row", classes="stat-row")
        yield Static("", id="state-row", classes="stat-row")
        yield ProgressBar(total=100, show_eta=False, show_percentage=True, id="progress-bar")
        yield Static("", id="stitch-row", classes="stat-row")
        yield Static("", id="time-row", classes="stat-row")
        yield Static("", id="speed-row", classes="stat-row")
        yield Static("", id="pos-row", classes="stat-row")

    def watch_connected(self, value: bool) -> None:
        label = "Connected" if value else "Disconnected"
        color = "green" if value else "red"
        self.query_one("#conn-row", Static).update(
            Text.assemble(("Connection: ", ""), (label, color))
        )

    def watch_status(self, value: SewingMachineStatus | None) -> None:
        if value is None:
            self.query_one("#state-row", Static).update("Status: --")
            return
        label, color = _STATE_LABELS.get(value, (value.name, "yellow"))
        self.query_one("#state-row", Static).update(
            Text.assemble(("Status: ", ""), (label, color))
        )

    def watch_current_stitches(self, value: int) -> None:
        self._update_progress()
        total = self.total_stitches or "?"
        self.query_one("#stitch-row", Static).update(f"Stitches: {value} / {total}")

    def watch_total_stitches(self, value: int) -> None:
        self._update_progress()

    def watch_current_time(self, value: int) -> None:
        self.query_one("#time-row", Static).update(
            f"Time: {_fmt_time(value)} / ~{_fmt_time(self.total_time)}"
        )

    def watch_total_time(self, value: int) -> None:
        self.query_one("#time-row", Static).update(
            f"Time: {_fmt_time(self.current_time)} / ~{_fmt_time(value)}"
        )

    def watch_speed(self, value: int) -> None:
        self.query_one("#speed-row", Static).update(f"Speed: {value} spm")

    def watch_stitch_x(self, value: int) -> None:
        self.query_one("#pos-row", Static).update(f"Position: ({value}, {self.stitch_y})")

    def watch_stitch_y(self, value: int) -> None:
        self.query_one("#pos-row", Static).update(f"Position: ({self.stitch_x}, {value})")

    def _update_progress(self) -> None:
        bar = self.query_one("#progress-bar", ProgressBar)
        if self.total_stitches > 0:
            bar.update(total=self.total_stitches, progress=self.current_stitches)
        else:
            bar.update(total=100, progress=0)

    def apply_emb_info(self, info: EmbroideryInfo) -> None:
        self.total_stitches = info.total_stitches
        self.total_time = info.total_time
        self.speed = info.speed

    def apply_monitor(self, mon: EmbroideryMonitorInfo) -> None:
        self.current_stitches = mon.current_stitches
        self.current_time = mon.current_time
        self.stitch_x = mon.current_stitch_x
        self.stitch_y = mon.current_stitch_y
