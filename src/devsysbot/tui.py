"""Textual front-end for the DevSysBot interview.

A full-screen TUI: a splash with the OCENOX logo (the real PNG, scaled on the fly with
rich-pixels — falling back to ASCII art, then a compact wordmark), an intro + disclaimer,
then one question per screen with Back/Next navigation.

This module imports ``textual`` at import time; ``wizard.run`` imports it lazily and falls
back to the plain rich/questionary flow if Textual (or this module) is unavailable — so the
tool still works on a bare host.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, RadioButton, RadioSet, SelectionList, Static
from textual.widgets.selection_list import Selection

from . import devices

_ASSETS = Path(__file__).parent / "assets"
_LOGO_PNG = _ASSETS / "ocenox-logo.png"
_LOGO_ASCII = _ASSETS / "ocenox-logo.txt"
MANUAL = "Other (enter manually)"

_WORDMARK = "O C E N O X   ·   DevSysBot"

INTRO = (
    "DevSysBot interviews you about a development environment and writes a reviewable "
    "implementation hypothesis — a document a coding agent (e.g. Claude Code) can then "
    "build into a complete, secure setup.\n\n"
    "It builds nothing itself. You answer a few questions, review the generated document, "
    "and only then hand it to the agent. Arrow keys to choose, Enter/Next to continue, "
    "Space to toggle multi-select."
)

DISCLAIMER = (
    "Provided as-is under the MIT license, with no warranty of any kind. You are solely "
    "responsible for what you run on your systems. Always review the generated document "
    "before letting an agent execute it."
)


def make_logo(max_width: int):
    """Return a renderable for the logo, scaled to ``max_width`` columns.

    Tries the real PNG via rich-pixels, then ASCII art, then a compact wordmark.
    """
    max_width = max(24, min(max_width, 120))
    try:
        from PIL import Image
        from rich_pixels import Pixels

        img = Image.open(_LOGO_PNG).convert("RGBA")
        w0, h0 = img.size
        target_w = max_width
        target_h = max(2, round(h0 * (target_w / w0)))
        if target_h % 2:  # half-block cells are 2 px tall
            target_h += 1
        img = img.resize((target_w, target_h))
        return Pixels.from_image(img)
    except Exception:
        pass
    try:
        return Text(_LOGO_ASCII.read_text(encoding="utf-8"), style="#3B8AB4")
    except Exception:
        return Text(_WORDMARK, style="bold #3B8AB4")


def _matches(condition: dict[str, Any], answers: dict[str, Any]) -> bool:
    for key, expected in condition.items():
        actual = answers.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


class WelcomeScreen(Screen):
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="welcome"):
            yield Static(id="logo")
            yield Static(INTRO, id="intro", classes="panel")
            yield Static(Text(DISCLAIMER), id="disclaimer", classes="panel warn")
            with Horizontal(id="buttons"):
                yield Button("Begin  ▶", id="begin", variant="primary")
                yield Button("Quit", id="quit")

    def on_mount(self) -> None:
        self.query_one("#logo", Static).update(make_logo(self.app.size.width - 4))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "begin":
            self.app.begin()
        else:
            self.app.action_cancel()


class QuestionScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    def compose(self) -> ComposeResult:
        section, q = self.app.flat[self.index]
        stored = self.app.answers.get(q["key"])
        with VerticalScroll(id="question"):
            yield Static(f"DevSysBot · by OCENOX     question {len(self.app.trail)}", classes="brand")
            yield Static(section["title"], classes="title")
            if section.get("subtitle"):
                yield Static(section["subtitle"], classes="subtitle")
            yield Static(q["message"], classes="prompt")
            if q.get("footprint"):
                yield Static(Text("ℹ " + q["footprint"]), classes="footprint")
            yield from self._inputs(q, stored)
            with Horizontal(id="buttons"):
                if len(self.app.trail) > 1:
                    yield Button("◀ Back", id="back")
                yield Button("Next ▶", id="next", variant="primary")

    def _inputs(self, q: dict[str, Any], stored: Any) -> ComposeResult:
        qtype = q["type"]
        default = q.get("default")

        if q.get("dynamic") == "block_devices":
            rows = devices.list_block_devices()
            if rows:
                with RadioSet(id="choice"):
                    for r in rows:
                        yield RadioButton(r)
                    yield RadioButton(MANUAL)
                yield Input(value=(stored if isinstance(stored, str) else default) or "",
                            placeholder="…or type a device path", id="manual")
            else:
                yield Input(value=(stored if isinstance(stored, str) else default) or "",
                            placeholder="device path, e.g. /dev/sdb", id="text")
            return

        if qtype == "text":
            val = "" if q.get("secret") else (stored if isinstance(stored, str) else default) or ""
            yield Input(value=val, password=bool(q.get("secret")), id="text")
        elif qtype == "confirm":
            cur = bool(stored) if isinstance(stored, bool) else bool(default)
            with RadioSet(id="choice"):
                yield RadioButton("Yes", value=cur)
                yield RadioButton("No", value=not cur)
        elif qtype == "select":
            choices = q["choices"]
            cur = stored if stored in choices else default
            with RadioSet(id="choice"):
                for c in choices:
                    yield RadioButton(c, value=(c == cur))
        elif qtype == "checkbox":
            choices = q["choices"]
            picked = stored if isinstance(stored, list) else (default or [])
            yield SelectionList(*[Selection(c, c, c in picked) for c in choices], id="multi")

    def _read(self, q: dict[str, Any]) -> Any:
        qtype = q["type"]
        if q.get("dynamic") == "block_devices":
            try:
                rs = self.query_one("#choice", RadioSet)
            except Exception:
                return self.query_one("#text", Input).value.strip()
            idx = rs.pressed_index
            label = rs.pressed_button.label.plain if rs.pressed_button else ""
            if label == MANUAL or idx < 0:
                return self.query_one("#manual", Input).value.strip()
            return devices.device_path(label)
        if qtype == "text":
            return self.query_one("#text", Input).value.strip()
        if qtype == "confirm":
            return self.query_one("#choice", RadioSet).pressed_index == 0
        if qtype == "select":
            rs = self.query_one("#choice", RadioSet)
            return q["choices"][rs.pressed_index] if rs.pressed_index >= 0 else q.get("default")
        if qtype == "checkbox":
            return list(self.query_one("#multi", SelectionList).selected)
        return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next":
            self.app.store(self.index, self._read(self.app.flat[self.index][1]))
            self.app.advance(self.index)
        elif event.button.id == "back":
            self.action_back()

    def action_back(self) -> None:
        if len(self.app.trail) > 1:
            self.app.trail.pop()
            self.app.pop_screen()


class WizardApp(App):
    CSS = """
    Screen { background: #0e1620; }
    #welcome, #question { padding: 1 2; }
    #logo { width: auto; height: auto; content-align: center middle; }
    .panel { border: round #295F7C; padding: 1 2; margin: 1 0 0 0; }
    .warn { border: round #E8A13C; }
    .brand { color: #3B8AB4; text-style: bold; }
    .title { color: #3B8AB4; text-style: bold; margin: 1 0 0 0; }
    .subtitle { color: #6B7380; }
    .prompt { text-style: bold; margin: 1 0; }
    .footprint { color: #6B7380; margin: 0 0 1 0; }
    #buttons { height: auto; align-horizontal: right; margin: 1 0 0 0; }
    Button { margin: 0 0 0 2; }
    RadioSet, SelectionList, Input { margin: 0 0 1 0; }
    """
    BINDINGS = [Binding("ctrl+c", "cancel", "Quit")]

    def __init__(self, sections: list[dict[str, Any]]) -> None:
        super().__init__()
        self.sections = sections
        self.flat: list[tuple[dict, dict]] = [(s, q) for s in sections for q in s["questions"]]
        self.answers: dict[str, Any] = {}
        self.secrets: dict[str, str] = {}
        self.trail: list[int] = []

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

    def _next_visible(self, after: int) -> int | None:
        for j in range(after + 1, len(self.flat)):
            cond = self.flat[j][1].get("when")
            if not cond or _matches(cond, self.answers):
                return j
        return None

    def begin(self) -> None:
        first = self._next_visible(-1)
        if first is None:
            self.exit((self.answers, self.secrets))
            return
        self.pop_screen()  # remove welcome
        self.trail = [first]
        self.push_screen(QuestionScreen(first))

    def store(self, index: int, value: Any) -> None:
        q = self.flat[index][1]
        if q.get("secret"):
            if value:
                self.secrets[q["key"]] = value
            self.answers[q["key"]] = "<stored in secret store>" if value else ""
        else:
            self.answers[q["key"]] = value

    def advance(self, index: int) -> None:
        nxt = self._next_visible(index)
        if nxt is None:
            self.exit((self.answers, self.secrets))
        else:
            self.trail.append(nxt)
            self.push_screen(QuestionScreen(nxt))

    def action_cancel(self) -> None:
        self.exit(None)


def run(sections: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, str]] | None:
    """Run the TUI; return (answers, secrets), or None if the user cancelled."""
    return WizardApp(sections).run()
