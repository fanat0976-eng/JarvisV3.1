# J.A.R.V.I.S V3.1 — Дорожная карта PR

## Стратегия: Two-Phase Release

### Phase 1: Core (стабильное ядро) → PR #1
### Phase 2: Extensions (расширения) → PR #2

---

## PHASE 1: Core — Стабильное ядро

**Цель:** Рабочий AI-ассистент с базовыми возможностями. Минимум зависимостей, максимальная стабильность.

### Что входит

#### 1.1 Серверное ядро
```
core/
├── server.py              # FastAPI orchestrator
├── config.yaml            # Конфигурация
├── plugin_manager.py      # Auto-discovery, lifecycle
├── plugin_sandbox.py      # Sandboxed execution
├── event_bus.py           # Pub/sub с wildcard
├── cache.py               # TTL cache, thread-safe
└── language.py            # Определение языка (ru/en/kz)
```

#### 1.2 Базовые плагины (10)
| Плагин | Описание | Зависимости |
|--------|----------|-------------|
| brain | Ядро мышления (router, context, personality, tools) | httpx |
| memory_v2 | Долгосрочная память (facts, sessions) | sqlite3 |
| rag | Векторная БД (ChromaDB + Ollama) | chromadb |
| files | Файловые операции (sandboxed) | — |
| web | Поиск (DuckDuckGo) | httpx |
| notifications | Уведомления | — |
| tts_bridge | Text-to-Speech | edge-tts |
| stt | Speech-to-Text | whisper |
| learning | Автообучение | — |
| wizard | First-run проверка | — |

#### 1.3 API Endpoints
```
GET  /health                   # Статус системы
POST /brain/chat               # Чат
POST /brain/chat/stream        # Чат (streaming)
POST /brain/agent              # Агент (tool execution)
GET  /brain/languages          # Поддерживаемые языки
POST /brain/detect             # Определение языка
POST /memory_v2/facts          # CRUD фактов
POST /rag/search               # Semantic search
POST /rag/ask                  # RAG ask
POST /files/ls                 # Файловые операции
POST /web/search               # Поиск в интернете
GET  /wizard/check             # Проверка системы
```

#### 1.4 Тесты
- Unit tests: router, tool_executor, personality, language
- Integration: RAG, NOMAD pipeline
- Всего: ~70 tests

#### 1.5 Docker
- Dockerfile (python:3.11-slim)
- docker-compose.yml (server + ollama)

#### 1.6 Клиенты
- Web Dashboard (`/dashboard`) — SPA чат/память/файлы/статус
- CLI (`jarvis_cli.py`) — health, wizard, benchmark

#### 1.7 Open Source
- README.md (полный мануал)
- LICENSE (Apache 2.0)
- CONTRIBUTING.md
- CHANGELOG.md
- SECURITY.md
- CODE_OF_CONDUCT.md
- .gitignore / .dockerignore
- .github/workflows/ci.yml

### Чего НЕТ в Phase 1
- ❌ Community plugins
- ❌ Voice plugin (полный цикл)
- ❌ Flutter клиент
- ❌ Electron HUD
- ❌ Мультиязычность UI
- ❌ Graph, Agents, NPU
- ❌ Benchmark

### Стабильность
- Все тесты проходят
- Нет breaking changes
- Минимум внешних зависимостей
- Работает на Python 3.10+

### Сроки
- Разработка: 2-3 недели
- Тестирование: 1 неделя
- Code review: 1 неделя
- **Итого: 4-5 недель**

---

## PHASE 2: Extensions — Расширения

**Цель:** Полный функционал с UI, голосом, community plugins, мультиязычностью.

### Что входит

#### 2.1 Расширенные плагины (8)
| Плагин | Описание | Зависимости |
|--------|----------|-------------|
| agents | Multi-agent orchestration | — |
| graph | Знания граф (networkx) | networkx |
| voice | Голосовой диалог (STT→Brain→TTS) | — |
| npu | Intel NPU acceleration | openvino |
| benchmark | Системный бенчмарк | — |
| watchers | Фоновый мониторинг | — |
| android | WebSocket bridge | — |
| nomad | Knowledge Pipeline | libzim |

