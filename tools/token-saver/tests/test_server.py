from __future__ import annotations

from pathlib import Path

import pytest

from token_saver import server as server_module
from token_saver.server import _parse_pages


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch, folder: Path, tmp_path: Path):
    monkeypatch.setenv("TOKEN_SAVER_FOLDER", str(folder))
    monkeypatch.setenv("TOKEN_SAVER_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("TOKEN_SAVER_EMBEDDINGS", "off")
    monkeypatch.setattr(server_module, "_config", None, raising=False)
    monkeypatch.setattr(server_module, "_index", None, raising=False)
    yield server_module
    if server_module._index is not None:
        server_module._index.close()
    server_module._config = None
    server_module._index = None


def test_page_spec_parsing() -> None:
    assert _parse_pages("7") == [7]
    assert _parse_pages("3-5") == [3, 4, 5]
    assert _parse_pages("1,4,9") == [1, 4, 9]
    assert _parse_pages("2, 1, 2") == [1, 2]


@pytest.mark.parametrize("spec", ["", "abc", "5-3", "1-", "1-9999"])
def test_bad_page_specs_are_rejected(spec: str) -> None:
    with pytest.raises(ValueError):
        _parse_pages(spec)


def test_list_documents_reports_cost(wired, sample_pdf: Path) -> None:
    output = wired.list_documents()
    assert "regulation.pdf" in output
    assert "3 pages" in output
    assert "tokens if pasted whole" in output


def test_list_documents_on_empty_folder(wired, folder: Path) -> None:
    assert "No supported documents" in wired.list_documents()


def test_search_returns_tagged_passages(wired, sample_pdf: Path) -> None:
    output = wired.search_documents("what are the penalties")
    assert 'source="regulation.pdf"' in output
    assert 'page="2"' in output


def test_search_rejects_a_path_outside_the_folder(
    wired, sample_pdf: Path, tmp_path: Path
) -> None:
    outsider = tmp_path / "elsewhere.md"
    outsider.write_text("secret", encoding="utf-8")
    output = wired.search_documents("anything", document=str(outsider))
    assert "outside the whitelisted folder" in output


def test_search_without_a_question(wired, sample_pdf: Path) -> None:
    assert "question" in wired.search_documents("   ").lower()


def test_read_pages_returns_verbatim_text(wired, sample_pdf: Path) -> None:
    output = wired.read_pages("regulation.pdf", "2")
    assert 'page="2"' in output
    assert "twenty million" in output


def test_read_pages_reports_missing_pages(wired, sample_pdf: Path) -> None:
    assert "none of" in wired.read_pages("regulation.pdf", "99")


def test_read_pages_refuses_a_huge_range(wired, sample_pdf: Path) -> None:
    assert "defeats the purpose" in wired.read_pages("regulation.pdf", "1-500")


def test_reindex_reports_counts(wired, sample_pdf: Path) -> None:
    output = wired.reindex()
    assert "Reindexed 1 document" in output
    assert "chunks" in output


def test_reindex_one_document(wired, sample_pdf: Path, folder: Path) -> None:
    (folder / "other.md").write_text("unrelated", encoding="utf-8")
    assert "Reindexed 1 document" in wired.reindex("regulation.pdf")


def test_tools_list_is_marked_cacheable() -> None:
    hints = server_module.server._lowlevel_server.cache_hints
    assert hints["tools/list"].ttl_ms > 0
    assert hints["tools/list"].scope == "public"
