from __future__ import annotations

from pathlib import Path

import pytest

from token_saver.config import (
    Config,
    ConfigError,
    iter_documents,
    load_config,
    resolve_in_folder,
)


def test_missing_folder_is_a_startup_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TOKEN_SAVER_FOLDER", raising=False)
    with pytest.raises(ConfigError, match="TOKEN_SAVER_FOLDER is not set"):
        load_config()


def test_nonexistent_folder_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TOKEN_SAVER_FOLDER", str(tmp_path / "nope"))
    with pytest.raises(ConfigError, match="does not exist"):
        load_config()


def test_defaults_are_applied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, folder: Path
) -> None:
    monkeypatch.setenv("TOKEN_SAVER_FOLDER", str(folder))
    monkeypatch.setenv("TOKEN_SAVER_CACHE", str(tmp_path / "cache"))
    config = load_config()
    assert config.max_chars == 8000
    assert config.embeddings == "auto"
    assert config.db_path.parent.exists()


def test_bad_embeddings_mode_is_rejected(
    monkeypatch: pytest.MonkeyPatch, folder: Path, tmp_path: Path
) -> None:
    monkeypatch.setenv("TOKEN_SAVER_FOLDER", str(folder))
    monkeypatch.setenv("TOKEN_SAVER_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("TOKEN_SAVER_EMBEDDINGS", "maybe")
    with pytest.raises(ConfigError, match="auto, on or off"):
        load_config()


def test_absolute_path_outside_folder_is_refused(
    config: Config, tmp_path: Path
) -> None:
    outsider = tmp_path / "secret.pdf"
    outsider.write_bytes(b"%PDF-1.4\n")
    with pytest.raises(ValueError, match="outside the whitelisted folder"):
        resolve_in_folder(config, str(outsider))


def test_traversal_out_of_folder_is_refused(config: Config, tmp_path: Path) -> None:
    (tmp_path / "secret.md").write_text("classified", encoding="utf-8")
    with pytest.raises(ValueError, match="outside the whitelisted folder"):
        resolve_in_folder(config, "../secret.md")


def test_symlink_escaping_the_folder_is_refused(
    config: Config, folder: Path, tmp_path: Path
) -> None:
    target = tmp_path / "secret.md"
    target.write_text("classified", encoding="utf-8")
    (folder / "innocent.md").symlink_to(target)
    with pytest.raises(ValueError, match="outside the whitelisted folder"):
        resolve_in_folder(config, "innocent.md")


def test_bare_filename_resolves(config: Config, sample_pdf: Path) -> None:
    assert resolve_in_folder(config, "regulation.pdf") == sample_pdf


def test_stem_without_extension_resolves(config: Config, sample_pdf: Path) -> None:
    assert resolve_in_folder(config, "regulation") == sample_pdf


def test_ambiguous_name_asks_for_clarification(config: Config, folder: Path) -> None:
    (folder / "a").mkdir()
    (folder / "b").mkdir()
    (folder / "a" / "notes.md").write_text("one", encoding="utf-8")
    (folder / "b" / "notes.md").write_text("two", encoding="utf-8")
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_in_folder(config, "notes.md")


def test_unsupported_type_is_refused(config: Config, folder: Path) -> None:
    (folder / "sheet.xlsx").write_bytes(b"x")
    with pytest.raises(ValueError, match="Unsupported file type"):
        resolve_in_folder(config, "sheet.xlsx")


def test_iter_documents_skips_hidden_and_unsupported(
    config: Config, folder: Path, sample_pdf: Path
) -> None:
    (folder / ".hidden.md").write_text("hidden", encoding="utf-8")
    (folder / "image.png").write_bytes(b"\x89PNG")
    (folder / "notes.md").write_text("visible", encoding="utf-8")
    names = {path.name for path in iter_documents(config)}
    assert names == {"regulation.pdf", "notes.md"}
