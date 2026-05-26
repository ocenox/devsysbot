"""Deterministic generator for the IMPLEMENTATION-HYPOTHESIS document.

Turns the interview answers into a structured, reviewable Markdown document that is
*also* a task list a coding agent can execute. The output never contains secret
values — only secret names and where to source them.

The skeleton is always produced in English (concept decision). When the user picks
German, the optional Claude refinement step translates it; the deterministic skeleton
stays English so the tool works fully offline regardless of language choice.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _g(answers: dict[str, Any], key: str, default: Any = "") -> Any:
    return answers.get(key, default)


def _yes(answers: dict[str, Any], key: str) -> bool:
    return bool(answers.get(key))


def _decisions_table(a: dict[str, Any]) -> str:
    rows = [
        ("Project", _g(a, "project.name")),
        ("Stack", _g(a, "project.stack")),
        ("ZFS /code partition", "yes" if _yes(a, "zfs.enabled") else "no"),
        ("Auto-snapshots (10 min)", "zfs-auto-snapshot" if _yes(a, "zfs.autosnapshot") else "no"),
        ("SMB + Windows shadow copies", "yes" if _yes(a, "smb.shadow_copy") else "no"),
        ("VCS", _g(a, "vcs.platform")),
        ("Branching", _g(a, "vcs.branching", "n/a")),
        ("Build stage", "yes" if _yes(a, "stages.build") else "no"),
        ("Database (host-native)", _g(a, "db.engine")),
        ("Docker for app stacks", "yes" if _yes(a, "docker.enabled") else "no"),
        ("Portainer", "yes" if _yes(a, "docker.portainer") else "no"),
        ("Reverse proxy", _g(a, "proxy.kind")),
        ("DNS control", _g(a, "dns.control")),
        ("TLS source", _g(a, "tls.source")),
        ("Mail", _g(a, "mail.kind")),
        ("Secret store", _g(a, "secrets.location")),
        ("Min. test coverage", f"{_g(a, 'testing.coverage_min')}%"),
        ("CI platform", _g(a, "ci.platform")),
        ("Token/cost monitoring", "yes" if _yes(a, "monitoring.enabled") else "no"),
        ("Dashboard", "yes" if _yes(a, "dashboard.enabled") else "no"),
    ]
    out = ["| Decision | Choice |", "|----------|--------|"]
    out += [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(out)


def _architecture(a: dict[str, Any]) -> str:
    name = _g(a, "project.name", "app")
    domain = _g(a, "stages.domain", "example.com")
    proxy = _g(a, "proxy.kind").split(" ")[0] or "Proxy"
    db = _g(a, "db.engine")
    lines = [
        "```",
        "Ubuntu host",
        " ├─ /code on ZFS  ──► 10-min snapshots (recover uncommitted work)" if _yes(a, "zfs.enabled") else " ├─ /code (plain filesystem)",
    ]
    if _yes(a, "smb.shadow_copy"):
        lines.append(" │     └─ Samba (shadow_copy2) ──► Windows 'Previous Versions'")
    if db != "None":
        lines.append(f" ├─ {db} (host-native, shared across stages)")
    lines.append(f" ├─ {proxy} reverse proxy ──► TLS for *.{domain}")
    if _yes(a, "docker.enabled"):
        lines.append(f" ├─ Docker: {name} dev stage (bind-mount /code/{name})")
        if _yes(a, "stages.build"):
            lines.append(f" │          {name} build stage (CI-built image)")
    if _g(a, "mail.kind") != "None":
        lines.append(f" ├─ Mail: {_g(a, 'mail.kind')}")
    lines.append(f" └─ Secret store: {_g(a, 'secrets.location')}")
    lines.append("```")
    return "\n".join(lines)


def _safety_nets(a: dict[str, Any]) -> str:
    rows = []
    if _yes(a, "zfs.autosnapshot"):
        rows.append("- **ZFS snapshots (10 min)** — recover accidentally overwritten, "
                    "uncommitted changes; reachable from Windows via Samba shadow copies.")
    if _yes(a, "vcs.protect_main") or _yes(a, "sandbox.protect_main"):
        rows.append("- **Git + branch protection** — feature branches only, MR/PR + review on main.")
    if _g(a, "ci.platform") != "None":
        rows.append(f"- **Automated tests + CI** — lint/test gate, min "
                    f"{_g(a, 'testing.coverage_min')}% coverage before the build stage.")
    rows.append("- **Sandbox & permissions** — agent scoped to /code/<project>, "
                "confirmation for destructive ops, secrets excluded from reads.")
    return "\n".join(rows)


def _agent_tasks(a: dict[str, Any]) -> str:
    name = _g(a, "project.name", "app")
    phases: list[tuple[str, list[str]]] = []

    if _yes(a, "zfs.enabled"):
        steps = [
            f"Create ZFS pool `{_g(a, 'zfs.pool')}` on `{_g(a, 'zfs.device')}` and dataset "
            f"`{_g(a, 'zfs.dataset')}` mounted at `/code`.",
        ]
        if _yes(a, "zfs.autosnapshot"):
            steps.append("Install `zfs-auto-snapshot`; set the `frequent` interval to 10 minutes; "
                         "configure retention (10-min×24h, hourly×7d, daily×30d).")
        phases.append(("Storage / ZFS", steps))

    if _yes(a, "smb.enabled"):
        steps = [f"Install Samba; share `/code` (auth: {_g(a, 'smb.auth')})."]
        if _yes(a, "smb.shadow_copy"):
            steps.append("Enable `vfs objects = shadow_copy2` with `shadow:snapdir = .zfs/snapshot` "
                         "and a format matching the zfs-auto-snapshot names, so snapshots appear "
                         "as Windows 'Previous Versions'.")
        phases.append(("SMB / Shadow copies", steps))

    base = ["Install Docker CE + Compose plugin." if _yes(a, "docker.enabled") else "Install base packages."]
    if _g(a, "db.engine") != "None":
        base.append(f"Install {_g(a, 'db.engine')} as a host service; create `{name}_dev`"
                    + (f" and `{name}_build`" if _yes(a, "stages.build") else "") + " databases.")
        if _yes(a, "docker.enabled"):
            base.append("Configure DB for container access (listen address, pg_hba/grants, "
                        "`host.docker.internal`).")
    phases.append(("Host base & database", base))

    proxy = _g(a, "proxy.kind")
    proxy_steps = [f"Set up the reverse proxy: {proxy}."]
    if "Apache" in proxy:
        proxy_steps.append("Host the dashboard, DB admin UI and webmail directly on Apache "
                           "(PHP-FPM) instead of separate containers.")
    tls = _g(a, "tls.source")
    if "Self-signed" in tls:
        if _yes(a, "tls.ca_reuse"):
            proxy_steps.append("Reuse the existing local Root CA and sign certificates for all stage domains.")
        else:
            proxy_steps.append("Generate a local Root CA and sign certificates for all stage domains.")
        if _yes(a, "tls.ca_download"):
            proxy_steps.append("Publish the Root CA on the dashboard with install instructions "
                               "(Windows/macOS/Linux/browser).")
    elif "Let's Encrypt" in tls:
        proxy_steps.append(f"Configure ACME ({tls}).")
    elif "Bring your own" in tls:
        proxy_steps.append(f"Expect certificates at `{_g(a, 'tls.byo_path')}`.")
    phases.append(("Reverse proxy & TLS", proxy_steps))

    if _g(a, "mail.kind") != "None":
        mail_steps = [f"Deploy {_g(a, 'mail.kind')}."]
        if _g(a, "mail.kind").startswith("docker-mailserver"):
            mail_steps.append(f"Provision per-user IMAP accounts and a catch-all mailbox "
                              f"`{_g(a, 'mail.catchall')}` that collects unassigned / would-be-external mail "
                              + ("(outbound relay enabled)." if _yes(a, "mail.outbound") else "(closed: mail never leaves the host)."))
            if _yes(a, "mail.webmail"):
                mail_steps.append("Add Roundcube webmail.")
        phases.append(("Mail", mail_steps))

    app_steps = [f"Create the dev stage for `{name}` ({_g(a, 'project.stack')})."]
    if _yes(a, "docker.enabled"):
        app_steps.append(f"Bind-mount `/code/{name}` into the dev container; pick a port; wire DB/mail hosts.")
    if _yes(a, "docker.portainer"):
        app_steps.append("Start Portainer.")
    phases.append(("Application stack", app_steps))

    if _g(a, "ci.platform") != "None":
        ci_steps = [f"Configure {_g(a, 'ci.platform')}: lint → test (min "
                    f"{_g(a, 'testing.coverage_min')}% coverage) → deploy build stage."]
        if _yes(a, "ci.browser_tests"):
            ci_steps.append("Include browser/E2E tests.")
        phases.append(("CI pipeline", ci_steps))

    sec = _g(a, "secrets.location")
    sec_steps = []
    if "Infisical" in sec:
        sec_steps.append("Deploy Infisical (Docker); create a project and a machine identity for the agent; "
                         "use `infisical run -- <cmd>` for runtime injection.")
    elif "existing" in sec:
        sec_steps.append("Connect to the existing secret store; reference secrets by name only.")
    else:
        sec_steps.append("Create `/code/.secrets` (chmod 700, files 600), outside any repo, in `.gitignore`"
                         + ("; encrypt with sops+age." if _yes(a, "secrets.encrypt_files") else "."))
    sec_steps.append("Install `.claude/settings.json` with: redaction hook, no-hardcoding rule, "
                     "read-deny on `/code/.secrets/**`"
                     + (", pre-commit gitleaks scan." if _yes(a, "sandbox.secret_scan") else "."))
    phases.append(("Secrets & agent sandbox", sec_steps))

    if _yes(a, "monitoring.enabled"):
        mon = ["Enable token/cost logging for agent sessions."]
        if _g(a, "monitoring.budget"):
            mon.append(f"Warn when monthly spend exceeds ${_g(a, 'monitoring.budget')}.")
        phases.append(("Token & cost monitoring", mon))

    if _yes(a, "dashboard.enabled"):
        dash = ["Generate the dashboard from a single source of truth, styled with the OCENOX "
                "corporate identity (Montserrat, brand palette, logo)."]
        if _yes(a, "dashboard.auto_regen"):
            dash.append("Auto-regenerate it whenever services change (systemd path/timer or post-start hook).")
        phases.append(("Dashboard", dash))

    out = []
    n = 1
    for title, steps in phases:
        out.append(f"### Phase {n}: {title}")
        for s in steps:
            out.append(f"- [ ] {s}")
        out.append("")
        n += 1
    return "\n".join(out).rstrip()


def _secrets_checklist(a: dict[str, Any], secret_keys: list[str]) -> str:
    if not secret_keys:
        return "_No secrets were captured during the interview. Add required secrets to the store as needed._"
    store = _g(a, "secrets.location")
    lines = [f"The following secrets must live in the secret store ({store}) — never in this document or any repo:", ""]
    label = {
        "vcs.token": "VCS access token",
        "dns.api_token": "DNS provider API token",
    }
    for key in secret_keys:
        lines.append(f"- `{key}` — {label.get(key, 'secret value')}")
    return "\n".join(lines)


def _assumptions(a: dict[str, Any]) -> str:
    items = ["Target host is a clean Ubuntu system; the operator runs the agent with sudo where needed."]
    if _yes(a, "zfs.enabled"):
        items.append(f"Disk `{_g(a, 'zfs.device')}` is available and may be formatted for ZFS — confirm before running.")
    if _g(a, "dns.control") != "No DNS control (local only)":
        items.append(f"Domain `{_g(a, 'stages.domain')}` is under your control via: {_g(a, 'dns.control')}.")
    if _g(a, "vcs.platform") == "GitLab (self-hosted)":
        items.append(f"GitLab instance reachable at `{_g(a, 'vcs.instance_url')}`.")
    return "\n".join(f"- {i}" for i in items)


def build(answers: dict[str, Any], secret_keys: list[str]) -> str:
    """Build the full Markdown document."""
    name = _g(answers, "project.name", "app")
    desc = _g(answers, "project.description") or "(no description provided)"
    today = date.today().isoformat()

    return f"""# Implementation Hypothesis — {name}

