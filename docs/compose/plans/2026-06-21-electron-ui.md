# Jarvis V3.1 Electron UI Implementation Plan

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/electron-ui.md)

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Electron desktop application for JARVIS V3.1 with Iron Man JARVIS style UI

**Architecture:** Electron app with custom frameless window, vanilla JS renderer, CSS variables for theming, SSE for chat streaming

**Tech Stack:** Electron 28+, Vanilla JS, CSS3, Node.js

---

## File Structure

```
client/
├── main.js              # Electron main process
├── preload.js           # Context bridge for IPC
├── package.json         # Dependencies
├── index.html           # Main HTML structure
├── css/
│   ├── variables.css    # CSS custom properties
│   ├── base.css         # Reset + typography
│   ├── layout.css       # Grid layout system
│   ├── components.css   # UI components
│   └── animations.css   # Keyframe animations
├── js/
│   ├── app.js           # Main app initialization
│   ├── api.js           # API client wrapper
│   ├── chat.js          # Chat streaming logic
│   ├── files.js         # File manager
│   ├── memory.js        # Memory management
│   ├── dashboard.js     # System dashboard
│   └── settings.js      # Settings panel
└── assets/
    └── icons/           # SVG icons
```

---

### Task 1: Project Setup

**Covers:** [S6]

**Files:**
- Create: `client/package.json`
- Create: `client/main.js`
- Create: `client/preload.js`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "jarvis-v3.1-client",
  "version": "3.1.0",
  "description": "JARVIS V3.1 Electron Client",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "dev": "electron . --dev"
  },
  "devDependencies": {
    "electron": "^28.0.0"
  }
}
```

- [ ] **Step 2: Create main.js**

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    frame: false,
    backgroundColor: '#000a14',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('index.html');

  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

ipcMain.handle('api:request', async (event, { method, urlPath, body }) => {
  try {
    const response = await fetch(`http://localhost:8003${urlPath}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-Key': 'jarvis-v3.1'
      },
      body: body ? JSON.stringify(body) : undefined
    });
    return await response.json();
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.on('window:minimize', () => mainWindow?.minimize());
ipcMain.on('window:maximize', () => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize();
  else mainWindow?.maximize();
});
ipcMain.on('window:close', () => mainWindow?.close());
```

- [ ] **Step 3: Create preload.js**

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvis', {
  api: (method, urlPath, body) => ipcRenderer.invoke('api:request', { method, urlPath, body }),
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close')
});
```

- [ ] **Step 4: Install dependencies and test**

Run: `cd client && npm install && npm start`
Expected: Electron window opens with blank page

- [ ] **Step 5: Commit**

```bash
git add client/
git commit -m "feat: add Electron project structure with main process"
```

---

### Task 2: HTML Structure

**Covers:** [S3]

**Files:**
- Create: `client/index.html`

- [ ] **Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'">
  <title>J.A.R.V.I.S V3.1</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Rajdhani:wght@300;400;600&family=Share+Tech+Mono&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/variables.css">
  <link rel="stylesheet" href="css/base.css">
  <link rel="stylesheet" href="css/layout.css">
  <link rel="stylesheet" href="css/components.css">
  <link rel="stylesheet" href="css/animations.css">
</head>
<body>
  <div id="app">
    <header id="titlebar">
      <div class="logo">
        <span class="logo-text">JARVIS</span>
        <span class="logo-version">V3.1</span>
      </div>
      <div class="status-ring" id="status-ring">
        <div class="status-ring-inner"></div>
        <span class="status-text" id="status-text">ОЖИДАНИЕ</span>
      </div>
      <div class="model-badge" id="model-badge">QWEN2.5:14B</div>
      <div class="spacer"></div>
      <div class="window-controls">
        <button class="win-btn" id="btn-minimize">─</button>
        <button class="win-btn" id="btn-maximize">□</button>
        <button class="win-btn win-btn-close" id="btn-close">✕</button>
      </div>
    </header>

    <main id="main-area">
      <nav id="side-panel">
        <div class="nav-section">
          <div class="nav-title">НАВИГАЦИЯ</div>
          <div id="nav-list"></div>
        </div>
        <div class="nav-section">
          <div class="nav-title">УПРАВЛЕНИЕ</div>
          <div class="controls">
            <button class="ctrl-btn" id="btn-agent">АГЕНТ</button>
            <button class="ctrl-btn" id="btn-memory">ПАМЯТЬ</button>
            <button class="ctrl-btn" id="btn-tts">ОЗВУЧКА</button>
          </div>
        </div>
        <div class="nav-section">
          <div class="nav-title">МОДУЛИ</div>
          <div id="plugins-list" class="plugins-grid"></div>
        </div>
        <div class="nav-section nav-bottom">
          <div class="nav-title">НАСТРОЙКИ</div>
          <input type="text" id="cfg-server" placeholder="URL сервера" value="http://localhost:8003">
          <input type="text" id="cfg-key" placeholder="Ключ доступа" value="jarvis-v3.1">
        </div>
      </nav>

      <div id="content-area">
        <div id="chat-panel">
          <div id="messages">
            <div class="welcome">
              <div class="welcome-logo">JARVIS</div>
              <div class="welcome-sub">VERSON 3.1 AI OS</div>
              <div class="welcome-divider"></div>
              <div class="welcome-hint">СИСТЕМА ГОТОВА</div>
            </div>
          </div>
          <div id="input-area">
            <textarea id="user-input" rows="1" placeholder="Введите команду..."></textarea>
            <button class="input-btn" id="btn-mic" title="Голосовой ввод">🎤</button>
            <button class="input-btn" id="btn-send">▶</button>
            <button class="input-btn input-btn-stop" id="btn-stop" style="display:none">⏹</button>
          </div>
        </div>
        <div id="divider"></div>
        <div id="workspace-panel">
          <div class="workspace-placeholder">
            <div class="placeholder-title">РАБОЧАЯ ОБЛАСТЬ</div>
            <div class="placeholder-text">ВЫБЕРИТЕ СТРАНИЦУ</div>
          </div>
        </div>
      </div>
    </main>

    <footer id="statusbar">
      <span id="status-message">СИСТЕМА ГОТОВА</span>
      <span class="spacer"></span>
      <span id="plugin-count">PLUGINS: 0/0</span>
    </footer>
  </div>

  <script src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add client/index.html
