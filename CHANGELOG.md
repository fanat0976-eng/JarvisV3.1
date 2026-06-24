# Changelog

All notable changes to J.A.R.V.I.S V3.1 will be documented in this file.

## [3.1.0] - 2026-06-24

### Added
- **Brain**: Router (qwen2.5/gemma2/gemma-4-coder), Context (sliding window), Personality (adaptive prompt), ToolExecutor
- **Memory V2**: Facts, entities, sessions, patterns, notes
- **RAG**: ChromaDB + Ollama embeddings (nomic-embed-text), semantic search, batch ingest
- **Files**: CRUD operations, file tree, diff, search, sandboxed workspace
- **Web**: DuckDuckGo search, page fetch, SSRF protection
- **Graph**: Knowledge graph (networkx + SQLite), entities, relations, shortest path
- **Agents**: Multi-agent orchestration (code, research, file_ops), auto-classification
- **Learning**: Fact extraction, command learner, router learner
- **Notifications**: Cooldown, priority, event bus integration
- **Watchers**: Disk, network, time-based triggers
- **TTS**: edge-tts (Dmitry, Svetlana voices)
- **STT**: Whisper (base model, local)
- **Android**: WebSocket bridge for mobile clients
- **NOMAD**: Knowledge Pipeline (file/text/directory ingest), ZIM Loader (Kiwix)
- **Voice**: Full voice conversation loop (audio → STT → Brain → TTS → audio), video transcription
- **Wizard**: First-run system check (Python, Ollama, ChromaDB, disk, config, RAG)
- **Benchmark**: System performance test (Ollama, embedding, RAG, file I/O, SQLite)
- **NPU**: Intel NPU acceleration (OpenVINO)
- **Web Dashboard**: SPA at /dashboard (chat, memory, files, status, plugins)
- **Flutter Client**: Mobile app (Material 3, chat streaming, memory, files, settings)
- **Electron Client**: Desktop HUD with sci-fi theme
- **CLI**: `jarvis_cli.py` (plugin management, health, benchmark, wizard)
- **Docker**: Dockerfile + docker-compose.yml (server + Ollama with GPU)
- **Community Plugins**: Plugin sandbox, registry, 5 example plugins (weather, todo, reminders, clipboard, system_stats)
- **Knowledge**: 2583 documents indexed (Python stdlib, Rust, StackOverflow topics)
- **Tests**: 103 tests (unit, integration, E2E)

### Security
- Auth via X-Auth-Key header only
- Path traversal protection for file operations
- SSRF protection for web fetch (private IP blocking)
- Sandboxed execution for community plugins
- CORS configurable via config.yaml

### Changed
- Server binds to 0.0.0.0 by default for network access
- Brain learning now works in all modes (chat, stream, agent)

### Fixed
- Route conflict in agents plugin (/{name} vs /{task_id}/status)
- Async blocking in RAG ask_rag (now uses aembed)
- Deprecated datetime.utcnow() calls
- Android plugin missing Request import
- SSRF protection for 172.x.x.x range (was blocking all, now only 172.16-31)
- Non-streaming chat missing learning integration
- Web dashboard plugin list overflow
- Electron HUD plugin cards layout
- ZIM pipeline test (entry iteration range expanded)
