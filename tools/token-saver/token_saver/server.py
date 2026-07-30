"""The MCP server: stdio only, no listening ports.

Tools are deliberately few and coarse. The model asks a question, the pipeline
decides what little text is worth sending back, and every passage carries the
page it came from.
"""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.caching import CacheHint

from .config import Config, ConfigError, iter_documents, load_config, resolve_in_folder
from .documents import extract_pages
from .index import Embedder, Index
from .retrieve import estimate_tokens_from_chars, render, retrieve

log = logging.getLogger("token_saver")

INSTRUCTIONS = """\
token-saver answers questions about local documents without loading them into
the conversation.

Call `search_documents` with the user's actual question instead of asking for a
whole file. It runs hybrid retrieval (BM25 + local embeddings) over a
whitelisted folder and returns only the passages that matter, each tagged with
its source file and page number. Cite those page numbers in your answer.

Use `read_pages` only when the user asks for a specific page verbatim, or when
a retrieved passage is clearly cut off. Reading a whole document is what this
server exists to avoid.
"""

_state_lock = threading.Lock()
_config: Config | None = None
_index: Index | None = None


def _ready() -> tuple[Config, Index]:
    """Build the index on first use, not at startup, so the client never waits."""

    global _config, _index
    with _state_lock:
        if _config is None:
            _config = load_config()
        if _index is None:
            embedder = Embedder(_config.embeddings)
            _index = Index(_config, embedder)
            _index.sync(iter_documents(_config))
        return _config, _index


server = MCPServer(
    name="token-saver",
    title="Token Saver",
    version="1.0.0",
    instructions=INSTRUCTIONS,
    # tools/list is cacheable under protocol revision 2026-07-28: the tool set
    # never changes at runtime, so clients can skip re-fetching it each turn.
    cache_hints={"tools/list": CacheHint(ttl_ms=3_600_000, scope="public")},
)


@server.tool(
    name="list_documents",
    title="List indexed documents",
    description=(
        "List every document in the whitelisted folder with its page count and "
        "index status. Call this first if the user refers to a file by a name "
        "you have not seen."
    ),
)
def list_documents() -> str:
    config, index = _ready()
    rows = index.document_rows()
    if not rows:
        return (
            f"No supported documents in {config.folder}. "
            "Supported types: .pdf, .md, .markdown, .txt"
        )

    lines = [f"Folder: {config.folder}", ""]
    for row in rows:
        name = str(Path(row["path"]).relative_to(config.folder))
        embedded = int(row["embedded"] or 0)
        total = int(row["chunks"])
        coverage = "hybrid" if embedded == total and total else "keyword-only"
        lines.append(
            f"- {name} — {row['pages']} pages, {total} chunks, "
            f"~{estimate_tokens_from_chars(int(row['chars']))} tokens if pasted "
            f"whole ({coverage})"
        )
    return "\n".join(lines)


@server.tool(
    name="search_documents",
    title="Search documents",
    description=(
        "Answer a question from the local documents. Pass the user's question "
        "verbatim — it is used for both keyword and semantic matching. Returns "
        "only the relevant passages, each tagged with source file and page "
        "number. Prefer this over reading a file."
    ),
)
def search_documents(
    question: str,
    document: str | None = None,
    max_chars: int | None = None,
) -> str:
    """Search the whitelisted folder.

    Args:
        question: The question to answer, in the user's own words.
        document: Optional filename to restrict the search to a single document.
        max_chars: Optional cap on returned text. Defaults to the server budget.
    """

    config, index = _ready()
    if not question.strip():
        return "Give me the question to search for."

    target = None
    if document:
        try:
            target = resolve_in_folder(config, document)
        except ValueError as exc:
            return f"{exc}\n\nCall list_documents to see what is available."

    index.sync(iter_documents(config))
    result = retrieve(index, config, question, document=target, max_chars=max_chars)
    return render(result, config.folder)


@server.tool(
    name="read_pages",
    title="Read specific pages",
    description=(
        "Read specific pages of one document verbatim, for example '3' or "
        "'12-15'. Use only when a passage is truncated or the user asks for a "
        "page by number."
    ),
)
def read_pages(document: str, pages: str) -> str:
    """Read exact pages.

    Args:
        document: Filename inside the whitelisted folder.
        pages: Page numbers, e.g. "7", "3-5" or "1,4,9".
    """

    config, _ = _ready()
    try:
        path = resolve_in_folder(config, document)
        wanted = _parse_pages(pages)
    except ValueError as exc:
        return str(exc)

    extracted = {page.number: page.text for page in extract_pages(path)}
    if not extracted:
        return f"{path.name} has no extractable text."

    missing = [number for number in wanted if number not in extracted]
    blocks = [
        f'<document source="{path.name}" page="{number}">\n{extracted[number]}\n</document>'
        for number in wanted
        if number in extracted
    ]
    if not blocks:
        return (
            f"{path.name} has pages 1-{max(extracted)}; none of {pages} exist."
        )
    if missing:
        blocks.append(f"[note] pages not in this document: {missing}")
    return "\n\n".join(blocks)


@server.tool(
    name="reindex",
    title="Rebuild the index",
    description=(
        "Force a rebuild of the local index. Only needed if a document changed "
        "in a way the size+mtime check missed."
    ),
)
def reindex(document: str | None = None) -> str:
    config, index = _ready()
    if document:
        try:
            paths = [resolve_in_folder(config, document)]
        except ValueError as exc:
            return str(exc)
    else:
        paths = iter_documents(config)

    statuses = index.sync(paths, force=True)
    ok = [status for status in statuses if status.indexed]
    failed = [status for status in statuses if not status.indexed]
    summary = (
        f"Reindexed {len(ok)} document(s), "
        f"{sum(status.chunks for status in ok)} chunks."
    )
    if failed:
        names = ", ".join(status.path.name for status in failed)
        summary += f" Could not extract text from: {names}"
    if not index.embedder.available:
        summary += (
            f" Embeddings unavailable ({index.embedder.unavailable_reason}); "
            "running keyword-only."
        )
    return summary


def _parse_pages(spec: str) -> list[int]:
    wanted: list[int] = []
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            start, _, end = part.partition("-")
            if not start.isdigit() or not end.isdigit():
                raise ValueError(f"Bad page range: {part!r}")
            first, last = int(start), int(end)
            if first > last:
                raise ValueError(f"Bad page range: {part!r}")
            if last - first > 50:
                raise ValueError(
                    f"{part!r} spans {last - first + 1} pages; that defeats the "
                    "purpose. Ask a question with search_documents instead."
                )
            wanted.extend(range(first, last + 1))
        elif part.isdigit():
            wanted.append(int(part))
        else:
            raise ValueError(f"Bad page number: {part!r}")
    if not wanted:
        raise ValueError("No page numbers given.")
    return sorted(set(wanted))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,  # stdout is the MCP transport
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        load_config()
    except ConfigError as exc:
        print(f"token-saver: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
