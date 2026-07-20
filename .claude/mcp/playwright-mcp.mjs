#!/usr/bin/env node
// Launcher for the Playwright MCP server that adapts to where it runs.
//
//   - Local machine (Claude Code CLI / desktop app on macOS, Windows, Linux):
//     plain launch — Playwright MCP opens a normal, visible browser using the
//     Chrome installed on your computer. Nothing extra to configure.
//
//   - Claude Code on the web (the ephemeral cloud container): there is no
//     display and the browser lives at a fixed path, so we add headless +
//     no-sandbox and point at the pre-installed Chromium.
//
// The environment is detected via CLAUDE_CODE_REMOTE, which the web container
// sets to "true". Node is used (not bash) so this works on Windows too.

import { spawn } from 'node:child_process';

const isRemote = process.env.CLAUDE_CODE_REMOTE === 'true';

const baseArgs = ['-y', '@playwright/mcp@latest'];

const remoteArgs = isRemote
  ? [
      '--browser', 'chromium',
      '--executable-path',
      `${process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers'}/chromium`,
      '--headless',
      '--no-sandbox',
    ]
  : [];

// Forward any extra args passed by the MCP client.
const args = [...baseArgs, ...remoteArgs, ...process.argv.slice(2)];

// On Windows, npx is a .cmd shim and must be run through the shell.
const child = spawn('npx', args, {
  stdio: 'inherit',
  shell: process.platform === 'win32',
});

child.on('exit', (code) => process.exit(code ?? 0));
child.on('error', (err) => {
  console.error('[playwright-mcp launcher] failed to start npx:', err.message);
  process.exit(1);
});
