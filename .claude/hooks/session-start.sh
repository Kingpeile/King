#!/bin/bash
# Auto-install agentmemory skill on session start (Claude Code on the web).
# The container is ephemeral, so the global install at ~/.claude/skills and
# ~/.local/bin doesn't survive between sessions. This hook restores it.
set -euo pipefail

# Only run on remote (web) sessions — local installs are managed by the user.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SHIM="$HOME/.local/bin/agent-memory"
SKILL="$HOME/.claude/skills/agent-memory/SKILL.md"
PKG_DIR="/opt/node22/lib/node_modules/myagentmemory"
CLI_JS="$PKG_DIR/dist/cli.js"

# Fast path: everything already in place.
if [ -f "$SKILL" ] && [ -x "$SHIM" ] && [ -f "$CLI_JS" ] && [ -d "$HOME/.agent-memory" ]; then
  echo "agentmemory: already installed, skipping"
  exit 0
fi

echo "agentmemory: installing..."

# 1. npm install (skip if package already on disk).
if [ ! -f "$CLI_JS" ]; then
  npm install -g myagentmemory >/dev/null 2>&1
fi

# 2. Install the SKILL.md into ~/.claude/skills/agent-memory/.
#    (The bundled installer also drops a symlink at ~/.local/bin/agent-memory
#    pointing at the prebuilt Mac arm64 binary, which doesn't work on Linux.
#    We overwrite that with a Node shim below.)
bash "$PKG_DIR/scripts/install-skills.sh" >/dev/null 2>&1 || true

# 3. Replace the broken Mac binary symlink with a Node shim that runs cli.js.
mkdir -p "$HOME/.local/bin"
rm -f "$SHIM"
cat > "$SHIM" <<'SHIM_EOF'
#!/usr/bin/env bash
exec node /opt/node22/lib/node_modules/myagentmemory/dist/cli.js "$@"
SHIM_EOF
chmod +x "$SHIM"

# Also override the broken symlink on PATH (npm bin dir).
ln -sf "$SHIM" /opt/node22/bin/agent-memory 2>/dev/null || true

# 4. Initialize the memory directory if it doesn't exist yet.
if [ ! -d "$HOME/.agent-memory" ]; then
  "$SHIM" init >/dev/null 2>&1 || true
fi

# Persist PATH so plain `agent-memory` resolves in this session's shells.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -w "$(dirname "$CLAUDE_ENV_FILE")" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi

echo "agentmemory: ready (skill: $SKILL, cli: $SHIM, memory: $HOME/.agent-memory)"
