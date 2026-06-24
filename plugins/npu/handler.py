"""
NPU Plugin — Intel NPU acceleration API.
OpenVINO backend для inference на NPU.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from plugins.npu.inference import npu_engine

router = APIRouter()


@router.get("/health")
def health():
    return npu_engine.get_status()


@router.post("/load")
async def load_model(request: Request):
    data = await request.json()
    model_path = data.get("path", "")
    device = data.get("device", None)

    if not model_path:
        return JSONResponse({"error": "path required"}, status_code=400)

    result = npu_engine.load_model(model_path, device)
    return result


@router.post("/benchmark")
async def benchmark(request: Request):
    data = await request.json()
    model_path = data.get("path", "")
    device = data.get("device", None)
    iterations = data.get("iterations", 10)

    if not model_path:
        return JSONResponse({"error": "path required"}, status_code=400)

    result = npu_engine.benchmark(model_path, device, iterations)
    return result


@router.get("/devices")
def list_devices():
    return {
        "devices": npu_engine.available_devices,
        "npu_available": npu_engine.npu_available,
        "preferred": npu_engine.preferred_device,
    }


def on_startup():
    status = "NPU ready" if npu_engine.npu_available else "NPU not available, using CPU"
    print(f"  [npu] Initialized: {status}")


def on_shutdown():
    print("  [npu] Shutdown complete")
