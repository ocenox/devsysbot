"""UI-Abstraktion für den Wizard.

Nutzt `questionary` + `rich` für eine schöne Pfeiltasten-Bedienung, fällt aber
auf reine stdlib-`input()`-Eingaben zurück, falls die Pakete fehlen. So bleibt
der Assistent auch auf einem jungfräulichen System ohne `pip install` lauffähig
— wichtig für eine Live-Demo, bei der nichts schiefgehen darf.
"""

from __future__ import annotations

import os
from typing import Sequence

# OCENOX brand colours (see corporate identity).
_BLUE = "#295F7C"     # Ocean Blue — titles, frames
_ACCENT = "#3B8AB4"   # Horizon Blue — accents, wordmark
_DIM = "#6B7380"      # Fog Grey — secondary text
_AMBER = "#E8A13C"    # Amber — warnings

OCENOX_LOGO = r"""
   ___   ___ ___ _  _  _____  __
  / _ \ / __| __| \| |/ _ \ \/ /
 | (_) | (__| _|| .` | (_) >  <
  \___/ \___|___|_|\_|\___/_/\_\
        D E V   S Y S   B O T
"""

try:  # bevorzugte, hübsche Variante
    import questionary

    _HAS_QUESTIONARY = True
except ImportError:  # pragma: no cover - reiner Fallback-Pfad
    _HAS_QUESTIONARY = False

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel

    _console: "Console | None" = Console()
except ImportError:  # pragma: no cover
    _console = None


def clear() -> None:
    """Clear the screen for a clean, one-question-at-a-time feel."""
    if _console:
        _console.clear()
    else:
        os.system("cls" if os.name == "nt" else "clear")


def info(message: str) -> None:
    """Gibt eine Hinweiszeile aus."""
    if _console:
        _console.print(message)
    else:
        print(message)


def welcome(intro: str, disclaimer: str) -> None:
    """Show the logo, a short intro and the disclaimer on a clean screen."""
    clear()
    if _console:
        _console.print(OCENOX_LOGO, style=f"bold {_ACCENT}")
        _console.print(Panel(intro, border_style=_BLUE, title="What this is", title_align="left"))
        _console.print(Panel(disclaimer, border_style=_AMBER, title="Disclaimer", title_align="left"))
    else:
        print(OCENOX_LOGO)
        print(intro)
        print("\nDisclaimer: " + disclaimer)


def pause(message: str = "Press Enter to begin…") -> None:
    """Wait for the user to acknowledge the welcome screen."""
    try:
        input(f"\n{message} ")
    except EOFError:  # pragma: no cover
        pass


def header(title: str, subtitle: str = "", progress: str = "") -> None:
    """Clear and render a compact per-question header so each question stands alone."""
    clear()
    if _console:
        line = f"[bold {_ACCENT}]DevSysBot[/]  [{_DIM}]· by OCENOX[/]"
        if progress:
            line += f"   [{_DIM}]{progress}[/]"
        _console.print(line)
        _console.rule(style=_BLUE)
        _console.print(f"[bold {_BLUE}]{title}[/]")
        if subtitle:
            _console.print(f"[{_DIM}]{subtitle}[/]")
        _console.print()
    else:
        print(f"\n=== DevSysBot — {title} ===")
        if subtitle:
            print(subtitle)


def banner(title: str, subtitle: str = "") -> None:
    """Zeigt eine hervorgehobene Überschrift."""
    if _console:
        body = f"[bold]{title}[/bold]"
        if subtitle:
            body += f"\n[{_DIM}]{subtitle}[/]"
        _console.print(Panel(body, expand=False, border_style=_BLUE))
    else:
        print(f"\n=== {title} ===")
        if subtitle:
            print(subtitle)


def markdown(text: str) -> None:
    """Rendert Markdown (Vorschau der Hypothese)."""
    if _console:
        _console.print(Markdown(text))
    else:
        print(text)


def text(question: str, default: str = "") -> str:
    """Freitext-Eingabe."""
    if _HAS_QUESTIONARY:
        return (questionary.text(question, default=default).ask() or "").strip()
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default


def confirm(question: str, default: bool = True) -> bool:
    """Ja/Nein-Frage."""
    if _HAS_QUESTIONARY:
        result = questionary.confirm(question, default=default).ask()
        return bool(default if result is None else result)
    hint = "J/n" if default else "j/N"
    answer = input(f"{question} ({hint}): ").strip().lower()
    if not answer:
        return default
    return answer in {"j", "ja", "y", "yes"}


def select(question: str, choices: Sequence[str], default: str | None = None) -> str:
    """Einfachauswahl aus einer Liste."""
    if _HAS_QUESTIONARY:
        return questionary.select(
            question, choices=list(choices), default=default or choices[0]
        ).ask()
    print(f"\n{question}")
    for idx, choice in enumerate(choices, start=1):
        marker = " (Standard)" if choice == default else ""
        print(f"  {idx}) {choice}{marker}")
    while True:
        raw = input("Auswahl (Nummer): ").strip()
        if not raw and default:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print("Bitte eine gültige Nummer eingeben.")


def checkbox(question: str, choices: Sequence[str]) -> list[str]:
    """Mehrfachauswahl."""
    if _HAS_QUESTIONARY:
        return questionary.checkbox(question, choices=list(choices)).ask() or []
    print(f"\n{question} (Mehrfachauswahl, Nummern mit Komma getrennt)")
    for idx, choice in enumerate(choices, start=1):
        print(f"  {idx}) {choice}")
    raw = input("Auswahl: ").strip()
    picked: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(choices):
            picked.append(choices[int(part) - 1])
    return picked
