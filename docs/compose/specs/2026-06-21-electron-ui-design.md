# Jarvis V3.1 — Electron UI Design

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/electron-ui.md)

## [S1] Problem

Нужно создать десктопное приложение Electron для JARVIS V3.1 с интерфейсом в стиле JARVIS из фильма "Железный человек". Приложение должно подключаться к существующему FastAPI серверу на порту 8003 и предоставлять доступ ко всем функциям системы.

## [S2] Solution Overview

### Архитектура

```
Electron App (main process)
    │
    ├── Window (BrowserWindow)
    │   └── Renderer Process
    │       ├── Chat Interface
    │       ├── Memory Management
    │       ├── File Manager
    │       ├── System Dashboard
    │       └── Settings Panel
    │
    └── IPC Bridge
        └── API Client → localhost:8003
```

### Визуальный стиль — Iron Man JARVIS Hub

**Цветовая палитра:**
- Фон: `#000a14` (глубокий черно-синий)
- Основной акцент: `#00d4ff` (голубой неон)
- Вторичный акцент: `#0066cc` (темно-голубой)
- Текст основной: `#b0e8ff` (светло-голубой)
- Текст приглушенный: `#336688`
- Успех: `#3fb950` (зеленый)
- Ошибка: `#ff3b30` (красный)
- Предупреждение: `#ffd60a` (желтый)

**Шрифты:**
- HUD/Заголовки: `Orbitron` ( futurist, tech)
- UI/Элементы: `Rajdhani` (чистый, читаемый)
- Код/Моноширинный: `Share Tech Mono`

**Элементы стиля:**
1. **Holographic Glow** — все элементы с мягким голубым свечением
2. **Circular Arcs** — декоративные дуги вокруг ключевых элементов
3. **Scan Lines** — тонкие горизонтальные линии для эффекта сканирования
4. **Glass Morphism** — полупрозрачные панели с blur эффектом
5. **Animated Transitions** — плавные анимации при наведении и клике
6. **Voice Indicator** — анимированный индикатор голосового ввода
7. **System Status Ring** — круговой индикатор статуса системы

## [S3] Структура экранов

### 3.1 Main Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] JARVIS V3.1    [Status Ring]    [Model] [Controls] │
├─────────┬───────────────────────────────────────────────────┤
│         │                                                   │
│  NAV    │              CONTENT AREA                         │
│  PANEL  │                                                   │
│         │  ┌─────────────────┬─────────────────────────┐   │
│  • Chat │  │                 │                         │   │
│  • Files│  │   Chat Panel    │    Workspace Panel      │   │
│  • RAG  │  │                 │                         │   │
│  • Mem  │  │                 │                         │   │
│  • Graph│  │                 │                         │   │
│  • Set  │  └─────────────────┴─────────────────────────┘   │
│         │                                                   │
├─────────┴───────────────────────────────────────────────────┤
│  [Status Bar]                              [Plugins: 12/16] │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Chat Interface

- **Welcome Screen** — анимированный логотип JARVIS с эффектом появления
- **Messages** — пузыри сообщений с role labels
- **Streaming** — посимвольное отображение с курсором
- **Tool Results** — отдельный блок для результатов инструментов
- **Voice Input** — кнопка микрофона с анимацией записи

### 3.3 Memory Management

- **Sessions** — список сессий с превью
- **Facts** — карточки фактов по сущностям
- **Notes** — заметки с поиском
- **Search** — полнотекстовый поиск по истории

### 3.4 File Manager

- **Tree View** — дерево файлов с иконками
- **Preview** — предпросмотр содержимого
- **Drag & Drop** — загрузка файлов перетаскиванием
- **Actions** — копирование, перемещение, удаление

### 3.5 System Dashboard

- **Health** — статус всех плагинов
- **Metrics** — сообщения, сессии, факты
- **Plugins** — карточки плагинов с toggle
- **Events** — лог событий

### 3.6 Settings

- **Server** — URL, ключ доступа
- **Model** — выбор модели Ollama
- **TTS/STT** — настройки голоса
- **Proactive** — приветствие, советы

## [S4] Технические требования

