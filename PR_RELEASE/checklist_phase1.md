# Phase 1: Core — Чеклист PR

## Готовность к PR

### Сервер
- [ ] server.py — FastAPI orchestrator работает
- [ ] config.yaml — конфигурация по умолчанию
- [ ] plugin_manager.py — auto-discovery плагинов
- [ ] event_bus.py — pub/sub работает
- [ ] cache.py — TTL cache работает
- [ ] language.py — определение языка работает

### Плагины
- [ ] brain — router, context, personality, tool_executor
- [ ] memory_v2 — facts CRUD, sessions
- [ ] rag — ChromaDB search, ask, add
- [ ] files — ls, read, write, mkdir, rm (sandboxed)
- [ ] web — DuckDuckGo search, fetch
- [ ] notifications — send, list, read
- [ ] tts_bridge — speak, voices
- [ ] stt — transcribe
- [ ] learning — fact_extractor, command_learner
- [ ] wizard — system check

### API
- [ ] /health — работает
- [ ] /brain/chat — работает
- [ ] /brain/chat/stream — работает
- [ ] /brain/agent — работает
- [ ] /brain/languages — работает
- [ ] /brain/detect — работает
- [ ] /memory_v2/facts — CRUD работает
- [ ] /rag/search — работает
- [ ] /rag/ask — работает
- [ ] /files/ls — работает
- [ ] /web/search — работает
- [ ] /wizard/check — работает

### Тесты
- [ ] pytest tests/test_unit.py — все проходят
- [ ] pytest tests/test_chunker.py — все проходят
- [ ] pytest tests/test_graph.py — все проходят
- [ ] pytest tests/test_learning.py — все проходят
- [ ] pytest tests/test_agents.py — все проходят
- [ ] pytest tests/test_npu.py — все проходят
- [ ] Итого: ~70 tests passing

### Docker
- [ ] Dockerfile — собирается
- [ ] docker-compose.yml — запускается
- [ ] docker compose up — сервер работает
- [ ] curl localhost:8003/health — OK

### Клиенты
- [ ] /dashboard — web dashboard работает
- [ ] jarvis_cli.py health — OK
- [ ] jarvis_cli.py wizard — OK

### Документация
- [ ] README.md — полный мануал
- [ ] LICENSE — Apache 2.0
- [ ] CONTRIBUTING.md — гид для контрибьюторов
- [ ] CHANGELOG.md — история версий
- [ ] SECURITY.md — политика безопасности
- [ ] CODE_OF_CONDUCT.md — кодекс поведения

### CI/CD
- [ ] .github/workflows/ci.yml — тесты на Python 3.10-3.12
- [ ] .github/ISSUE_TEMPLATE/ — шаблоны issues
- [ ] .github/PULL_REQUEST_TEMPLATE.md — шаблон PR

### Безопасность
- [ ] Auth через X-Auth-Key header
- [ ] Path traversal защита для files
- [ ] SSRF защита для web fetch
- [ ] CORS настраивается

### Код
- [ ] Нет deprecated warnings
- [ ] Нет unused imports
- [ ] Все функции имеют docstrings
- [ ] Code style консистентный

---

## Готовность к merge

- [ ] Все тесты проходят
- [ ] Docker собирается и запускается
- [ ] README понятен для нового разработчика
- [ ] LICENSE правильный (Apache 2.0)
- [ ] CI/CD работает
- [ ] Нет security issues
- [ ] Code review пройден
