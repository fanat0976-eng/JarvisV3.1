"""
Android plugin — WebSocket bridge for mobile clients.
Supports: chat, agent mode, streaming, health check.
Uses async httpx to avoid blocking event loop.
"""
import json
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import httpx

router = APIRouter()

CHAT_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"
connected_clients = set()


def _load_config():
    global CHAT_URL, AUTH_KEY
    try:
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / "core" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        server = config.get("server", {})
        port = server.get("port", 8003)
        host = server.get("host", "127.0.0.1")
        CHAT_URL = f"http://{host}:{port}"
        AUTH_KEY = server.get("auth_key", AUTH_KEY)
    except Exception:
        pass


_load_config()


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


@router.get("/health")
def health():
    return {"status": "ok", "clients": len(connected_clients)}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                msg_type = data.get("type", "chat")
                message = data.get("message", "")

                if msg_type == "health":
                    await websocket.send_json({
                        "type": "health",
                        "core_online": True,
                        "clients": len(connected_clients),
                    })
                    continue

                if not message:
                    await websocket.send_json({"type": "error", "message": "No message"})
                    continue

                if msg_type == "agent":
                    await handle_agent(websocket, message, data)
                else:
                    await handle_chat(websocket, message)

            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except Exception:
        connected_clients.discard(websocket)


async def handle_chat(websocket: WebSocket, message: str):
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=300) as client:
            r = await client.post(f"{CHAT_URL}/brain/chat", json={
                "messages": [{"role": "user", "content": message}],
            }, headers=get_headers())
            reply = r.json().get("reply", "Error")
    except Exception as e:
        reply = f"Error: {str(e)}"

    await websocket.send_json({"type": "reply", "message": reply})


async def handle_agent(websocket: WebSocket, message: str, data: dict):
    max_iterations = data.get("max_iterations", 3)
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=300) as client:
            r = await client.post(f"{CHAT_URL}/brain/agent", json={
                "messages": [{"role": "user", "content": message}],
                "max_iterations": max_iterations,
            }, headers=get_headers())
            result = r.json()
        reply = result.get("reply", "Error")
        tool_calls = result.get("tool_calls", 0)
        tool_results = result.get("tool_results", [])

        await websocket.send_json({
            "type": "agent_reply",
            "message": reply,
            "tool_calls": tool_calls,
            "tool_results": [
                {"tool": tr.get("tool"), "status": tr.get("status")}
                for tr in tool_results
            ],
            "iterations": result.get("iterations", 0),
            "model": result.get("model", ""),
        })
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


@router.post("/send")
async def http_send(request: Request):
    """HTTP fallback for sending messages."""
    data = await request.json()
    message = data.get("message", "")
    msg_type = data.get("type", "chat")

    if not message:
        return JSONResponse({"error": "No message"}, status_code=400)

    try:
        async with httpx.AsyncClient(trust_env=False, timeout=300) as client:
            if msg_type == "agent":
                r = await client.post(f"{CHAT_URL}/brain/agent", json={
                    "messages": [{"role": "user", "content": message}],
                    "max_iterations": data.get("max_iterations", 3),
                }, headers=get_headers())
            else:
                r = await client.post(f"{CHAT_URL}/brain/chat", json={
                    "messages": [{"role": "user", "content": message}],
                }, headers=get_headers())
            return r.json()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