#### 2.2 Community Plugins
```
plugins/community/
├── registry.json           # Реестр плагинов
├── weather/                # Погода (Open-Meteo)
├── todo/                   # Задачи
├── reminders/              # Напоминания
├── clipboard/              # Буфер обмена
└── system_stats/           # Мониторинг
```

#### 2.3 Клиенты
| Клиент | Технология | Фичи |
|--------|-----------|-------|
| Electron HUD | Electron + Vanilla JS | Полный HUD с голосом |
| Flutter Mobile | Flutter + Material 3 | Чат, память, файлы, настройки |
| Web Dashboard | Vanilla HTML/CSS/JS | SPA с plugins |

#### 2.4 Мультиязычность
- Language detection (ru/en/kz)
- Multilingual system prompts
- UI: переключатель языка
- API: параметр `language`

#### 2.5 Knowledge
- Python stdlib docs (34 модуля)
- Rust Book + stdlib (36 источников)
- StackOverflow topics (23 топика)

#### 2.6 Тесты
- Дополнительные: ~30 tests
- Итого: ~103 tests

### Стабильность
- Все тесты проходят
- Breaking changes: обновление API (добавлены параметры)
- Требуется Ollama + Whisper

### Сроки
- Разработка: 3-4 недели
- Тестирование: 1 неделя
- Code review: 1 неделя
- **Итого: 5-6 недель**

---

## ИТОГО: Общая дорожная карта

```
Неделя 1-3:   Phase 1 — Core (ядро + базовые плагины + Docker)
Неделя 4:     Phase 1 — Тестирование + Code Review
Неделя 5:     Phase 1 — PR #1 → Merge
Неделя 6-9:   Phase 2 — Extensions (голос, plugins, UI)
Неделя 10:    Phase 2 — Тестирование + Code Review
Неделя 11:    Phase 2 — PR #2 → Merge
```

### Зависимости между фазами

```
Phase 1 (Core)
    │
    ├── server.py + config
    ├── plugin_manager
    ├── event_bus + cache
    ├── brain (router, context, personality)
    ├── memory_v2
    ├── rag (ChromaDB)
    ├── files (sandboxed)
    ├── web (search)
    ├── tts + stt
    ├── learning
    ├── wizard
    ├── Docker
    ├── Web Dashboard
    ├── CLI
    └── Tests + CI/CD
         │
         ▼
Phase 2 (Extensions)
    │
    ├── agents (multi-agent)
    ├── graph (knowledge graph)
    ├── voice (full loop)
    ├── npu (Intel acceleration)
    ├── benchmark
    ├── watchers
    ├── android (WebSocket)
    ├── nomad (knowledge pipeline)
    ├── community plugins (5)
    ├── Electron HUD
    ├── Flutter mobile
    ├── Multilingual (ru/en/kz)
    ├── Knowledge (Python/Rust/SO)
    └── Additional tests
```

---

## Файлы для PR

### Phase 1 (обязательные)
```
core/                    # Все файлы ядра
plugins/brain/           # Ядро мышления
plugins/memory_v2/       # Память
plugins/rag/             # RAG
plugins/files/           # Файлы
plugins/web/             # Поиск
plugins/notifications/   # Уведомления
plugins/tts_bridge/      # TTS
plugins/stt/             # STT
plugins/learning/        # Обучение
plugins/wizard/          # Wizard
web/                     # Dashboard
tests/                   # Тесты
scripts/                 # Скрипты индексации
Dockerfile
docker-compose.yml
.pydockerignore
.gitignore
pyproject.toml
jarvis_cli.py
README.md
LICENSE
CONTRIBUTING.md
CHANGELOG.md
SECURITY.md
CODE_OF_CONDUCT.md
.github/workflows/ci.yml
.github/ISSUE_TEMPLATE/
.github/PULL_REQUEST_TEMPLATE.md
```

### Phase 2 (дополнительные)
```
plugins/agents/
plugins/graph/
plugins/voice/
plugins/npu/
plugins/benchmark/
plugins/watchers/
plugins/android/
plugins/nomad/
plugins/community/
client/                  # Electron HUD
client/flutter/          # Flutter mobile
core/language.py
ROADMAP.md
```
