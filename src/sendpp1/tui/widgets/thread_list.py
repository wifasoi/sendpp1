"""Thread list widget — shows embroidery thread colors from the loaded pattern."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import VerticalScroll
from rich.text import Text


class ThreadItem(Static):
    """Single thread row: index, color swatch, hex, name."""

    active: reactive[bool] = reactive(False, layout=True)

    def __init__(self, index: int, color_hex: str, name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.thread_index = index
        self.color_hex = color_hex
        self.thread_name = name

    def render(self) -> Text:
        marker = " > " if self.active else "   "
        swatch = Text("\u2588\u2588", style=self.color_hex)
        line = (
            Text(f"{marker}{self.thread_index + 1:2d} ")
            + swatch
            + Text(f"  {self.color_hex}  {self.thread_name}")
        )
        if self.active:
            line.stylize("bold")
        return line

    def watch_active(self, value: bool) -> None:
        if value:
            self.add_class("thread-active")
        else:
            self.remove_class("thread-active")


class ThreadList(Widget):
    """Scrollable list of threads extracted from an EmbPattern."""

    DEFAULT_CSS = """
    ThreadList {
        width: 1fr;
        height: 1fr;
        border: round $accent;
    }
    ThreadList > #thread-header {
        height: 1;
        text-style: bold;
        color: $text-muted;
        padding: 0 1;
    }
    ThreadList VerticalScroll {
        height: 1fr;
    }
    .thread-active {
        background: $boost;
    }
    """

    active_thread: reactive[int] = reactive(-1)

    def compose(self) -> ComposeResult:
        yield Static("Threads", id="thread-header")
        yield VerticalScroll(id="thread-scroll")

    def set_threads(self, threadlist: list) -> None:
        """Populate from pyembroidery pattern.threadlist."""
        scroll = self.query_one("#thread-scroll", VerticalScroll)
        scroll.remove_children()
        self._items: list[ThreadItem] = []
        for i, thread in enumerate(threadlist):
            color_hex = (
                thread.hex_color()
                if hasattr(thread, "hex_color")
                else f"#{thread.color:06X}"
            )
            name = (
                getattr(thread, "description", "")
                or getattr(thread, "name", "")
                or "Thread"
            )
            item = ThreadItem(i, color_hex, name)
            self._items.append(item)
            scroll.mount(item)

    def watch_active_thread(self, old: int, new: int) -> None:
        if not hasattr(self, "_items"):
            return
        if 0 <= old < len(self._items):
            self._items[old].active = False
        if 0 <= new < len(self._items):
            self._items[new].active = True
            self._items[new].scroll_visible()
