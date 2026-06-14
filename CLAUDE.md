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

- **`.claude/hooks/session-start.sh`** — installs [agentmemory](https://github.com/jayzeng/agentmemory) (persistent cross-session memory CLI) and the [mattpocock/skills](https://github.com/mattpocock/skills) pack (14 engineering/productivity skills). Idempotent: ~2ms when already installed, ~3s cold. Only runs when `CLAUDE_CODE_REMOTE=true`.
- Registered in `.claude/settings.json` under `hooks.SessionStart`.
- The same hook is mirrored at the user level (`~/.claude/hooks/install-skills.sh` + `~/.claude/settings.json`) so other repos / fresh conversations get the same skills automatically. The user-level copy is the primary; this repo-level copy is a safety net in case `~/.claude/` is wiped.

After install, available skills include: `diagnose`, `tdd`, `prototype`, `triage`, `to-issues`, `to-prd`, `grill-me`, `grill-with-docs`, `improve-codebase-architecture`, `handoff`, `write-a-skill`, `caveman`, `zoom-out`, `setup-matt-pocock-skills`, and `agent-memory`. Most are auto-invoked from natural-language intent; `/zoom-out` and `/setup-matt-pocock-skills` must be typed explicitly.

## Coding principles

Four principles for reducing coding mistakes (adapted from [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)). Apply these on every change in this repo.

### 1. Think Before Coding

State your assumptions explicitly. If uncertain, ask. Surface tradeoffs and multiple interpretations rather than deciding silently. When something is ambiguous, stop and clarify instead of guessing and running with it.

### 2. Simplicity First

Write the minimum code that solves the problem — nothing speculative. Avoid unrequested features, premature abstractions, and unnecessary error handling. Ask yourself: would a senior engineer call this overcomplicated?

### 3. Surgical Changes

Touch only what you must, and clean up only your own mess. Preserve the existing style and resist improving unrelated code. Remove only the imports or variables that *your* changes made unused.

### 4. Goal-Driven Execution

Define success criteria, then loop until verified. Convert vague tasks into testable goals with measurable checks. For multi-step work, outline the plan with its verification steps before executing.
