"""Tests for text chunker."""
import pytest
from plugins.nomad.chunker import chunk_text


def test_chunk_text_basic():
    text = "A" * 4000
    chunks = chunk_text(text, chunk_size=2000, overlap=200)
    assert len(chunks) > 0
    assert all(len(c) <= 2200 for c in chunks)


def test_chunk_text_small():
    text = "Short text"
    chunks = chunk_text(text, chunk_size=2000, overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_overlap():
    text = "A" * 3000
    chunks = chunk_text(text, chunk_size=2000, overlap=200)
    assert len(chunks) >= 2


def test_chunk_text_section_aware():
    text = "Intro\n\n## Section 1\n" + "A" * 1500 + "\n\n## Section 2\n" + "B" * 1500
    chunks = chunk_text(text, chunk_size=2000, overlap=200, section_aware=True)
    assert len(chunks) >= 2
    assert any("Section 1" in c for c in chunks)
    assert any("Section 2" in c for c in chunks)
