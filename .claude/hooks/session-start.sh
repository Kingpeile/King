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
# 3) Global "confirm before run" hook — restore the user-level PreToolUse hook
#    that forces a confirmation prompt before Bash/Edit/Write tools, in EVERY
#    repo. ~/.claude is wiped on cold web containers, so recreate it each
#    session. Idempotent: rewrites the (tiny) script and only appends the
#    PreToolUse entry to ~/.claude/settings.json if it isn't already there.
# ---------------------------------------------------------------------------
CONFIRM_HOOK="$HOME/.claude/hooks/confirm-before-run.sh"
USER_SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOME/.claude/hooks"
cat > "$CONFIRM_HOOK" <<'HOOK_EOF'
#!/bin/bash
# PreToolUse hook (global): force a confirmation prompt before commands/edits.
set -euo pipefail
cat <<'JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "Manual confirmation required (global policy)."
  }
}
JSON
HOOK_EOF
chmod +x "$CONFIRM_HOOK"

# Merge the PreToolUse hook into user settings without clobbering other keys.
python3 - "$USER_SETTINGS" <<'PY' || echo "confirm-before-run: settings merge failed (continuing)"
import json, sys
path = sys.argv[1]
cmd = "$HOME/.claude/hooks/confirm-before-run.sh"
try:
    with open(path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}
data.setdefault("$schema", "https://json.schemastore.org/claude-code-settings.json")
pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
existing = [h.get("command") for e in pre for h in e.get("hooks", [])]
if cmd not in existing:
    pre.append({
        "matcher": "Bash|Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [{"type": "command", "command": cmd}],
    })
with open(path, "w") as f:
    json.dump(data, f, indent=4)
    f.write("\n")
PY
echo "global confirm-before-run hook: ready"

# Persist PATH so plain `agent-memory` resolves in this session's shells.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -w "$(dirname "$CLAUDE_ENV_FILE")" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
