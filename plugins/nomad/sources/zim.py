# plugins/nomad/sources/zim.py
"""ZIM adapter for NOMAD pipeline - supports any Kiwix ZIM file."""
import json
import httpx
from pathlib import Path
from bs4 import BeautifulSoup
from ..pipeline import Pipeline
from ..chunker import chunk_text


class ZimAdapter:
    def __init__(self, language: str = "en"):
        self.language = language
        self.pipeline = Pipeline("zim_loader")
        self.collections_file = Path(__file__).parent / "collections.json"
    
    def get_collections(self) -> list[dict]:
        """Get available ZIM collections."""
        if self.collections_file.exists():
            with open(self.collections_file) as f:
                data = json.load(f)
                return data.get("categories", [])
        return []
    
    def get_collection(self, slug: str) -> dict | None:
        """Get collection by slug."""
        for cat in self.get_collections():
            if cat.get("slug") == slug:
                return cat
        return None
    
    def download_from_kiwix(self, url: str) -> Path:
        """Download ZIM file from Kiwix URL.
        
        Args:
            url: Direct URL to ZIM file
            
        Returns:
            Path to downloaded ZIM file
        """
        filename = url.split("/")[-1]
        zim_path = self.pipeline.data_dir / filename
        
        self.pipeline.update_status("downloading", url=url, progress=0)
        
        try:
            with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                
                with open(zim_path, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.pipeline.update_status(
                                "downloading",
                                progress=int(downloaded / total * 100)
                            )
            
            self.pipeline.update_status("downloaded", size=zim_path.stat().st_size)
            return zim_path
        except Exception as e:
            self.pipeline.update_status("error", error=str(e))
            raise
    
    def parse_zim(self, zim_path: Path) -> list[dict]:
        """Parse ZIM file and extract articles.
        
        Args:
            zim_path: Path to ZIM file
            
        Returns:
            List of article dicts with title, text, url
        """
        import libzim
        
        self.pipeline.update_status("parsing", zim_path=str(zim_path))
        articles = []
        
        try:
            archive = libzim.Archive(str(zim_path))
            
            # Iterate through entries by ID
            for i in range(archive.entry_count):
                try:
                    entry = archive._get_entry_by_id(i)
                    if entry.is_redirect:
                        continue
                    
                    item = entry.get_item()
                    content = bytes(item.content)
                    
                    # Decode to text
                    text = content.decode("utf-8", errors="ignore")
                    
                    # Skip non-HTML content (CSS, JS, images)
                    if entry.path.endswith(('.css', '.js', '.png', '.jpg', '.gif', '.svg', '.ico')):
                        continue
                    
                    # Parse HTML to text
                    soup = BeautifulSoup(text, "lxml")
                    for element in soup(["script", "style", "nav", "footer"]):
                        element.decompose()
                    
                    clean_text = soup.get_text(separator="\n", strip=True)
                    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
                    clean_text = "\n".join(lines)
                    
                    if len(clean_text) > 100:  # Skip very short articles
                        articles.append({
                            "title": entry.title,
                            "text": clean_text,
                            "url": entry.path,
                            "size": len(clean_text)
                        })
                except Exception:
                    continue
            
            self.pipeline.update_status("parsed", articles=len(articles))
            return articles
        except Exception as e:
            self.pipeline.update_status("error", error=str(e))
            raise
    
    def ingest_to_rag(self, zim_path: Path) -> dict:
        """Full pipeline: parse → chunk → RAG.
        
        Args:
            zim_path: Path to ZIM file
            
        Returns:
            Status dict with counts
        """
        import httpx
        
        self.pipeline.update_status("ingesting", zim_path=str(zim_path))
        
        # Parse ZIM
        articles = self.parse_zim(zim_path)
        
        # Chunk and send to RAG
        total_chunks = 0
        for article in articles:
            chunks = chunk_text(article["text"], chunk_size=2000, overlap=200)
            for i, chunk in enumerate(chunks):
                try:
                    httpx.post(
                        "http://127.0.0.1:8003/rag/add",
                        json={
                            "text": chunk,
                            "metadata": {
                                "title": article["title"],
                                "source": "kiwix",
                                "url": article["url"],
                                "chunk_index": i,
                                "total_chunks": len(chunks)
                            }
                        },
                        headers={"X-Auth-Key": "jarvis-v3.1"},
                        timeout=60
                    )
                    total_chunks += 1
                except Exception:
                    continue
        
        self.pipeline.update_status("ready", chunks=total_chunks, articles=len(articles))
        return {
            "status": "ok",
            "articles": len(articles),
            "chunks": total_chunks
        }
