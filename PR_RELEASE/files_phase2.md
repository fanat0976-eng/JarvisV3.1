# Phase 2: Extensions — Список файлов

## Дополнительные файлы для PR #2

### Расширенные плагины
```
plugins/agents/__init__.py
plugins/agents/handler.py
plugins/agents/registry.py
plugins/agents/orchestrator.py

plugins/graph/__init__.py
plugins/graph/handler.py
plugins/graph/graph_engine.py

plugins/voice/__init__.py
plugins/voice/handler.py

plugins/npu/__init__.py
plugins/npu/handler.py
plugins/npu/inference.py

plugins/benchmark/__init__.py
plugins/benchmark/handler.py

plugins/watchers/__init__.py
plugins/watchers/handler.py

plugins/android/__init__.py
plugins/android/handler.py

plugins/nomad/__init__.py
plugins/nomad/handler.py
plugins/nomad/pipeline.py
plugins/nomad/chunker.py
plugins/nomad/sources/__init__.py
plugins/nomad/sources/zim.py
```

### Community Plugins
```
plugins/community/registry.json

plugins/community/weather/__init__.py
plugins/community/weather/handler.py

plugins/community/todo/__init__.py
plugins/community/todo/handler.py

plugins/community/reminders/__init__.py
plugins/community/reminders/handler.py

plugins/community/clipboard/__init__.py
plugins/community/clipboard/handler.py

plugins/community/system_stats/__init__.py
plugins/community/system_stats/handler.py
```

### Electron HUD
```
client/index.html
client/main.js
client/preload.js
client/package.json
client/package-lock.json
client/css/variables.css
client/css/base.css
client/css/layout.css
client/css/components.css
client/css/animations.css
client/js/api.js
client/js/chat.js
client/js/app.js
```

### Flutter
```
client/flutter/pubspec.yaml
client/flutter/lib/main.dart
client/flutter/lib/app.dart
client/flutter/lib/theme.dart
client/flutter/lib/models/message.dart
client/flutter/lib/services/api_service.dart
client/flutter/lib/providers/chat_provider.dart
client/flutter/lib/providers/memory_provider.dart
client/flutter/lib/providers/files_provider.dart
client/flutter/lib/providers/settings_provider.dart
client/flutter/lib/screens/home_screen.dart
client/flutter/lib/screens/chat_screen.dart
client/flutter/lib/screens/memory_screen.dart
client/flutter/lib/screens/files_screen.dart
client/flutter/lib/screens/settings_screen.dart
client/flutter/lib/widgets/message_bubble.dart
client/flutter/lib/widgets/typing_indicator.dart
client/flutter/android/...
client/flutter/ios/...
client/flutter/web/...
```

### Дополнительные тесты
```
tests/test_agents.py      # Обновлён
tests/test_npu.py          # Обновлён
```

---

## Итого дополнительных файлов: ~60

## Размер PR: ~4000 строк кода
