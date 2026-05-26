"""Optional hybrid step: let Claude polish the deterministic document.

This is the "hybrid" half of the hybrid implementation hypothesis. The deterministic
generator (``document.py``) produces a complete, offline-safe skeleton; Claude turns it
into a fluent, well-reasoned document and, if requested, translates it.

The refinement is best-effort: if there is no API key, no SDK, or the call fails, the
caller keeps the deterministic document. Secret *values* are never sent — only the
non-secret answers and the already secret-free skeleton.
"""

from __future__ import annotations

import os
from typing import Any

MODEL = "claude-opus-4-7"

_SYSTEM = (
    "You are a senior platform engineer. You receive a deterministic draft of an "
    "'Implementation Hypothesis' for setting up a development environment, plus the raw "
    "interview answers. Improve it into a clear, professional document a human can review "
    "and a coding agent can execute.\n"
    "Rules:\n"
    "- Keep the exact section structure and the agent task checkboxes.\n"
    "- Add concrete, correct commands and short rationales where helpful.\n"
    "- Never invent secret values; keep secrets as names only.\n"
    "- Never use the former product brand name; use neutral terms or the OCENOX umbrella brand.\n"
    "- Emphasise the four safety nets (ZFS snapshots, Git/branch protection, tests/CI, sandbox)."
)


def is_available() -> bool:
    """True if a refinement attempt makes sense (key present and SDK importable)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def refine(draft: str, answers: dict[str, Any], language: str = "English") -> tuple[str, str | None]:
    """Return (document, error). On success error is None and document is refined.

    On any failure the original ``draft`` is returned together with a short error string,
    so the caller can fall back gracefully and tell the user what happened.
    """
    if not is_available():
        return draft, "no ANTHROPIC_API_KEY or anthropic SDK; using deterministic draft"

    try:
        import anthropic

        client = anthropic.Anthropic()
        # answers are already secret-free (secret values were never stored here)
        summary = "\n".join(f"- {k}: {v}" for k, v in answers.items())
        lang_note = "" if language == "English" else f"\nWrite the final document in {language}."

        message = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Interview answers:\n{summary}\n\n"
                        f"Deterministic draft to improve:\n\n{draft}{lang_note}\n\n"
                        "Return only the improved Markdown document."
                    ),
                }
            ],
        )
        text = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
        return (text.strip() or draft), None
    except Exception as exc:  # pragma: no cover - network/SDK errors
        return draft, f"refinement failed ({exc}); using deterministic draft"
