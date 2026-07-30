"""Stages 3-8: score, gate, dedupe, trim, budget, wrap.

The point of every stage after scoring is to shrink what crosses the wire. A
chunk that survives scoring still has to earn each of its sentences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import (
    BM25_WEIGHT,
    DEDUP_THRESHOLD,
    SEMANTIC_GATE,
    SEMANTIC_WEIGHT,
    Config,
)
from .documents import fts_text, split_sentences
from .index import Index, cosine, query_terms

CANDIDATE_LIMIT = 80
MAX_PASSAGES = 12


@dataclass(frozen=True)
class Passage:
    path: str
    page: int
    text: str
    score: float
    bm25: float
    semantic: float


@dataclass
class Retrieval:
    passages: list[Passage] = field(default_factory=list)
    mode: str = "keyword-only"
    notes: list[str] = field(default_factory=list)
    sent_tokens: int = 0
    corpus_tokens: int = 0

    @property
    def saved_percent(self) -> float:
        if self.corpus_tokens <= 0:
            return 0.0
        saved = max(0, self.corpus_tokens - self.sent_tokens)
        return round(100.0 * saved / self.corpus_tokens, 1)


def retrieve(
    index: Index,
    config: Config,
    question: str,
    *,
    document: Path | None = None,
    max_chars: int | None = None,
) -> Retrieval:
    budget = max_chars or config.max_chars
    scope = str(document) if document else None
    result = Retrieval()

    # --- stage 3: score -----------------------------------------------------
    keyword = index.keyword_candidates(
        question, limit=CANDIDATE_LIMIT, document_path=scope
    )
    semantic = index.semantic_candidates(
        question, limit=CANDIDATE_LIMIT, document_path=scope
    )

    if semantic:
        result.mode = "hybrid"
    else:
        reason = index.embedder.unavailable_reason
        result.notes.append(
            "Keyword-only retrieval"
            + (f" ({reason})" if reason else "")
            + ". Results are still page-accurate, but paraphrased questions may "
            "miss."
        )

    if not keyword and not semantic:
        result.notes.append("No passage matched the question.")
        return result

    fused: dict[int, tuple[float, float, float]] = {}
    for chunk_id in set(keyword) | set(semantic):
        bm25 = keyword.get(chunk_id, 0.0)
        sim = semantic.get(chunk_id, 0.0)
        fused[chunk_id] = (BM25_WEIGHT * bm25 + SEMANTIC_WEIGHT * sim, bm25, sim)

    rows = index.load_chunks(list(fused))
    terms = query_terms(question)

    # --- stage 4: gate ------------------------------------------------------
    gated: list[tuple[int, float, float, float]] = []
    for chunk_id, (score, bm25, sim) in fused.items():
        row = rows.get(chunk_id)
        if row is None:
            continue
        if not _shares_keyword(row["text"], terms) and sim < SEMANTIC_GATE:
            continue
        gated.append((chunk_id, score, bm25, sim))

    gated.sort(key=lambda item: item[1], reverse=True)
    if not gated:
        result.notes.append(
            "Matches were found but none cleared the relevance threshold "
            f"(semantic >= {SEMANTIC_GATE} without a shared keyword)."
        )
        return result

    # --- stage 5: dedupe ----------------------------------------------------
    kept: list[tuple[int, float, float, float]] = []
    seen: list[set[str]] = []
    for entry in gated:
        signature = _signature(rows[entry[0]]["text"])
        if any(_jaccard(signature, other) >= DEDUP_THRESHOLD for other in seen):
            continue
        seen.append(signature)
        kept.append(entry)
        if len(kept) >= MAX_PASSAGES:
            break

    # --- stage 6: trim ------------------------------------------------------
    trimmed = _trim(index, question, terms, [(entry, rows[entry[0]]) for entry in kept])

    # --- stage 7: budget ----------------------------------------------------
    passages: list[Passage] = []
    used = 0
    for passage in trimmed:
        if used + len(passage.text) > budget:
            remaining = budget - used
            if remaining < 200:
                break
            # Reserve room for the ellipsis so the budget is a hard cap.
            ellipsis = " …"
            truncated = passage.text[: remaining - len(ellipsis)].rstrip() + ellipsis
            passages.append(
                Passage(
                    path=passage.path,
                    page=passage.page,
                    text=truncated,
                    score=passage.score,
                    bm25=passage.bm25,
                    semantic=passage.semantic,
                )
            )
            break
        passages.append(passage)
        used += len(passage.text)

    result.passages = passages
    result.sent_tokens = estimate_tokens("".join(p.text for p in passages))
    result.corpus_tokens = _corpus_tokens(index, {p.path for p in passages})
    return result


def _shares_keyword(text: str, terms: set[str]) -> bool:
    if not terms:
        return False
    haystack = fts_text(text).lower()
    return any(term in haystack for term in terms)


def _signature(text: str) -> set[str]:
    return set(fts_text(text).lower().split())


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    if not intersection:
        return 0.0
    return intersection / len(left | right)


def _trim(
    index: Index,
    question: str,
    terms: set[str],
    entries: list[tuple[tuple[int, float, float, float], object]],
) -> list[Passage]:
    """Narrow each chunk to the sentences that actually answer the question.

    Sentences are ranked by keyword overlap, and by cosine against the question
    when embeddings are loaded. A chunk that ends up with nothing selected keeps
    its highest-overlap sentence rather than dropping out silently.
    """

    sentences_per_chunk = [split_sentences(row["text"]) for _, row in entries]
    flat = [sentence for group in sentences_per_chunk for sentence in group]

    similarities: dict[int, float] = {}
    vectors = index.embedder.encode([question, *flat]) if flat else None
    if vectors:
        needle = vectors[0]
        for position, vector in enumerate(vectors[1:]):
            similarities[position] = cosine(needle, vector)

    passages: list[Passage] = []
    offset = 0
    for entry_index, ((_, score, bm25, sim), row) in enumerate(entries):
        group = sentences_per_chunk[entry_index]
        selected: list[tuple[int, str]] = []
        best: tuple[float, int, str] | None = None

        for position, sentence in enumerate(group):
            overlap = _overlap(sentence, terms)
            similarity = similarities.get(offset + position, 0.0)
            rank = 0.5 * overlap + 0.5 * similarity
            if best is None or rank > best[0]:
                best = (rank, position, sentence)
            if overlap > 0 or similarity >= SEMANTIC_GATE:
                selected.append((position, sentence))

        offset += len(group)
        if not selected and best is not None:
            selected = [(best[1], best[2])]

        selected.sort(key=lambda item: item[0])
        text = " ".join(sentence for _, sentence in selected).strip()
        if not text:
            continue
        passages.append(
            Passage(
                path=row["path"],
                page=int(row["page"]),
                text=text,
                score=score,
                bm25=bm25,
                semantic=sim,
            )
        )
    return passages


def _overlap(sentence: str, terms: set[str]) -> float:
    if not terms:
        return 0.0
    haystack = fts_text(sentence).lower()
    hits = sum(1 for term in terms if term in haystack)
    return hits / len(terms)


def _corpus_tokens(index: Index, paths: set[str]) -> int:
    """Tokens the same answer would have cost by pasting the whole documents."""

    total = 0
    for row in index.document_rows():
        if row["path"] in paths:
            total += estimate_tokens_from_chars(int(row["chars"]))
    return total


def estimate_tokens(text: str) -> int:
    try:
        import tiktoken  # type: ignore[import-not-found]
    except ImportError:
        return estimate_tokens_from_chars(len(text))
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:  # noqa: BLE001 - offline encoding download failure
        return estimate_tokens_from_chars(len(text))
    return len(encoding.encode(text))


def estimate_tokens_from_chars(chars: int) -> int:
    """~4 characters per token, the standard rough conversion."""

    return max(1, round(chars / 4)) if chars else 0


def render(retrieval: Retrieval, folder: Path) -> str:
    """Stage 8: wrap each passage with its source file and page number."""

    if not retrieval.passages:
        return "\n".join(retrieval.notes) or "No matching passages."

    blocks: list[str] = []
    for passage in retrieval.passages:
        try:
            name = str(Path(passage.path).relative_to(folder))
        except ValueError:
            name = Path(passage.path).name
        blocks.append(
            f'<document source="{name}" page="{passage.page}" '
            f'relevance="{passage.score:.2f}">\n{passage.text}\n</document>'
        )

    footer = (
        f"\n[token-saver] {len(retrieval.passages)} passages, "
        f"~{retrieval.sent_tokens} tokens sent vs ~{retrieval.corpus_tokens} "
        f"for the full document(s) — {retrieval.saved_percent}% saved. "
        f"mode={retrieval.mode}"
    )
    notes = ("\n" + "\n".join(f"[note] {note}" for note in retrieval.notes)) if retrieval.notes else ""
    return "\n\n".join(blocks) + "\n" + footer + notes
