"""
Jarvis V3.1 — Core Server
FastAPI orchestrator: plugin system, event bus, cache, auth.
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.plugin_manager import PluginManager
from core.event_bus import event_bus
from core.cache import cache
from core.db import close_all

manager = PluginManager()
config = manager.config
server_config = config.get("server", {})

loaded_plugins = manager.load_all()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("  J.A.R.V.I.S V3.1 — AI OS")
    print(f"  Port: {server_config.get('port', 8003)}")
    print("=" * 60)

    for name, info in loaded_plugins.items():
        print(f"  [+] {name}: {info.get('description', '')}")

    print(f"  Loaded: {len(loaded_plugins)} plugins")
    print("  Event Bus: ready")
    print("  Cache: ready")
    print("=" * 60)

    event_bus.emit("server.startup", {"plugins": list(loaded_plugins.keys())}, source="core")
    manager.startup_all()
    community_sandbox.startup_all()

    yield

    event_bus.emit("server.shutdown", {}, source="core")
    community_sandbox.shutdown_all()
    manager.shutdown_all()
    close_all()
    print("\nShutting down...")


app = FastAPI(
    title=server_config.get("title", "J.A.R.V.I.S V3.1"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.get("cors_origins", ["http://localhost:8003"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_KEY = server_config.get("auth_key", "")


def verify_auth(request: Request) -> bool:
    if not AUTH_KEY:
        return True
    key = request.headers.get("X-Auth-Key", "")
    return key == AUTH_KEY


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    path = request.url.path
    if path == "/health" or path.endswith("/health") or path.endswith("/ws"):
        return await call_next(request)
    if path.startswith("/dashboard") or path == "/":
        return await call_next(request)
    if "/audio/" in path:
        return await call_next(request)
    if not verify_auth(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)


@app.get("/health")
def health():
    plugins = manager.get_status()
    online = sum(1 for p in plugins.values() if p["loaded"])
    return {
        "status": "ok",
        "version": "3.1",
        "plugins_loaded": online,
        "plugins_total": len(plugins),
        "plugins": plugins,
        "event_bus": event_bus.get_subscribers(),
        "cache": cache.stats(),
    }


@app.get("/plugins")
def list_plugins():
    return manager.get_status()


@app.post("/plugins/{name}/toggle")
async def toggle_plugin(name: str, request: Request):
    body = await request.json()
    enabled = body.get("enabled", True)
    ok = manager.toggle_plugin(name, enabled)
    if not ok:
        return JSONResponse({"error": f"Plugin '{name}' not found"}, status_code=404)
    return {"status": "ok", "plugin": name, "enabled": enabled}


@app.get("/events")
def get_events(event_type: str = None, limit: int = 20):
    return {"events": event_bus.history(event_type, limit)}


@app.post("/events/publish")
async def publish_event(request: Request):
    data = await request.json()
    topic = data.get("topic", "")
    event_data = data.get("data", {})
    source = data.get("source", "api")
    if not topic:
        return JSONResponse({"error": "topic required"}, status_code=400)
    event_bus.emit(topic, event_data, source)
    return {"status": "ok", "topic": topic}


@app.get("/cache/stats")
def cache_stats():
    return cache.stats()


@app.post("/cache/clear")
def cache_clear():
    cache.clear()
    return {"status": "ok"}


for name, info in loaded_plugins.items():
    router = info.get("router")
    if router:
        app.include_router(router, prefix=f"/{name}")

# Community plugins (imported here to avoid circular imports)
from core.plugin_sandbox import PluginSandbox  # noqa: E402
community_sandbox = PluginSandbox()
community_manifests = community_sandbox.discover_community()
for manifest in community_manifests:
    info = community_sandbox.load_plugin(manifest.name)
    if info:
        router = info.get("router")
        if router:
            app.include_router(router, prefix=f"/{manifest.name}")
        loaded_plugins[f"community:{manifest.name}"] = info


@app.get("/plugins/community")
def list_community_plugins():
    manifests = community_sandbox.discover_community()
    return {
        "plugins": [
            {
                "name": m.name,
                "version": m.version,
                "description": m.description,
                "author": m.author,
                "enabled": m.enabled,
                "loaded": m.name in [k.split(":")[1] for k in loaded_plugins if k.startswith("community:")],
            }
            for m in manifests
        ]
    }


WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/dashboard", response_class=HTMLResponse)
    @app.get("/dashboard/", response_class=HTMLResponse)
    def dashboard():
        index = WEB_DIR / "index.html"
        if index.exists():
            return HTMLResponse(content=index.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    port = server_config.get("port", 8003)
    host = server_config.get("host", "127.0.0.1")
    uvicorn.run(app, host=host, port=port, log_level="info")
