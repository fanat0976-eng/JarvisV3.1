"""
TTS Bridge plugin — edge-tts (Microsoft Neural voices).
"""
import os
import uuid
import asyncio
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse

router = APIRouter()

AUDIO_DIR = str(Path(__file__).parent.parent.parent / "data" / "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

VOICES = {
    "dmitry": "ru-RU-DmitryNeural",
    "svetlana": "ru-RU-SvetlanaNeural",
}


def on_shutdown():
    for f in Path(AUDIO_DIR).glob("tts_*.mp3"):
        try:
            f.unlink()
        except Exception:
            pass


@router.get("/health")
def health():
    return {"status": "ok", "engine": "edge-tts", "voices": list(VOICES.keys())}


@router.get("/voices")
def voices():
    return {"voices": [
        {"id": "dmitry", "name": "Dmitry", "engine": "edge-tts"},
        {"id": "svetlana", "name": "Svetlana", "engine": "edge-tts"},
    ]}


@router.post("/speak")
async def speak(request: Request):
    data = await request.json()
    text = data.get("text", "")
    voice = data.get("voice", "dmitry")
    if not text:
        return JSONResponse({"error": "No text"}, status_code=400)
    voice_id = VOICES.get(voice, "ru-RU-DmitryNeural")
    try:
        import edge_tts
        comm = edge_tts.Communicate(text, voice_id)
        audio_data = b""
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return StreamingResponse(iter([audio_data]), media_type="audio/mpeg")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/speak/base64")
async def speak_base64(request: Request):
    data = await request.json()
    text = data.get("text", "")
    voice = data.get("voice", "dmitry")
    if not text:
        return JSONResponse({"error": "No text"}, status_code=400)
    voice_id = VOICES.get(voice, "ru-RU-DmitryNeural")
    try:
        import edge_tts
        import base64
        comm = edge_tts.Communicate(text, voice_id)
        audio_data = b""
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return {"status": "ok", "audio_b64": base64.b64encode(audio_data).decode(), "engine": "edge-tts"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename or not filename.startswith("tts_"):
        return JSONResponse({"error": "Invalid filename"}, status_code=400)
    filepath = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(filepath):
        return JSONResponse({"error": "Not found"}, status_code=404)
    return FileResponse(filepath, media_type="audio/mpeg")
