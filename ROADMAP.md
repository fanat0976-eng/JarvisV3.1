# Jarvis V3.1 — Roadmap

## Текущий статус: Все фазы завершены ✅

## Phase 1: Ядро ✅
- [x] Core (server, plugin_manager, event_bus, cache)
- [x] Brain (router, context, personality, tool_executor)
- [x] Memory_v2 (facts, entities, sessions, patterns)
- [x] Files plugin
- [x] Web plugin
- [x] Notifications plugin
- [x] Watchers plugin
- [x] TTS plugin (edge-tts)
- [x] STT plugin (Whisper)
- [x] Android plugin (WebSocket)

## Phase 2: RAG + Knowledge ✅
- [x] ChromaDB установлен (v1.5.9)
- [x] nomic-embed-text скачан (dim 768, 274MB)
- [x] RAG handler.py написан (Ollama embeddings)
- [x] Включить RAG в config.yaml
- [x] Протестировать RAG endpoints (add/search/ask)
- [x] Интегрировать RAG с brain (context из RAG)
- [x] NOMAD Knowledge Pipeline: ingest/file, ingest/text, ingest/directory
- [x] ZIM Loader pipeline (download → parse → RAG)
- [x] Kiwix collections catalog (Medicine, Survival, Education, DIY, Agriculture, Computing)
- [x] NOMAD API endpoints (status, download, zim/*)
- [x] E2E тест пайплайна
- [ ] Загрузка реального Wikipedia ZIM файла (30GB)
- [x] StackOverflow docs → RAG index
- [x] Python/Rust docs → RAG index

## Phase 3: Продвинутое ✅
- [x] Auto-learning (автоматическое изучение навыков)
- [x] Multi-agent orchestration
- [x] Knowledge graph (networkx + SQLite)
- [x] NPU acceleration (Intel OpenVINO, NPU detected)

## Phase 4: UI 📋
- [x] Electron desktop client
- [x] Flutter mobile client
- [x] Web dashboard

## Phase 5: Деплой ✅
- [x] Docker Compose оркестрация
- [x] First-Run Wizard
- [x] System benchmark

## Зависимости
```
Ollama (qwen2.5:14b + nomic-embed-text)
  ├── Brain (chat, reasoning, code, analysis)
  ├── RAG (embeddings, semantic search)
  └── Memory (fact extraction)

ChromaDB (vector DB)
  ├── RAG storage
  └── Knowledge index

SQLite (memory.db)
  ├── Sessions + Messages
  ├── Facts + Entities
  ├── Notifications
  └── Patterns

edge-tts (TTS)
Whisper (STT)
```
