# Changelog

All notable changes to J.A.R.V.I.S V3.1 will be documented in this file.

## [3.1.0-core] - 2026-06-24

### Added
- **Brain**: Router (qwen2.5/gemma2/gemma-4-coder), Context (sliding window), Personality (adaptive prompt), ToolExecutor
- **Memory V2**: Facts, entities, sessions, patterns, notes
- **RAG**: ChromaDB + Ollama embeddings (nomic-embed-text), semantic search, batch ingest
- **Files**: CRUD operations, file tree, diff, search, sandboxed workspace
- **Web**: DuckDuckGo search, page fetch, SSRF protection
- **Learning**: Fact extraction, command learner, router learner
- **Notifications**: Cooldown, priority, event bus integration
- **TTS**: edge-tts (Dmitry, Svetlana voices)
- **STT**: Whisper (base model, local)
- **Wizard**: First-run system check (Python, Ollama, ChromaDB, disk, config, RAG)
- **Web Dashboard**: SPA at /dashboard (chat, memory, files, status, plugins)
- **CLI**: `jarvis_cli.py` (plugin management, health, benchmark, wizard)
- **Docker**: Dockerfile + docker-compose.yml (server + Ollama with GPU)
- **Tests**: 79 unit tests (router, personality, language, learning, RAG)

### Security
- Auth via X-Auth-Key header only
- Path traversal protection for file operations
- SSRF protection for web fetch (private IP blocking)
- Sandboxed execution for community plugins
- CORS configurable via config.yaml

### Changed
- Server binds to 0.0.0.0 by default for network access

### Fixed
- Async blocking in RAG ask_rag (now uses aembed)
- Deprecated datetime.utcnow() calls
- SSRF protection for 172.x.x.x range (was blocking all, now only 172.16-31)
- Non-streaming chat missing learning integration
- Web dashboard plugin list overflow
