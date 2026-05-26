#!/usr/bin/env bash
#
# DevSysBot PreToolUse guard for Bash commands.
# Install to <project>/.claude/hooks/guard.sh (referenced from settings.json).
#
# Reads the tool-call JSON on stdin, inspects the command, and blocks (exit 2) the worst
# footguns the sandbox is meant to prevent. Exit 0 lets the command through.
#
# Complements the permission rules in settings.json (which deny reading secret files and
# ask before destructive ops). This catches a few patterns those rules can miss.
set -euo pipefail

input="$(cat)"

# Extract the command field without requiring jq.
cmd="$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p')"

block() { echo "BLOCKED by guard: $1" >&2; exit 2; }

# 1. No printing of secret files.
case "$cmd" in
  *cat*/.secrets/*|*cat*\.env*|*less*/.secrets/*|*head*/.secrets/*|*tail*/.secrets/*)
    block "reading secret files is not allowed; reference secrets by name" ;;
esac

# 2. No force-push to main/master.
case "$cmd" in
  *git*push*--force*main*|*git*push*-f*main*|*git*push*--force*master*|*git*push*-f*master*)
    block "force-push to main/master is not allowed" ;;
esac

# 3. No direct commit/push onto main (use a feature branch).
case "$cmd" in
  *git*push*origin*main*|*git*push*origin*master*)
    block "pushing directly to main/master is not allowed; use a feature branch + MR/PR" ;;
esac

# 4. Obvious catastrophic deletes.
case "$cmd" in
  *"rm -rf /"|*"rm -rf /*"|*"rm -rf ~"*|*":(){ :|:& };:"*)
    block "refusing a catastrophic delete / fork bomb" ;;
esac

exit 0
