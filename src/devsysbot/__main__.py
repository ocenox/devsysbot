"""DevSysBot entry point: interview → draft → optional Claude refinement → review → write.

Usage:
    python -m devsysbot [options]

Options:
    --output PATH       Where to write the hypothesis (default: ./IMPLEMENTATION-HYPOTHESIS.md)
    --secrets-dir PATH  Where captured secret values are staged (default: /code/.secrets)
    --defaults          Non-interactive: answer everything with defaults (smoke test / CI)
    --no-refine         Skip the Claude refinement step
    -h, --help          Show this help
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

from . import document, prompt, refine, wizard


def _require_tty() -> None:
    """Fail clearly if there is no interactive terminal (e.g. raw `curl | bash`)."""
    if not sys.stdin.isatty():
        sys.stderr.write(
            "DevSysBot needs an interactive terminal.\n"
            "If you started it via `curl ... | bash`, the installer reconnects the terminal\n"
            "for you. To run it directly, use an interactive shell, or pass --defaults for a\n"
            "non-interactive run with default answers.\n"
        )
        raise SystemExit(2)


def _stage_secrets(secrets: dict[str, str], secrets_dir: str) -> str | None:
    """Write captured secret values to the staging store with restrictive permissions.

    Returns the file path, or None if there were no secrets. Values land here ONLY — never
    in the hypothesis document. The agent later imports them into the chosen store.
    """
    if not secrets:
        return None
    target = Path(secrets_dir)
    target.mkdir(parents=True, exist_ok=True)
    env_path = target / "devsysbot.captured.env"
    lines = [f"{key.replace('.', '_').upper()}={value}" for key, value in secrets.items()]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:  # POSIX only; no-op on Windows
        os.chmod(target, stat.S_IRWXU)
        os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)
    except (PermissionError, OSError):
        pass
    return str(env_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devsysbot", add_help=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--secrets-dir", default="/code/.secrets")
    parser.add_argument("--defaults", action="store_true")
    parser.add_argument("--no-refine", action="store_true")
    parser.add_argument("--add-project", action="store_true",
                        help="Add a single application to an existing environment")
    args = parser.parse_args(argv)

    if not args.defaults:
        _require_tty()

    if args.add_project:
        from .schema import APP_SECTIONS
        answers, secrets = wizard.run(non_interactive=args.defaults, sections=APP_SECTIONS)
        secret_keys = sorted(secrets.keys())
        draft = document.build_add_project(answers, secret_keys)
        default_out = "ADD-PROJECT.md"
    else:
        answers, secrets = wizard.run(non_interactive=args.defaults)
        secret_keys = sorted(secrets.keys())
        draft = document.build(answers, secret_keys)
        default_out = "IMPLEMENTATION-HYPOTHESIS.md"

    if args.output is None:
        args.output = default_out
    language = answers.get("meta.doc_language", "English")

    final = draft
    if not args.no_refine:
        if refine.is_available():
            if not args.defaults:
                prompt.info("\n[cyan]Refining with Claude…[/cyan]")
            final, err = refine.refine(draft, answers, language=language)
            if err and not args.defaults:
                prompt.info(f"[dim]{err}[/dim]")
        elif not args.defaults:
            prompt.info("[dim]No ANTHROPIC_API_KEY set — using the deterministic draft.[/dim]")

    # Review step (interactive only)
    if not args.defaults:
        prompt.banner("Preview", "Review the draft below, then confirm to write it.")
        prompt.markdown(final)
        if not prompt.confirm("Write this document?", default=True):
            prompt.info("Aborted. Nothing written.")
            return 1

    out_path = Path(args.output)
    out_path.write_text(final, encoding="utf-8")

    staged = _stage_secrets(secrets, args.secrets_dir)
    if not args.defaults:
        prompt.info(f"\n[green]Wrote[/green] {out_path}")
        if staged:
            prompt.info(f"[green]Staged {len(secrets)} secret(s) to[/green] {staged} "
                        f"[dim](import into your store; never commit)[/dim]")
        prompt.info("\nNext: review the document, then run your coding agent to build the environment.")
    else:
        print(f"wrote {out_path}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stderr.write("\nAborted. Nothing written.\n")
        sys.exit(130)
