# Phase 2: Extensions — Чеклист PR

## Готовность к PR

### Сервер
- [ ] language.py — мультиязычность работает
- [ ] config.yaml — обновлён с новыми плагинами

### Плагины
- [ ] agents — multi-agent orchestration
- [ ] graph — knowledge graph (networkx)
- [ ] voice — полный цикл (STT → Brain → TTS)
- [ ] npu — Intel NPU acceleration
- [ ] benchmark — системный бенчмарк
- [ ] watchers — фоновый мониторинг
- [ ] android — WebSocket bridge
- [ ] nomad — knowledge pipeline

### Community Plugins
- [ ] registry.json — реестр плагинов
- [ ] weather — погода (Open-Meteo)
- [ ] todo — задачи
- [ ] reminders — напоминания
- [ ] clipboard — буфер обмена
- [ ] system_stats — мониторинг

### API
- [ ] /voice/converse — голосовой диалог
- [ ] /voice/transcribe — транскрипция
- [ ] /voice/video/summarize — видео → суммаризация
- [ ] /agents/list — список агентов
- [ ] /agents/spawn — запуск агента
- [ ] /graph/entity — CRUD сущностей
- [ ] /graph/neighbors — соседи
- [ ] /benchmark/run — полный бенчмарк
- [ ] /plugins/community — список community плагинов
- [ ] /weather/current — погода
- [ ] /todo/list — задачи
- [ ] /reminders/list — напоминания
- [ ] /clipboard/history — буфер обмена
- [ ] /system_stats/overview — система

### Клиенты
- [ ] Electron HUD — чат, файлы, память, граф, агенты, голос
- [ ] Flutter APK — чат, память, файлы, настройки
- [ ] Web Dashboard — plugins страница

### Мультиязычность
- [ ] detect_language() — ru/en/kz
- [ ] get_system_prompt() — промпты на 3 языках
- [ ] /brain/languages — список языков
- [ ] /brain/detect — определение языка
- [ ] Chat: параметр language работает
- [ ] Web Dashboard: селектор языка
- [ ] Flutter: язык в настройках

### Knowledge
- [ ] Python docs — 34 модуля indexed
- [ ] Rust docs — 36 источников indexed
- [ ] StackOverflow — 23 топика indexed
- [ ] Итого: 2583 документов в RAG

### Тесты
- [ ] Все Phase 1 тесты проходят
- [ ] Дополнительные тесты: agents, graph, voice, language
- [ ] Итого: ~103 tests passing

### Документация
- [ ] README.md обновлён (Phase 2 фичи)
- [ ] CHANGELOG.md обновлён

---

## Готовность к merge

- [ ] Все тесты проходят (103+)
- [ ] Docker собирается
- [ ] Electron HUD работает
- [ ] Flutter APK собирается
- [ ] Web Dashboard работает
- [ ] Community plugins загружаются
- [ ] Мультиязычность работает
- [ ] Code review пройден
- [ ] Нет breaking changes для Phase 1
