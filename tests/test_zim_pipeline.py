"""Test ZIM file processing pipeline."""
import pytest
import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"


def _server_available():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


requires_server = pytest.mark.skipif(not _server_available(), reason="Server not running")


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


@requires_server
def test_zim_pipeline():
    """Test full ZIM processing pipeline."""
    zim_path = Path("data/knowledge/wikipedia/ruwiki_chemistry.zim")
    assert zim_path.exists(), f"ZIM file not found: {zim_path}"
    
    # 1. Open ZIM file
    import libzim
    archive = libzim.Archive(str(zim_path))
    print(f"ZIM file opened: {archive.article_count} articles")
    
    # 2. Parse articles (skip redirects, find up to 10 real articles)
    articles = []
    max_scan = min(archive.entry_count, 200)
    for i in range(max_scan):
        if len(articles) >= 10:
            break
        try:
            entry = archive._get_entry_by_id(i)
            if entry.is_redirect:
                continue
            
            item = entry.get_item()
            html = bytes(item.content).decode("utf-8", errors="replace")
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            text = soup.get_text(separator="\n", strip=True)
            
            if len(text) > 100:
                articles.append({
                    "title": entry.title,
                    "text": text[:1000],
                    "url": f"https://ru.wikipedia.org/wiki/{entry.title}"
                })
        except Exception:
            continue
    
    print(f"Parsed {len(articles)} articles")
    assert len(articles) > 0, "No articles parsed from ZIM"
    
    # 3. Ingest articles into RAG
    for article in articles:
        doc = {
            "text": article["text"],
            "metadata": {
                "source": "wikipedia",
                "language": "ru",
                "title": article["title"],
                "url": article["url"]
            }
        }
        r = httpx.post(f"{BASE_URL}/rag/add", json=doc, headers=get_headers())
        assert r.status_code == 200, f"Failed to ingest article: {article['title']}"
    
    print(f"Ingested {len(articles)} articles into RAG")
    
    # 4. Test search
    search_query = {"query": "химия", "n_results": 3}
    r = httpx.post(f"{BASE_URL}/rag/search", json=search_query, headers=get_headers())
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) > 0, "No search results found"
    
    print(f"Search returned {len(results)} results")
    for i, res in enumerate(results):
        print(f"  {i+1}. {res['metadata'].get('title', 'Unknown')} (distance: {res['distance']:.3f})")
    
    # 5. Test RAG ask
    ask_query = {"question": "Что такое химия?", "n_context": 3}
    r = httpx.post(f"{BASE_URL}/rag/ask", json=ask_query, headers=get_headers())
    assert r.status_code == 200
    context = r.json()["context"]
    assert len(context) > 0, "No context returned"
    
    print(f"RAG ask returned context: {len(context)} chars")
    
    print("\n✅ ZIM pipeline test passed!")


if __name__ == "__main__":
    test_zim_pipeline()