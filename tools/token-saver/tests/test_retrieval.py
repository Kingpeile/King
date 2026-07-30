from __future__ import annotations

from pathlib import Path

from token_saver.config import Config, iter_documents
from token_saver.index import Index
from token_saver.retrieve import estimate_tokens_from_chars, render, retrieve


def _sync(index: Index, config: Config) -> None:
    index.sync(iter_documents(config))


def test_retrieval_finds_the_right_page(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    _sync(index, config)
    result = retrieve(index, config, "What are the penalties for infringement?")
    assert result.passages
    assert result.passages[0].page == 2
    assert "twenty million" in result.passages[0].text


def test_retrieval_answers_from_a_different_page(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    _sync(index, config)
    result = retrieve(index, config, "How long may data be retained?")
    assert result.passages[0].page == 1
    assert "retention" in result.passages[0].text.lower()


def test_payload_is_far_smaller_than_the_document(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    _sync(index, config)
    result = retrieve(index, config, "penalties for infringement")
    assert result.corpus_tokens > 0
    assert result.sent_tokens < result.corpus_tokens
    assert result.saved_percent > 0


def test_budget_is_enforced(index: Index, config: Config, folder: Path) -> None:
    (folder / "big.md").write_text(
        "\n\n".join(["retention of personal data " * 40] * 40), encoding="utf-8"
    )
    _sync(index, config)
    result = retrieve(index, config, "retention of personal data", max_chars=500)
    assert sum(len(passage.text) for passage in result.passages) <= 500


def test_scope_to_one_document(index: Index, config: Config, folder: Path) -> None:
    (folder / "a.md").write_text("Penalties reach twenty million euros.", encoding="utf-8")
    (folder / "b.md").write_text("Penalties reach thirty million euros.", encoding="utf-8")
    _sync(index, config)
    result = retrieve(index, config, "penalties", document=(folder / "b.md").resolve())
    assert result.passages
    assert all(Path(p.path).name == "b.md" for p in result.passages)


def test_duplicate_passages_are_collapsed(
    index: Index, config: Config, folder: Path
) -> None:
    body = "The supervisory authority issues the fine for late notification."
    for name in ("one.md", "two.md", "three.md"):
        (folder / name).write_text(body, encoding="utf-8")
    _sync(index, config)
    result = retrieve(index, config, "who issues the fine")
    assert len(result.passages) == 1


def test_unmatched_question_returns_a_note_not_a_dump(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    _sync(index, config)
    result = retrieve(index, config, "zzzqqq unrelated xylophone")
    assert result.passages == []
    assert result.notes


def test_keyword_only_mode_is_declared(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    _sync(index, config)
    result = retrieve(index, config, "penalties")
    assert result.mode == "keyword-only"
    assert any("Keyword-only" in note for note in result.notes)


def test_chinese_question_matches_chinese_document(
    index: Index, config: Config, folder: Path
) -> None:
    (folder / "notes.md").write_text(
        "第一章 讲的是无关内容。\n\n"
        "第二章 数据保护的核心是最小化收集，控制者不得超出目的保留数据。\n\n"
        "第三章 讨论人员任命流程。",
        encoding="utf-8",
    )
    _sync(index, config)
    result = retrieve(index, config, "数据保护的核心是什么")
    assert result.passages
    assert "数据保护" in result.passages[0].text


def test_index_picks_up_a_changed_file(
    index: Index, config: Config, folder: Path
) -> None:
    path = folder / "notes.md"
    path.write_text("Original text about penguins.", encoding="utf-8")
    _sync(index, config)
    assert retrieve(index, config, "penguins").passages

    path.write_text("Rewritten text about walruses.", encoding="utf-8")
    _sync(index, config)
    assert not retrieve(index, config, "penguins").passages
    assert retrieve(index, config, "walruses").passages


def test_deleted_file_leaves_the_index(
    index: Index, config: Config, folder: Path
) -> None:
    path = folder / "temp.md"
    path.write_text("Ephemeral content about narwhals.", encoding="utf-8")
    _sync(index, config)
    assert retrieve(index, config, "narwhals").passages

    path.unlink()
    _sync(index, config)
    assert not retrieve(index, config, "narwhals").passages


def test_render_tags_source_and_page(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    _sync(index, config)
    output = render(retrieve(index, config, "penalties"), config.folder)
    assert 'source="regulation.pdf"' in output
    assert 'page="2"' in output
    assert "% saved" in output


def test_render_without_matches_is_a_short_message(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    _sync(index, config)
    output = render(retrieve(index, config, "zzzqqq xylophone"), config.folder)
    assert "<document" not in output
    assert len(output) < 400


def test_punctuation_heavy_question_does_not_break_fts(
    index: Index, config: Config, sample_pdf: Path
) -> None:
    result = retrieve(index, config, 'What about "penalties" (Article 5) -- 4%?')
    assert isinstance(result.passages, list)


def test_token_estimate_is_monotonic() -> None:
    assert estimate_tokens_from_chars(0) == 0
    assert estimate_tokens_from_chars(4000) > estimate_tokens_from_chars(400)
