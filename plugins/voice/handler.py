"""
Voice Plugin — Full voice conversation loop for Jarvis V3.1.
Audio → STT (Whisper) → Brain → TTS (edge-tts) → Audio response.
Also: audio file transcription, video subtitle extraction.
"""
import os
import json
import tempfile
import subprocess
import httpx
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter()

BASE_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "audio"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WHISPER_MODEL = None
WHISPER_MODEL_NAME = "base"


def _load_auth_key():
    global AUTH_KEY, BASE_URL
    try:
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / "core" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        server = config.get("server", {})
        port = server.get("port", 8003)
        host = server.get("host", "127.0.0.1")
        BASE_URL = f"http://{host}:{port}"
        AUTH_KEY = server.get("auth_key", AUTH_KEY)
    except Exception:
        pass


_load_auth_key()


def _get_whisper():
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        try:
            import whisper
            model_dir = str(Path(__file__).parent.parent.parent / "models")
            WHISPER_MODEL = whisper.load_model(WHISPER_MODEL_NAME, download_root=model_dir)
        except Exception:
            return None
    return WHISPER_MODEL


def _headers():
    return {"X-Auth-Key": AUTH_KEY, "Content-Type": "application/json"}


def _transcribe_file(filepath: str, language: str = None) -> dict:
    model = _get_whisper()
    if model is None:
        return {"error": "Whisper not available"}
    opts = {}
    if language:
        opts["language"] = language
    result = model.transcribe(filepath, **opts)
    return {
        "text": result["text"],
        "language": result.get("language", "unknown"),
        "segments": [
            {"start": s["start"], "end": s["end"], "text": s["text"]}
            for s in result.get("segments", [])
        ],
    }


async def _brain_chat(text: str, session_id: str = "") -> str:
    async with httpx.AsyncClient(trust_env=False, timeout=120) as client:
        r = await client.post(
            f"{BASE_URL}/brain/chat",
            json={
                "messages": [{"role": "user", "content": text}],
                "use_memory": True,
                "session_id": session_id,
            },
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json().get("reply", "")


async def _tts_speak(text: str, voice: str = "dmitry") -> bytes:
    async with httpx.AsyncClient(trust_env=False, timeout=60) as client:
        r = await client.post(
            f"{BASE_URL}/tts_bridge/speak",
            json={"text": text, "voice": voice},
            headers=_headers(),
        )
        r.raise_for_status()
        filename = r.json().get("filename", "")
        if not filename:
            return b""
        audio_r = await client.get(
            f"{BASE_URL}/tts_bridge/audio/{filename}",
            headers=_headers(),
        )
        return audio_r.content


def _extract_video_subtitles(video_path: str) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", video_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {"has_subtitles": False, "error": "ffprobe not found or failed"}
        info = json.loads(result.stdout)
        streams = info.get("streams", [])
        subtitle_streams = [s for s in streams if s.get("codec_type") == "subtitle"]
        return {
            "has_subtitles": len(subtitle_streams) > 0,
            "subtitle_streams": len(subtitle_streams),
            "streams": [
                {"index": s["index"], "codec": s.get("codec_name"), "language": s.get("tags", {}).get("language")}
                for s in subtitle_streams
            ],
        }
    except Exception as e:
        return {"has_subtitles": False, "error": str(e)}


def _extract_audio_from_video(video_path: str) -> str:
    audio_path = tempfile.mktemp(suffix=".wav")
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path, "-y"],
            capture_output=True, timeout=120,
        )
        if result.returncode != 0:
            return ""
        return audio_path
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


# ── Endpoints ──

@router.get("/health")
def health():
    try:
        import whisper  # noqa: F401
        whisper_importable = True
    except ImportError:
        whisper_importable = False
    return {
        "status": "ok",
        "whisper_available": whisper_importable,
        "whisper_model": WHISPER_MODEL_NAME,
        "whisper_loaded": WHISPER_MODEL is not None,
    }


@router.post("/converse")
async def voice_converse(request: Request):
    """Full voice conversation: audio in → STT → Brain → TTS → audio out."""
    data = await request.json()
    audio_b64 = data.get("audio", "")
    language = data.get("language", None)
    voice = data.get("voice", "dmitry")
    session_id = data.get("session_id", "")

    if not audio_b64:
        return JSONResponse({"error": "No audio data"}, status_code=400)

    tmp_path = None
    try:
        import base64
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        stt_result = _transcribe_file(tmp_path, language)
        if "error" in stt_result:
            return JSONResponse({"error": stt_result["error"]}, status_code=500)

        user_text = stt_result["text"]
        if not user_text.strip():
            return JSONResponse({"error": "No speech detected"}, status_code=400)

        reply_text = await _brain_chat(user_text, session_id)

        tts_audio = await _tts_speak(reply_text, voice)
        audio_out_b64 = ""
        if tts_audio:
            audio_out_b64 = base64.b64encode(tts_audio).decode()

        return {
            "user_text": user_text,
            "reply_text": reply_text,
            "audio_b64": audio_out_b64,
            "language": stt_result.get("language"),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/transcribe")
async def transcribe_audio(request: Request):
    """Transcribe audio from base64."""
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

        result = _transcribe_file(tmp_path, language)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/transcribe/file")
async def transcribe_file_upload(file: UploadFile = File(...), language: str = None):
    """Transcribe uploaded audio file."""
    tmp_path = None
    try:
        suffix = Path(file.filename).suffix if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = _transcribe_file(tmp_path, language)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/video/subtitles")
async def video_subtitles(request: Request):
    """Extract subtitle info from video file."""
    data = await request.json()
    video_path = data.get("path", "")

    if not video_path or not os.path.exists(video_path):
        return JSONResponse({"error": f"Video not found: {video_path}"}, status_code=404)

    info = _extract_video_subtitles(video_path)
    return info


@router.post("/video/transcribe")
async def video_transcribe(request: Request):
    """Extract audio from video and transcribe."""
    data = await request.json()
    video_path = data.get("path", "")
    language = data.get("language", None)

    if not video_path or not os.path.exists(video_path):
        return JSONResponse({"error": f"Video not found: {video_path}"}, status_code=404)

    audio_path = _extract_audio_from_video(video_path)
    if not audio_path or not os.path.exists(audio_path):
        return JSONResponse({"error": "Failed to extract audio from video"}, status_code=500)

    try:
        result = _transcribe_file(audio_path, language)
        return result
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


@router.post("/video/summarize")
async def video_summarize(request: Request):
    """Extract audio from video → transcribe → summarize via Brain."""
    data = await request.json()
    video_path = data.get("path", "")
    language = data.get("language", None)

    if not video_path or not os.path.exists(video_path):
        return JSONResponse({"error": f"Video not found: {video_path}"}, status_code=404)

    audio_path = _extract_audio_from_video(video_path)
    if not audio_path or not os.path.exists(audio_path):
        return JSONResponse({"error": "Failed to extract audio"}, status_code=500)

    try:
        stt_result = _transcribe_file(audio_path, language)
        if "error" in stt_result:
            return JSONResponse({"error": stt_result["error"]}, status_code=500)

        transcript = stt_result["text"]
        summary_prompt = (
            f"Просуммируй следующий транскрипт видео кратко (5-10 пунктов):\n\n{transcript[:8000]}"
        )
        summary = await _brain_chat(summary_prompt)

        return {
            "transcript_length": len(transcript),
            "transcript_preview": transcript[:500],
            "summary": summary,
            "language": stt_result.get("language"),
        }
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


def on_startup():
    print("  [voice] Initialized: STT + TTS + voice conversation loop")


def on_shutdown():
    pass
