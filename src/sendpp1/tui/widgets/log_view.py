"""Scrolling event log widget."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, RichLog


class LogView(Widget):
    """Scrolling log that captures machine events, transfer progress, errors."""

    DEFAULT_CSS = """
    LogView {
        width: 1fr;
        height: 1fr;
        border: round $accent;
    }
    LogView > #log-header {
        height: 1;
        text-style: bold;
        color: $text-muted;
        padding: 0 1;
    }
    LogView RichLog {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Log", id="log-header")
        yield RichLog(highlight=True, markup=True, wrap=True, id="log-content")

    def log(self, message: str, level: str = "info") -> None:
        """Append a timestamped message.

        level: info | success | warning | error
        """
        ts = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "info": "dim",
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
        }
        style = color_map.get(level, "")
        rich_log = self.query_one("#log-content", RichLog)
        rich_log.write(f"[{style}]{ts} {message}[/{style}]")
