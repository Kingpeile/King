#!/bin/bash
# PreToolUse hook: force a confirmation prompt before running commands or
# editing files, regardless of permission mode or allow-list entries.
# The matcher in settings.json restricts which tools trigger this, so the
# script just emits an "ask" decision for whatever reached it.
set -euo pipefail

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "Manual confirmation required by project policy."
  }
}
EOF
