"""Stage 1 (extract) and stage 2 (chunk) of the pipeline.

Text is kept page-addressed the whole way through so every chunk that reaches
the model can cite the page it came from.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .config import CHUNK_OVERLAP_WORDS, CHUNK_WORDS

# Scripts written without spaces between words. These need character-level
# handling: the default FTS5 tokenizer swallows a whole Chinese sentence as one
# token, and splitting on whitespace would make a "180 word" chunk enormous.
_CJK_RANGES = (
    "　-〿"  # CJK punctuation
    "぀-ヿ"  # kana
    "㐀-䶿"  # CJK extension A
    "一-鿿"  # CJK unified ideographs
    "가-힯"  # hangul
    "豈-﫿"  # compatibility ideographs
    "＀-￯"  # fullwidth forms
)
_IS_CJK = re.compile(f"[{_CJK_RANGES}]")
_CJK_RUN = re.compile(f"[{_CJK_RANGES}]+")
# One unit is a single CJK character, or a run of non-space non-CJK text.
_UNIT = re.compile(f"[{_CJK_RANGES}]|[^\\s{_CJK_RANGES}]+")

_WHITESPACE = re.compile(r"[^\S\n]+")
_BLANK_LINES = re.compile(r"\n{3,}")
# Latin punctuation ends a sentence when followed by space; CJK punctuation
# ends one on its own.
_SENTENCE = re.compile(r"(?<=[.!?;])\s+|(?<=[。！？；])|\n{2,}")


@dataclass(frozen=True)
class Page:
    number: int  # 1-based, as printed in a PDF reader
    text: str


@dataclass(frozen=True)
class Chunk:
    page: int
    ordinal: int
    text: str


def is_cjk(char: str) -> bool:
    return bool(_IS_CJK.match(char))


def split_units(text: str) -> list[str]:
    """Tokenise into comparable units across scripts."""

    return _UNIT.findall(text)


def join_units(units: list[str]) -> str:
    """Reassemble units, inserting a space only where the script needs one."""

    parts: list[str] = []
    previous = ""
    for unit in units:
        if previous and not is_cjk(unit[0]) and not is_cjk(previous[-1]):
            parts.append(" ")
        parts.append(unit)
        previous = unit
    return "".join(parts)


def fts_text(text: str) -> str:
    """Rewrite CJK runs as overlapping character bigrams for FTS5.

    `unicode61` treats an unbroken run of Chinese as a single token, which makes
    keyword search useless on Chinese documents. Emitting bigrams gives the
    tokenizer word-sized units it can actually match and rank.
    """

    return _CJK_RUN.sub(lambda match: " " + _bigrams(match.group()) + " ", text)


def _bigrams(run: str) -> str:
    if len(run) < 2:
        return run
    return " ".join(run[index : index + 2] for index in range(len(run) - 1))


def file_fingerprint(path: Path) -> str:
    """Cheap change detector: size + mtime, so reindexing is incremental."""

    stat = path.stat()
    raw = f"{path}|{stat.st_size}|{stat.st_mtime_ns}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def extract_pages(path: Path) -> list[Page]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    return _extract_text(path)


def _extract_pdf(path: Path) -> list[Page]:
    pages = _extract_pdf_pypdfium2(path)
    if pages is not None:
        return pages
    pages = _extract_pdf_pypdf(path)
    if pages is not None:
        return pages
    raise RuntimeError(
        f"Could not extract text from {path.name}. Install pypdfium2 (preferred) "
        "or pypdf, and check the file is not a scan without an OCR layer."
    )


def _extract_pdf_pypdfium2(path: Path) -> list[Page] | None:
    try:
        import pypdfium2  # type: ignore[import-not-found]
    except ImportError:
        return None

    pages: list[Page] = []
    document = pypdfium2.PdfDocument(str(path))
    try:
        for number, page in enumerate(document, start=1):
            textpage = page.get_textpage()
            try:
                text = textpage.get_text_range()
            finally:
                textpage.close()
                page.close()
            pages.append(Page(number=number, text=_normalise(text, join_lines=True)))
    finally:
        document.close()
    return pages


def _extract_pdf_pypdf(path: Path) -> list[Page] | None:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError:
        return None

    reader = PdfReader(str(path))
    return [
        Page(number=number, text=_normalise(page.extract_text() or "", join_lines=True))
        for number, page in enumerate(reader.pages, start=1)
    ]


def _extract_text(path: Path) -> list[Page]:
    """Plain text and Markdown have no pages, so paginate by size.

    Roughly 3000 characters per synthetic page keeps citations useful without
    inventing page numbers that mean nothing.
    """

    raw = _normalise(path.read_text(encoding="utf-8", errors="replace"))
    if not raw:
        return []

    window = 3000
    pages: list[Page] = []
    buffer: list[str] = []
    size = 0
    for paragraph in raw.split("\n\n"):
        if size and size + len(paragraph) > window:
            pages.append(Page(number=len(pages) + 1, text="\n\n".join(buffer)))
            buffer, size = [], 0
        buffer.append(paragraph)
        size += len(paragraph) + 2
    if buffer:
        pages.append(Page(number=len(pages) + 1, text="\n\n".join(buffer)))
    return pages


def _normalise(text: str, *, join_lines: bool = False) -> str:
    """Clean up extracted text.

    `join_lines` folds single newlines into spaces. PDF line breaks are layout
    artifacts — a sentence wrapped across two lines is still one sentence — but
    in Markdown a newline is authored structure, so it is left alone there.
    """

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Rejoin words split across a line break by hyphenation.
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    if join_lines:
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = _WHITESPACE.sub(" ", text)
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def chunk_pages(pages: list[Page]) -> list[Chunk]:
    """Split each page into overlapping windows of `CHUNK_WORDS` units.

    Chunks never span a page boundary, which is what keeps the page citation on
    each chunk honest.
    """

    step = CHUNK_WORDS - CHUNK_OVERLAP_WORDS
    if step <= 0:
        raise ValueError("CHUNK_OVERLAP_WORDS must be smaller than CHUNK_WORDS")

    chunks: list[Chunk] = []
    ordinal = 0
    for page in pages:
        units = split_units(page.text)
        if not units:
            continue
        start = 0
        while start < len(units):
            text = join_units(units[start : start + CHUNK_WORDS]).strip()
            if text:
                chunks.append(Chunk(page=page.number, ordinal=ordinal, text=text))
                ordinal += 1
            if start + CHUNK_WORDS >= len(units):
                break
            start += step
    return chunks


def split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in _SENTENCE.split(text) if part and part.strip()]
    return parts or [text.strip()]
