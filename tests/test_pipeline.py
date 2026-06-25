"""Tests for pipeline orchestrator."""
from plugins.nomad.pipeline import Pipeline


def test_pipeline_status():
    pipeline = Pipeline("test_source")
    if pipeline.status_file.exists():
        pipeline.status_file.unlink()
    status = pipeline.get_status()
    assert status["source"] == "test_source"
    assert status["status"] == "idle"


def test_pipeline_update_status():
    pipeline = Pipeline("test_source")
    pipeline.update_status("downloading", progress=50)
    status = pipeline.get_status()
    assert status["status"] == "downloading"
    assert status["progress"] == 50
