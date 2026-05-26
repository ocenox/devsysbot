---
name: add-project
description: Add a new project or stage to an existing environment following the established blueprint. Use when the user says "add a project", "add a stage", or "spin up another app".
---

# Add Project / Stage

Add a new project (or another stage of an existing one) to the host, reusing the
established patterns so everything stays consistent.

## Steps

1. Ask for: project name, stack, port, and whether a build stage is needed.
2. Create host databases: `<project>_dev` (and `<project>_build` if requested).
3. Add the dev stack: bind-mount `/code/<project>`, pick a free port, wire DB/mail hosts
   via `host.docker.internal` (or host-native for Apache setups).
4. Add reverse-proxy entries for `<service>-<stage>.<domain>` and reload the proxy.
5. Add stage subdomains to DNS if DNS control is configured.
6. Run `generate-dashboard` to add the new swimlane.
7. If CI is used, derive the pipeline (lint/test/deploy) from the existing template.

## Rules

- Feature branch only; no direct `main` writes.
- No hardcoded secrets — reference the secret store by name.
- Never use the former product brand name in generated files.