> Generated by DevSysBot on {today}. **Review and edit this document, then hand it to a
> coding agent (Claude Code) to build the environment.** It contains secret *names* only —
> never secret *values*.

**Project:** {name}
**Description:** {desc}
**Summary:** A single Ubuntu host running {_g(answers, 'project.stack')} with host-native
{_g(answers, 'db.engine')}, app stacks {'in Docker' if _yes(answers, 'docker.enabled') else 'on the host'},
behind {_g(answers, 'proxy.kind').split(' (')[0]}, with ZFS snapshots, CI tests and a sandboxed agent as safety nets.

---

## 1. Decisions

{_decisions_table(answers)}

---

## 2. Target architecture

{_architecture(answers)}

---

## 3. Assumptions & open points

{_assumptions(answers)}

---

## 4. Safety nets

{_safety_nets(answers)}

---

## 5. Agent task list

Work through the phases in order. Tick each box as you complete it. Do not write to `main`;
do not hardcode secret values; never print secret files.

{_agent_tasks(answers)}

---

## 6. Acceptance criteria

- [ ] All chosen services are running (`docker ps` / `systemctl status`).
- [ ] Health URLs reachable for each stage over TLS.
- [ ] `zfs list -t snapshot` shows recent 10-minute snapshots.
- [ ] CI pipeline is green (lint + tests at the required coverage).
- [ ] No secret values appear in any repo, script or log.

---

## 7. Secrets checklist

{_secrets_checklist(answers, secret_keys)}
"""
