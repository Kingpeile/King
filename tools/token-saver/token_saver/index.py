"""On-disk chunk index: SQLite FTS5 for BM25, plus optional local embeddings.

The index lives in the cache directory, never in the document folder, so the
whitelisted folder stays read-only in practice.
"""

from __future__ import annotations

import array
import logging
import math
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

from .config import EMBED_MODEL, Config
from .documents import (
    Chunk,
    chunk_pages,
    extract_pages,
    file_fingerprint,
    fts_text,
)

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY,
    path        TEXT NOT NULL UNIQUE,
    fingerprint TEXT NOT NULL,
    pages       INTEGER NOT NULL,
    chars       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page        INTEGER NOT NULL,
    ordinal     INTEGER NOT NULL,
    text        TEXT NOT NULL,
    embedding   BLOB
);

CREATE INDEX IF NOT EXISTS chunks_by_document ON chunks(document_id);

-- Standalone (not external-content) FTS index: the indexed text is a rewritten
-- form of chunks.text, with CJK runs expanded to bigrams, so it deliberately
-- differs from the stored original. rowid always equals chunks.id.
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text,
    tokenize='unicode61 remove_diacritics 2'
);
"""


@dataclass(frozen=True)
class ScoredChunk:
    chunk_id: int
    document_path: str
    page: int
    text: str
    bm25: float
    semantic: float
    score: float


@dataclass(frozen=True)
class DocumentStatus:
    path: Path
    pages: int
    chars: int
    chunks: int
    indexed: bool


class Embedder:
    """Lazy wrapper around a local ONNX embedding model.

    The model is optional by design. If it cannot be loaded — no package, no
    downloaded weights, no network — retrieval degrades to keyword-only rather
    than failing, and `unavailable_reason` explains why.
    """

    def __init__(self, mode: str) -> None:
        self._mode = mode
        self._model = None
        self._tried = False
        self._lock = threading.Lock()
        self.unavailable_reason: str | None = None
        if mode == "off":
            self._tried = True
            self.unavailable_reason = "disabled via TOKEN_SAVER_EMBEDDINGS=off"

    @property
    def available(self) -> bool:
        self._ensure()
        return self._model is not None

    def _ensure(self) -> None:
        if self._tried:
            return
        with self._lock:
            if self._tried:
                return
            self._tried = True
            try:
                from fastembed import TextEmbedding  # type: ignore[import-not-found]
            except ImportError:
                self.unavailable_reason = (
                    "fastembed is not installed; run install.sh to add it"
                )
                return
            try:
                self._model = TextEmbedding(model_name=EMBED_MODEL)
            except Exception as exc:  # noqa: BLE001 - any failure means keyword-only
                self.unavailable_reason = (
                    f"could not load {EMBED_MODEL} ({type(exc).__name__}: {exc}). "
                    "The weights download from huggingface.co on first use."
                )
                log.warning("Embeddings unavailable: %s", self.unavailable_reason)

    def encode(self, texts: list[str]) -> list[array.array] | None:
        self._ensure()
        if self._model is None or not texts:
            return None
        try:
            vectors = list(self._model.embed(texts))
        except Exception as exc:  # noqa: BLE001
            log.warning("Embedding failed, falling back to keyword-only: %s", exc)
            self._model = None
            self.unavailable_reason = f"embedding call failed ({exc})"
            return None
        return [_normalise_vector(vector) for vector in vectors]


def _normalise_vector(values) -> array.array:
    vector = array.array("f", (float(value) for value in values))
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    for position in range(len(vector)):
        vector[position] /= norm
    return vector


def cosine(left: array.array, right: array.array) -> float:
    """Both operands are unit vectors, so the dot product is the cosine."""

    if len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))


class Index:
    def __init__(self, config: Config, embedder: Embedder) -> None:
        self.config = config
        self.embedder = embedder
        self._lock = threading.Lock()
        self._db = sqlite3.connect(config.db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(SCHEMA)
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    # ---------------------------------------------------------------- indexing

    def sync(self, paths: list[Path], *, force: bool = False) -> list[DocumentStatus]:
        statuses: list[DocumentStatus] = []
        with self._lock:
            self._forget_missing(paths)
            for path in paths:
                statuses.append(self._sync_one(path, force=force))
            self._db.commit()
        return statuses

    def _forget_missing(self, paths: list[Path]) -> None:
        known = {str(path) for path in paths}
        rows = self._db.execute("SELECT id, path FROM documents").fetchall()
        for row in rows:
            if row["path"] not in known:
                self._delete_document(row["id"])

    def _delete_document(self, document_id: int) -> None:
        ids = [
            row["id"]
            for row in self._db.execute(
                "SELECT id FROM chunks WHERE document_id = ?", (document_id,)
            )
        ]
        for chunk_id in ids:
            self._db.execute("DELETE FROM chunks_fts WHERE rowid = ?", (chunk_id,))
        self._db.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        self._db.execute("DELETE FROM documents WHERE id = ?", (document_id,))

    def _sync_one(self, path: Path, *, force: bool) -> DocumentStatus:
        fingerprint = file_fingerprint(path)
        row = self._db.execute(
            "SELECT id, fingerprint, pages, chars FROM documents WHERE path = ?",
            (str(path),),
        ).fetchone()

        if row and row["fingerprint"] == fingerprint and not force:
            count = self._db.execute(
                "SELECT COUNT(*) AS n FROM chunks WHERE document_id = ?", (row["id"],)
            ).fetchone()["n"]
            return DocumentStatus(path, row["pages"], row["chars"], count, indexed=True)

        if row:
            self._delete_document(row["id"])

        try:
            pages = extract_pages(path)
        except Exception as exc:  # noqa: BLE001 - one bad file must not kill the index
            log.warning("Skipping %s: %s", path.name, exc)
            return DocumentStatus(path, 0, 0, 0, indexed=False)

        chunks = chunk_pages(pages)
        chars = sum(len(page.text) for page in pages)
        cursor = self._db.execute(
            "INSERT INTO documents(path, fingerprint, pages, chars) VALUES(?, ?, ?, ?)",
            (str(path), fingerprint, len(pages), chars),
        )
        document_id = int(cursor.lastrowid)
        self._insert_chunks(document_id, chunks)
        return DocumentStatus(path, len(pages), chars, len(chunks), indexed=True)

    def _insert_chunks(self, document_id: int, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        vectors = self.embedder.encode([chunk.text for chunk in chunks])
        for position, chunk in enumerate(chunks):
            blob = vectors[position].tobytes() if vectors else None
            cursor = self._db.execute(
                "INSERT INTO chunks(document_id, page, ordinal, text, embedding) "
                "VALUES(?, ?, ?, ?, ?)",
                (document_id, chunk.page, chunk.ordinal, chunk.text, blob),
            )
            self._db.execute(
                "INSERT INTO chunks_fts(rowid, text) VALUES(?, ?)",
                (cursor.lastrowid, fts_text(chunk.text)),
            )

    # --------------------------------------------------------------- retrieval

    def keyword_candidates(
        self, query: str, *, limit: int, document_path: str | None = None
    ) -> dict[int, float]:
        """FTS5 BM25 scores, normalised so the best match is 1.0.

        `bm25()` returns a negative number where lower is better, so it is
        flipped before normalisation.
        """

        match = _to_fts_query(query)
        if not match:
            return {}

        sql = (
            "SELECT c.id AS id, bm25(chunks_fts, 1.0) AS rank "
            "FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.rowid "
            "WHERE chunks_fts MATCH ?"
        )
        params: list[object] = [match]
        if document_path:
            sql += " AND c.document_id = (SELECT id FROM documents WHERE path = ?)"
            params.append(document_path)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        try:
            rows = self._db.execute(sql, params).fetchall()
        except sqlite3.OperationalError as exc:
            log.warning("FTS query failed for %r: %s", match, exc)
            return {}

        if not rows:
            return {}
        scores = {int(row["id"]): -float(row["rank"]) for row in rows}
        best = max(scores.values())
        if best <= 0:
            return {chunk_id: 0.0 for chunk_id in scores}
        return {chunk_id: value / best for chunk_id, value in scores.items()}

    def semantic_candidates(
        self, query: str, *, limit: int, document_path: str | None = None
    ) -> dict[int, float]:
        vectors = self.embedder.encode([query])
        if not vectors:
            return {}
        needle = vectors[0]

        sql = "SELECT c.id AS id, c.embedding AS embedding FROM chunks c WHERE c.embedding IS NOT NULL"
        params: list[object] = []
        if document_path:
            sql += " AND c.document_id = (SELECT id FROM documents WHERE path = ?)"
            params.append(document_path)

        scored: list[tuple[int, float]] = []
        for row in self._db.execute(sql, params):
            vector = array.array("f")
            vector.frombytes(row["embedding"])
            scored.append((int(row["id"]), cosine(needle, vector)))

        scored.sort(key=lambda item: item[1], reverse=True)
        return dict(scored[:limit])

    def load_chunks(self, chunk_ids: list[int]) -> dict[int, sqlite3.Row]:
        if not chunk_ids:
            return {}
        placeholders = ",".join("?" for _ in chunk_ids)
        rows = self._db.execute(
            f"SELECT c.id AS id, c.page AS page, c.text AS text, d.path AS path "
            f"FROM chunks c JOIN documents d ON d.id = c.document_id "
            f"WHERE c.id IN ({placeholders})",
            chunk_ids,
        ).fetchall()
        return {int(row["id"]): row for row in rows}

    def document_rows(self) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT d.path AS path, d.pages AS pages, d.chars AS chars, "
            "COUNT(c.id) AS chunks, SUM(c.embedding IS NOT NULL) AS embedded "
            "FROM documents d LEFT JOIN chunks c ON c.document_id = d.id "
            "GROUP BY d.id ORDER BY d.path"
        ).fetchall()


_FTS_SPECIAL = str.maketrans({ch: " " for ch in '"*():^-'})

# Question words and function words carry no signal but appear everywhere, so
# BM25 ranks whichever passage happens to contain the most of them. Only Latin
# terms are filtered; CJK bigrams are left alone because a bigram is a fragment
# of a word, not a word.
_STOPWORDS = frozenset(
    """
    a about all also an and any are as at be been but by can could did do does
    for from had has have how i if in into is it its may me might must my no
    not of on or our shall should so than that the their them then there these
    they this those to up was we were what when where which while who whom why
    will with would you your
    """.split()
)


def _terms(query: str) -> list[str]:
    cleaned = fts_text(query).translate(_FTS_SPECIAL)
    candidates = [term for term in cleaned.split() if len(term) > 1]
    if not candidates:
        candidates = [term for term in cleaned.split() if term]
    kept = [term for term in candidates if term.lower() not in _STOPWORDS]
    # A question made entirely of stopwords still deserves an attempt.
    return (kept or candidates)[:48]


def _to_fts_query(query: str) -> str:
    """Turn a natural-language question into a safe FTS5 OR query.

    The query goes through the same CJK bigram rewrite as the indexed text, and
    every term is quoted, so punctuation in the question can never be parsed as
    FTS5 syntax.
    """

    return " OR ".join(f'"{term}"' for term in _terms(query))


def query_terms(query: str) -> set[str]:
    """The same terms, unquoted — used by the keyword gate in stage 4."""

    return {term.lower() for term in _terms(query)}
