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
# 3) Chinese content-creation skills (community, installed from GitHub).
#    - guizang-social-card-skill : 小红书/公众号 social cards (SKILL.md at repo root)
#    - ian-xiaohei-illustrations : 中文正文配图 "小黑" (SKILL.md in a subfolder)
#    Each is restored on cold sessions; idempotent via the SKILL.md marker.
# ---------------------------------------------------------------------------
install_git_skill() {
  # $1 = repo URL, $2 = skill/dir name, $3 = subpath within repo ("" = root)
  local url="$1" name="$2" subpath="$3"
  local dest="$HOME/.claude/skills/$name"
  if [ -f "$dest/SKILL.md" ]; then
    echo "$name: already installed, skipping"
    return 0
  fi
  echo "$name: installing..."
  local tmp; tmp="$(mktemp -d)"
  if git clone --depth 1 -q "$url" "$tmp" 2>/dev/null; then
    mkdir -p "$dest"
    cp -R "$tmp/${subpath:+$subpath/}." "$dest/" 2>/dev/null || true
    rm -rf "$dest/.git"
    if [ -f "$dest/SKILL.md" ]; then echo "$name: ready"; else echo "$name: install failed (no SKILL.md)"; fi
  else
    echo "$name: clone failed (continuing)"
  fi
  rm -rf "$tmp"
}

install_git_skill "https://github.com/op7418/guizang-social-card-skill" "guizang-social-card-skill" ""
install_git_skill "https://github.com/helloianneo/ian-xiaohei-illustrations" "ian-xiaohei-illustrations" "ian-xiaohei-illustrations"

# Persist PATH so plain `agent-memory` resolves in this session's shells.
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -w "$(dirname "$CLAUDE_ENV_FILE")" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