git commit -m "feat: add main HTML structure with titlebar and panels"
```

---

### Task 3: CSS Variables and Base Styles

**Covers:** [S2]

**Files:**
- Create: `client/css/variables.css`
- Create: `client/css/base.css`

- [ ] **Step 1: Create variables.css**

```css
:root {
  --bg: #000a14;
  --bg-deep: #000610;
  --bg-panel: #000d1a;
  --bg-panel2: #001020;
  --bg-msg-user: #001830;
  --bg-msg-ai: #000c18;
  
  --border: #003366;
  --border-bright: #0055aa;
  --border-glow: #0088ff;
  
  --blue: #00d4ff;
  --blue-bright: #40e8ff;
  --blue-dim: #004466;
  --blue-glow: rgba(0, 212, 255, 0.15);
  
  --accent: #0088ff;
  --text: #b0e8ff;
  --text-bright: #e0f8ff;
  --text-dim: #336688;
  --text-muted: #1a3a55;
  
  --green: #3fb950;
  --red: #ff3b30;
  --yellow: #ffd60a;
  
  --font-mono: 'Share Tech Mono', 'Courier New', monospace;
  --font-hud: 'Orbitron', sans-serif;
  --font-ui: 'Rajdhani', sans-serif;
  
  --radius: 3px;
  --titlebar-h: 42px;
  --side-w: 220px;
  --statusbar-h: 28px;
}
```

- [ ] **Step 2: Create base.css**

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  overflow: hidden;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-ui);
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 180, 255, 0.018) 2px,
    rgba(0, 180, 255, 0.018) 4px
  );
}

::selection {
  background: var(--blue);
  color: var(--bg);
}

::-webkit-scrollbar {
  width: 3px;
}

::-webkit-scrollbar-track {
  background: var(--bg-deep);
}

::-webkit-scrollbar-thumb {
  background: var(--blue-dim);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--blue);
}

a {
  color: var(--blue);
  text-decoration: none;
}

a:hover {
  color: var(--blue-bright);
}
```

- [ ] **Step 3: Commit**

```bash
git add client/css/variables.css client/css/base.css
git commit -m "feat: add CSS variables and base styles"
```

---

### Task 4: Layout Styles

**Covers:** [S3]

**Files:**
- Create: `client/css/layout.css`

- [ ] **Step 1: Create layout.css**

```css
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  border: 1px solid var(--border-bright);
  box-shadow: 0 0 40px rgba(0, 100, 255, 0.15), inset 0 0 100px rgba(0, 0, 0, 0.8);
  position: relative;
  z-index: 1;
}

#titlebar {
  height: var(--titlebar-h);
  display: flex;
  align-items: center;
  padding: 0 14px;
  background: linear-gradient(180deg, #001830 0%, #000d1a 100%);
  border-bottom: 1px solid var(--border-bright);
  -webkit-app-region: drag;
  flex-shrink: 0;
  gap: 10px;
  box-shadow: 0 2px 20px rgba(0, 100, 255, 0.2);
}

#main-area {
  display: flex;
  flex: 1;
  overflow: hidden;
}

#side-panel {
  width: var(--side-w);
  flex-shrink: 0;
  background: linear-gradient(180deg, #000d1a 0%, #000810 100%);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 14px 12px;
  gap: 18px;
  overflow-y: auto;
}

#content-area {
  flex: 1;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

#chat-panel {
  width: 50%;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  overflow: hidden;
}

#divider {
  width: 5px;
  cursor: col-resize;
  flex-shrink: 0;
  background: var(--border);
  transition: background 0.2s;
  position: relative;
}

#divider:hover, #divider.dragging {
  background: var(--blue);
}

#divider::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 1px;
  height: 40px;
  background: repeating-linear-gradient(
    180deg,
    var(--text-muted) 0px,
    var(--text-muted) 3px,
    transparent 3px,
    transparent 6px
  );
}

#workspace-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

#messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

#input-area {
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  background: linear-gradient(0deg, #000810 0%, #000d1a 100%);
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

#statusbar {
  height: var(--statusbar-h);
  display: flex;
  align-items: center;
  padding: 0 14px;
  background: var(--bg-deep);
  border-top: 1px solid var(--border);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--text-muted);
  gap: 20px;
}

.spacer {
  flex: 1;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-title {
  font-family: var(--font-hud);
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 4px;
  color: var(--blue);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.4);
}

.nav-bottom {
  margin-top: auto;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
```

