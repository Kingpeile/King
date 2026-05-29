# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repository is currently empty. No source files, build configuration, or commits exist yet. Update this file once the project is initialized with its stack, structure, and workflows.

## Agent skills

### Issue tracker

Issues for this repo live on GitHub (Kingpeile/King) and are managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical 5-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`); labels are created lazily on first triage. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` at the repo root and `docs/adr/` for architectural decisions (both created lazily by `/grill-with-docs`). See `docs/agents/domain.md`.

## Session setup (Claude Code on the web)

The cloud container is ephemeral, so a `SessionStart` hook restores user-level skills on every cold session:

- **`.claude/hooks/session-start.sh`** — installs [agentmemory](https://github.com/jayzeng/agentmemory) (persistent cross-session memory CLI), the [mattpocock/skills](https://github.com/mattpocock/skills) pack (14 engineering/productivity skills), and [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) (女娲 `huashu-nuwa` — distills a person / thinking style into a runnable persona Skill). Idempotent: ~2ms when already installed, ~3s cold. Only runs when `CLAUDE_CODE_REMOTE=true`.
- Registered in `.claude/settings.json` under `hooks.SessionStart`.
- The same hook is mirrored at the user level (`~/.claude/hooks/install-skills.sh` + `~/.claude/settings.json`) so other repos / fresh conversations get the same skills automatically. The user-level copy is the primary; this repo-level copy is a safety net in case `~/.claude/` is wiped.

After install, available skills include: `diagnose`, `tdd`, `prototype`, `triage`, `to-issues`, `to-prd`, `grill-me`, `grill-with-docs`, `improve-codebase-architecture`, `handoff`, `write-a-skill`, `caveman`, `zoom-out`, `setup-matt-pocock-skills`, `agent-memory`, and `huashu-nuwa`. Most are auto-invoked from natural-language intent; `/zoom-out` and `/setup-matt-pocock-skills` must be typed explicitly. `huashu-nuwa` triggers on phrases like 「造skill」「蒸馏XX」「女娲」「XX的思维方式」.
