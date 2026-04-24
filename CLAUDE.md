# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repository is effectively empty. As of the latest check, the working tree contains only this `CLAUDE.md` — there are no source files, no package manifest (no `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.), no build or test configuration, and no application code.

Because nothing has been scaffolded yet, there is no stack, architecture, module layout, build command, test command, lint command, or runtime entry point to document.

## What To Do When The Project Is Initialized

The next assistant (or human) who adds real code should replace this section with concrete guidance. At minimum, capture:

- **Stack and language(s)** — runtime, framework, package manager.
- **Directory layout** — where source, tests, and configuration live, and the purpose of each top-level folder.
- **Common commands** — how to install dependencies, run the app locally, run tests (single test and full suite), lint, typecheck, and build.
- **Architecture notes** — any non-obvious design decisions, module boundaries, or cross-cutting concerns that can only be understood by reading multiple files.
- **Conventions** — naming, formatting, commit message style, or branch-naming rules that aren't enforced by tooling.

Keep the file focused on information that isn't already obvious from a quick `ls` or from reading a single file. Remove this "What To Do When The Project Is Initialized" section once the real content is in place.

## Git Workflow

- Default branch: `main`.
- Ongoing documentation work happens on `claude/add-claude-documentation-*` branches.
- Remote: `origin` (GitHub: `kingpeile/king`).
