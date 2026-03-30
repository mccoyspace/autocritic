"""Shared test fixtures for autocritic evals."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = PROJECT_ROOT / "books"
CORPUS_DIR = PROJECT_ROOT / "v0" / "corpus"  # extracted text from prior work


def has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


skip_no_api = pytest.mark.skipif(
    not has_api_key(),
    reason="ANTHROPIC_API_KEY not set",
)


@pytest.fixture
def raw_text_dir() -> Path:
    d = CORPUS_DIR / "raw_text"
    if not d.exists():
        pytest.skip("No extracted corpus found — run extract_books.py first")
    return d


@pytest.fixture
def wolfflin_text(raw_text_dir: Path) -> str:
    p = raw_text_dir / "principles_of_art_history_heinrich_wolfflin.txt"
    return p.read_text(encoding="utf-8", errors="replace")


@pytest.fixture
def kandinsky_text(raw_text_dir: Path) -> str:
    p = raw_text_dir / "point_line_to_plane_kandinsky.txt"
    return p.read_text(encoding="utf-8", errors="replace")


@pytest.fixture
def dow_text(raw_text_dir: Path) -> str:
    p = raw_text_dir / "composition_arthur_wesley_dow.txt"
    return p.read_text(encoding="utf-8", errors="replace")
