from __future__ import annotations

from pathlib import Path

from token_saver.config import CHUNK_OVERLAP_WORDS, CHUNK_WORDS
from token_saver.documents import (
    Page,
    chunk_pages,
    extract_pages,
    fts_text,
    join_units,
    split_sentences,
    split_units,
)


def test_pdf_pages_keep_their_numbers(sample_pdf: Path) -> None:
    pages = extract_pages(sample_pdf)
    assert [page.number for page in pages] == [1, 2, 3]
    assert "Article 5" in pages[0].text
    assert "twenty million" in pages[1].text
    assert "data protection officer" in pages[2].text


def test_markdown_is_paginated_by_size(folder: Path) -> None:
    path = folder / "long.md"
    path.write_text("\n\n".join(["paragraph " * 60] * 10), encoding="utf-8")
    pages = extract_pages(path)
    assert len(pages) > 1
    assert [page.number for page in pages] == list(range(1, len(pages) + 1))


def test_chunks_never_span_a_page() -> None:
    pages = [
        Page(number=1, text=" ".join(f"alpha{i}" for i in range(400))),
        Page(number=2, text=" ".join(f"beta{i}" for i in range(400))),
    ]
    chunks = chunk_pages(pages)
    for chunk in chunks:
        words = chunk.text.split()
        prefix = "alpha" if chunk.page == 1 else "beta"
        assert all(word.startswith(prefix) for word in words)


def test_chunks_overlap_by_the_configured_amount() -> None:
    words = [f"w{i}" for i in range(CHUNK_WORDS * 2)]
    chunks = chunk_pages([Page(number=1, text=" ".join(words))])
    assert len(chunks) >= 2
    first = chunks[0].text.split()
    second = chunks[1].text.split()
    assert len(first) == CHUNK_WORDS
    assert first[-CHUNK_OVERLAP_WORDS:] == second[:CHUNK_OVERLAP_WORDS]


def test_hyphenated_line_breaks_are_rejoined(folder: Path) -> None:
    path = folder / "hyphen.txt"
    path.write_text("The super-\nvisory authority acts.", encoding="utf-8")
    assert "supervisory" in extract_pages(path)[0].text


def test_cjk_counts_as_one_unit_per_character() -> None:
    assert split_units("数据保护") == ["数", "据", "保", "护"]
    assert split_units("hello world") == ["hello", "world"]
    assert split_units("hello 世界") == ["hello", "世", "界"]


def test_join_units_only_spaces_where_needed() -> None:
    assert join_units(["数", "据", "保", "护"]) == "数据保护"
    assert join_units(["hello", "world"]) == "hello world"
    assert join_units(["read", "《", "臣", "服", "实", "验", "》"]) == "read《臣服实验》"


def test_cjk_chunks_are_bounded_by_character_count() -> None:
    text = "数" * (CHUNK_WORDS * 3)
    chunks = chunk_pages([Page(number=1, text=text)])
    assert len(chunks) >= 3
    assert all(len(chunk.text) <= CHUNK_WORDS for chunk in chunks)


def test_fts_text_expands_cjk_into_bigrams() -> None:
    assert fts_text("数据保护").split() == ["数据", "据保", "保护"]


def test_fts_text_leaves_latin_alone() -> None:
    assert fts_text("retention period").split() == ["retention", "period"]


def test_fts_text_handles_mixed_scripts() -> None:
    tokens = fts_text("GDPR 数据保护 rules").split()
    assert "GDPR" in tokens
    assert "数据" in tokens
    assert "rules" in tokens


def test_sentences_split_on_both_punctuation_families() -> None:
    assert len(split_sentences("One thing. Another thing. A third.")) == 3
    assert len(split_sentences("第一句。第二句。第三句。")) == 3


def test_split_sentences_never_returns_empty() -> None:
    assert split_sentences("   ") == [""]
    assert split_sentences("no punctuation here") == ["no punctuation here"]
