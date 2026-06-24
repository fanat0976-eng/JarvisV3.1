"""
Download full Russian Wikipedia (NoPic version, ~13.4 GB)
This script runs in the background and saves progress to status.json
"""
import httpx
import json
from pathlib import Path
from datetime import datetime

# Configuration - Mini version (4.8 GB, text only, no images)
ZIM_URL = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/wikipedia_ru_all_mini_2026-04.zim"
ZIM_PATH = Path("data/knowledge/wikipedia/ruwiki_mini.zim")
STATUS_PATH = Path("data/knowledge/wikipedia/download_status.json")

# Create directory
ZIM_PATH.parent.mkdir(parents=True, exist_ok=True)


def update_status(status: str, **kwargs):
    """Update download status."""
    data = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "url": ZIM_URL,
        "file": str(ZIM_PATH),
        **kwargs
    }
    with open(STATUS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status}")


def download():
    """Download ZIM file with progress tracking."""
    update_status("starting")

    try:
        with httpx.stream("GET", ZIM_URL, timeout=300) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            start_time = datetime.now()

            update_status("downloading", total=total, downloaded=0, progress=0)

            with open(ZIM_PATH, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Calculate progress and speed
                    elapsed = (datetime.now() - start_time).total_seconds()
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    percent = (downloaded / total * 100) if total > 0 else 0
                    eta = (total - downloaded) / speed if speed > 0 else 0

                    # Update status every 10MB
                    if downloaded % (10 * 1024 * 1024) < 1024 * 1024:
                        update_status(
                            "downloading",
                            total=total,
                            downloaded=downloaded,
                            progress=round(percent, 1),
                            speed_mbps=round(speed / 1024 / 1024, 2),
                            eta_seconds=round(eta)
                        )
                        print(f"  Progress: {percent:.1f}% ({downloaded/1024/1024:.0f}/{total/1024/1024:.0f} MB) - Speed: {speed/1024/1024:.1f} MB/s - ETA: {eta/60:.0f} min")

            update_status("completed", size=ZIM_PATH.stat().st_size)
            print(f"\n✅ Download complete! Size: {ZIM_PATH.stat().st_size / 1024 / 1024 / 1024:.2f} GB")

    except Exception as e:
        update_status("error", error=str(e))
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    print(f"Downloading Russian Wikipedia (NoPic): {ZIM_URL}")
    print(f"Target: {ZIM_PATH}")
    print(f"Estimated size: ~13.4 GB")
    print("=" * 60)
    download()