"""
NPU Inference — OpenVINO inference engine с NPU/CPU fallback.
Конвертация GGUF → OpenVINO IR и inference.
"""
import os
import time
import subprocess
from pathlib import Path

try:
    from openvino import Core, CompiledModel
    HAS_OV = True
except ImportError:
    HAS_OV = False


class NPUEngine:
    def __init__(self):
        self.core = Core() if HAS_OV else None
        self.compiled_model = None
        self.preferred_device = "NPU"
        self._check_devices()

    def _check_devices(self):
        if not self.core:
            self.available_devices = []
            self.npu_available = False
            return
        self.available_devices = self.core.available_devices
        self.npu_available = "NPU" in self.available_devices
        if not self.npu_available:
            self.preferred_device = "CPU"

    def get_status(self) -> dict:
        return {
            "openvino_available": HAS_OV,
            "devices": self.available_devices if HAS_OV else [],
            "npu_available": self.npu_available,
            "preferred_device": self.preferred_device,
            "model_loaded": self.compiled_model is not None,
        }

    def load_model(self, model_path: str, device: str = None) -> dict:
        if not self.core:
            return {"status": "error", "error": "OpenVINO not available"}

        device = device or self.preferred_device
        if device not in self.available_devices:
            return {"status": "error", "error": f"Device {device} not available. Use: {self.available_devices}"}

        try:
            start = time.time()
            model = self.core.read_model(model_path)
            self.compiled_model = self.core.compile_model(model, device)
            load_time = time.time() - start
            return {
                "status": "ok",
                "device": device,
                "load_time": round(load_time, 3),
                "inputs": len(self.compiled_model.inputs),
                "outputs": len(self.compiled_model.outputs),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def benchmark(self, model_path: str, device: str = None, iterations: int = 10) -> dict:
        if not self.core:
            return {"status": "error", "error": "OpenVINO not available"}

        device = device or self.preferred_device
        try:
            model = self.core.read_model(model_path)
            compiled = self.core.compile_model(model, device)

            input_shape = compiled.inputs[0].shape
            import numpy as np
            dummy_input = np.random.randn(*input_shape).astype(np.float32)

            times = []
            for _ in range(iterations):
                start = time.time()
                compiled(dummy_input)
                times.append(time.time() - start)

            avg_ms = (sum(times) / len(times)) * 1000
            return {
                "status": "ok",
                "device": device,
                "iterations": iterations,
                "avg_ms": round(avg_ms, 2),
                "min_ms": round(min(times) * 1000, 2),
                "max_ms": round(max(times) * 1000, 2),
                "throughput": round(1000 / avg_ms, 1) if avg_ms > 0 else 0,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


npu_engine = NPUEngine()
