---
name: secrets-guard
description: Safely add, rotate and reference secrets via the chosen secret store without ever exposing values. Use when handling tokens, passwords, API keys, or wiring secrets into services.
---

# Secrets Guard

Handle secrets so that values live only in the secret store and never in the repo, a
script, a config file, or the conversation transcript.

## Rules

- **Reference, never inline.** Configs read secrets at runtime (env var / store lookup),
  e.g. `infisical run -- <cmd>` or an explicit env-var name. Do not paste values.
- **Never read `/code/.secrets/**`.** It is denied by the project settings; reference the
  names instead.
- **Never echo a secret.** Do not `cat`, `echo` or log secret values.
- When you must create a value (e.g. a generated DB password), write it straight into the
  store, then reference it — do not print it.

## Adding a secret

1. Determine the store in use (existing store / local Infisical / `/code/.secrets` file).
2. Add the value to the store under a clear name.
3. Wire the service to read it by name at runtime.
4. Confirm nothing was written to a tracked file (the gitleaks pre-commit hook backs this up).

## Rotation

Replace the value in the store and restart the consuming services. No code change should
be required if everything references by name.
