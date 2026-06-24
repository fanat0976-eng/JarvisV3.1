"""
Graph Engine — In-memory knowledge graph via networkx.
SQLite-backed persistence. Supports entities, relations, queries.
"""
import json

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False


class GraphEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        self.graph = nx.DiGraph() if HAS_NX else None
        self._load_from_db()

    def _get_conn(self):
        from core.db import get_graph_conn
        return get_graph_conn()

    def refresh(self):
        """Reload graph from SQLite to pick up external changes."""
        if self.graph is not None:
            self.graph.clear()
            self._load_from_db()

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS graph_entities (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS graph_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                UNIQUE(source, target, relation_type)
            );
            CREATE INDEX IF NOT EXISTS idx_rel_source ON graph_relations(source);
            CREATE INDEX IF NOT EXISTS idx_rel_target ON graph_relations(target);
        """)

    def _load_from_db(self):
        if self.graph is None:
            return
        conn = self._get_conn()

        for row in conn.execute("SELECT id, type, name, metadata FROM graph_entities"):
            self.graph.add_node(row["id"], type=row["type"], name=row["name"],
                                **json.loads(row["metadata"]))

        for row in conn.execute("SELECT source, target, relation_type, weight, metadata FROM graph_relations"):
            self.graph.add_edge(row["source"], row["target"],
                                relation=row["relation_type"], weight=row["weight"],
                                **json.loads(row["metadata"]))

    def add_entity(self, entity_id: str, entity_type: str, name: str, metadata: dict = None) -> dict:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        meta = json.dumps(metadata or {})

        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO graph_entities (id, type, name, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (entity_id, entity_type, name, meta, now)
        )
        conn.commit()

        if self.graph is not None:
            self.graph.add_node(entity_id, type=entity_type, name=name, **(metadata or {}))

        return {"id": entity_id, "type": entity_type, "name": name}

    def add_relation(self, source: str, target: str, relation_type: str,
                     weight: float = 1.0, metadata: dict = None) -> dict:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        meta = json.dumps(metadata or {})

        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO graph_relations (source, target, relation_type, weight, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (source, target, relation_type, weight, meta, now)
        )
        conn.commit()

        if self.graph is not None:
            self.graph.add_edge(source, target, relation=relation_type, weight=weight, **(metadata or {}))

        return {"source": source, "target": target, "relation": relation_type}

    def get_entity(self, entity_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM graph_entities WHERE id = ?", (entity_id,)).fetchone()
        if not row:
            return None
        return dict(row)

    def neighbors(self, entity_id: str, depth: int = 1) -> dict:
        if self.graph is None or entity_id not in self.graph:
            return {"entity": entity_id, "neighbors": []}

        result = []
        visited = set()

        def _traverse(node, current_depth):
            if current_depth > depth or node in visited:
                return
            visited.add(node)
            for neighbor in self.graph.successors(node):
                edge_data = self.graph.edges[node, neighbor]
                result.append({
                    "from": node,
                    "to": neighbor,
                    "relation": edge_data.get("relation", "unknown"),
                    "depth": current_depth,
                })
                _traverse(neighbor, current_depth + 1)
            for neighbor in self.graph.predecessors(node):
                if neighbor not in visited:
                    edge_data = self.graph.edges[neighbor, node]
                    result.append({
                        "from": neighbor,
                        "to": node,
                        "relation": edge_data.get("relation", "unknown"),
                        "depth": current_depth,
                    })

        _traverse(entity_id, 1)
        return {"entity": entity_id, "neighbors": result}

    def shortest_path(self, source: str, target: str) -> dict:
        if self.graph is None:
            return {"error": "graph not available"}
        try:
            path = nx.shortest_path(self.graph, source, target)
            edges = []
            for i in range(len(path) - 1):
                edge_data = self.graph.edges[path[i], path[i + 1]]
                edges.append({
                    "from": path[i],
                    "to": path[i + 1],
                    "relation": edge_data.get("relation", "unknown"),
                })
            return {"path": path, "edges": edges, "length": len(path) - 1}
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return {"path": [], "edges": [], "length": 0, "error": "no path found"}

    def query(self, relation_type: str = None, entity_type: str = None,
              limit: int = 50) -> list[dict]:
        conn = self._get_conn()

        if relation_type:
            rows = conn.execute(
                "SELECT * FROM graph_relations WHERE relation_type = ? LIMIT ?",
                (relation_type, limit)
            ).fetchall()
        elif entity_type:
            rows = conn.execute(
                "SELECT r.* FROM graph_relations r "
                "JOIN graph_entities e ON r.source = e.id OR r.target = e.id "
                "WHERE e.type = ? LIMIT ?",
                (entity_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM graph_relations LIMIT ?", (limit,)
            ).fetchall()

        return [dict(r) for r in rows]

    def stats(self) -> dict:
        conn = self._get_conn()
        entities = conn.execute("SELECT COUNT(*) as c FROM graph_entities").fetchone()[0]
        relations = conn.execute("SELECT COUNT(*) as c FROM graph_relations").fetchone()[0]
        types = conn.execute("SELECT type, COUNT(*) as c FROM graph_entities GROUP BY type").fetchall()
        rel_types = conn.execute(
            "SELECT relation_type, COUNT(*) as c FROM graph_relations GROUP BY relation_type"
        ).fetchall()
        return {
            "entities": entities,
            "relations": relations,
            "entity_types": {r[0]: r[1] for r in types},
            "relation_types": {r[0]: r[1] for r in rel_types},
            "networkx_nodes": self.graph.number_of_nodes() if self.graph else 0,
            "networkx_edges": self.graph.number_of_edges() if self.graph else 0,
        }
