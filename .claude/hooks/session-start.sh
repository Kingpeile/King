#!/bin/bash
# Auto-install user-level Claude skills on session start (Claude Code on the web).
# The container is ephemeral, so anything in ~/.claude/skills doesn't survive
# between sessions. This hook restores them.
set -euo pipefail

# Only run on remote (web) sessions — local installs are managed by the user.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# 1) agentmemory (jayzeng/agentmemory) — persistent memory CLI + skill.
# ---------------------------------------------------------------------------
AM_SHIM="$HOME/.local/bin/agent-memory"
AM_SKILL="$HOME/.claude/skills/agent-memory/SKILL.md"
AM_PKG_DIR="/opt/node22/lib/node_modules/myagentmemory"
AM_CLI_JS="$AM_PKG_DIR/dist/cli.js"

if [ -f "$AM_SKILL" ] && [ -x "$AM_SHIM" ] && [ -f "$AM_CLI_JS" ] && [ -d "$HOME/.agent-memory" ]; then
  echo "agentmemory: already installed, skipping"
else
  echo "agentmemory: installing..."
  if [ ! -f "$AM_CLI_JS" ]; then
    npm install -g myagentmemory >/dev/null 2>&1
  fi
  # Bundled installer drops the SKILL.md and an ~/.local/bin symlink to the
  # prebuilt Mac arm64 binary (broken on Linux). We replace that with a Node shim.
  bash "$AM_PKG_DIR/scripts/install-skills.sh" >/dev/null 2>&1 || true
  mkdir -p "$HOME/.local/bin"
  rm -f "$AM_SHIM"
  cat > "$AM_SHIM" <<'SHIM_EOF'
#!/usr/bin/env bash
exec node /opt/node22/lib/node_modules/myagentmemory/dist/cli.js "$@"
SHIM_EOF
  chmod +x "$AM_SHIM"
  ln -sf "$AM_SHIM" /opt/node22/bin/agent-memory 2>/dev/null || true
  if [ ! -d "$HOME/.agent-memory" ]; then
    "$AM_SHIM" init >/dev/null 2>&1 || true
  fi
  echo "agentmemory: ready"
fi

# ---------------------------------------------------------------------------
# 2) mattpocock/skills — engineering & productivity skill pack (14 skills).
#    Uses the `skills` CLI (vercel-labs) to install globally for claude-code.
#    Marker: presence of the `diagnose` skill (first skill alphabetically).
# ---------------------------------------------------------------------------
MP_MARKER="$HOME/.claude/skills/diagnose/SKILL.md"

if [ -f "$MP_MARKER" ]; then
  echo "mattpocock/skills: already installed, skipping"
else
  echo "mattpocock/skills: installing..."
  npx -y skills@latest add mattpocock/skills -g -a claude-code -s '*' -y >/dev/null 2>&1 || \
    echo "mattpocock/skills: install failed (continuing)"
  if [ -f "$MP_MARKER" ]; then
    echo "mattpocock/skills: ready"
  fi
fi

# ---------------------------------------------------------------------------
# 3) eastmoney-data — in-repo 东方财富行情数据 skill. Mirror it from the repo
#    to the user level so it's globally triggerable (and survives cold sessions).
#    Source lives in this repo, so no network needed; always re-sync to stay current.
# ---------------------------------------------------------------------------
EM_SRC="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/skills/eastmoney-data"
EM_DST="$HOME/.claude/skills/eastmoney-data"
if [ -d "$EM_SRC" ]; then
  mkdir -p "$HOME/.claude/skills"
  rm -rf "$EM_DST"
  cp -r "$EM_SRC" "$EM_DST"
  rm -rf "$EM_DST/scripts/__pycache__"
  echo "eastmoney-data: ready (user-level)"
else
  echo "eastmoney-data: source not found in repo, skipping"
fi

# Persist PATH so plain `agent-memory` resolves in this session's shells.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -w "$(dirname "$CLAUDE_ENV_FILE")" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
