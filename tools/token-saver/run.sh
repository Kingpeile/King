#!/usr/bin/env bash
# Launcher used by .mcp.json and by Claude Desktop.
#
# Resolves its own location, so the MCP config never needs an absolute path,
# and installs the venv on first run — which matters in ephemeral containers
# where the previous session's .venv is gone.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
BIN="$HERE/.venv/bin/token-saver"

if [ ! -x "$BIN" ]; then
  # stdout is the MCP transport; the installer already logs to stderr.
  if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
    "$HERE/install.sh" --core
  else
    "$HERE/install.sh"
  fi
fi

export TOKEN_SAVER_FOLDER="${TOKEN_SAVER_FOLDER:-$REPO/documents}"
mkdir -p "$TOKEN_SAVER_FOLDER"

exec "$BIN"
