"""
STT plugin — Speech-to-Text via Whisper (local).
Adapted from V2.1 for V3.1.
"""
import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter()

MODEL_DIR = str(Path(__file__).parent.parent.parent / "models")
WHISPER_MODEL = None
WHISPER_MODEL_NAME = "base"


def get_model():
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        try:
            import whisper
            WHISPER_MODEL = whisper.load_model(WHISPER_MODEL_NAME, download_root=MODEL_DIR)
        except Exception:
            return None
    return WHISPER_MODEL


@router.get("/health")
def health():
    return {"status": "ok", "model": WHISPER_MODEL_NAME, "loaded": WHISPER_MODEL is not None}


@router.post("/transcribe")
async def transcribe(request: Request):
    data = await request.json()
    filepath = data.get("path", "")
    language = data.get("language", None)
    if not filepath or not os.path.exists(filepath):
        return JSONResponse({"error": f"File not found: {filepath}"}, status_code=404)
    try:
        model = get_model()
        if model is None:
            return JSONResponse({"error": "Whisper not available"}, status_code=503)
        options = {}
        if language:
            options["language"] = language
        result = model.transcribe(filepath, **options)
        return {
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "segments": [{"start": s["start"], "end": s["end"], "text": s["text"]}
                         for s in result.get("segments", [])],
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/transcribe/upload")
async def transcribe_upload(file: UploadFile = File(...), language: str = None):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        model = get_model()
        if model is None:
            return JSONResponse({"error": "Whisper not available"}, status_code=503)
        options = {}
        if language:
            options["language"] = language
        result = model.transcribe(tmp_path, **options)
        return {
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "segments": [{"start": s["start"], "end": s["end"], "text": s["text"]}
                         for s in result.get("segments", [])],
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/transcribe/buffer")
async def transcribe_buffer(request: Request):
    data = await request.json()
    audio_b64 = data.get("audio", "")
    language = data.get("language", None)
    if not audio_b64:
        return JSONResponse({"error": "No audio data"}, status_code=400)
    tmp_path = None
    try:
        import base64
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        model = get_model()
        if model is None:
            return JSONResponse({"error": "Whisper not available"}, status_code=503)
        options = {}
        if language:
            options["language"] = language
        result = model.transcribe(tmp_path, **options)
        return {"text": result["text"], "language": result.get("language", "unknown")}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/models")
def list_models():
    return {
        "current": WHISPER_MODEL_NAME,
        "available": ["tiny", "base", "small", "medium", "large"],
        "sizes": {"tiny": "39MB", "base": "150MB", "small": "460MB", "medium": "1.5GB", "large": "3GB"},
    }
