"""
Web plugin — DuckDuckGo search + page fetch.
Adapted from V2.1 for V3.1.
"""
import re
from urllib.parse import urlparse
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

_BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0",
    "169.254.169.254", "metadata.google.internal",
    "[::1]", "0:0:0:0:0:0:0:1",
}


def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname or ""
        if hostname in _BLOCKED_HOSTS:
            return False
        if hostname.startswith("10.") or hostname.startswith("192.168."):
            return False
        if re.match(r'^172\.(1[6-9]|2\d|3[01])\.', hostname):
            return False
        if re.match(r'^169\.254\.', hostname):
            return False
        return True
    except Exception:
        return False


@router.get("/health")
def health():
    return {"status": "ok", "engines": ["duckduckgo"]}


def search_ddg(query, max_results=5):
    import httpx
    try:
        r = httpx.post("https://lite.duckduckgo.com/lite/", data={"q": query}, headers=HEADERS, timeout=10)
        r.raise_for_status()
        text = r.text
        results = []
        links = re.findall(r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', text, re.DOTALL)
        snippets = re.findall(r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>', text, re.DOTALL)
        for i, (href, title_raw) in enumerate(links[:max_results]):
            title = re.sub(r'<[^>]+>', '', title_raw).strip()
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
            if title:
                results.append({"title": title, "url": href, "body": snippet, "engine": "duckduckgo"})
        return results
    except Exception:
        return []


def fetch_page(url):
    import httpx
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        r.raise_for_status()
        text = r.text
        title_m = re.search(r'<title[^>]*>(.*?)</title>', text, re.DOTALL | re.IGNORECASE)
        title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else ""
        body = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL | re.IGNORECASE)
        body = re.sub(r'<[^>]+>', ' ', body)
        body = re.sub(r'&[a-z]+;', ' ', body)
        body = re.sub(r'\s+', ' ', body).strip()
        return {"url": url, "title": title, "text": body[:15000], "status": r.status_code}
    except Exception as e:
        return {"url": url, "error": str(e)}


@router.post("/search")
async def search(request: Request):
    data = await request.json()
    query = data.get("query", "")
    max_results = data.get("max_results", 5)
    if not query:
        return JSONResponse({"error": "No query provided"}, status_code=400)
    results = search_ddg(query, max_results)
    return {"results": results, "query": query}


@router.post("/fetch")
async def fetch_endpoint(request: Request):
    data = await request.json()
    url = data.get("url", "")
    if not url:
        return JSONResponse({"error": "No url provided"}, status_code=400)
    if not _is_safe_url(url):
        return JSONResponse({"error": "Access denied: internal/private URLs are blocked"}, status_code=403)
    return fetch_page(url)
