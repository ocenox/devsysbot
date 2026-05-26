#!/usr/bin/env bash
#
# DevSysBot bootstrap — run on a clean Ubuntu host:
#
#     curl -fsSL https://raw.githubusercontent.com/ocenox/devsysbot/main/bootstrap.sh | bash
#
# Installs the prerequisites (Python, Node, Claude Code), fetches DevSysBot, and starts
# the interview. Idempotent: safe to run again. Override defaults via environment:
#
#     DEVSYSBOT_REPO   git URL to clone               (default: placeholder below)
#     DEVSYSBOT_HOME   install location               (default: /code/devsysbot)
#     CODE_ROOT        future working-dir root        (default: /code)
#     DEVSYSBOT_HOME   where the bot lives            (default: /devsysbot)
#
# IMPORTANT: DevSysBot, the generated document and staged secrets all live under
# /devsysbot — OUTSIDE $CODE_ROOT. The agent later creates a ZFS dataset mounted at
# $CODE_ROOT and populates it *after* mounting. If we wrote into $CODE_ROOT now, the ZFS
# mount would shadow those files. So nothing is written into $CODE_ROOT here.
set -euo pipefail

DEVSYSBOT_REPO="${DEVSYSBOT_REPO:-https://github.com/ocenox/devsysbot.git}"
CODE_ROOT="${CODE_ROOT:-/code}"
DEVSYSBOT_HOME="${DEVSYSBOT_HOME:-/devsysbot}"
HYPOTHESIS_OUT="${HYPOTHESIS_OUT:-$DEVSYSBOT_HOME/docs/IMPLEMENTATION-HYPOTHESIS.md}"
SECRETS_DIR="${SECRETS_DIR:-$DEVSYSBOT_HOME/.secrets}"

log()  { printf '\033[36m==>\033[0m %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

# Use sudo only when not already root.
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  have sudo && SUDO="sudo" || { echo "Need root or sudo." >&2; exit 1; }
fi

log "Updating apt and installing base packages (git, curl, python3, venv)"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq git curl ca-certificates python3 python3-venv python3-pip

if ! have node; then
  log "Installing Node.js LTS (for Claude Code)"
  curl -fsSL https://deb.nodesource.com/setup_lts.x | $SUDO -E bash -
  $SUDO apt-get install -y -qq nodejs
else
  log "Node.js already present ($(node --version))"
fi

if ! have claude; then
  log "Installing Claude Code (@anthropic-ai/claude-code)"
  $SUDO npm install -g @anthropic-ai/claude-code
else
  log "Claude Code already present"
fi

# $CODE_ROOT is intentionally NOT created here — the agent creates it as a ZFS mount later.

log "Preparing $DEVSYSBOT_HOME (the bot lives here, outside $CODE_ROOT)"
$SUDO mkdir -p "$DEVSYSBOT_HOME"
$SUDO chown "$(id -un)":"$(id -gn)" "$DEVSYSBOT_HOME" 2>/dev/null || true

if [ -d "$DEVSYSBOT_HOME/.git" ]; then
  log "Updating existing DevSysBot checkout"
  git -C "$DEVSYSBOT_HOME" pull --ff-only
else
  log "Cloning DevSysBot into $DEVSYSBOT_HOME"
  git clone --depth 1 "$DEVSYSBOT_REPO" "$DEVSYSBOT_HOME"
fi

mkdir -p "$(dirname "$HYPOTHESIS_OUT")" "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR" 2>/dev/null || true

log "Setting up the Python environment"
cd "$DEVSYSBOT_HOME"
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

log "Starting the DevSysBot interview"
echo
# When this script is run via `curl | bash`, stdin is the script pipe, not the terminal.
# Reconnect the interview to the controlling terminal so the interactive prompts work.
if [ -e /dev/tty ]; then
  PYTHONPATH="$DEVSYSBOT_HOME/src" python3 -m devsysbot \
    --output "$HYPOTHESIS_OUT" --secrets-dir "$SECRETS_DIR" < /dev/tty
else
  echo "No controlling terminal available. Run inside an interactive shell, e.g.:" >&2
  echo "  PYTHONPATH=$DEVSYSBOT_HOME/src python3 -m devsysbot" >&2
  exit 1
fi

echo
log "Done. Review the document, then start the build with Claude Code:"
echo
echo "  1) Review:  $HYPOTHESIS_OUT"
echo "  2) Launch:  cd $DEVSYSBOT_HOME && claude"
echo "  3) Paste this prompt to start the implementation:"
echo
cat <<EOF
  ----------------------------------------------------------------------------
  Read $HYPOTHESIS_OUT and implement it phase by phase using the
  "implement-hypothesis" skill. First confirm the assumptions in section 3
  (disk/ZFS device, domains, DNS) with me before any destructive action.
  Create $CODE_ROOT as the ZFS mount and populate it only after mounting.
  Do not write to main, do not hardcode secrets, never print secret files.
  ----------------------------------------------------------------------------
EOF
echo
log "Tip: the skills live in $DEVSYSBOT_HOME/skills — copy them to your project's .claude/skills/ if needed."
