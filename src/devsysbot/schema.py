"""Declarative question tree for the DevSysBot interview.

Each section maps to a block of the concept document. Questions are plain data so
the tree stays easy to read, extend and review during the talk. Branching is
expressed with a ``when`` predicate evaluated against the answers collected so far.

Conventions
-----------
* ``key``      unique answer key (dotted, e.g. ``db.engine``)
* ``type``     one of ``text | confirm | select | checkbox | info``
* ``message``  the question shown to the user
* ``default``  default value (string / bool / list)
* ``choices``  for ``select`` / ``checkbox``
* ``when``     optional ``{key: value}`` or ``{key: [values]}``; the question is
               only asked when every entry matches the current answers
* ``secret``   if true, the value is a secret: it must go to the secret store and
               NEVER into the generated hypothesis document
* ``footprint`` optional note shown to nudge the user about resource cost

Defaults follow the OCENOX reference setup but every option stays freely choosable
(generic-with-OCENOX-defaults, per the concept decisions).
"""

from __future__ import annotations

from typing import Any

# Stacks generally well-suited to AI coding agents (from the recommendation table).
STACKS = [
    "Laravel + Livewire (PHP)",
    "Next.js + TypeScript",
    "Django (Python)",
    "FastAPI + React (Python)",
    "Ruby on Rails",
    "T3 Stack (TypeScript)",
    "SvelteKit (TypeScript)",
    "Spring Boot + React (Java)",
    "Custom / other",
]

