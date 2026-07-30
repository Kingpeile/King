# token-saver

A local MCP server that answers questions about your documents **without
putting the documents in the conversation**.

Pasting a 200-page PDF into a chat is not a one-time charge — the whole
conversation is resent to the model on every turn, so that PDF is billed again
with each follow-up question. token-saver keeps the file on disk, retrieves only
the passages that answer the question, and hands those over with page numbers
attached.

Typical result on a large document: a few hundred tokens instead of tens of
thousands.

## What it does

Retrieval is hybrid — keyword and meaning — because either one alone misses.

| Stage | What happens |
| --- | --- |
| 1. Extract | `pypdfium2` per page, `pypdf` as fallback. Markdown and text files are paginated by size. |
| 2. Chunk | 180-unit windows, 40 units of overlap, never spanning a page. A unit is a word, or a single character in Chinese/Japanese/Korean. |
| 3. Score | SQLite FTS5 BM25 (weight 0.4) fused with cosine similarity from a local `all-MiniLM-L6-v2` (weight 0.6). |
| 4. Gate | A passage sharing no keyword with the question must reach 0.25 cosine to survive. |
| 5. Dedupe | Near-identical passages dropped (Jaccard ≥ 0.92). |
| 6. Trim | Each surviving passage is narrowed to the sentences that answer the question. |
| 7. Budget | Total payload capped at 8000 characters. |
| 8. Wrap | Each passage is returned as `<document source="..." page="...">`, so answers can cite a page you can open and check. |

Every response ends with a line reporting tokens sent versus tokens the whole
document would have cost.

### Chinese, Japanese and Korean

FTS5's default tokenizer treats an unbroken run of Chinese as a single token,
which makes keyword search useless on Chinese documents. token-saver rewrites
CJK runs into overlapping character bigrams before indexing, and puts the query
through the same rewrite. Chunk sizes are counted in characters for CJK and in
words elsewhere, so chunks stay comparable across scripts.

## Security

- **No uploads.** Documents are read from disk and never sent anywhere except
  the passages the model asked for.
- **Folder whitelist.** `TOKEN_SAVER_FOLDER` is the only readable directory.
  Paths are resolved through symlinks before the containment check, so a
  symlink pointing outside is refused like any other outside path.
- **No network listener.** stdio transport only. Nothing binds a port.
- **Index lives outside the folder.** The SQLite index is written to the cache
  directory, so the document folder stays untouched.

The embedding model downloads from `huggingface.co` on first use. That is the
only outbound request, and the server runs keyword-only if it fails.

## Install

```bash
./install.sh
```

Creates `.venv/` next to the script and installs everything. Re-running is a
no-op. Requires Python 3.10+; uses `uv` when available, `python3 -m venv`
otherwise.

## Configure

| Variable | Required | Default | Meaning |
| --- | --- | --- | --- |
| `TOKEN_SAVER_FOLDER` | yes | — | The one folder the server may read. |
| `TOKEN_SAVER_CACHE` | no | `~/.cache/token-saver` | Where the index is stored. |
| `TOKEN_SAVER_MAX_CHARS` | no | `8000` | Cap on returned text per search. |
| `TOKEN_SAVER_EMBEDDINGS` | no | `auto` | `auto`, `on`, or `off` (keyword-only). |

Keep the folder small and specific. It bounds what is readable, it lets you
refer to files by bare name, and its file list is shown to the model at the
start of a conversation — a folder holding only what you intend to ask about
works far better than pointing at your entire documents directory.

### Claude Code

`.mcp.json` in the repo root already registers the server. Point it at your own
folder by setting `TOKEN_SAVER_FOLDER` there.

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "token-saver": {
      "command": "/absolute/path/to/tools/token-saver/.venv/bin/token-saver",
      "env": {
        "TOKEN_SAVER_FOLDER": "/absolute/path/to/your/documents"
      }
    }
  }
}
```

Config file locations:

- macOS — `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows — `%APPDATA%\Claude\claude_desktop_config.json`

Restart Claude Desktop after editing.

## Tools

| Tool | Use it for |
| --- | --- |
| `search_documents(question, document?, max_chars?)` | The main one. Ask the question; get back the passages that answer it. |
| `list_documents()` | What is indexed, page counts, and what each would cost pasted whole. |
| `read_pages(document, pages)` | Verbatim pages, e.g. `"7"`, `"3-5"`, `"1,4,9"`. Capped at 50 pages. |
| `reindex(document?)` | Force a rebuild. Rarely needed — changes are picked up by size and mtime. |

## Testing

```bash
.venv/bin/python -m pytest tests/ -q
```

## License

MIT.
