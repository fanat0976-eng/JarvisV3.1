"""Tests for ZIM adapter (formerly Wikipedia adapter)."""
import pytest
from plugins.nomad.sources.zim import ZimAdapter


def test_zim_adapter_init():
    adapter = ZimAdapter()
    assert adapter.language == "en"


def test_zim_get_collections():
    adapter = ZimAdapter()
    collections = adapter.get_collections()
    assert len(collections) > 0


def test_zim_get_collection():
    adapter = ZimAdapter()
    collection = adapter.get_collection("medicine")
    assert collection is not None
    assert collection["name"] == "Medicine"


def test_zim_parse_article():
    adapter = ZimAdapter()
    # Test that parse_zim method exists
    assert hasattr(adapter, 'parse_zim')