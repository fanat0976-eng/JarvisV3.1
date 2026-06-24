"""Tests for ZIM Loader."""
import pytest
from pathlib import Path
from plugins.nomad.sources.zim import ZimAdapter


@pytest.fixture
def adapter():
    return ZimAdapter()


def test_get_collections(adapter):
    """Test getting collections."""
    collections = adapter.get_collections()
    assert len(collections) > 0
    assert any(c["slug"] == "medicine" for c in collections)


def test_get_collection(adapter):
    """Test getting specific collection."""
    collection = adapter.get_collection("medicine")
    assert collection is not None
    assert collection["name"] == "Medicine"
    assert len(collection["resources"]) > 0


def test_get_collection_not_found(adapter):
    """Test getting non-existent collection."""
    collection = adapter.get_collection("nonexistent")
    assert collection is None


def test_collections_have_required_fields(adapter):
    """Test that collections have required fields."""
    collections = adapter.get_collections()
    for cat in collections:
        assert "name" in cat
        assert "slug" in cat
        assert "resources" in cat
        for resource in cat["resources"]:
            assert "id" in resource
            assert "title" in resource
            assert "url" in resource
            assert "size_mb" in resource


def test_download_from_kiwix(adapter, tmp_path):
    """Test downloading ZIM file."""
    # This test would need network access
    # For now, just test the method exists
    assert hasattr(adapter, 'download_from_kiwix')


def test_parse_zim(adapter):
    """Test parsing ZIM file."""
    # This test would need a real ZIM file
    # For now, just test the method exists
    assert hasattr(adapter, 'parse_zim')


def test_ingest_to_rag(adapter):
    """Test ingest to RAG."""
    # This test would need RAG to be running
    # For now, just test the method exists
    assert hasattr(adapter, 'ingest_to_rag')
