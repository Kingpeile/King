# documents

Drop the PDFs, Markdown and text files you want to ask questions about here.

`token-saver` (see `tools/token-saver/`) indexes this folder and answers
questions from it without loading whole files into the conversation. It will
not read anything outside this folder.

Everything in here except this README is gitignored — your documents stay
local and are never committed.

Keep the folder small and specific. Its file list is shown to Claude at the
start of a conversation, and a folder holding only what you actually intend to
ask about works far better than one pointed at everything you own.

To index a different folder instead, change `TOKEN_SAVER_FOLDER` in
`.mcp.json` at the repo root.