- [ ] **Step 2: Commit**

```bash
git add client/css/layout.css
git commit -m "feat: add layout styles for main panels"
```

---

### Task 5: Component Styles

**Covers:** [S2, S5]

**Files:**
- Create: `client/css/components.css`

- [ ] **Step 1: Create components.css**

```css
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-hud);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 5px;
  color: var(--blue);
  text-shadow: 0 0 20px var(--blue), 0 0 40px rgba(0, 212, 255, 0.3);
}

.logo-version {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-dim);
  letter-spacing: 2px;
}

.status-ring {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.status-ring.active {
  border-color: var(--blue);
  box-shadow: 0 0 15px var(--blue-glow);
}

.status-ring-inner {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: all 0.3s;
}

.status-ring.active .status-ring-inner {
  background: var(--blue);
  box-shadow: 0 0 10px var(--blue);
}

.status-text {
  position: absolute;
  bottom: -18px;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-hud);
  font-size: 7px;
  letter-spacing: 2px;
  color: var(--text-dim);
  white-space: nowrap;
}

.model-badge {
  font-family: var(--font-hud);
  font-size: 9px;
  font-weight: 600;
  color: var(--blue);
  letter-spacing: 2px;
  background: rgba(0, 180, 255, 0.06);
  border: 1px solid var(--blue-dim);
  padding: 3px 8px;
  border-radius: 2px;
}

.window-controls {
  display: flex;
  gap: 2px;
  -webkit-app-region: no-drag;
}

.win-btn {
  width: 30px;
  height: 24px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-dim);
  font-size: 10px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.win-btn:hover {
  background: var(--blue-dim);
  color: var(--text);
  border-color: var(--blue);
}

.win-btn-close:hover {
  background: var(--red);
  border-color: var(--red);
  color: white;
}

.module-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 7px 8px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.module-item:hover {
  border-color: var(--blue-dim);
  background: var(--bg-panel2);
}

.module-item.active {
  border-color: var(--blue);
  background: rgba(0, 180, 255, 0.08);
}

.module-name {
  font-family: var(--font-hud);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--text-dim);
}

.module-item.active .module-name {
  color: var(--blue);
}

.plugins-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.plugin-card {
  background: var(--bg-panel2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.plugin-card:hover {
  border-color: var(--blue-dim);
}

.plugin-card.active {
  border-color: var(--green);
}

.plugin-card .name {
  font-family: var(--font-hud);
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--text-dim);
}

.plugin-card.active .name {
  color: var(--green);
}

.ctrl-btn {
  background: rgba(0, 180, 255, 0.06);
  cursor: pointer;
  font-family: var(--font-hud);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 2px;
  padding: 6px 10px;
  width: 100%;
  border: 1px solid var(--blue-dim);
  border-radius: 2px;
  color: var(--blue);
  transition: all 0.2s;
  text-align: center;
}

.ctrl-btn:hover {
  background: rgba(0, 180, 255, 0.15);
  border-color: var(--blue);
}

.ctrl-btn.active {
  background: var(--blue);
  color: var(--bg);
}

.input-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--blue);
  cursor: pointer;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.input-btn:hover {
  background: var(--blue);
  color: var(--bg);
}

.input-btn:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.input-btn-stop {
  color: var(--red);
}

.input-btn-stop:hover {
  background: var(--red);
  color: white;
}

#user-input {
  flex: 1;
  background: var(--bg-deep);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-bright);
  font-family: var(--font-mono);
  font-size: 13px;
  padding: 10px 14px;
  resize: none;
  outline: none;
  min-height: 40px;
  max-height: 120px;
  line-height: 1.5;
}

#user-input:focus {
  border-color: var(--blue-dim);
  box-shadow: 0 0 12px var(--blue-glow);
}

#user-input::placeholder {
  color: var(--text-muted);
}

.message {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message.user {
  align-items: flex-end;
}

.message.ai {
  align-items: flex-start;
}

.message.system {
  align-items: center;
}

.msg-role {
  font-family: var(--font-hud);
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 3px;
  color: var(--text-dim);
  padding: 0 4px;
}

.message.user .msg-role {
  color: var(--blue-dim);
}

.message.ai .msg-role {
  color: var(--blue);
}

.msg-body {
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  padding: 10px 14px;
  border-radius: var(--radius);
  max-width: 80%;
  border: 1px solid var(--border);
}

.message.user .msg-body {
  background: var(--bg-msg-user);
  color: var(--text-bright);
  border-color: var(--blue-dim);
}

.message.ai .msg-body {
  background: var(--bg-msg-ai);
  color: var(--text);
  border-color: var(--border);
}

.message.system .msg-body {
  background: none;
  border: none;
  padding: 4px 10px;
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--text-muted);
}

.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  opacity: 0.6;
}

.welcome-logo {
  font-family: var(--font-hud);
  font-size: 48px;
  font-weight: 900;
  letter-spacing: 15px;
  color: var(--blue);
  text-shadow: 0 0 40px var(--blue), 0 0 80px rgba(0, 212, 255, 0.3);
}

.welcome-sub {
  font-family: var(--font-hud);
  font-size: 11px;
  letter-spacing: 6px;
  color: var(--text-dim);
}

.welcome-divider {
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--blue), transparent);
}

.welcome-hint {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 3px;
  color: var(--text-muted);
}

.workspace-placeholder {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  opacity: 0.4;
}

.placeholder-title {
  font-family: var(--font-hud);
  font-size: 11px;
  letter-spacing: 4px;
  color: var(--text-dim);
  margin-bottom: 8px;
}

.placeholder-text {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--text-muted);
}

#status-message {
  color: var(--text-dim);
}

#status-message.active {
  color: var(--blue);
  animation: statusPulse 1s infinite;
}

#cfg-server, #cfg-key {
  background: var(--bg-deep);
  border: 1px solid var(--border);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 4px 6px;
  border-radius: 2px;
  outline: none;
}

#cfg-server:focus, #cfg-key:focus {
  border-color: var(--blue-dim);
}
```

