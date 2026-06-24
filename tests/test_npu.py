"""Unit tests for NPU plugin."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.npu.inference import NPUEngine


class TestNPUEngine:
    def setup_method(self):
        self.engine = NPUEngine()

    def test_status(self):
        status = self.engine.get_status()
        assert "openvino_available" in status
        assert "devices" in status
        assert "npu_available" in status

    def test_devices_listed(self):
        status = self.engine.get_status()
        assert len(status["devices"]) > 0
        assert "CPU" in status["devices"]

    def test_npu_detected(self):
        status = self.engine.get_status()
        assert status["npu_available"] is True
        assert "NPU" in status["devices"]

    def test_preferred_device(self):
        assert self.engine.preferred_device == "NPU"

    def test_load_model_missing(self):
        result = self.engine.load_model("nonexistent.xml")
        assert result["status"] == "error"

    def test_benchmark_missing(self):
        result = self.engine.benchmark("nonexistent.xml")
        assert result["status"] == "error"
