"""Simple Wikipedia download script."""
import httpx
from pathlib import Path

url = "https://dumps.wikimedia.org/other/kiwix/zim/wikipedia/wikipedia_ru_all_mini_2026-04.zim"
zim_path = Path("data/knowledge/wikipedia/ruwiki_mini.zim")

print(f"Downloading: {url}")
print(f"Target: {zim_path}")

try:
    with httpx.stream("GET", url, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        print(f"Total size: {total/1024/1024:.0f} MB")

        downloaded = 0
        with open(zim_path, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=1024*1024):
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded % (50*1024*1024) == 0:
                    print(f"Downloaded: {downloaded/1024/1024:.0f} MB / {total/1024/1024:.0f} MB ({downloaded/total*100:.1f}%)")

        print(f"Complete! Size: {zim_path.stat().st_size/1024/1024:.0f} MB")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()