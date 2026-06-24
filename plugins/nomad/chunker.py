"""Text chunking utilities for NOMAD pipeline."""
import re


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200, section_aware: bool = True) -> list[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: Input text
        chunk_size: Approximate number of characters per chunk (default: 2000 ≈ 500 tokens)
        overlap: Number of characters to overlap between chunks (default: 200 ≈ 50 tokens)
        section_aware: If True, try to split on section boundaries
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    if overlap >= chunk_size:
        overlap = chunk_size // 4
    
    if section_aware:
        # Split on section headers (##, ###, etc.)
        sections = re.split(r'(\n##+\s.*\n)', text)
        if len(sections) > 1:
            # Reconstruct sections with their headers
            chunks = []
            current = ""
            for part in sections:
                if re.match(r'\n##+\s', part):
                    # This is a header - start new section
                    if current.strip():
                        chunks.extend(chunk_text(current, chunk_size, overlap, section_aware=False))
                    current = part
                else:
                    current += part
            if current.strip():
                chunks.extend(chunk_text(current, chunk_size, overlap, section_aware=False))
            return chunks
    
    # Naive sliding window
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    
    return chunks
