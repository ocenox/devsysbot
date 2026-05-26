#!/usr/bin/env bash
#
# DevSysBot bootstrap — run on a clean Ubuntu host:
#
#     curl -fsSL https://example.com/devsysbot/bootstrap.sh | bash
#
# Installs the prerequisites (Python, Node, Claude Code), fetches DevSysBot, and starts
# the interview. Idempotent: safe to run again. Override defaults via environment:
#
#     DEVSYSBOT_REPO   git URL to clone               (default: placeholder below)
#     DEVSYSBOT_HOME   install location               (default: /code/devsysbot)
#     CODE_ROOT        working-directory root         (default: /code)
#
set -euo pipefail

DEVSYSBOT_REPO="${DEVSYSBOT_REPO:-https://github.com/ocenox/devsysbot.git}"
CODE_ROOT="${CODE_ROOT:-/code}"
DEVSYSBOT_HOME="${DEVSYSBOT_HOME:-$CODE_ROOT/devsysbot}"

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

log "Preparing $CODE_ROOT"
$SUDO mkdir -p "$CODE_ROOT"
$SUDO chown "$(id -un)":"$(id -gn)" "$CODE_ROOT" 2>/dev/null || true

if [ -d "$DEVSYSBOT_HOME/.git" ]; then
  log "Updating existing DevSysBot checkout"
  git -C "$DEVSYSBOT_HOME" pull --ff-only
else
  log "Cloning DevSysBot into $DEVSYSBOT_HOME"
  git clone --depth 1 "$DEVSYSBOT_REPO" "$DEVSYSBOT_HOME"
fi

log "Setting up the Python environment"
cd "$DEVSYSBOT_HOME"
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

log "Starting the DevSysBot interview"
echo
PYTHONPATH="$DEVSYSBOT_HOME/src" python3 -m devsysbot --output "$CODE_ROOT/IMPLEMENTATION-HYPOTHESIS.md"

echo
log "Done. Review $CODE_ROOT/IMPLEMENTATION-HYPOTHESIS.md, then run 'claude' to build the environment."
