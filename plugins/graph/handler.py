"""
Graph Plugin — Knowledge Graph API.
"""
import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from plugins.graph.graph_engine import GraphEngine

router = APIRouter()

DATA_DIR = str(Path(__file__).parent.parent.parent / "data")
DB_PATH = os.path.join(DATA_DIR, "knowledge_graph.db")

engine = GraphEngine(DB_PATH)


@router.get("/health")
def health():
    stats = engine.stats()
    return {"status": "ok", **stats}


@router.post("/entity")
async def add_entity(request: Request):
    data = await request.json()
    entity_id = data.get("id", "")
    entity_type = data.get("type", "")
    name = data.get("name", "")
    metadata = data.get("metadata", {})

    if not entity_id or not entity_type or not name:
        return JSONResponse({"error": "id, type, name required"}, status_code=400)

    result = engine.add_entity(entity_id, entity_type, name, metadata)
    return {"status": "ok", **result}


@router.get("/entity/{entity_id}")
def get_entity(entity_id: str):
    entity = engine.get_entity(entity_id)
    if not entity:
        return JSONResponse({"error": "not found"}, status_code=404)
    return entity


@router.post("/relation")
async def add_relation(request: Request):
    data = await request.json()
    source = data.get("source", "")
    target = data.get("target", "")
    relation_type = data.get("relation", "")
    weight = data.get("weight", 1.0)
    metadata = data.get("metadata", {})

    if not source or not target or not relation_type:
        return JSONResponse({"error": "source, target, relation required"}, status_code=400)

    result = engine.add_relation(source, target, relation_type, weight, metadata)
    return {"status": "ok", **result}


@router.get("/neighbors/{entity_id}")
def get_neighbors(entity_id: str, depth: int = 1):
    return engine.neighbors(entity_id, depth)


@router.get("/path/{source}/{target}")
def get_path(source: str, target: str):
    return engine.shortest_path(source, target)


@router.post("/query")
async def query_graph(request: Request):
    data = await request.json()
    relation_type = data.get("relation", None)
    entity_type = data.get("entity_type", None)
    limit = data.get("limit", 50)
    results = engine.query(relation_type, entity_type, limit)
    return {"results": results, "count": len(results)}


@router.get("/stats")
def graph_stats():
    return engine.stats()


@router.post("/refresh")
def refresh_graph():
    engine.refresh()
    return {"status": "ok", **engine.stats()}


def on_startup():
    print("  [graph] Initialized: networkx + SQLite knowledge graph")


def on_shutdown():
    print("  [graph] Shutdown complete")
