# Contributing to J.A.R.V.I.S V3.1

Спасибо за интерес к проекту! Вот как контрибьютьить.

## Быстрый старт

```bash
# Клонировать
git clone https://github.com/xiaomi/jarvis.git
cd jarvis

# Установить зависимости
pip install -e ".[dev]"

# Запустить тесты
pytest

# Запустить сервер
python core/server.py
```

## Типы контрибьюшна

### 1. Bug Fix

1. Найди баг или создай issue
2. Напиши тест, воспроизводящий баг
3. Исправь баг
4. Убедись что все тесты проходят
5. Отправь PR

### 2. New Feature

1. Создай issue с описанием фичи
2. Обсуди подход с мейнтейнерами
3. Реализуй в отдельной ветке
4. Добавь тесты
5. Обнови README если нужно
6. Отправь PR

### 3. Community Plugin

```bash
python jarvis_cli.py plugin create my_plugin -d "Описание" -a "Твоё имя"
```

См. секцию [Community Plugins](README.md#community-plugins) в README.

### 4. Documentation

- Исправления опечаток
- Добавление примеров
- Улучшение описания API

## Code Style

### Python

- PEP 8
- Type hints где уместно
- Docstrings для публичных функций
- Минимум зависимостей

```python
# Good
def get_user_facts(entity: str = "user") -> list[dict]:
    """Get facts for an entity."""
    ...

# Bad
def get_user_facts(entity="user"):
    ...
```

### JavaScript

- Минимум фреймворков
- ES6+ синтаксис
- CSS variables для тем

### Commits

```
type(scope): description

# Examples:
feat(plugins): add weather plugin
fix(brain): resolve streaming timeout
docs(readme): update API reference
test(rag): add search integration tests
refactor(memory): optimize fact extraction
```

Типы: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`

## Pull Request

1. Fork → Branch → Commit → PR
2. Название: `feat(plugins): add weather plugin`
3. Описание: что сделано, почему, как тестировать
4. Скриншоты если есть UI изменения
5. Все тесты должны проходить

```bash
# Перед PR
pytest
python jarvis_cli.py health
```

## Issue Template

### Bug Report
```markdown
**Описание**
Что произошло

**Шаги для воспроизведения**
1. ...
2. ...

**Ожидаемое поведение**
...

**Система**
- OS: ...
- Python: ...
- Jarvis: ...
```

### Feature Request
```markdown
**Описание**
Что хочется

**Зачем**
Какую проблему решает

**Варианты реализации**
- ...
```

## Структура PR

```
feat(plugins): add weather plugin

- Добавлен weather плагин (Open-Meteo API)
- Эндпоинты: /weather/current, /weather/forecast
- Тесты: tests/test_weather.py
- Документация: README.md обновлён
```

## Вопросы?

- GitHub Issues: для багов и фич
- GitHub Discussions: для вопросов
