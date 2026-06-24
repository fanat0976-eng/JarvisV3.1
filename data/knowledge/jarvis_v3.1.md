# Jarvis V3.1 - AI OS

Jarvis V3.1 is an AI Operating System with the following components:

## Core
- FastAPI server on port 8003
- Plugin system with auto-discovery
- EventBus for inter-plugin communication
- TTL Cache

## Brain Plugin
- Router: routes tasks to appropriate models
- Context: sliding window management
- Personality: adaptive system prompts
- Tool Executor: executes tool calls

## Memory V2 Plugin
- Facts extraction and storage
- Entity linking
- Session management
- Pattern learning

## RAG Plugin
- ChromaDB vector storage
- Ollama embeddings (nomic-embed-text)
- File indexing (txt, md, pdf, docx)
- Semantic search

## Other Plugins
- Files: file operations
- Web: DuckDuckGo search
- TTS: edge-tts (Dmitry, Svetlana voices)
- STT: Whisper speech-to-text
- Notifications: system notifications
- Watchers: disk/network monitoring
- Android: WebSocket bridge
- NOMAD: Knowledge Pipeline for content ingestion