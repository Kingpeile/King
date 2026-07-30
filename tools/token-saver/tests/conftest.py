from __future__ import annotations

import os
from pathlib import Path

import pytest

from token_saver.config import Config
from token_saver.index import Embedder, Index

PAGE_ONE = (
    "The retention period for personal data is defined in Article 5. "
    "Controllers must not keep data longer than necessary for the purpose. "
    "Storage limitation is the governing principle here."
)
PAGE_TWO = (
    "Penalties for infringement can reach twenty million euros. "
    "Alternatively the fine may be four percent of total worldwide annual turnover. "
    "Supervisory authorities decide which figure applies."
)
PAGE_THREE = (
    "Nothing on this page is about money or retention. "
    "It describes the appointment procedure for a data protection officer. "
    "The officer reports to the highest management level."
)


def write_pdf(path: Path, pages: list[str]) -> Path:
    fpdf = pytest.importorskip("fpdf")
    document = fpdf.FPDF()
    document.set_font("Helvetica", size=11)
    for text in pages:
        document.add_page()
        document.multi_cell(0, 6, text)
    document.output(str(path))
    return path


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    return docs


@pytest.fixture
def config(folder: Path, tmp_path: Path) -> Config:
    return Config(
        folder=folder.resolve(),
        cache_dir=(tmp_path / "cache").resolve(),
        max_chars=8000,
        embeddings="off",
    )


@pytest.fixture
def index(config: Config) -> Index:
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    built = Index(config, Embedder("off"))
    yield built
    built.close()


@pytest.fixture
def sample_pdf(folder: Path) -> Path:
    return write_pdf(folder / "regulation.pdf", [PAGE_ONE, PAGE_TWO, PAGE_THREE])


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("TOKEN_SAVER_"):
            monkeypatch.delenv(name, raising=False)