- [ ] **Step 2: Commit**

```bash
git add client/css/components.css
git commit -m "feat: add component styles for UI elements"
```

---

### Task 6: Animation Styles

**Covers:** [S5]

**Files:**
- Create: `client/css/animations.css`

- [ ] **Step 1: Create animations.css**

```css
@keyframes holoPulse {
  0%, 100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.3); }
  50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.6); }
}

@keyframes ringRotate {
  to { transform: rotate(360deg); }
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes thinkDot {
  0%, 80%, 100% { opacity: 0.2; }
  40% { opacity: 1; }
}

@keyframes wave {
  0%, 100% { height: 4px; }
  50% { height: 16px; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.thinking {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 2px;
}

.thinking-dots span {
  display: inline-block;
  width: 4px;
  height: 4px;
  background: var(--blue);
  border-radius: 50%;
  animation: thinkDot 1.4s infinite;
  margin: 0 2px;
}

.thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots span:nth-child(3) { animation-delay: 0.4s; }

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
.voice-wave span:nth-child(4) { animation-delay: 0.3s; }
.voice-wave span:nth-child(5) { animation-delay: 0.4s; }

.fade-in {
  animation: fadeIn 0.3s ease-out;
}

.slide-in {
  animation: slideIn 0.3s ease-out;
}
```

- [ ] **Step 2: Commit**

```bash
git add client/css/animations.css
git commit -m "feat: add CSS animations for holographic effects"
```

---

### Task 7: API Client

**Covers:** [S4, S7]

**Files:**
- Create: `client/js/api.js`

- [ ] **Step 1: Create api.js**

```javascript
const API = {
  getConfig() {
    return {
      server: document.getElementById('cfg-server')?.value?.trim() || 'http://localhost:8003',
      key: document.getElementById('cfg-key')?.value?.trim() || ''
    };
  },

  authHeaders() {
    const cfg = this.getConfig();
    const headers = { 'Content-Type': 'application/json' };
    if (cfg.key) headers['X-Auth-Key'] = cfg.key;
    return headers;
  },

  async request(method, urlPath, body) {
    try {
      const cfg = this.getConfig();
      const opts = {
        method,
        headers: this.authHeaders()
      };
      if (body) opts.body = JSON.stringify(body);
      const response = await fetch(`${cfg.server}${urlPath}`, opts);
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      return { error: error.message };
    }
  },

  async stream(method, urlPath, body, onChunk, onDone) {
    const cfg = this.getConfig();
    const opts = {
      method,
      headers: this.authHeaders(),
      signal: window._abortController?.signal
    };
    if (body) opts.body = JSON.stringify(body);

    try {
      const response = await fetch(`${cfg.server}${urlPath}`, opts);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;
          const data = trimmed.slice(6);
          if (data === '[DONE]') {
            onDone?.();
            return;
          }
          try {
            const json = JSON.parse(data);
            onChunk?.(json);
          } catch (e) {
            if (!e.message?.includes('JSON')) throw e;
          }
        }
      }
      onDone?.();
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Stream Error:', error);
        throw error;
      }
    }
  }
};
```