# A section is a titled group of questions.
SECTIONS: list[dict[str, Any]] = [
    {
        "id": "meta",
        "title": "Interview language & basics",
        "questions": [
            {
                "key": "meta.doc_language",
                "type": "select",
                "message": "Language of the generated IMPLEMENTATION-HYPOTHESIS.md",
                "choices": ["English", "German"],
                "default": "English",
            },
            {
                "key": "project.name",
                "type": "text",
                "message": "Project name (used for paths, DBs, domains)",
                "default": "myapp",
            },
            {
                "key": "project.description",
                "type": "text",
                "message": "One-line project description",
                "default": "",
            },
            {
                "key": "project.stack",
                "type": "select",
                "message": "Application stack",
                "choices": STACKS,
                "default": STACKS[0],
            },
            {
                "key": "project.stack_custom",
                "type": "text",
                "message": "Describe your custom stack",
                "default": "",
                "when": {"project.stack": "Custom / other"},
            },
        ],
    },
    {
        "id": "storage",
        "title": "Storage & safety net (ZFS)",
        "subtitle": "Versioned filesystem for /code — recover overwritten, uncommitted changes.",
        "questions": [
            {
                "key": "zfs.enabled",
                "type": "confirm",
                "message": "Put /code on a separate ZFS partition (versioned filesystem)?",
                "default": True,
            },
            {
                "key": "zfs.pool",
                "type": "text",
                "message": "ZFS pool name",
                "default": "tank",
                "when": {"zfs.enabled": True},
            },
            {
                "key": "zfs.dataset",
                "type": "text",
                "message": "ZFS dataset for /code",
                "default": "tank/code",
                "when": {"zfs.enabled": True},
            },
            {
                "key": "zfs.device",
                "type": "select",
                "dynamic": "block_devices",
                "message": "Target disk/partition for /code (pick from detected devices)",
                "default": "/dev/sdb",
                "when": {"zfs.enabled": True},
            },
            {
                "key": "zfs.autosnapshot",
                "type": "confirm",
                "message": "Enable automatic snapshots (10-minute cadence) via zfs-auto-snapshot?",
                "default": True,
                "when": {"zfs.enabled": True},
            },
        ],
    },
    {
        "id": "smb",
        "title": "SMB share with Windows snapshot access",
        "questions": [
            {
                "key": "smb.enabled",
                "type": "confirm",
                "message": "Expose /code as an SMB share for Windows workstations?",
                "default": True,
                "when": {"zfs.enabled": True},
            },
            {
                "key": "smb.shadow_copy",
                "type": "confirm",
                "message": "Enable vfs_shadow_copy2 so ZFS snapshots show as Windows 'Previous Versions'?",
                "default": True,
                "when": {"smb.enabled": True},
            },
            {
                "key": "smb.auth",
                "type": "select",
                "message": "SMB authentication",
                "choices": ["Local users", "Active Directory", "Decide later"],
                "default": "Local users",
                "when": {"smb.enabled": True},
            },
        ],
    },
    {
        "id": "vcs",
        "title": "Version control & Git workflow",
        "questions": [
            {
                "key": "vcs.platform",
                "type": "select",
                "message": "Version control platform",
                "choices": ["GitLab (self-hosted)", "GitLab SaaS", "GitHub", "Local only"],
                "default": "GitLab (self-hosted)",
            },
            {
                "key": "vcs.instance_url",
                "type": "text",
                "message": "Self-hosted GitLab instance URL",
                "default": "https://git.example.com",
                "when": {"vcs.platform": "GitLab (self-hosted)"},
            },
            {
                "key": "vcs.token",
                "type": "text",
                "message": "Access token for the VCS (stored in the secret store, not the document)",
                "default": "",
                "secret": True,
                "when": {"vcs.platform": ["GitLab (self-hosted)", "GitLab SaaS", "GitHub"]},
            },
            {
                "key": "vcs.branching",
                "type": "select",
                "message": "Branching strategy",
                "choices": ["Trunk-based", "GitHub Flow", "Git Flow"],
                "default": "Trunk-based",
                "when": {"vcs.platform": ["GitLab (self-hosted)", "GitLab SaaS", "GitHub"]},
            },
            {
                "key": "vcs.protect_main",
                "type": "confirm",
                "message": "Protect main (no direct pushes, MR/PR + review required)?",
                "default": True,
                "when": {"vcs.platform": ["GitLab (self-hosted)", "GitLab SaaS", "GitHub"]},
            },
        ],
    },
    {
        "id": "access",
        "title": "Host access & credentials",
        "subtitle": "How you reach the host and retrieve generated credentials — no passwords in the document.",
        "questions": [
            {
                "key": "access.sshd",
                "type": "confirm",
                "message": "Install and enable OpenSSH server (sshd) for remote access?",
                "default": True,
            },
            {
                "key": "access.ssh_pubkey",
                "type": "text",
                "message": "Your SSH public key to authorize (paste; blank = keep password login)",
                "default": "",
                "when": {"access.sshd": True},
            },
            {
                "key": "access.ssh_disable_password",
                "type": "confirm",
                "message": "Disable SSH password login (key-only, recommended)?",
                "default": True,
                "when": {"access.sshd": True},
            },
            {
                "key": "access.remote_desktop",
                "type": "select",
                "message": "Remote desktop access to a GUI?",
                "choices": ["None (headless, smallest footprint)", "xrdp (Windows Remote Desktop)", "VNC", "NoMachine"],
                "default": "None (headless, smallest footprint)",
                "footprint": "A desktop environment is rarely needed for an agent-driven dev host.",
            },
            {
                "key": "access.summary",
                "type": "confirm",
                "message": "Produce a one-time access summary (where each credential lives + first-login notes)?",
                "default": True,
            },
        ],
    },
    {
        "id": "stages",
        "title": "Stage concept (dev / build)",
        "questions": [
            {
                "key": "stages.build",
                "type": "confirm",
                "message": "Add an independent 'build' stage (fresh CI checkout + built image)?",
                "default": True,
            },
            {
                "key": "stages.domain",
                "type": "text",
                "message": "Base domain for stage hostnames (<service>-<stage>.<domain>)",
                "default": "example.com",
            },
        ],
    },
    {
        "id": "db",
        "title": "Database (runs on the host)",
        "questions": [
            {
                "key": "db.engine",
                "type": "select",
                "message": "Database engine (host-native, shared across stages)",
                "choices": ["PostgreSQL 16", "MySQL / MariaDB", "SQLite", "None"],
                "default": "PostgreSQL 16",
            },
            {
                "key": "db.admin_ui",
                "type": "confirm",
                "message": "Install a DB admin UI (pgAdmin / phpMyAdmin)?",
                "default": True,
                "footprint": "Adds one tool; can be served host-native under Apache.",
                "when": {"db.engine": ["PostgreSQL 16", "MySQL / MariaDB"]},
            },
        ],
    },
    {
        "id": "docker",
        "title": "Containerisation & footprint",
        "subtitle": "Docker for app stacks; host-native for cross-cutting infra to keep the footprint small.",
        "questions": [
            {
                "key": "docker.enabled",
                "type": "confirm",
                "message": "Use Docker + Compose for application stacks?",
                "default": True,
            },
            {
                "key": "docker.portainer",
                "type": "confirm",
                "message": "Run Portainer to manage Docker?",
                "default": True,
                "footprint": "One container; the usual Docker management UI.",
                "when": {"docker.enabled": True},
            },
        ],
    },
    {
        "id": "proxy",
        "title": "Reverse proxy, DNS & TLS",
        "questions": [
            {
                "key": "proxy.kind",
                "type": "select",
                "message": "Reverse proxy & PHP-tool hosting",
                "choices": [
                    "Apache (mod_proxy) + host-native PHP tools (smallest footprint)",
                    "Caddy + tools as containers",
                    "Nginx",
                    "Traefik",
                    "None",
                ],
                "default": "Apache (mod_proxy) + host-native PHP tools (smallest footprint)",
                "footprint": "Apache hosts dashboard/phpMyAdmin/webmail directly — saves a container per tool.",
            },
            {
                "key": "net.public",
                "type": "confirm",
                "message": "Is the host reachable from the public internet?",
                "default": False,
            },
            {
                "key": "net.fixed_ip",
                "type": "confirm",
                "message": "Does it have a fixed public IP? (No = DynDNS needed)",
                "default": False,
                "when": {"net.public": True},
            },
            {
                "key": "dns.control",
                "type": "select",
                "message": "DNS control for your domain",
                "choices": ["Provider API", "Manual records", "DynDNS service", "No DNS control (local only)"],
                "default": "No DNS control (local only)",
            },
            {
                "key": "dns.api_token",
                "type": "text",
                "message": "DNS provider API token (secret store only)",
                "default": "",
                "secret": True,
                "when": {"dns.control": "Provider API"},
            },
            {
                "key": "tls.source",
                "type": "select",
                "message": "TLS certificate source",
                "choices": [
                    "Let's Encrypt (HTTP-01)",
                    "Let's Encrypt (DNS-01, wildcards)",
                    "Bring your own certificates",
                    "Self-signed local CA (fallback)",
                    "No TLS (HTTP only, local)",
                ],
                "default": "Self-signed local CA (fallback)",
            },
            {
                "key": "tls.byo_path",
                "type": "text",
                "message": "Path where you will place fullchain.pem / privkey.pem",
                "default": "/etc/ssl/local",
                "when": {"tls.source": "Bring your own certificates"},
            },
            {
                "key": "tls.ca_reuse",
                "type": "confirm",
                "message": "Reuse an existing local Root CA (instead of generating a new one)?",
                "default": False,
                "when": {"tls.source": "Self-signed local CA (fallback)"},
            },
            {
                "key": "tls.ca_download",
                "type": "confirm",
                "message": "Offer the Root CA for download on the dashboard (with install instructions)?",
                "default": True,
                "when": {"tls.source": "Self-signed local CA (fallback)"},
            },
        ],
    },
    {
        "id": "firewall",
        "title": "Firewall & egress control",
        "subtitle": "Default-deny inbound; restrict where the dev host (and agent) may reach OUTBOUND.",
        "questions": [
            {
                "key": "firewall.enabled",
                "type": "confirm",
                "message": "Set up a host firewall (default-deny inbound, allow only needed ports)?",
                "default": True,
            },
            {
                "key": "firewall.engine",
                "type": "select",
                "message": "Firewall engine",
                "choices": ["ufw", "nftables"],
                "default": "ufw",
                "when": {"firewall.enabled": True},
            },
            {
                "key": "firewall.egress",
                "type": "select",
                "message": "Outbound (egress) policy",
                "choices": [
                    "Denylist (block specific targets, otherwise open)",
                    "Allowlist (deny outbound by default, allow only listed)",
                    "Open outbound",
                ],
                "default": "Denylist (block specific targets, otherwise open)",
                "when": {"firewall.enabled": True},
            },
            {
                "key": "firewall.block",
                "type": "checkbox",
                "message": "Outbound targets the dev host must NEVER reach",
                "choices": [
                    "Cloud metadata endpoint (169.254.169.254)",
                    "Outbound SMTP to the internet (port 25)",
                    "Private/corporate networks (RFC1918: 10/8, 172.16/12, 192.168/16)",
                    "Production database/hosts",
                ],
                "default": [
                    "Cloud metadata endpoint (169.254.169.254)",
                    "Outbound SMTP to the internet (port 25)",
                    "Private/corporate networks (RFC1918: 10/8, 172.16/12, 192.168/16)",
                ],
                "when": {"firewall.egress": "Denylist (block specific targets, otherwise open)"},
            },
            {
                "key": "firewall.block_custom",
                "type": "text",
                "message": "Additional hosts/CIDRs to block (comma-separated, blank = none)",
                "default": "",
                "when": {"firewall.egress": "Denylist (block specific targets, otherwise open)"},
            },
            {
                "key": "firewall.allow",
                "type": "text",
                "message": "Allowed outbound destinations (comma-separated, e.g. package repos, github.com, api.anthropic.com, DNS)",
                "default": "package repos, github.com, api.anthropic.com, DNS",
                "when": {"firewall.egress": "Allowlist (deny outbound by default, allow only listed)"},
            },
        ],
    },
    {
        "id": "mail",
        "title": "Mail",
        "questions": [
            {
                "key": "mail.kind",
                "type": "select",
                "message": "Mail server",
                "choices": [
                    "docker-mailserver (Postfix+Dovecot, dev-simplified)",
                    "Mailpit (catch-all test server)",
                    "External SMTP relay",
                    "None",
                ],
                "default": "docker-mailserver (Postfix+Dovecot, dev-simplified)",
            },
            {
                "key": "mail.webmail",
                "type": "confirm",
                "message": "Add Roundcube webmail?",
                "default": True,
                "when": {"mail.kind": "docker-mailserver (Postfix+Dovecot, dev-simplified)"},
            },
            {
                "key": "mail.outbound",
                "type": "confirm",
                "message": "Allow outbound relay? (No = closed; mail never leaves the host)",
                "default": False,
                "when": {"mail.kind": "docker-mailserver (Postfix+Dovecot, dev-simplified)"},
            },
            {
                "key": "mail.catchall",
                "type": "text",
                "message": "Catch-all mailbox for unassigned / would-be-external mail",
                "default": "catchall@localhost",
                "when": {"mail.kind": "docker-mailserver (Postfix+Dovecot, dev-simplified)"},
            },
        ],
    },
    {
        "id": "secrets",
        "title": "Secrets management",
        "subtitle": "Values go to the store only — never into the hypothesis document.",
        "questions": [
            {
                "key": "secrets.location",
                "type": "select",
                "message": "Secret store location",
                "choices": [
                    "Use an existing store (Infisical/Vault/Doppler)",
                    "Install Infisical locally (Docker)",
                    "File fallback: /code/.secrets",
                ],
                "default": "Install Infisical locally (Docker)",
            },
            {
                "key": "secrets.existing_url",
                "type": "text",
                "message": "Existing store connection (URL / project)",
                "default": "",
                "when": {"secrets.location": "Use an existing store (Infisical/Vault/Doppler)"},
            },
            {
                "key": "secrets.encrypt_files",
                "type": "confirm",
                "message": "Encrypt the file fallback with sops+age?",
                "default": False,
                "when": {"secrets.location": "File fallback: /code/.secrets"},
            },
        ],
    },
    {
        "id": "testing",
        "title": "Testing & CI",
        "subtitle": "A safety net against AI-generated code that only looks runnable.",
        "questions": [
            {
                "key": "testing.coverage_min",
                "type": "text",
                "message": "Minimum test coverage percentage",
                "default": "60",
            },
            {
                "key": "ci.platform",
                "type": "select",
                "message": "CI platform",
                "choices": ["GitLab CI", "GitHub Actions", "None"],
                "default": "GitLab CI",
            },
            {
                "key": "ci.browser_tests",
                "type": "confirm",
                "message": "Include browser/E2E tests in the pipeline?",
                "default": False,
                "when": {"ci.platform": ["GitLab CI", "GitHub Actions"]},
            },
        ],
    },
    {
        "id": "sandbox",
        "title": "Agent sandboxing & permissions",
        "subtitle": "Keep the coding agent on a short, explicit leash.",
        "questions": [
            {
                "key": "sandbox.protect_main",
                "type": "confirm",
                "message": "Forbid the agent from writing to main (feature branches only)?",
                "default": True,
            },
            {
                "key": "sandbox.confirm_destructive",
                "type": "confirm",
                "message": "Require confirmation for destructive ops (rm -rf, db drop, force-push)?",
                "default": True,
            },
            {
                "key": "sandbox.network",
                "type": "select",
                "message": "Agent network access",
                "choices": ["Restricted", "Open"],
                "default": "Restricted",
            },
            {
                "key": "sandbox.redaction_hook",
                "type": "confirm",
                "message": "Install a redaction hook (mask secrets in tool output)?",
                "default": True,
            },
            {
                "key": "sandbox.secret_scan",
                "type": "confirm",
                "message": "Add a pre-commit secret scan (gitleaks)?",
                "default": True,
            },
        ],
    },
    {
        "id": "monitoring",
        "title": "Token & cost monitoring",
        "questions": [
            {
                "key": "monitoring.enabled",
                "type": "confirm",
                "message": "Enable token/cost monitoring for agent sessions?",
                "default": True,
            },
            {
                "key": "monitoring.budget",
                "type": "text",
                "message": "Monthly budget warning threshold (USD, blank = none)",
                "default": "",
                "when": {"monitoring.enabled": True},
            },
        ],
    },
    {
        "id": "dashboard",
        "title": "Dashboard / portal",
        "subtitle": "Auto-regenerated, styled with the OCENOX corporate identity.",
        "questions": [
            {
                "key": "dashboard.enabled",
                "type": "confirm",
                "message": "Generate a central dashboard linking all services?",
                "default": True,
            },
            {
                "key": "dashboard.auto_regen",
                "type": "confirm",
                "message": "Auto-regenerate the dashboard when services change?",
                "default": True,
                "when": {"dashboard.enabled": True},
            },
        ],
    },
]
