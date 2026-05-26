"""Runs the interview: walks the question tree, evaluates branching, collects answers.

Returns two maps kept strictly apart:

* ``answers``  — every non-secret answer; this is what the document generator and the
  Claude refinement see.
* ``secrets``  — secret values entered during the interview. These are returned
  separately so the caller can write them to the chosen secret store and never into
  the hypothesis document.
"""

from __future__ import annotations

from typing import Any

from . import devices, prompt
from .schema import SECTIONS

_MANUAL = "Other (enter manually)"

WELCOME_INTRO = (
    "DevSysBot interviews you about a development environment and writes a reviewable "
    "[bold]implementation hypothesis[/] — a document a coding agent (e.g. Claude Code) can "
    "then build into a complete, secure setup.\n\n"
    "It [bold]builds nothing itself[/]. You answer a few questions, review the generated "
    "document, and only then hand it to the agent. Each question stands on its own — "
    "use the arrow keys to choose, Enter to confirm, Space to toggle multi-select."
)

DISCLAIMER = (
    "Provided as-is under the MIT license, with [bold]no warranty of any kind[/]. You are "
    "solely responsible for what you run on your systems. Always review the generated "
    "document before letting an agent execute it."
)


def _matches(condition: dict[str, Any], answers: dict[str, Any]) -> bool:
    """Return True if every entry in ``condition`` matches the collected answers."""
    for key, expected in condition.items():
        actual = answers.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


def _ask(question: dict[str, Any], answers: dict[str, Any]) -> Any:
    qtype = question["type"]
    message = question["message"]
    default = question.get("default")

    if question.get("dynamic") == "block_devices":
        rows = devices.list_block_devices()
        if rows:
            choice = prompt.select(message, rows + [_MANUAL], default=rows[0])
            if choice == _MANUAL:
                return prompt.text("Enter device path", default=default or "")
            return devices.device_path(choice)
        # No detection possible (e.g. non-Linux) — fall back to free text.
        return prompt.text(message + " (could not detect devices; enter path)", default=default or "")

    if qtype == "text":
        return prompt.text(message, default=default or "")
    if qtype == "confirm":
        return prompt.confirm(message, default=bool(default))
    if qtype == "select":
        return prompt.select(message, question["choices"], default=default)
    if qtype == "checkbox":
        return prompt.checkbox(message, question["choices"])
    raise ValueError(f"Unknown question type: {qtype}")


def _default_value(question: dict[str, Any]) -> Any:
    """Resolve the default for non-interactive runs."""
    if question["type"] == "checkbox":
        return question.get("default", [])
    if question["type"] == "confirm":
        return bool(question.get("default"))
    return question.get("default", "")


def run(
    non_interactive: bool = False,
    sections: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Execute the interview and return (answers, secrets).

    ``sections`` selects the question set (defaults to the full ``SECTIONS``; pass
    ``APP_SECTIONS`` for the add-project flow). When ``non_interactive`` is True every
    question is answered with its default and no secrets are captured — for tests/CI.
    """
    sections = sections if sections is not None else SECTIONS
    answers: dict[str, Any] = {}
    secrets: dict[str, str] = {}

    if not non_interactive:
        # Preferred: full-screen Textual UI. Fall back to the rich/questionary flow if
        # Textual is unavailable or the app fails to start — so the tool always works.
        try:
            from . import tui

            result = tui.run(sections)
            if result is None:
                raise KeyboardInterrupt  # user cancelled the TUI
            return result
        except KeyboardInterrupt:
            raise
        except Exception:
            pass  # fall through to the plain flow

        prompt.welcome(WELCOME_INTRO, DISCLAIMER)
        prompt.pause()

    asked = 0
    for section in sections:
        for question in section["questions"]:
            condition = question.get("when")
            if condition and not _matches(condition, answers):
                continue

            if non_interactive:
                value = _default_value(question)
                if question.get("secret"):
                    answers[question["key"]] = ""
                else:
                    answers[question["key"]] = value
                continue

            asked += 1
            prompt.header(section["title"], section.get("subtitle", ""), progress=f"Question {asked}")

            if question.get("footprint"):
                prompt.info(f"[#6B7380]ℹ {question['footprint']}[/]\n")

            value = _ask(question, answers)

            if question.get("secret"):
                # Never store secret values in `answers`; keep only a placeholder marker
                # so the document can list the secret by name without exposing the value.
                if value:
                    secrets[question["key"]] = value
                answers[question["key"]] = "<stored in secret store>" if value else ""
            else:
                answers[question["key"]] = value

    return answers, secrets