- [ ] **Step 2: Commit**

```bash
git add client/js/api.js
git commit -m "feat: add API client with streaming support"
```

---

### Task 8: Chat Functionality

**Covers:** [S3, S7]

**Files:**
- Create: `client/js/chat.js`

- [ ] **Step 1: Create chat.js**

```javascript
const Chat = {
  history: [],
  isStreaming: false,
  abortController: null,
  agentMode: false,
  memoryEnabled: true,
  ttsEnabled: false,

  init() {
    this.messages = document.getElementById('messages');
    this.input = document.getElementById('user-input');
    this.sendBtn = document.getElementById('btn-send');
    this.stopBtn = document.getElementById('btn-stop');

    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    });

    this.input.addEventListener('input', () => {
      this.input.style.height = 'auto';
      this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
    });

    this.sendBtn.addEventListener('click', () => this.send());
    this.stopBtn.addEventListener('click', () => this.stop());
  },

  async send() {
    const content = this.input.value.trim();
    if (!content || this.isStreaming) return;

    this.input.value = '';
    this.input.style.height = 'auto';

    const welcome = this.messages.querySelector('.welcome');
    if (welcome) welcome.remove();

    this.setStreaming(true);
    this.appendMessage('user', content);
    this.history.push({ role: 'user', content });

    const aiEl = this.appendMessage('ai', '');
    const bodyEl = aiEl.querySelector('.msg-body');
    const think = this.createThinking();
    bodyEl.appendChild(think);
    this.scrollToBottom();

    try {
      this.abortController = new AbortController();
      window._abortController = this.abortController;

      const endpoint = this.agentMode ? '/brain/agent' : '/brain/chat/stream';
      const body = {
        messages: this.history,
        use_memory: this.memoryEnabled
      };

      let fullText = '';
      let first = true;

      await API.stream('POST', endpoint, body, (chunk) => {
        if (chunk.error) throw new Error(chunk.error);
        
        if (first && chunk.content) {
          think.remove();
          first = false;
        }
        
        if (chunk.content) {
          fullText += chunk.content;
          bodyEl.innerHTML = this.renderMD(fullText);
          this.scrollToBottom();
        }
      }, () => {
        this.history.push({ role: 'assistant', content: fullText });
      });
    } catch (error) {
      think.remove();
      if (error.name === 'AbortError') {
        this.appendSystem('ГЕНЕРАЦИЯ ОСТАНОВЛЕНА');
      } else {
        bodyEl.innerHTML = this.renderMD(`**Error:** ${error.message}`);
        this.appendSystem('ПОТЕРЯ СВЯЗИ');
      }
    } finally {
      this.abortController = null;
      window._abortController = null;
      this.setStreaming(false);
    }
  },

  stop() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  },

  appendMessage(role, content) {
    const wrapper = document.createElement('div');
    wrapper.className = `message ${role} fade-in`;
    
    const label = document.createElement('div');
    label.className = 'msg-role';
    label.textContent = role === 'user' ? '// ОПЕРАТОР' : '// J.A.R.V.I.S';
    
    const body = document.createElement('div');
    body.className = 'msg-body';
    if (content) {
      body.innerHTML = role === 'ai' ? this.renderMD(content) : this.escapeHtml(content);
    }
    
    wrapper.appendChild(label);
    wrapper.appendChild(body);
    this.messages.appendChild(wrapper);
    this.scrollToBottom();
    return wrapper;
  },

  appendSystem(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message system fade-in';
    const body = document.createElement('div');
    body.className = 'msg-body';
    body.textContent = `>> ${text}`;
    wrapper.appendChild(body);
    this.messages.appendChild(wrapper);
    this.scrollToBottom();
  },

  createThinking() {
    const el = document.createElement('div');
    el.className = 'thinking';
    el.innerHTML = `<span>ОБРАБОТКА</span>
      <div class="thinking-dots"><span></span><span></span><span></span></div>`;
    return el;
  },

  setStreaming(val) {
    this.isStreaming = val;
    this.sendBtn.disabled = val;
    this.stopBtn.style.display = val ? 'flex' : 'none';
    this.sendBtn.style.display = val ? 'none' : 'flex';
    
    const statusRing = document.getElementById('status-ring');
    const statusText = document.getElementById('status-text');
    
    if (val) {
      statusRing?.classList.add('active');
      statusText.textContent = 'ГЕНЕРАЦИЯ';
    } else {
      statusRing?.classList.remove('active');
      statusText.textContent = 'ОЖИДАНИЕ';
    }
  },

  scrollToBottom() {
    requestAnimationFrame(() => {
      this.messages.scrollTop = this.messages.scrollHeight;
    });
  },

  renderMD(text) {
    if (!text) return '';
    return this.escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^- (.*$)/gm, '<li>$1</li>')
      .replace(/\n/g, '<br>');
  },

  escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  },

  clear() {
    this.history = [];
    this.messages.innerHTML = `
      <div class="welcome">
        <div class="welcome-logo">JARVIS</div>
        <div class="welcome-sub">VERSION 3.1 AI OS</div>
        <div class="welcome-divider"></div>
        <div class="welcome-hint">СЕССИЯ ОЧИЩЕНА</div>
      </div>`;
  },

  toggleAgent() {
    this.agentMode = !this.agentMode;
    document.getElementById('btn-agent')?.classList.toggle('active', this.agentMode);
    this.appendSystem(this.agentMode ? 'РЕЖИМ АГЕНТА: ВКЛ' : 'РЕЖИМ АГЕНТА: ВЫКЛ');
  },

  toggleMemory() {
    this.memoryEnabled = !this.memoryEnabled;
    document.getElementById('btn-memory')?.classList.toggle('active', this.memoryEnabled);
    this.appendSystem(this.memoryEnabled ? 'ПАМЯТЬ: ВКЛ' : 'ПАМЯТЬ: ВЫКЛ');
  },

  toggleTTS() {
    this.ttsEnabled = !this.ttsEnabled;
    document.getElementById('btn-tts')?.classList.toggle('active', this.ttsEnabled);
    this.appendSystem(this.ttsEnabled ? 'ОЗВУЧКА: ВКЛ' : 'ОЗВУЧКА: ВЫКЛ');
  }
};
```

