"""Runtime configuration and the folder whitelist.

Every path the server touches is resolved against a single whitelisted folder.
Anything that lands outside it is refused before the file is opened.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".pdf", ".md", ".txt", ".markdown"}

# Pipeline defaults, matching the reference description of the 8-stage pipeline.
CHUNK_WORDS = 180
CHUNK_OVERLAP_WORDS = 40
BM25_WEIGHT = 0.4
SEMANTIC_WEIGHT = 0.6
SEMANTIC_GATE = 0.25
DEDUP_THRESHOLD = 0.92
DEFAULT_MAX_CHARS = 8000

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class ConfigError(RuntimeError):
    """Raised when the server is started without a usable whitelist folder."""


@dataclass(frozen=True)
class Config:
    folder: Path
    cache_dir: Path
    max_chars: int
    embeddings: str  # "auto" | "on" | "off"

    @property
    def db_path(self) -> Path:
        return self.cache_dir / "index.db"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be positive, got {value}")
    return value


def load_config() -> Config:
    raw_folder = os.environ.get("TOKEN_SAVER_FOLDER", "").strip()
    if not raw_folder:
        raise ConfigError(
            "TOKEN_SAVER_FOLDER is not set. Point it at the folder holding the "
            "documents you want to ask about; the server refuses to read anything "
            "outside that folder."
        )

    folder = Path(raw_folder).expanduser()
    try:
        folder = folder.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ConfigError(f"TOKEN_SAVER_FOLDER does not exist: {folder}") from exc
    if not folder.is_dir():
        raise ConfigError(f"TOKEN_SAVER_FOLDER is not a directory: {folder}")

    raw_cache = os.environ.get("TOKEN_SAVER_CACHE", "").strip()
    if raw_cache:
        cache_dir = Path(raw_cache).expanduser()
    else:
        xdg = os.environ.get("XDG_CACHE_HOME", "").strip()
        base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
        cache_dir = base / "token-saver"
    cache_dir.mkdir(parents=True, exist_ok=True)

    embeddings = os.environ.get("TOKEN_SAVER_EMBEDDINGS", "auto").strip().lower()
    if embeddings not in {"auto", "on", "off"}:
        raise ConfigError(
            f"TOKEN_SAVER_EMBEDDINGS must be auto, on or off; got {embeddings!r}"
        )

    return Config(
        folder=folder,
        cache_dir=cache_dir.resolve(),
        max_chars=_env_int("TOKEN_SAVER_MAX_CHARS", DEFAULT_MAX_CHARS),
        embeddings=embeddings,
    )


def resolve_in_folder(config: Config, candidate: str) -> Path:
    """Resolve `candidate` to a real file inside the whitelisted folder.

    Accepts a bare filename, a path relative to the folder, or an absolute path
    that already sits inside it. Symlinks are resolved before the containment
    check, so a link pointing outside the folder is refused like any other
    outside path.
    """

    name = candidate.strip()
    if not name:
        raise ValueError("No document name given.")
    if "\x00" in name:
        raise ValueError("Document name contains a null byte.")

    path = Path(name).expanduser()
    path = path if path.is_absolute() else config.folder / path

    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        match = _match_by_name(config, name)
        if match is None:
            raise ValueError(
                f"No document named {candidate!r} in {config.folder}."
            ) from None
        resolved = match

    if not _is_within(resolved, config.folder):
        raise ValueError(
            f"Refused: {candidate!r} resolves outside the whitelisted folder "
            f"{config.folder}."
        )
    if not resolved.is_file():
        raise ValueError(f"Not a file: {resolved}")
    if resolved.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported file type {resolved.suffix!r}; supported: "
            + ", ".join(sorted(SUPPORTED_SUFFIXES))
        )
    return resolved


def _match_by_name(config: Config, name: str) -> Path | None:
    """Fall back to a loose filename match so users can say "the GDPR pdf"."""

    needle = Path(name).name.lower()
    candidates = [
        path
        for path in iter_documents(config)
        if path.name.lower() == needle or path.stem.lower() == needle
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        listing = ", ".join(sorted(p.name for p in candidates))
        raise ValueError(f"{name!r} is ambiguous; candidates: {listing}")
    return None


def _is_within(path: Path, folder: Path) -> bool:
    return path == folder or folder in path.parents


def iter_documents(config: Config) -> list[Path]:
    """Every supported document inside the whitelist, sorted by relative path."""

    found: list[Path] = []
    for path in config.folder.rglob("*"):
        if path.name.startswith("."):
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            continue
        if resolved.is_file() and _is_within(resolved, config.folder):
            found.append(resolved)
    return sorted(set(found), key=lambda p: str(p.relative_to(config.folder)))
