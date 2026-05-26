---
name: refresh-env
description: Reproducibly reset the dev stage to a clean, seeded data state. Use when the user says "refresh", "reset the dev data", or "clean rebuild".
---

# Refresh Environment (dev stage)

Reset the dev stage to a known-good state without touching committed code. This is the
central reset workflow; run it whenever the dev data has drifted.

## Steps (adapt to the chosen stack)

0. Update DNS/certs if applicable; regenerate proxy config (single source of truth) and
   reload the proxy.
1. Recreate databases and run migrations + seeds (`migrate:fresh` / equivalent).
2. Re-provision integrations: mail accounts + catch-all mailbox, OIDC/SSO clients, API
   tokens — pull secret values from the secret store, never from the repo.
3. Clear application caches.
4. Fix bind-mount file permissions if needed.
5. Print the reachable URLs at the end.

## Safety net interaction

This operates on **dev data only**. Committed code is protected by Git; uncommitted file
changes are protected by ZFS snapshots — if a refresh clobbers local edits, recover them
from a snapshot ("Previous Versions" on Windows) rather than re-typing.
