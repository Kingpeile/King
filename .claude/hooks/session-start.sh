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
# 3) Global coding principles — user-level ~/.claude/CLAUDE.md.
#    Four principles adapted from andrej-karpathy-skills, applied across every
#    repo and conversation. The container is ephemeral, so recreate it here.
# ---------------------------------------------------------------------------
GLOBAL_CLAUDE_MD="$HOME/.claude/CLAUDE.md"

if [ -f "$GLOBAL_CLAUDE_MD" ]; then
  echo "global coding principles: already present, skipping"
else
  echo "global coding principles: installing..."
  mkdir -p "$HOME/.claude"
  cat > "$GLOBAL_CLAUDE_MD" <<'PRINCIPLES_EOF'
# CLAUDE.md (user-level)

Global guidance applied across every repo and conversation.

## Coding principles

Four principles for reducing coding mistakes (adapted from [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)). Apply these on every change.

### 1. Think Before Coding

State your assumptions explicitly. If uncertain, ask. Surface tradeoffs and multiple interpretations rather than deciding silently. When something is ambiguous, stop and clarify instead of guessing and running with it.

### 2. Simplicity First

Write the minimum code that solves the problem — nothing speculative. Avoid unrequested features, premature abstractions, and unnecessary error handling. Ask yourself: would a senior engineer call this overcomplicated?

### 3. Surgical Changes

Touch only what you must, and clean up only your own mess. Preserve the existing style and resist improving unrelated code. Remove only the imports or variables that *your* changes made unused.

### 4. Goal-Driven Execution

Define success criteria, then loop until verified. Convert vague tasks into testable goals with measurable checks. For multi-step work, outline the plan with its verification steps before executing.
PRINCIPLES_EOF
  echo "global coding principles: ready"
fi

# Persist PATH so plain `agent-memory` resolves in this session's shells.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -w "$(dirname "$CLAUDE_ENV_FILE")" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
