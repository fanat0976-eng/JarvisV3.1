# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in J.A.R.V.I.S V3.1, please report it responsibly.

**DO NOT** open a public GitHub issue for security vulnerabilities.

### How to Report

1. Email: security@jarvis-ai.dev (или создайте приватный issue)
2. Опишите уязвимость
3. Укажите шаги для воспроизведения
4. Предложите исправление если возможно

### What to Expect

- Подтверждение в течение 48 часов
- Исправление в течение 7 дней для критических
- Credit в CHANGELOG.md

## Security Measures

### Authentication

- Все API endpoints (кроме `/health` и `/dashboard`) требуют `X-Auth-Key` header
- Query param аутентификация отключена
- Ключ настраивается в `core/config.yaml`

### Network

- По умолчанию сервер слушает `127.0.0.1` (только localhost)
- Для сетевого доступа нужно явно указать `0.0.0.0`
- CORS настраивается в config.yaml

### File Operations

- Все операции с файлами ограничены директорией `workspace/`
- Path traversal защита (проверка resolved path)
- Нет доступа к системным файлам

### Web Fetch

- Блокировка internal/private IP адресов (SSRF защита)
- Заблокированы: localhost, 127.0.0.1, 10.x.x.x, 172.16-31.x.x, 192.168.x.x, 169.254.x.x

### Community Plugins

- Песочница (sandbox) для выполнения плагинов
- Ограниченный доступ к файлам (только workspace)
- Проверка зависимостей перед загрузкой
- Whitelist разрешений (events, cache, files)

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.1.x | ✅ |
| < 3.1 | ❌ |

## Best Practices

1. Используйте сильный auth key
2. Не запускайте на `0.0.0.0` без необходимости
3. Регулярно обновляйте Ollama модели
4. Проверяйте community плагины перед установкой
5. Используйте Docker для изоляции
