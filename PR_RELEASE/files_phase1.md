# Phase 1: Core — Список файлов

## Обязательные файлы для PR #1

### Ядро сервера
```
core/__init__.py
core/server.py
core/config.yaml
core/plugin_manager.py
core/plugin_sandbox.py
core/event_bus.py
core/cache.py
core/language.py
```

### Базовые плагины
```
plugins/__init__.py
plugins/brain/__init__.py
plugins/brain/handler.py
plugins/brain/router.py
plugins/brain/context.py
plugins/brain/personality.py
plugins/brain/tool_executor.py

plugins/memory_v2/__init__.py
plugins/memory_v2/handler.py

plugins/rag/__init__.py
plugins/rag/handler.py

plugins/files/__init__.py
plugins/files/handler.py

plugins/web/__init__.py
plugins/web/handler.py

plugins/notifications/__init__.py
plugins/notifications/handler.py

plugins/tts_bridge/__init__.py
plugins/tts_bridge/handler.py

plugins/stt/__init__.py
plugins/stt/handler.py

plugins/learning/__init__.py
plugins/learning/handler.py
plugins/learning/fact_extractor.py
plugins/learning/command_learner.py
plugins/learning/router_learner.py

plugins/wizard/__init__.py
plugins/wizard/handler.py
```

### Тесты
```
tests/__init__.py
tests/test_unit.py
tests/test_chunker.py
tests/test_graph.py
tests/test_learning.py
tests/test_agents.py
tests/test_npu.py
tests/test_pipeline.py
tests/test_rag.py
tests/test_brain_rag.py
tests/test_nomad.py
tests/test_zim_pipeline.py
```

### Клиенты
```
web/index.html
jarvis_cli.py
```

### Docker
```
Dockerfile
docker-compose.yml
.dockerignore
```

### Open Source
```
.gitignore
.pytest_cache/
pyproject.toml
README.md
LICENSE
CONTRIBUTING.md
CHANGELOG.md
SECURITY.md
CODE_OF_CONDUCT.md
.github/workflows/ci.yml
.github/ISSUE_TEMPLATE/bug_report.md
.github/ISSUE_TEMPLATE/feature_request.md
.github/PULL_REQUEST_TEMPLATE.md
```

### Скрипты
```
scripts/ingest_python_docs.py
scripts/ingest_rust_docs.py
scripts/ingest_stackoverflow.py
```

### Данные (gitignore)
```
data/                    # Не коммитится
workspace/               # Не коммитится
models/                  # Не коммитится
*.log                    # Не коммитится
```

---

## Итого файлов: ~50

## Размер PR: ~3000 строк кода
