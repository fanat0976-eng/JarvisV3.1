# nasti-core - Shared Library

nasti-core is a shared Python library for all Nasti AI projects.

## Modules

### ai
- Ollama API wrappers (sync/stream/async)
- LiteLLM integration

### event
- EventBus with wildcard subscriptions
- Thread-safe publish/subscribe

### cache
- TTLCache with lazy eviction
- Time-based expiration

### crypto
- Argon2id key derivation
- XChaCha20-Poly1305 encryption
- BLAKE2b HMAC
- Binary header format (79 bytes)

### rag
- RAGEngine (ChromaDB + SentenceTransformer)
- Document ingestion and retrieval

### osint
- detect_target_type (regex cascade)
- run_wsl (WSL command execution)
- TOOL_REGISTRY (18+ tools)

## Usage
```python
from nasti_core.ai.ollama import OllamaClient
from nasti_core.event.bus import EventBus
from nasti_core.cache.ttl import TTLCache
```