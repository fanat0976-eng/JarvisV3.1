"""
Ingest Python stdlib documentation into RAG.
Downloads docs.python.org pages, extracts text, chunks, and sends to RAG.
"""
import os
import sys
import time
import json
import httpx
from pathlib import Path
from bs4 import BeautifulSoup

RAG_URL = "http://127.0.0.1:8003/rag/add_batch"
AUTH_KEY = "jarvis-v3.1"
DATA_DIR = Path(__file__).parent.parent / "data" / "knowledge" / "python_docs"
CHUNK_SIZE = 1500
OVERLAP = 200

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JarvisBot/1.0)",
    "Accept": "text/html",
}

# Key Python stdlib modules to index
MODULES = [
    ("builtins", "https://docs.python.org/3/library/builtins.html"),
    ("os", "https://docs.python.org/3/library/os.html"),
    ("sys", "https://docs.python.org/3/library/sys.html"),
    ("pathlib", "https://docs.python.org/3/library/pathlib.html"),
    ("json", "https://docs.python.org/3/library/json.html"),
    ("re", "https://docs.python.org/3/library/re.html"),
    ("datetime", "https://docs.python.org/3/library/datetime.html"),
    ("collections", "https://docs.python.org/3/library/collections.html"),
    ("functools", "https://docs.python.org/3/library/functools.html"),
    ("itertools", "https://docs.python.org/3/library/itertools.html"),
    ("typing", "https://docs.python.org/3/library/typing.html"),
    ("asyncio", "https://docs.python.org/3/library/asyncio.html"),
    ("http", "https://docs.python.org/3/library/http.html"),
    ("urllib", "https://docs.python.org/3/library/urllib.html"),
    ("sqlite3", "https://docs.python.org/3/library/sqlite3.html"),
    ("threading", "https://docs.python.org/3/library/threading.html"),
    ("multiprocessing", "https://docs.python.org/3/library/multiprocessing.html"),
    ("subprocess", "https://docs.python.org/3/library/subprocess.html"),
    ("logging", "https://docs.python.org/3/library/logging.html"),
    ("unittest", "https://docs.python.org/3/library/unittest.html"),
    ("argparse", "https://docs.python.org/3/library/argparse.html"),
    ("csv", "https://docs.python.org/3/library/csv.html"),
    ("xml", "https://docs.python.org/3/library/xml.html"),
    ("html", "https://docs.python.org/3/library/html.html"),
    ("hashlib", "https://docs.python.org/3/library/hashlib.html"),
    ("base64", "https://docs.python.org/3/library/base64.html"),
    ("struct", "https://docs.python.org/3/library/struct.html"),
    ("io", "https://docs.python.org/3/library/io.html"),
    ("contextlib", "https://docs.python.org/3/library/contextlib.html"),
    ("dataclasses", "https://docs.python.org/3/library/dataclasses.html"),
    ("enum", "https://docs.python.org/3/library/enum.html"),
    ("abc", "https://docs.python.org/3/library/abc.html"),
    ("copy", "https://docs.python.org/3/library/copy.html"),
    ("pprint", "https://docs.python.org/3/library/pprint.html"),
    ("textwrap", "https://docs.python.org/3/library/textwrap.html"),
    ("string", "https://docs.python.org/3/library/string.html"),
    ("fnmatch", "https://docs.python.org/3/library/fnmatch.html"),
    ("glob", "https://docs.python.org/3/library/glob.html"),
    ("shutil", "https://docs.python.org/3/library/shutil.html"),
    ("tempfile", "https://docs.python.org/3/library/tempfile.html"),
    ("warnings", "https://docs.python.org/3/library/warnings.html"),
    ("traceback", "https://docs.python.org/3/library/traceback.html"),
    ("inspect", "https://docs.python.org/3/library/inspect.html"),
    ("platform", "https://docs.python.org/3/library/platform.html"),
]


def fetch_page(url: str) -> str:
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        r = client.get(url, headers=HEADERS)
        r.raise_for_status()
        return r.text


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for el in soup(["script", "style", "nav", "footer", "header", "aside"]):
        el.decompose()
    content = soup.find("div", class_="body")
    if not content:
        content = soup.find("div", class_="document")
    if not content:
        content = soup.find("body")
    if not content:
        return ""
    text = content.get_text(separator="\n", strip=True)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def send_to_rag(documents: list[dict]) -> bool:
    try:
        r = httpx.post(
            RAG_URL,
            json={"documents": documents},
            headers={"X-Auth-Key": AUTH_KEY, "Content-Type": "application/json"},
            timeout=120,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"  RAG error: {e}")
        return False


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    total_chunks = 0
    total_modules = 0

    print(f"Python docs: {len(MODULES)} modules to index")
    print("=" * 60)

    for name, url in MODULES:
        print(f"  [{name}] Fetching {url}...")
        try:
            html = fetch_page(url)
            text = extract_text(html)
            if len(text) < 100:
                print(f"  [{name}] Skipped (too short: {len(text)} chars)")
                continue
            save_path = DATA_DIR / f"{name}.txt"
            save_path.write_text(text, encoding="utf-8")
            chunks = chunk_text(text)
            documents = [
                {
                    "text": chunk,
                    "id": f"py3_{name}_{i}",
                    "metadata": {
                        "source": "python_docs",
                        "module": name,
                        "url": url,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                }
                for i, chunk in enumerate(chunks)
            ]
            if send_to_rag(documents):
                total_chunks += len(chunks)
                total_modules += 1
                print(f"  [{name}] OK: {len(chunks)} chunks ({len(text)} chars)")
            else:
                print(f"  [{name}] FAILED to send to RAG")
        except Exception as e:
            print(f"  [{name}] Error: {e}")

        time.sleep(0.5)

    print("=" * 60)
    print(f"Done: {total_modules}/{len(MODULES)} modules, {total_chunks} chunks ingested")


if __name__ == "__main__":
    main()
