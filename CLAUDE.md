# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**King** is a personal health-management app (个人健康管理). The same product ships as two
independent front-ends, both fully client-side with no backend and no build step:

- **`miniprogram/`** — a WeChat Mini Program (微信小程序). Five tab pages: 首页 / 记录 / 趋势 / 报告 / 我的.
  Users log health metrics (体重、血压、血糖、睡眠、步数, etc.) and view trends and reports.
  State is persisted **locally** via WeChat storage, wrapped in `utils/storage.js`.
- **`webapp/`** — a browser version of the same app. Plain vanilla JS (no framework, no bundler),
  state persisted in `localStorage` (keys like `hr_<type>`, `health_reports`, `user_profile`).

The two front-ends share the product concept but **not** their data — each stores to its own
device. There is no server, no API, and no shared database.

## Repository Structure

```
miniprogram/            WeChat Mini Program (primary client)
  app.js / app.json     app entry + page/tabBar registration
  pages/                index · record · trends · reports · profile (each: .js/.json/.wxml/.wxss)
  utils/storage.js      local-storage wrapper + TYPE_CONFIG (the metric definitions)
  cloud/functions/      ⚠️ legacy dead code — cloud deps were removed (commit 57c7f5b),
                           healthData is no longer referenced anywhere. Safe to delete.
webapp/                 Browser version (vanilla JS): index.html · app.js · style.css
docs/agents/            Agent-facing docs (issue tracker, triage labels, domain layout)
docs/loops/             The morning-triage loop (see "Loops" below)
.claude/                Skills, hooks, settings (see "Agent skills" / "Session setup")
.github/workflows/      triage-loop.yml — scheduled trigger for the triage loop
Obsidian/               Personal Obsidian notes synced into the repo (not app code)
```

## Conventions & gotchas

- **No build / no tests / no CI.** Both clients are run-as-is. Open `miniprogram/` in WeChat
  DevTools; open `webapp/index.html` in a browser. Don't add tooling unasked.
- **Local-only storage.** Data lives on-device. Cloud development was deliberately removed
  (`refactor: 移除云开发依赖，改为纯本地存储`). Don't reintroduce `wx.cloud` without a reason.
- **`miniprogram/cloud/functions/healthData/` is dead code** left over from that refactor.
- **Metric types live in one place:** `utils/storage.js` `TYPE_CONFIG`. Add a metric there.

## Agent skills

### Issue tracker

Issues for this repo live on GitHub (Kingpeile/King). On Claude Code on the web they're managed
via the GitHub MCP tools (`mcp__github__*`); locally, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical 5-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`); labels are created lazily on first triage. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` at the repo root and `docs/adr/` for architectural decisions (both created lazily by `/grill-with-docs`). See `docs/agents/domain.md`.

## Loops (loop engineering)

A minimal morning-**triage loop** lives in `docs/loops/` — it auto-discovers work (open issues,
PRs, recent commits), classifies it, runs an independent skeptical evaluator, and routes
anything needing a human into `docs/loops/inbox.md`. Start at **`docs/loops/README.md`**.

- Discovery + classify: `.claude/skills/triage/SKILL.md`
- Evaluator (the part that can say "no"): `.claude/skills/triage-review/SKILL.md`
- On-disk memory: `docs/loops/triage-state.md` · Human inbox: `docs/loops/inbox.md`
- Schedule: `.github/workflows/triage-loop.yml` (needs `ANTHROPIC_API_KEY` secret to actually run)

Discovery/classify only — it does **not** auto-change code, open PRs, or merge. Background and
method come from the Loop Engineering Orange Book; the full notes are in agentmemory topic
`loop-engineering`.

## Session setup (Claude Code on the web)

The cloud container is ephemeral, so a `SessionStart` hook restores user-level skills on every cold session:

- **`.claude/hooks/session-start.sh`** — installs [agentmemory](https://github.com/jayzeng/agentmemory) (persistent cross-session memory CLI) and the [mattpocock/skills](https://github.com/mattpocock/skills) pack (14 engineering/productivity skills). Idempotent: ~2ms when already installed, ~3s cold. Only runs when `CLAUDE_CODE_REMOTE=true`.
- Registered in `.claude/settings.json` under `hooks.SessionStart`.
- The same hook is mirrored at the user level (`~/.claude/hooks/install-skills.sh` + `~/.claude/settings.json`) so other repos / fresh conversations get the same skills automatically. The user-level copy is the primary; this repo-level copy is a safety net in case `~/.claude/` is wiped.

After install, available skills include: `diagnose`, `tdd`, `prototype`, `triage`, `to-issues`, `to-prd`, `grill-me`, `grill-with-docs`, `improve-codebase-architecture`, `handoff`, `write-a-skill`, `caveman`, `zoom-out`, `setup-matt-pocock-skills`, and `agent-memory`. Most are auto-invoked from natural-language intent; `/zoom-out` and `/setup-matt-pocock-skills` must be typed explicitly.
