---
name: implement-hypothesis
description: Read IMPLEMENTATION-HYPOTHESIS.md and build the development environment phase by phase. Use when the user says "build the environment", "implement the hypothesis", or "set up the dev environment".
---

# Implement Hypothesis

You build a development environment from an approved `IMPLEMENTATION-HYPOTHESIS.md`.

## Steps

1. Read the hypothesis document. Files are timestamped (`IMPLEMENTATION-HYPOTHESIS-*.md`);
   use the **newest** one. Look in `/devsysbot/docs`, the current dir and `/code`.
2. Confirm the **Assumptions & open points** with the user before any destructive action
   (especially disk/ZFS device and domain/DNS).
3. Work the **Agent task list** in phase order. After each phase, run a quick check and
   report status before moving on.
4. Honour the safety rules at all times:
   - Never write to `main`; use a feature branch.
   - Never hardcode secret values into scripts, Compose files or configs. Reference them
     from the secret store by name.
   - Never read or print files under `/code/.secrets/**`.
5. When all phases are done, verify the **Acceptance criteria** and summarise what is
   running (services, URLs, snapshot status, pipeline state).

## Notes

- Prefer host-native services for cross-cutting infrastructure (database, reverse proxy,
  PHP tools) and containers for application stacks — keep the footprint small.
- If a step fails, stop and report; do not improvise around safety rules.
