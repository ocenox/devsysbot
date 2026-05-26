# DevSysBot

**Interview a clean host, get a reviewable plan, let a coding agent build it.**

DevSysBot is an interactive CLI that runs on a fresh Linux host and walks you through a
short set of decisions — which stack, database, version control, mail, secrets store,
safety nets — and turns your answers into a **hybrid implementation hypothesis**: a
reviewable Markdown document that is *also* a task list a coding agent (e.g. Claude Code)
can execute to provision a complete, secure development environment.

> **Human in the loop by design.** DevSysBot never builds anything itself. It interviews
> and writes the document. You review and approve it. Only then does the agent build —
> so the review step can never be skipped.

## Why "hybrid"

1. A **deterministic question tree** produces a complete skeleton offline (no API key
   needed — demo-safe).
2. **Claude** then refines that skeleton into a fluent, well-reasoned document (and can
   translate it). If there is no API key or the call fails, you keep the deterministic
   draft.

## Quick start

On a clean Ubuntu host you need either `curl` or `wget` to fetch the bootstrap (the
bootstrap installs everything else). A minimal Ubuntu may have neither.

With `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/ocenox/devsysbot/main/bootstrap.sh | bash
```

With `curl` (install it first if missing: `sudo apt update && sudo apt install -y curl`):

```bash
curl -fsSL https://raw.githubusercontent.com/ocenox/devsysbot/main/bootstrap.sh | bash
```

The bootstrap installs Python, Node and Claude Code, fetches DevSysBot into `/devsysbot`,
runs the interview, and writes the hypothesis to `/devsysbot/docs/`. It then prints a
ready-to-paste prompt to start the build with Claude Code. Nothing is written into `/code`
— the agent creates that as a ZFS mount and populates it afterwards.

### Run it manually

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m devsysbot                 # interactive
PYTHONPATH=src python -m devsysbot --defaults      # non-interactive (all defaults)
PYTHONPATH=src python -m devsysbot --no-refine     # skip the Claude step
```

Set `ANTHROPIC_API_KEY` to enable the Claude refinement step.

### Add a project later

To add a single application to an environment that already exists — either scaffolded from
a stack or cloned from an existing `.git` URL — run the focused add-project interview:

```bash
PYTHONPATH=src python -m devsysbot --add-project
```

It writes `ADD-PROJECT.md`; hand that to the agent and run the `add-project` skill. Only
infrastructure that is missing is provisioned (idempotent) — shared services are reused.

## What it asks about

Storage & ZFS snapshots · SMB with Windows "Previous Versions" · version control & Git
workflow · dev/build stages · host-native database · Docker & footprint · reverse proxy
(Apache vs Caddy) · DNS & TLS (incl. self-signed CA fallback) · mail & catch-all ·
secrets store (existing / Infisical / file fallback) · testing & CI · agent sandbox &
permissions · token/cost monitoring · auto-regenerated dashboard.

## The five safety nets

| Layer | Protects against | Mechanism |
|-------|------------------|-----------|
| ZFS snapshots (10 min) | overwritten, uncommitted changes | `zfs-auto-snapshot`; reachable from Windows via Samba shadow copies |
| Git + branch protection | lost commits, direct `main` writes | feature branches, MR/PR + review |
| Tests + CI | AI code that only looks runnable | lint/test/coverage gate before the build stage |
| Sandbox & permissions | uncontrolled agent actions | scoped writes, confirmations, secrets excluded from reads |
| Firewall & egress control | data exfiltration, credential theft | default-deny inbound; outbound can't reach cloud metadata, SMTP or private/prod networks |

## Repository layout

```
devsysbot/
├── bootstrap.sh            curl | bash entry point
├── README.md  LICENSE  requirements.txt  pyproject.toml
├── src/devsysbot/          the bot (Python package)
│   ├── __main__.py         orchestration & CLI
│   ├── prompt.py           UI layer (questionary → stdlib fallback)
│   ├── schema.py           the question tree
│   ├── wizard.py           runs the interview
│   ├── document.py         deterministic document generator
│   └── refine.py           optional Claude refinement
├── skills/                 Claude Code skills for the generated environment
│   ├── implement-hypothesis/  generate-dashboard/  add-project/
│   └── refresh-env/           secrets-guard/
└── templates/              settings.json + hooks/guard.sh for the agent sandbox
```

## Secrets

Secret *values* never enter the hypothesis document. If you enter secrets during the
interview they are staged only to the chosen store (or `/code/.secrets`, outside any repo,
`chmod 600`). The document lists secrets by **name** in a checklist. The agent sandbox
denies reading secret files and blocks hardcoding.

## License

MIT © OCENOX
