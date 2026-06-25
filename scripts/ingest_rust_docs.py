"""
Ingest Rust documentation into RAG.
Fetches The Rust Book and stdlib docs, extracts text, chunks, sends to RAG.
"""
import time
import httpx
from pathlib import Path
from bs4 import BeautifulSoup

RAG_URL = "http://127.0.0.1:8003/rag/add_batch"
AUTH_KEY = "jarvis-v3.1"
DATA_DIR = Path(__file__).parent.parent / "data" / "knowledge" / "rust_docs"
CHUNK_SIZE = 1500
OVERLAP = 200

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JarvisBot/1.0)",
    "Accept": "text/html",
}

# The Rust Book chapters
BOOK_CHAPTERS = [
    ("getting_started", "https://doc.rust-lang.org/book/ch01-00-getting-started.html"),
    ("installing_rust", "https://doc.rust-lang.org/book/ch01-03-hello-cargo.html"),
    ("common_programming", "https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html"),
    ("variables", "https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html"),
    ("data_types", "https://doc.rust-lang.org/book/ch03-02-data-types.html"),
    ("functions", "https://doc.rust-lang.org/book/ch03-03-how-functions-work.html"),
    ("control_flow", "https://doc.rust-lang.org/book/ch03-05-control-flow.html"),
    ("ownership", "https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html"),
    ("structs", "https://doc.rust-lang.org/book/ch05-00-structs.html"),
    ("enums", "https://doc.rust-lang.org/book/ch06-00-enums.html"),
    ("modules", "https://doc.rust-lang.org/book/ch07-00-managing-growing-projects.html"),
    ("packages_crates", "https://doc.rust-lang.org/book/ch07-01-packages-and-crates.html"),
    ("error_handling", "https://doc.rust-lang.org/book/ch09-00-error-handling.html"),
    ("generics", "https://doc.rust-lang.org/book/ch10-00-generics.html"),
    ("traits", "https://doc.rust-lang.org/book/ch10-02-trait-bounds.html"),
    ("lifetime_annotations", "https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html"),
    ("closures", "https://doc.rust-lang.org/book/ch13-01-closures.html"),
    ("iterators", "https://doc.rust-lang.org/book/ch13-03-improving-our-iterators-and-adapters.html"),
    ("smart_pointers", "https://doc.rust-lang.org/book/ch15-00-smart-pointers.html"),
    ("concurrency", "https://doc.rust-lang.org/book/ch16-00-concurrency.html"),
    ("testing", "https://doc.rust-lang.org/book/ch11-00-writing-tests.html"),
    ("cargo", "https://doc.rust-lang.org/book/ch14-00-more-about-cargo.html"),
    ("unsafe", "https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html"),
    ("async_await", "https://doc.rust-lang.org/book/ch17-03-async-await-for-future-apis.html"),
]

# Key stdlib modules
STDLIB_MODULES = [
    ("std::collections", "https://doc.rust-lang.org/std/collections/index.html"),
    ("std::string", "https://doc.rust-lang.org/std/string/index.html"),
    ("std::vec", "https://doc.rust-lang.org/std/vec/index.html"),
    ("std::option", "https://doc.rust-lang.org/std/option/index.html"),
    ("std::result", "https://doc.rust-lang.org/std/result/index.html"),
    ("std::io", "https://doc.rust-lang.org/std/io/index.html"),
    ("std::fs", "https://doc.rust-lang.org/std/fs/index.html"),
    ("std::path", "https://doc.rust-lang.org/std/path/index.html"),
    ("std::env", "https://doc.rust-lang.org/std/env/index.html"),
    ("std::process", "https://doc.rust-lang.org/std/process/index.html"),
    ("std::thread", "https://doc.rust-lang.org/std/thread/index.html"),
    ("std::sync", "https://doc.rust-lang.org/std/sync/index.html"),
    ("std::time", "https://doc.rust-lang.org/std/time/index.html"),
    ("std::fmt", "https://doc.rust-lang.org/std/fmt/index.html"),
    ("std::error", "https://doc.rust-lang.org/std/error/index.html"),
    ("std::collections::HashMap", "https://doc.rust-lang.org/std/collections/struct.HashMap.html"),
    ("std::collections::VecDeque", "https://doc.rust-lang.org/std/collections/struct.VecDeque.html"),
    ("std::collections::HashSet", "https://doc.rust-lang.org/std/collections/struct.HashSet.html"),
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
    content = soup.find("main")
    if not content:
        content = soup.find("div", class_="content")
    if not content:
        content = soup.find("body")
    if not content:
        return ""
    text = content.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
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


def ingest_source(name: str, url: str, source_tag: str) -> tuple[int, int]:
    print(f"  [{name}] Fetching...")
    try:
        html = fetch_page(url)
        text = extract_text(html)
        if len(text) < 100:
            print(f"  [{name}] Skipped (too short)")
            return 0, 0

        save_path = DATA_DIR / f"{name.replace('::', '_')}.txt"
        save_path.write_text(text, encoding="utf-8")

        chunks = chunk_text(text)
        documents = [
            {
                "text": chunk,
                "id": f"rust_{name.replace('::', '_')}_{i}",
                "metadata": {
                    "source": source_tag,
                    "module": name,
                    "url": url,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]

        if send_to_rag(documents):
            print(f"  [{name}] OK: {len(chunks)} chunks")
            return len(chunks), 1
        else:
            print(f"  [{name}] FAILED")
            return 0, 0
    except Exception as e:
        print(f"  [{name}] Error: {e}")
        return 0, 0


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    total_chunks = 0
    total_sources = 0

    print(f"Rust docs: {len(BOOK_CHAPTERS)} book chapters + {len(STDLIB_MODULES)} stdlib modules")
    print("=" * 60)

    print("\n--- The Rust Book ---")
    for name, url in BOOK_CHAPTERS:
        chunks, count = ingest_source(name, url, "rust_book")
        total_chunks += chunks
        total_sources += count
        time.sleep(0.5)

    print("\n--- Rust stdlib ---")
    for name, url in STDLIB_MODULES:
        chunks, count = ingest_source(name, url, "rust_stdlib")
        total_chunks += chunks
        total_sources += count
        time.sleep(0.5)

    print("=" * 60)
    print(f"Done: {total_sources} sources, {total_chunks} chunks ingested")


if __name__ == "__main__":
    main()
