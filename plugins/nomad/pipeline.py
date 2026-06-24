# plugins/nomad/pipeline.py
"""Pipeline orchestration for NOMAD sources."""
import json
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


class Pipeline:
    def __init__(self, source_name: str, data_dir: str = "data/knowledge"):
        self.source_name = source_name
        self.data_dir = Path(data_dir) / source_name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.data_dir / "status.json"
        self._lock = threading.Lock()

    def get_status(self) -> dict:
        """Get current pipeline status."""
        if self.status_file.exists():
            try:
                with open(self.status_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return {
            "source": self.source_name,
            "status": "idle",
            "progress": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def update_status(self, status: str, **kwargs: Any) -> None:
        """Update pipeline status.
        
        Args:
            status: New status value (e.g., 'downloading', 'processing', 'ready')
            **kwargs: Additional status fields to merge (e.g., progress=50, error='...')
        """
        with self._lock:
            current = self.get_status()
            current["status"] = status
            current["updated_at"] = datetime.now(timezone.utc).isoformat()
            current.update(kwargs)
            with open(self.status_file, "w") as f:
                json.dump(current, f, indent=2)