"""Batch ingest ZIM files into RAG."""
import httpx
import time

BASE = "http://127.0.0.1:8003"
HEADERS = {"X-Auth-Key": "jarvis-v3.1"}

files = [
    "data/knowledge/zim_loader/devdocs_en_docker_2026-01.zim",
    "data/knowledge/zim_loader/devdocs_en_git_2026-01.zim",
    "data/knowledge/zim_loader/devdocs_en_bash_2026-01.zim",
    "data/knowledge/zim_loader/freecodecamp_en_all_2026-02.zim",
    "data/knowledge/zim_loader/based.cooking_en_all_2026-02.zim",
    "data/knowledge/zim_loader/nhs.uk_en_medicines_2025-12.zim",
    "data/knowledge/zim_loader/foss.cooking_en_all_2026-02.zim",
    "data/knowledge/zim_loader/zimgit-medicine_en_2024-08.zim",
    "data/knowledge/zim_loader/fas-military-medicine_en_2025-06.zim",
]

for f in files:
    name = f.split("/")[-1]
    print(f"Ingesting {name}...")
    try:
        r = httpx.post(f"{BASE}/nomad/zim/ingest",
            json={"path": f},
            headers=HEADERS,
            timeout=30
        )
        print(f"  Started: {r.json()}")
    except Exception as e:
        print(f"  Error starting: {e}")

# Wait and check status
time.sleep(10)
r = httpx.get(f"{BASE}/nomad/zim/status", headers=HEADERS, timeout=5)
print(f"\nStatus: {r.json()}")

# Check RAG document count
r = httpx.get(f"{BASE}/rag/health", headers=HEADERS, timeout=5)
print(f"RAG documents: {r.json().get('documents', 0)}")