### Electron Main Process

```javascript
// main.js
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    frame: false, // Кастомный titlebar
    backgroundColor: '#000a14',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('index.html');
}

// IPC handlers для API вызовов
ipcMain.handle('api:request', async (event, { method, path, body }) => {
  const response = await fetch(`http://localhost:8003${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Auth-Key': 'jarvis-v3.1'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  return response.json();
});
```

### Preload Script

```javascript
// preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvis', {
  api: (method, path, body) => ipcRenderer.invoke('api:request', { method, path, body }),
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close')
});
```

### Renderer Process

- Vanilla JS (без фреймворков для минимизации размера)
- CSS Variables для темы
- Custom Elements для переиспользования
- SSE для стриминга чата

## [S5] Анимации и эффекты

### 1. Holographic Pulse

```css
@keyframes holoPulse {
  0%, 100% { box-shadow: 0 0 5px rgba(0,212,255,0.3); }
  50% { box-shadow: 0 0 20px rgba(0,212,255,0.6); }
}
```

### 2. Scan Line Effect

```css
.scan-lines::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,180,255,0.03) 2px,
    rgba(0,180,255,0.03) 4px
  );
  pointer-events: none;
}
```

### 3. Circular Status Ring

```css
.status-ring {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 2px solid var(--blue);
  position: relative;
}

.status-ring::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1px solid transparent;
  border-top-color: var(--blue);
  animation: ringRotate 2s linear infinite;
}

@keyframes ringRotate {
  to { transform: rotate(360deg); }
}
```

### 4. Voice Wave Animation

```css
.voice-wave {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 20px;
}

.voice-wave span {
  width: 3px;
  background: var(--blue);
  animation: wave 0.8s ease-in-out infinite;
}

.voice-wave span:nth-child(2) { animation-delay: 0.1s; }
.voice-wave span:nth-child(3) { animation-delay: 0.2s; }

@keyframes wave {
  0%, 100% { height: 4px; }
  50% { height: 16px; }
}
```

## [S6] File Structure

```
client/
├── main.js              # Electron main process
├── preload.js           # Context bridge
├── package.json         # Dependencies
├── index.html           # Main HTML
├── css/
│   ├── variables.css    # CSS variables
│   ├── base.css         # Reset + base styles
│   ├── layout.css       # Grid layout
│   ├── components.css   # UI components
│   └── animations.css   # Animations
├── js/
│   ├── app.js           # Main app logic
│   ├── api.js           # API client
│   ├── chat.js          # Chat functionality
│   ├── files.js         # File manager
│   ├── memory.js        # Memory management
│   ├── dashboard.js     # System dashboard
│   └── settings.js      # Settings panel
└── assets/
    ├── logo.svg         # JARVIS logo
    └── icons/           # UI icons
```

## [S7] API Integration

### Endpoints для UI

| Screen | Endpoint | Method | Description |
|--------|----------|--------|-------------|
| Chat | `/brain/chat/stream` | POST | Стриминг чата |
| Chat | `/brain/agent` | POST | Агент с tool execution |
| Memory | `/memory_v2/facts/get` | POST | Получение фактов |
| Memory | `/memory_v2/sessions` | GET | Список сессий |
| Memory | `/memory_v2/history` | POST | История чата |
| Files | `/files/ls` | POST | Список файлов |
| Files | `/files/read` | POST | Чтение файла |
| Dashboard | `/health` | GET | Статус системы |
| Dashboard | `/plugins` | GET | Список плагинов |
| Settings | `/brain/personality` | GET | Настройки персоны |

## [S8] Success Criteria

1. ✅ Electron app запускается и показывает окно
2. ✅ Кастомный titlebar с drag functionality
3. ✅ Все 6 экранов работают
4. ✅ Chat streaming работает через SSE
5. ✅ File manager позволяет просматривать и открывать файлы
6. ✅ Memory management показывает сессии и факты
7. ✅ Dashboard отображает статус всех плагинов
8. ✅ Settings позволяют менять конфигурацию
9. ✅ Все анимации работают плавно
10. ✅ Приложение весит < 100MB
