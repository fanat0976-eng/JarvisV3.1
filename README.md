# J.A.R.V.I.S V3.1 — AI OS

Мыслящий помощник с адаптивной памятью, multi-agent оркестрацией, голосовым общением и экосистемой community-плагинов.

---

## Содержание

1. [Обзор](#обзор)
2. [Быстрый старт](#быстрый-старт)
3. [Установка](#установка)
4. [Docker](#docker)
5. [Архитектура](#архитектура)
6. [Плагины](#плагины)
7. [API Reference](#api-reference)
8. [Как писать запросы](#как-писать-запросы)
9. [Community Plugins](#community-plugins)
10. [CLI](#cli)
11. [Конфигурация](#конфигурация)
12. [Клиенты](#клиенты)
13. [Безопасность](#безопасность)
14. [Тесты](#тесты)
15. [Контрибьюшн](#контрибьюшн)
16. [Структура проекта](#структура-проекта)

---

## Обзор

**Jarvis V3.1** — это AI-ассистент с полноценной операционной системой:

- **Brain** — ядро мышления с маршрутизацией задач к разным моделям
- **Memory** — долгосрочная память (факты, сессии, паттерны)
- **RAG** — база знаний с семантическим поиском (2583 документов)
- **Agents** — мульти-агентная оркестрация (code, research, file_ops)
- **Voice** — голосовое общение (STT → Brain → TTS)
- **Graph** — граф знаний (networkx + SQLite)
- **Learning** — автообучение (извлечение фактов, паттернов)
- **Community Plugins** — экосистема плагинов (weather, todo, reminders...)

### Возможности

| Возможность | Описание |
|-------------|----------|
| Чат | Streaming,普通ный, с контекстом |
| Агент | Автоматическое выполнение задач с инструментами |
| Голос | Полный цикл: аудио → транскрипция → ответ → озвучка |
| Файлы | CRUD операции в sandboxed workspace |
| Поиск | DuckDuckGo + RAG семантический поиск |
| Память | Автоматическое запоминание фактов о пользователе |
| Погода | Текущая погода и прогноз (Open-Meteo) |
| Задачи | TODO список с приоритетами |
| Напоминания | Одноразовые и повторяющиеся |
| Мониторинг | CPU, RAM, диск, сеть |

---

## Быстрый старт

### 1. Установить зависимости

```bash
cd JarvisV3.1
pip install -e ".[rag]"
```

### 2. Установить Ollama и модели

```bash
# Установить Ollama: https://ollama.ai
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### 3. Запустить сервер

```bash
python core/server.py
```

Сервер запустится на `http://127.0.0.1:8003`

### 4. Открыть дашборд

```
http://localhost:8003/dashboard
```

---

## Установка

### Требования

- Python 3.10+
- Ollama (для LLM и embeddings)
- ChromaDB (векторная БД)
- SQLite (встроен в Python)
- ffmpeg (для видео-транскрипции, опционально)

### Установка зависимостей

```bash
# Базовые зависимости
pip install -e .

# С RAG (ChromaDB + embeddings)
pip install -e ".[rag]"

# Для разработки (тесты)
pip install -e ".[dev]"

# С Wikipedia/ZIM поддержкой
pip install -e ".[wikipedia]"
```

### Установка моделей Ollama

```bash
# Основная модель для чата
ollama pull qwen2.5:7b

# Простая модель для быстрых ответов
ollama pull gemma2:2b

# Кодовая модель
ollama pull hf.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF:Q4_K_M

# Embeddings (обязательно для RAG)
ollama pull nomic-embed-text
```

### Проверка установки

```bash
# Через CLI
python jarvis_cli.py wizard

# Или через API
curl http://localhost:8003/wizard/check
```

---

## Docker

### Запуск через Docker Compose

```bash
# Собрать и запустить
docker compose up -d

# Проверить статус
docker compose ps

# Логи
docker compose logs -f jarvis

# Остановить
docker compose down
```

### Что делает Docker Compose

| Сервис | Описание | Порт |
|--------|----------|------|
| `jarvis` | Основной сервер Jarvis | 8003 |
| `ollama` | LLM inference (с GPU) | 11434 |

### Объёмы данных

| Volume | Описание |
|--------|----------|
| `jarvis-data` | SQLite, ChromaDB, конфиги |
| `jarvis-workspace` | Рабочие файлы |
| `ollama-data` | Модели Ollama |

### Ручная сборка Docker

```bash
# Собрать образ
docker build -t jarvis-v3.1 .

# Запустить
docker run -d \
  --name jarvis \
  -p 8003:8003 \
  -v jarvis-data:/app/data \
  -v jarvis-workspace:/app/workspace \
  jarvis-v3.1
```

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential curl
COPY pyproject.toml .
RUN pip install -e ".[rag]"
COPY core/ core/
COPY plugins/ plugins/
COPY web/ web/
EXPOSE 8003
CMD ["python", "core/server.py"]
```

**Зачем нужен Dockerfile:**
- Изолированное окружение — не зависит от системных библиотек
- Воспроизводимость — одинаковый старт на любой машине
- Безопасность — контейнер с минимальными правами
- Масштабируемость — легко добавить replica или scale

---

## Архитектура

```
┌─────────────────────────────────────────────────┐
│                  FastAPI Server                   │
│              (core/server.py)                     │
├─────────────────────────────────────────────────┤
│  EventBus (pub/sub)  │  Cache (TTL)  │  Auth    │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  BRAIN   │  │  MEMORY  │  │   RAG    │       │
│  │ router   │  │ facts    │  │ ChromaDB │       │
│  │ context  │  │ sessions │  │ embeds   │       │
│  │ persona  │  │ patterns │  │ search   │       │
│  │ tools    │  │ entities │  │ NOMAD    │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  AGENTS  │  │  GRAPH   │  │ LEARNING │       │
│  │ code     │  │ networkx │  │ fact ext │       │
│  │ research │  │ entities │  │ commands │       │
│  │ file_ops │  │ relations│  │ router   │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  VOICE   │  │  FILES   │  │   WEB    │       │
│  │ STT      │  │ CRUD     │  │ search   │       │
│  │ TTS      │  │ sandbox  │  │ fetch    │       │
│  │ converse │  │ tree     │  │ SSRF     │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                   │
│  ┌──────────────────────────────────────┐        │
│  │       COMMUNITY PLUGINS              │        │
│  │ weather │ todo │ reminders │ ...     │        │
│  └──────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
```

---

## Плагины

### Core плагины (18)

| Плагин | Описание | Эндпоинты |
|--------|----------|-----------|
| **brain** | Ядро мышления: router, context, personality, tools | `/brain/chat`, `/brain/agent`, `/brain/chat/stream` |
| **memory_v2** | Долгосрочная память: facts, entities, sessions | `/memory_v2/facts`, `/memory_v2/sessions` |
| **rag** | Векторная база знаний (ChromaDB + Ollama embeddings) | `/rag/search`, `/rag/ask`, `/rag/add` |
| **files** | Файловые операции (sandboxed workspace) | `/files/ls`, `/files/read`, `/files/write` |
| **web** | Поиск в интернете (DuckDuckGo) | `/web/search`, `/web/fetch` |
| **graph** | Граф знаний (networkx + SQLite) | `/graph/entity`, `/graph/neighbors` |
| **agents** | Мульти-агентная оркестрация | `/agents/spawn`, `/agents/orchestrate` |
| **learning** | Автообучение (факты, команды, router) | `/learning/commands`, `/learning/scores` |
| **notifications** | Система уведомлений | `/notifications/send`, `/notifications/list` |
| **watchers** | Фоновый мониторинг (диск, сеть) | `/watchers/status` |
| **tts_bridge** | Text-to-Speech (edge-tts) | `/tts_bridge/speak`, `/tts_bridge/voices` |
| **stt** | Speech-to-Text (Whisper) | `/stt/transcribe` |
| **android** | WebSocket мост для мобильных клиентов | `/android/ws` |
| **nomad** | Knowledge Pipeline (ингест документов) | `/nomad/ingest/file`, `/nomad/zim/*` |
| **voice** | Голосовой диалог (STT → Brain → TTS) | `/voice/converse`, `/voice/transcribe` |
| **wizard** | First-run проверка системы | `/wizard/check`, `/wizard/steps` |
| **benchmark** | Системный бенчмарк | `/benchmark/run`, `/benchmark/quick` |
| **npu** | Intel NPU acceleration (OpenVINO) | `/npu/health`, `/npu/load` |

### Community плагины (5)

| Плагин | Описание | Эндпоинты |
|--------|----------|-----------|
| **weather** | Погода (Open-Meteo, бесплатно) | `/weather/current`, `/weather/forecast` |
| **todo** | Список задач с приоритетами | `/todo/add`, `/todo/list`, `/todo/done` |
| **reminders** | Напоминания (одноразовые + повторяющиеся) | `/reminders/add`, `/reminders/list` |
| **clipboard** | Буфер обмена (история, поиск, pin) | `/clipboard/copy`, `/clipboard/search` |
| **system_stats** | Мониторинг: CPU, RAM, диск, сеть | `/system_stats/overview`, `/system_stats/cpu` |

---

## API Reference

### Аутентификация

Все запросы (кроме `/health` и `/dashboard`) требуют заголовок:

```
X-Auth-Key: jarvis-v3.1
```

### Brain — Ядро мышления

#### Чат (обычный)
```bash
curl -X POST http://localhost:8003/brain/chat \
  -H "X-Auth-Key: jarvis-v3.1" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Привет"}],
    "use_memory": true
  }'
```

#### Чат (streaming)
```bash
curl -X POST http://localhost:8003/brain/chat/stream \
  -H "X-Auth-Key: jarvis-v3.1" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Расскажи анекдот"}]}'
```

#### Агент (с tool execution)
```bash
curl -X POST http://localhost:8003/brain/agent \
  -H "X-Auth-Key: jarvis-v3.1" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Покажи файлы в workspace"}],
    "max_iterations": 3
  }'
```

#### Инструменты доступные агенту

| Инструмент | Описание |
|------------|----------|
| `files/ls` | Список файлов |
| `files/read` | Чтение файла |
| `files/write` | Запись в файл |
| `files/mkdir` | Создание папки |
| `files/rm` | Удаление файла |
| `files/search` | Поиск по содержимому |
| `memory/remember` | Запомнить факт |
| `memory/recall` | Вспомнить факты |
| `web/search` | Поиск в интернете |
| `web/fetch` | Чтение веб-страницы |

### Memory — Память

```bash
# Добавить факт
curl -X POST http://localhost:8003/memory_v2/facts \
  -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"entity": "user", "key": "name", "value": "badge"}'

# Получить факты
curl -X POST http://localhost:8003/memory_v2/facts/get \
  -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"entity": "user"}'

# Сессии
curl http://localhost:8003/memory_v2/sessions -H "X-Auth-Key: jarvis-v3.1"

# Инсайты
curl http://localhost:8003/memory_v2/insights -H "X-Auth-Key: jarvis-v3.1"
```

### RAG — База знаний

```bash
# Добавить документ
curl -X POST http://localhost:8003/rag/add \
  -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"text": "FastAPI — modern Python framework", "metadata": {"source": "docs"}}'

# Поиск
curl -X POST http://localhost:8003/rag/search \
  -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"query": "Python framework", "n_results": 5}'

# Ask (с контекстом)
curl -X POST http://localhost:8003/rag/ask \
  -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"question": "Что такое FastAPI?", "n_context": 3}'
```

### Voice — Голос

```bash
# Голосовой диалог (audio base64 → text → audio base64)
curl -X POST http://localhost:8003/voice/converse \
  -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"audio": "<base64-wav>", "voice": "dmitry"}'

# Транскрипция видео
curl -X POST http://localhost:8003/voice/video/summarize \
  -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"path": "workspace/video.mp4"}'
```

### Community Plugins

```bash
# Погода
curl "http://localhost:8003/weather/current?city=Moscow" -H "X-Auth-Key: jarvis-v3.1"
curl "http://localhost:8003/weather/forecast?city=London&days=5" -H "X-Auth-Key: jarvis-v3.1"

# Задачи
curl -X POST http://localhost:8003/todo/add -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"text": "Купить молоко", "priority": "high"}'
curl http://localhost:8003/todo/list -H "X-Auth-Key: jarvis-v3.1"

# Напоминания
curl -X POST http://localhost:8003/reminders/add/quick -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"text": "Позвонить маме", "minutes": 60}'

# Буфер обмена
curl -X POST http://localhost:8003/clipboard/copy -H "X-Auth-Key: jarvis-v3.1" \
  -d '{"text": "import os"}'

# Система
curl http://localhost:8003/system_stats/overview -H "X-Auth-Key: jarvis-v3.1"
```

---

## Как писать запросы

### Чат

**Простые вопросы:**
```
Привет
Как дела?
Что ты умеешь?
```

**С контекстом:**
```
Мой проект называется Jarvis
Помнишь мой стек технологий?
```

**С инструментами (агент режим):**
```
Покажи файлы в workspace
Напиши скрипт для бэкапа
Найди в интернете как настроить nginx
```

### Интеграция с другими системами

**Через API:**
```python
import httpx

r = httpx.post("http://localhost:8003/brain/chat", json={
    "messages": [{"role": "user", "content": "Твой вопрос"}],
    "use_memory": True
}, headers={"X-Auth-Key": "jarvis-v3.1"})

print(r.json()["reply"])
```

**Через WebSocket (для real-time):**
```javascript
const ws = new WebSocket("ws://localhost:8003/android/ws");
ws.send(JSON.stringify({type: "chat", message: "Привет"}));
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## Community Plugins

### Создание плагина

```bash
python jarvis_cli.py plugin create my_plugin -d "Описание" -a "Автор"
```

Генерируется:
```
plugins/community/my_plugin/
├── plugin.json    # Манифест
└── handler.py     # Код плагина
```

### Структура plugin.json

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "Описание плагина",
  "author": "your_name",
  "dependencies": ["httpx"],
  "permissions": ["events", "cache"],
  "api_version": "1.0",
  "min_jarvis_version": "3.1",
  "enabled": true
}
```

### API для плагинов

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

# Доступ к событийной шине
def on_startup():
    api.emit("my.event", {"data": 123})
    api.subscribe("other.event", handler)

# Доступ к кэшу
def cached_data():
    data = api.cache_get("my_key")
    if data is None:
        data = expensive_computation()
        api.cache_set("my_key", data, ttl=300)
    return data

# Доступ к файлам (sandboxed)
def read_workspace():
    content = api.read_file("config.json")
    api.write_file("output.txt", "result")
```

### Установка из реестра

```bash
python jarvis_cli.py plugin install weather
python jarvis_cli.py plugin list
python jarvis_cli.py plugin uninstall weather
```

---

## CLI

```bash
# Плагины
python jarvis_cli.py plugin list
python jarvis_cli.py plugin install <name>
python jarvis_cli.py plugin uninstall <name>
python jarvis_cli.py plugin create <name>
python jarvis_cli.py plugin info <name>

# Система
python jarvis_cli.py health
python jarvis_cli.py benchmark
python jarvis_cli.py benchmark --quick
python jarvis_cli.py wizard
```

---

## Конфигурация

Файл: `core/config.yaml`

```yaml
server:
  host: "0.0.0.0"       # 0.0.0.0 для доступа по сети
  port: 8003
  auth_key: "jarvis-v3.1"
  cors_origins:
    - "http://localhost:8003"
    - "*"

plugins:
  brain:
    enabled: true
    model: "qwen2.5:7b"
    model_simple: "gemma2:2b"
    model_code: "hf.co/.../gemma-4-12B-coder...:Q4_K_M"
    temperature: 0.7
    max_context_tokens: 4096

  memory_v2:
    enabled: true

  rag:
    enabled: true

  voice:
    enabled: true

  weather:
    enabled: true

  todo:
    enabled: true

ollama:
  url: "http://localhost:11434"
  default_model: "qwen2.5:14b"

workspace: "./workspace"
data_dir: "./data"
```

### Переключение на сетевой доступ

Для доступа с телефона/другого компьютера:

```yaml
server:
  host: "0.0.0.0"    # слушать все интерфейсы
```

Затем найдите IP компьютера:
```bash
# Windows
ipconfig

# Linux/Mac
ip addr
```

---

## Клиенты

### Web Dashboard

Доступен по адресу: `http://localhost:8003/dashboard`

Включает:
- Чат (streaming + agent mode)
- Память (CRUD фактов)
- Файлы (навигация + просмотр)
- Статус системы
- Community Plugins

### Electron Desktop

```bash
cd client
npm install
npm start
```

### Flutter Mobile

```bash
cd client/flutter
flutter pub get
flutter run

# Сборка APK
flutter build apk --release
```

### Android (Native)

```bash
cd android
./gradlew assembleDebug
```

---

## Безопасность

| Мера | Описание |
|------|----------|
| **Auth** | Заголовок `X-Auth-Key` (query param отключён) |
| **CORS** | Настраивается в config.yaml |
| **Files** | Операции ограничены `workspace/` (path traversal защита) |
| **Web** | Блокировка internal/private IP (SSRF защита) |
| **Bind** | По умолчанию `127.0.0.1` (не `0.0.0.0`) |
| **Sandbox** | Community плагины с ограниченным доступом к файлам |

---

## Тесты

```bash
# Все тесты (103 passed)
pytest

# Только unit тесты
pytest tests/test_unit.py tests/test_chunker.py tests/test_graph.py

# Интеграционные (требуют сервер)
pytest tests/test_rag.py tests/test_brain_rag.py

# С verbose
pytest -v
```

---

## Контрибьюшн

### Добавление нового core плагина

1. Создайте директорию `plugins/my_plugin/`
2. Создайте `handler.py` с `router`, `on_startup()`, `on_shutdown()`
3. Добавьте в `core/config.yaml`:
   ```yaml
   plugins:
     my_plugin:
       enabled: true
       description: "Описание"
   ```
4. Добавьте тесты в `tests/test_my_plugin.py`
5. Запустите `pytest`

### Добавление community плагина

```bash
python jarvis_cli.py plugin create my_plugin -d "Описание" -a "Автор"
# Редактируйте handler.py
# Добавьте в registry.json
```

### Code Style

- Python: PEP 8
- JavaScript: минимум зависимостей
- CSS: CSS variables для тем
- Тесты: pytest + pytest-asyncio

---

## Структура проекта

```
JarvisV3.1/
├── core/                    # Ядро сервера
│   ├── server.py            # FastAPI orchestrator
│   ├── config.yaml          # Конфигурация
│   ├── plugin_manager.py    # Auto-discovery, lifecycle
│   ├── plugin_sandbox.py    # Sandboxed execution для community
│   ├── event_bus.py         # Pub/sub с wildcard
│   └── cache.py             # TTL cache, thread-safe
├── plugins/                 # Плагины
│   ├── brain/               # Ядро мышления
│   │   ├── handler.py       # API endpoints
│   │   ├── router.py        # Task classification → model
│   │   ├── context.py       # Sliding window context
│   │   ├── personality.py   # Adaptive system prompt
│   │   └── tool_executor.py # Tool call execution
│   ├── memory_v2/           # Долгосрочная память
│   ├── rag/                 # ChromaDB + Ollama embeddings
│   ├── files/               # Файловые операции (sandboxed)
│   ├── web/                 # DuckDuckGo search + fetch
│   ├── graph/               # Knowledge graph (networkx)
│   ├── agents/              # Multi-agent orchestration
│   ├── learning/            # Auto-learning
│   ├── voice/               # Голосовой диалог (STT + TTS)
│   ├── notifications/       # Система уведомлений
│   ├── watchers/            # Background monitoring
│   ├── tts_bridge/          # Text-to-Speech (edge-tts)
│   ├── stt/                 # Speech-to-Text (Whisper)
│   ├── android/             # WebSocket bridge
│   ├── nomad/               # Knowledge Pipeline
│   ├── wizard/              # First-run checker
│   ├── benchmark/           # System benchmark
│   ├── npu/                 # Intel NPU acceleration
│   └── community/           # Community plugins
│       ├── registry.json    # Реестр плагинов
│       ├── weather/         # Погода
│       ├── todo/            # Задачи
│       ├── reminders/       # Напоминания
│       ├── clipboard/       # Буфер обмена
│       └── system_stats/    # Мониторинг
├── web/                     # Web dashboard (SPA)
│   └── index.html
├── client/                  # Клиенты
│   ├── index.html           # Electron
│   ├── flutter/             # Flutter mobile
│   └── css/, js/            # Electron UI
├── scripts/                 # Скрипты индексации
│   ├── ingest_python_docs.py
│   ├── ingest_rust_docs.py
│   └── ingest_stackoverflow.py
├── tests/                   # Тесты (103 tests)
├── data/                    # Данные
│   ├── memory.db            # SQLite
│   ├── knowledge_graph.db   # Graph DB
│   ├── chroma_db/           # Vector DB
│   └── knowledge/           # Документация
├── workspace/               # Sandboxed файлы
├── Dockerfile               # Docker образ
├── docker-compose.yml       # Docker Compose
├── pyproject.toml           # Python package config
├── jarvis_cli.py            # CLI интерфейс
├── ROADMAP.md               # Дорожная карта
└── README.md                # Этот файл
```

---

## Лицензия

[Apache License 2.0](LICENSE)

---

## Контакты

- GitHub Issues: для багов и фич
- Discord: для обсуждений