- [ ] **Step 2: Commit**

```bash
git add client/js/chat.js
git commit -m "feat: add chat functionality with streaming"
```

---

### Task 9: Main App Initialization

**Covers:** [S3, S4]

**Files:**
- Create: `client/js/app.js`

- [ ] **Step 1: Create app.js**

```javascript
const App = {
  currentPage: 'chat',
  pages: [
    { id: 'chat', title: 'ЧАТ' },
    { id: 'files', title: 'ФАЙЛЫ' },
    { id: 'rag', title: 'ЗНАНИЯ' },
    { id: 'memory', title: 'ПАМЯТЬ' },
    { id: 'graph', title: 'ГРАФ' },
    { id: 'settings', title: 'НАСТРОЙКИ' }
  ],

  init() {
    Chat.init();
    this.buildNav();
    this.bindEvents();
    this.checkHealth();
    setInterval(() => this.checkHealth(), 15000);
  },

  buildNav() {
    const nav = document.getElementById('nav-list');
    if (!nav) return;
    
    nav.innerHTML = this.pages.map(p => `
      <div class="module-item ${p.id === this.currentPage ? 'active' : ''}" data-page="${p.id}">
        <div class="module-name">${p.title}</div>
      </div>
    `).join('');

    nav.querySelectorAll('.module-item').forEach(item => {
      item.addEventListener('click', () => {
        this.showPage(item.dataset.page);
      });
    });
  },

  showPage(id) {
    this.currentPage = id;
    this.buildNav();
    
    const workspace = document.getElementById('workspace-panel');
    if (!workspace) return;

    switch (id) {
      case 'chat':
        workspace.innerHTML = `
          <div class="workspace-placeholder">
            <div class="placeholder-title">РАБОЧАЯ ОБЛАСТЬ</div>
            <div class="placeholder-text">ВЫБЕРИТЕ СТРАНИЦУ</div>
          </div>`;
        break;
      case 'files':
        this.showFiles();
        break;
      case 'rag':
        this.showRAG();
        break;
      case 'memory':
        this.showMemory();
        break;
      case 'graph':
        this.showGraph();
        break;
      case 'settings':
        this.showSettings();
        break;
    }
  },

  async checkHealth() {
    try {
      const data = await API.request('GET', '/health');
      if (data.status === 'ok') {
        document.getElementById('status-ring')?.classList.add('active');
        document.getElementById('plugin-count').textContent = 
          `PLUGINS: ${data.plugins_loaded}/${data.plugins_total}`;
        this.updatePlugins(data.plugins || {});
      }
    } catch (error) {
      document.getElementById('status-ring')?.classList.remove('active');
      document.getElementById('plugin-count').textContent = 'PLUGINS: 0/0';
    }
  },

  updatePlugins(plugins) {
    const list = document.getElementById('plugins-list');
    if (!list) return;

    list.innerHTML = Object.entries(plugins).map(([name, info]) => `
      <div class="plugin-card ${info.loaded ? 'active' : ''}">
        <div class="name">${name.toUpperCase()}</div>
      </div>
    `).join('');
  },

  async showFiles() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div class="nav-title" style="margin-bottom:16px">ФАЙЛОВАЯ СИСТЕМА</div>
        <div id="files-content"></div>
      </div>`;

    try {
      const data = await API.request('POST', '/files/ls', {});
      const el = document.getElementById('files-content');
      const items = data.items || [];

      el.innerHTML = items.map(item => `
        <div class="module-item" data-path="${item.path}">
          <div class="module-name">${item.is_dir ? '📁' : '📄'} ${item.name}</div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Files error:', error);
    }
  },

  async showRAG() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div class="nav-title" style="margin-bottom:16px">БАЗА ЗНАНИЙ</div>
        <div style="display:flex;gap:8px;margin-bottom:16px">
          <input type="text" id="rag-query" placeholder="Поиск в базе знаний..."
            style="flex:1;background:var(--bg-deep);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:var(--radius);font-family:var(--font-mono);font-size:12px">
          <button class="ctrl-btn" onclick="App.searchRAG()">ПОИСК</button>
        </div>
        <div id="rag-results"></div>
      </div>`;
  },

  async searchRAG() {
    const query = document.getElementById('rag-query')?.value;
    if (!query) return;

    try {
      const data = await API.request('POST', '/rag/search', { query, n_results: 5 });
      const el = document.getElementById('rag-results');
      const results = data.results || [];

      el.innerHTML = results.map(r => `
        <div style="padding:10px;margin:8px 0;background:rgba(0,180,255,0.04);border:1px solid var(--border);border-radius:var(--radius)">
          <div style="font-family:var(--font-mono);font-size:12px;color:var(--text)">${r.text}</div>
          <div style="font-family:var(--font-mono);font-size:10px;color:var(--text-dim);margin-top:8px">
            Distance: ${r.distance?.toFixed(4) || 'N/A'}
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('RAG search error:', error);
    }
  },

  async showMemory() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div class="nav-title" style="margin-bottom:16px">ПАМЯТЬ</div>
        <div style="display:flex;gap:8px;margin-bottom:16px">
          <button class="ctrl-btn" onclick="App.loadSessions()">СЕССИИ</button>
          <button class="ctrl-btn" onclick="App.loadFacts()">ФАКТЫ</button>
          <button class="ctrl-btn" onclick="App.loadNotes()">ЗАМЕТКИ</button>
        </div>
        <div id="memory-content"></div>
      </div>`;
    this.loadSessions();
  },

  async loadSessions() {
    try {
      const data = await API.request('GET', '/memory_v2/sessions');
      const el = document.getElementById('memory-content');
      const sessions = data.sessions || [];

      el.innerHTML = sessions.map(s => `
        <div style="padding:10px;margin:8px 0;background:rgba(0,180,255,0.04);border:1px solid var(--border);border-radius:var(--radius)">
          <div style="font-family:var(--font-hud);font-size:10px;color:var(--blue)">${s.id.substring(0, 20)}</div>
          <div style="font-family:var(--font-mono);font-size:11px;color:var(--text-dim);margin-top:4px">
            ${s.message_count || 0} сообщений
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Sessions error:', error);
    }
  },

  async loadFacts() {
    try {
      const data = await API.request('POST', '/memory_v2/facts/get', {});
      const el = document.getElementById('memory-content');
      const facts = data.facts || [];

      el.innerHTML = facts.map(f => `
        <div style="padding:10px;margin:8px 0;background:rgba(0,180,255,0.04);border:1px solid var(--border);border-radius:var(--radius)">
          <div style="font-family:var(--font-hud);font-size:10px;color:var(--yellow)">${f.entity} → ${f.key}</div>
          <div style="font-family:var(--font-mono);font-size:12px;color:var(--text);margin-top:4px">${f.value}</div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Facts error:', error);
    }
  },

  async loadNotes() {
    try {
      const data = await API.request('GET', '/memory_v2/notes');
      const el = document.getElementById('memory-content');
      const notes = data.notes || [];

      el.innerHTML = notes.map(n => `
        <div style="padding:10px;margin:8px 0;background:rgba(0,180,255,0.04);border:1px solid var(--border);border-radius:var(--radius)">
          <div style="font-family:var(--font-hud);font-size:10px;color:var(--green)">${n.key}</div>
          <div style="font-family:var(--font-mono);font-size:12px;color:var(--text);margin-top:4px">${n.content?.substring(0, 200)}</div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Notes error:', error);
    }
  },

  async showGraph() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div class="nav-title" style="margin-bottom:16px">ГРАФ ЗНАНИЙ</div>
        <div id="graph-content">
          <div style="font-family:var(--font-mono);font-size:12px;color:var(--text-dim)">
            Загрузка графа...
          </div>
        </div>
      </div>`;

    try {
      const data = await API.request('GET', '/graph/stats');
      const el = document.getElementById('graph-content');
      el.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <div style="padding:12px;background:rgba(0,180,255,0.04);border:1px solid var(--border);border-radius:var(--radius)">
            <div style="font-family:var(--font-hud);font-size:9px;color:var(--text-dim)">СУЩНОСТИ</div>
            <div style="font-family:var(--font-hud);font-size:24px;color:var(--blue)">${data.entities || 0}</div>
          </div>
          <div style="padding:12px;background:rgba(0,180,255,0.04);border:1px solid var(--border);border-radius:var(--radius)">
            <div style="font-family:var(--font-hud);font-size:9px;color:var(--text-dim)">СВЯЗИ</div>
            <div style="font-family:var(--font-hud);font-size:24px;color:var(--blue)">${data.relations || 0}</div>
          </div>
        </div>`;
    } catch (error) {
      console.error('Graph error:', error);
    }
  },

  showSettings() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div class="nav-title" style="margin-bottom:16px">НАСТРОЙКИ</div>
        <div style="max-width:400px;display:flex;flex-direction:column;gap:16px">
          <div>
            <label style="font-family:var(--font-hud);font-size:9px;color:var(--blue);display:block;margin-bottom:6px">URL СЕРВЕРА</label>
            <input type="text" id="settings-server" value="${API.getConfig().server}"
              style="width:100%;background:var(--bg-deep);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:var(--radius);font-family:var(--font-mono);font-size:12px">
          </div>
          <div>
            <label style="font-family:var(--font-hud);font-size:9px;color:var(--blue);display:block;margin-bottom:6px">КЛЮЧ ДОСТУПА</label>
            <input type="text" id="settings-key" value="${API.getConfig().key}"
              style="width:100%;background:var(--bg-deep);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:var(--radius);font-family:var(--font-mono);font-size:12px">
          </div>
          <button class="ctrl-btn" onclick="App.saveSettings()">СОХРАНИТЬ</button>
        </div>
      </div>`;
  },

  saveSettings() {
    const server = document.getElementById('settings-server')?.value;
    const key = document.getElementById('settings-key')?.value;
    
    document.getElementById('cfg-server').value = server;
    document.getElementById('cfg-key').value = key;
    
    Chat.appendSystem('Настройки сохранены');
  },

  bindEvents() {
    document.getElementById('btn-minimize')?.addEventListener('click', () => window.jarvis?.minimize());
    document.getElementById('btn-maximize')?.addEventListener('click', () => window.jarvis?.maximize());
    document.getElementById('btn-close')?.addEventListener('click', () => window.jarvis?.close());

    document.getElementById('btn-agent')?.addEventListener('click', () => Chat.toggleAgent());
    document.getElementById('btn-memory')?.addEventListener('click', () => Chat.toggleMemory());
    document.getElementById('btn-tts')?.addEventListener('click', () => Chat.toggleTTS());

    this.initDivider();
  },

  initDivider() {
    const divider = document.getElementById('divider');
    const chatPanel = document.getElementById('chat-panel');
    if (!divider || !chatPanel) return;

    let dragging = false;
    divider.addEventListener('mousedown', (e) => {
      dragging = true;
      divider.classList.add('dragging');
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const mainArea = document.getElementById('main-area');
      const rect = mainArea.getBoundingClientRect();
      const sideW = document.getElementById('side-panel').offsetWidth;
      const x = e.clientX - rect.left - sideW;
      const pct = Math.max(20, Math.min(80, (x / (rect.width - sideW)) * 100));
      chatPanel.style.width = pct + '%';
    });

    document.addEventListener('mouseup', () => {
      dragging = false;
      divider.classList.remove('dragging');
    });
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
```

- [ ] **Step 2: Commit**

```bash
git add client/js/app.js
git commit -m "feat: add main app initialization and navigation"
```

---

### Task 10: Final Testing

**Covers:** [S8]

**Files:**
- None (testing only)

- [ ] **Step 1: Install dependencies**

Run: `cd client && npm install`
Expected: Dependencies installed successfully

- [ ] **Step 2: Start Electron app**

Run: `cd client && npm start`
Expected: Electron window opens with JARVIS UI

- [ ] **Step 3: Verify all screens work**

1. Click each navigation item
2. Verify content loads in workspace panel
3. Test chat input and send button
4. Test window controls (minimize, maximize, close)

- [ ] **Step 4: Test API connection**

1. Ensure JarvisV3.1 server is running on port 8003
2. Check plugin status in side panel updates
3. Send a test message in chat

- [ ] **Step 5: Final commit**

```bash
git add client/
git commit -m "feat: complete Electron client for Jarvis V3.1"
```

---

## Summary

This plan creates a complete Electron desktop application with:
- Custom frameless window with Iron Man JARVIS styling
- 6 functional screens (Chat, Files, RAG, Memory, Graph, Settings)
- Real-time chat streaming via SSE
- API integration with JarvisV3.1 backend
- Holographic animations and visual effects
- Window controls and navigation

**Total Tasks:** 10
**Estimated Time:** 2-3 hours
