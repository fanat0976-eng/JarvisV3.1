const App = {
  currentPage: 'chat',
  pages: [
    { id: 'chat', title: 'ЧАТ' },
    { id: 'files', title: 'ФАЙЛЫ' },
    { id: 'rag', title: 'ЗНАНИЯ' },
    { id: 'memory', title: 'ПАМЯТЬ' },
    { id: 'agents', title: 'АГЕНТЫ' },
    { id: 'graph', title: 'ГРАФ' },
    { id: 'learning', title: 'ОБУЧЕНИЕ' },
    { id: 'settings', title: 'НАСТРОЙКИ' }
  ],

  init() {
    Chat.init();
    this.buildNav();
    this.bindEvents();
    this.checkHealth();
    this.checkNotifications();
    setInterval(() => this.checkHealth(), 15000);
    setInterval(() => this.checkNotifications(), 30000);
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
      case 'agents':
        this.showAgents();
        break;
      case 'graph':
        this.showGraph();
        break;
      case 'learning':
        this.showLearning();
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
        this.loadCommunityPlugins();
      }
    } catch (error) {
      document.getElementById('status-ring')?.classList.remove('active');
      document.getElementById('plugin-count').textContent = 'PLUGINS: 0/0';
    }
  },

  updatePlugins(plugins) {
    const list = document.getElementById('plugins-list');
    if (!list) return;

    const coreHtml = Object.entries(plugins).map(([name, info]) => `
      <div class="plugin-card ${info.loaded ? 'active' : ''}">
        <span class="dot"></span>
        <span class="name">${name}</span>
      </div>
    `).join('');

    list.innerHTML = `<div style="margin-bottom:4px;font-family:var(--font-hud);font-size:7px;color:var(--blue);letter-spacing:1px">CORE</div>${coreHtml}<div id="community-plugins"></div>`;
  },

  async loadCommunityPlugins() {
    const container = document.getElementById('community-plugins');
    if (!container) return;
    try {
      const data = await API.request('GET', '/plugins/community');
      const plugins = data.plugins || [];
      if (!plugins.length) {
        container.innerHTML = '';
        return;
      }
      const communityHtml = `
        <div style="margin:4px 0 2px;font-family:var(--font-hud);font-size:7px;color:var(--green);letter-spacing:1px">COMMUNITY</div>
        ${plugins.map(p => `
          <div class="plugin-card ${p.loaded ? 'active' : ''}" onclick="App.showPluginDetail('${p.name}')" title="${p.description}">
            <span class="dot"></span>
            <span class="name">${p.name}</span>
          </div>
        `).join('')}
      `;
      container.innerHTML = communityHtml;
    } catch (e) {}
  },

  async showPluginDetail(name) {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.showPage('chat')">← НАЗАД</button>
          <div class="nav-title" style="flex:1">${name.toUpperCase()}</div>
        </div>
        <div id="plugin-detail"></div>
      </div>`;
    const el = document.getElementById('plugin-detail');
    try {
      const health = await API.request('GET', `/${name}/health`);
      el.innerHTML = `
        <div class="mem-item" style="border-color:var(--green)">
          <div class="mem-item-header"><span class="mem-item-key">HEALTH</span></div>
          <div class="mem-item-value"><pre style="margin:0;font-family:var(--font-mono);font-size:11px">${JSON.stringify(health, null, 2)}</pre></div>
        </div>`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async showFiles(path) {
    const workspace = document.getElementById('workspace-panel');
    const currentPath = path || '';
    this._filesPath = currentPath;

    workspace.innerHTML = `
      <div style="padding:20px;height:100%;display:flex;flex-direction:column">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
          <div class="nav-title" style="flex:1">ФАЙЛОВАЯ СИСТЕМА</div>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.filesNewFolder()">+ ПАПКА</button>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.filesRefresh()">ОБНОВИТЬ</button>
        </div>
        <div id="files-breadcrumb" style="margin-bottom:10px;font-family:var(--font-mono);font-size:10px;color:var(--text-dim)"></div>
        <div id="files-content" style="flex:1;overflow-y:auto"></div>
      </div>`;

    await this._loadFiles(currentPath);
  },

  async _loadFiles(currentPath) {
    const el = document.getElementById('files-content');
    const bc = document.getElementById('files-breadcrumb');
    try {
      const body = currentPath ? { path: currentPath } : {};
      const data = await API.request('POST', '/files/ls', body);
      if (data.error) throw new Error(data.error);
      const items = data.items || [];

      if (currentPath) {
        const parts = currentPath.replace(/\\/g, '/').split('/');
        const folderName = parts[parts.length - 1];
        bc.innerHTML = `<span style="cursor:pointer;color:var(--blue)" onclick="App.filesGoUp()">WORKSPACE</span> / <span style="color:var(--text)">${folderName}</span>`;
      } else {
        bc.innerHTML = '<span style="color:var(--text)">WORKSPACE</span>';
      }

      if (!items.length) {
        el.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:20px;text-align:center">Папка пуста</div>';
        return;
      }

      el.innerHTML = items.map(item => `
        <div class="file-item" data-path="${item.path.replace(/\\/g, '\\\\')}" data-isdir="${item.is_dir}" data-name="${item.name}">
          <div class="file-icon">${item.is_dir ? '📁' : '📄'}</div>
          <div class="file-name">${item.name}</div>
          <div class="file-size">${item.is_dir ? '' : this._formatSize(item.size || 0)}</div>
          <div class="file-actions">
            ${item.is_dir
              ? `<button class="file-btn" title="Открыть" onclick="App.filesOpen('${item.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}')">→</button>`
              : `<button class="file-btn" title="Читать" onclick="App.filesRead('${item.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}')">👁</button>
                 <button class="file-btn" title="Открыть в OS" onclick="App.filesOpenOS('${item.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}')">↗</button>`
            }
            <button class="file-btn file-btn-danger" title="Удалить" onclick="App.filesDelete('${item.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}', '${item.name}', ${item.is_dir})">✕</button>
          </div>
        </div>
      `).join('');

      el.querySelectorAll('.file-item[data-isdir="true"]').forEach(item => {
        item.addEventListener('dblclick', () => App.filesOpen(item.dataset.path));
      });
    } catch (error) {
      el.innerHTML = `<div style="color:var(--red);font-size:12px">Ошибка: ${error.message}</div>`;
    }
  },

  filesGoUp() {
    const p = this._filesPath || '';
    if (!p) return;
    const parts = p.replace(/\\/g, '/').split('/');
    parts.pop();
    const parent = parts.join('/');
    const data = API.getConfig();
    const ws = data.server ? '' : '';
    this.showFiles(parent || '');
  },

  filesOpen(path) {
    this.showFiles(path);
  },

  async filesRead(path) {
    try {
      const data = await API.request('POST', '/files/read', { path });
      if (data.error) throw new Error(data.error);
      const content = data.text || JSON.stringify(data, null, 2);
      const workspace = document.getElementById('workspace-panel');
      const fileName = path.replace(/\\/g, '/').split('/').pop();
      workspace.innerHTML = `
        <div style="padding:20px;height:100%;display:flex;flex-direction:column">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
            <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.filesOpen('${path.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\\/g, '\\\\')}')">← НАЗАД</button>
            <div class="nav-title" style="flex:1;font-size:11px;color:var(--text)">${fileName}</div>
            <div style="font-family:var(--font-mono);font-size:9px;color:var(--text-muted)">${data.type || 'text'} | ${content.length} chars</div>
          </div>
          <div style="flex:1;overflow:auto;background:var(--bg-deep);border:1px solid var(--border);border-radius:var(--radius);padding:12px">
            <pre style="font-family:var(--font-mono);font-size:12px;color:var(--text);white-space:pre-wrap;word-break:break-all;margin:0">${this.escapeHtml(content).substring(0, 50000)}</pre>
          </div>
        </div>`;
    } catch (error) {
      alert('Ошибка чтения: ' + error.message);
    }
  },

  async filesOpenOS(path) {
    await API.request('POST', '/files/open', { path });
  },

  async filesDelete(path, name, isDir) {
    const type = isDir ? 'папку' : 'файл';
    if (!confirm(`Удалить ${type} "${name}"?`)) return;
    try {
      const body = { path, confirm: 'yes' };
      const data = await API.request('POST', '/files/rm', body);
      if (data.error) throw new Error(data.error);
      await this._loadFiles(this._filesPath);
    } catch (error) {
      alert('Ошибка удаления: ' + error.message);
    }
  },

  async filesNewFolder() {
    const name = prompt('Имя новой папки:');
    if (!name) return;
    const basePath = this._filesPath || '';
    const cfg = API.getConfig();
    const wsResp = await API.request('GET', '/files/health');
    const ws = wsResp.workspace || '';
    const newPath = basePath ? basePath + '/' + name : name;
    try {
      const data = await API.request('POST', '/files/mkdir', { path: newPath });
      if (data.error) throw new Error(data.error);
      await this._loadFiles(this._filesPath);
    } catch (error) {
      alert('Ошибка: ' + error.message);
    }
  },

  filesRefresh() {
    this._loadFiles(this._filesPath);
  },

  _formatSize(bytes) {
    if (bytes < 1024) return bytes + 'B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB';
    return (bytes / 1048576).toFixed(1) + 'MB';
  },

  async showRAG() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
          <div class="nav-title" style="flex:1">БАЗА ЗНАНИЙ</div>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.ragHealth()">СТАТУС</button>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.nomadCollections()">ZIM</button>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:16px">
          <input type="text" id="rag-query" placeholder="Поиск в базе знаний..."
            style="flex:1;background:var(--bg-deep);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:var(--radius);font-family:var(--font-mono);font-size:12px">
          <button class="ctrl-btn" onclick="App.searchRAG()">ПОИСК</button>
          <button class="ctrl-btn" onclick="App.askRAG()">СПРОСИТЬ</button>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:16px">
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.ragAddText()">+ ТЕКСТ</button>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.ragAddFile()">+ ФАЙЛ</button>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.nomadIngestDir()">+ ДИРЕКТОРИЯ</button>
        </div>
        <div id="rag-results"></div>
      </div>`;
  },

  async ragHealth() {
    try {
      const data = await API.request('GET', '/rag/health');
      const el = document.getElementById('rag-results');
      el.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="mem-stat"><div class="mem-stat-label">СТАТУС</div><div class="mem-stat-value" style="font-size:14px">${data.status || 'N/A'}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">ДОКУМЕНТОВ</div><div class="mem-stat-value">${data.documents || 0}</div></div>
        </div>`;
    } catch (e) {
      document.getElementById('rag-results').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async searchRAG() {
    const query = document.getElementById('rag-query')?.value;
    if (!query) return;
    try {
      const data = await API.request('POST', '/rag/search', { query, n_results: 5 });
      const el = document.getElementById('rag-results');
      const results = data.results || [];
      el.innerHTML = results.length ? results.map(r => `
        <div class="mem-item">
          <div class="mem-item-header">
            <span class="mem-item-key">${r.metadata?.title || r.id || 'Document'}</span>
            <span class="mem-item-meta">dist: ${r.distance?.toFixed(4) || 'N/A'}</span>
          </div>
          <div class="mem-item-value">${(r.text || '').substring(0, 500)}</div>
        </div>
      `).join('') : '<div class="mem-empty">Ничего не найдено</div>';
    } catch (e) {
      document.getElementById('rag-results').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async askRAG() {
    const query = document.getElementById('rag-query')?.value;
    if (!query) return;
    try {
      const data = await API.request('POST', '/rag/ask', { question: query, n_context: 3 });
      const el = document.getElementById('rag-results');
      const ctx = data.context || '';
      const sources = data.sources || [];
      el.innerHTML = `
        <div class="mem-item" style="border-color:var(--blue)">
          <div class="mem-item-header"><span class="mem-item-key">КОНТЕКСТ</span></div>
          <div class="mem-item-value">${ctx.substring(0, 2000) || 'Нет контекста'}</div>
        </div>
        ${sources.map(s => `
          <div class="mem-item">
            <div class="mem-item-header">
              <span class="mem-item-key">${s.metadata?.title || s.id}</span>
              <span class="mem-item-meta">dist: ${s.distance?.toFixed(4) || 'N/A'}</span>
            </div>
            <div class="mem-item-value" style="font-size:11px;color:var(--text-dim)">${(s.preview || '').substring(0, 200)}</div>
          </div>
        `).join('')}`;
    } catch (e) {
      document.getElementById('rag-results').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async ragAddText() {
    const text = prompt('Текст для добавления в базу знаний:', '');
    if (!text) return;
    const source = prompt('Источник (test, docs, ...):', 'manual');
    try {
      await API.request('POST', '/rag/add', { text, metadata: { source } });
      alert('Добавлено!');
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  },

  async ragAddFile() {
    const path = prompt('Путь к файлу в workspace:', '');
    if (!path) return;
    try {
      const data = await API.request('POST', '/nomad/ingest/file', { path });
      alert(data.status === 'ok' ? `Индексировано: ${data.chunks_added || 0} чанков` : 'Ошибка');
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  },

  async nomadCollections() {
    const el = document.getElementById('rag-results');
    el.innerHTML = '<div class="mem-empty">Загрузка...</div>';
    try {
      const data = await API.request('GET', '/nomad/zim/collections');
      const cats = data.collections || [];
      el.innerHTML = cats.length ? cats.map(cat => `
        <div class="mem-item">
          <div class="mem-item-header">
            <span class="mem-item-key">${cat.name || cat.slug || 'Collection'}</span>
            <span class="mem-item-meta">${(cat.zims || []).length} ZIM файлов</span>
          </div>
          <div class="mem-item-value">${cat.description || ''}</div>
          ${(cat.zims || []).slice(0, 3).map(z => `
            <div style="margin-top:4px;font-family:var(--font-mono);font-size:10px;color:var(--text-dim)">
              ${z.title || z.url || z.filename || ''}
            </div>
          `).join('')}
        </div>
      `).join('') : '<div class="mem-empty">Нет коллекций</div>';
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async nomadIngestDir() {
    const path = prompt('Путь к директории:', '');
    if (!path) return;
    const exts = prompt('Расширения (через запятую):', '.txt,.md,.py,.json');
    if (!exts) return;
    const extensions = exts.split(',').map(e => e.trim());
    const el = document.getElementById('rag-results');
    el.innerHTML = '<div class="mem-empty">Индексирование...</div>';
    try {
      const data = await API.request('POST', '/nomad/ingest/directory', { path, extensions });
      const results = data.results || [];
      el.innerHTML = `
        <div class="mem-item" style="border-color:var(--green)">
          <div class="mem-item-header">
            <span class="mem-item-key" style="color:var(--green)">ГОТОВО</span>
            <span class="mem-item-meta">${data.processed || 0} файлов</span>
          </div>
        </div>
        ${results.slice(0, 20).map(r => `
          <div class="mem-item">
            <div class="mem-item-header">
              <span class="mem-item-key" style="font-size:8px">${r.file || ''}</span>
              <span class="mem-item-meta">${r.error || 'ok'}</span>
            </div>
          </div>
        `).join('')}`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async showMemory() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
          <div class="nav-title" style="flex:1">ПАМЯТЬ</div>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.loadMemoryInsights()">ИНСАЙТЫ</button>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:16px">
          <button class="ctrl-btn" onclick="App.loadSessions()">СЕССИИ</button>
          <button class="ctrl-btn" onclick="App.loadFacts()">ФАКТЫ</button>
          <button class="ctrl-btn" onclick="App.loadNotes()">ЗАМЕТКИ</button>
          <button class="ctrl-btn" onclick="App.loadPatterns()">ПАТТЕРНЫ</button>
        </div>
        <div id="memory-content"></div>
      </div>`;
    this.loadFacts();
  },

  async loadSessions() {
    try {
      const data = await API.request('GET', '/memory_v2/sessions');
      const el = document.getElementById('memory-content');
      const sessions = data.sessions || [];
      el.innerHTML = sessions.length ? sessions.map(s => `
        <div class="mem-item">
          <div class="mem-item-header">
            <span class="mem-item-key">${s.id.substring(0, 25)}</span>
            <span class="mem-item-meta">${s.message_count || 0} сообщений</span>
          </div>
          ${s.title ? `<div class="mem-item-value">${s.title}</div>` : ''}
          <div class="mem-item-time">${s.started_at ? new Date(s.started_at).toLocaleString('ru-RU') : ''}</div>
        </div>
      `).join('') : '<div class="mem-empty">Нет сессий</div>';
    } catch (e) {
      document.getElementById('memory-content').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async loadFacts() {
    try {
      const data = await API.request('POST', '/memory_v2/facts/get', {});
      const el = document.getElementById('memory-content');
      const facts = data.facts || [];
      el.innerHTML = `
        <div style="margin-bottom:10px">
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.addFact()">+ ФАКТ</button>
        </div>
        ${facts.length ? facts.map(f => `
          <div class="mem-item">
            <div class="mem-item-header">
              <span class="mem-item-key">${f.entity} → ${f.key}</span>
              <button class="mem-delete" onclick="App.deleteFact('${f.entity}', '${f.key}')">✕</button>
            </div>
            <div class="mem-item-value">${f.value}</div>
          </div>
        `).join('') : '<div class="mem-empty">Нет фактов</div>'}`;
    } catch (e) {
      document.getElementById('memory-content').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async addFact() {
    const entity = prompt('Сущность (user, project, ...):', 'user');
    if (!entity) return;
    const key = prompt('Ключ:', '');
    if (!key) return;
    const value = prompt('Значение:', '');
    if (!value) return;
    await API.request('POST', '/memory_v2/facts', { entity, key, value });
    this.loadFacts();
  },

  async deleteFact(entity, key) {
    if (!confirm(`Удалить факт "${entity} → ${key}"?`)) return;
    await API.request('POST', '/memory_v2/facts/delete', { entity, key });
    this.loadFacts();
  },

  async loadNotes() {
    try {
      const data = await API.request('GET', '/memory_v2/notes');
      const el = document.getElementById('memory-content');
      const notes = data.notes || [];
      el.innerHTML = `
        <div style="margin-bottom:10px">
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.addNote()">+ ЗАМЕТКА</button>
        </div>
        ${notes.length ? notes.map(n => `
          <div class="mem-item">
            <div class="mem-item-header">
              <span class="mem-item-key">${n.key}</span>
              <button class="mem-delete" onclick="App.deleteNote('${n.key}')">✕</button>
            </div>
            <div class="mem-item-value">${(n.content || '').substring(0, 300)}</div>
            <div class="mem-item-time">${n.updated_at ? new Date(n.updated_at).toLocaleString('ru-RU') : ''}</div>
          </div>
        `).join('') : '<div class="mem-empty">Нет заметок</div>'}`;
    } catch (e) {
      document.getElementById('memory-content').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async addNote() {
    const key = prompt('Имя заметки:', '');
    if (!key) return;
    const content = prompt('Содержимое:', '');
    if (!content) return;
    await API.request('POST', '/memory_v2/note/set', { key, content });
    this.loadNotes();
  },

  async deleteNote(key) {
    if (!confirm(`Удалить заметку "${key}"?`)) return;
    await API.request('POST', '/memory_v2/note/set', { key, content: '' });
    this.loadNotes();
  },

  async loadPatterns() {
    try {
      const data = await API.request('GET', '/memory_v2/patterns/top');
      const el = document.getElementById('memory-content');
      const kw = data.keywords || [];
      const cmd = data.commands || [];
      el.innerHTML = `
        <div style="margin-bottom:16px">
          <div style="font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px;margin-bottom:8px">КЛЮЧЕВЫЕ СЛОВА</div>
          ${kw.length ? kw.map(p => `<div class="mem-item"><div class="mem-item-header"><span class="mem-item-key">${p.key}</span><span class="mem-item-meta">${p.count}x</span></div></div>`).join('') : '<div class="mem-empty">Нет данных</div>'}
        </div>
        <div>
          <div style="font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px;margin-bottom:8px">КОМАНДЫ</div>
          ${cmd.length ? cmd.map(p => `<div class="mem-item"><div class="mem-item-header"><span class="mem-item-key">${p.key}</span><span class="mem-item-meta">${p.count}x</span></div></div>`).join('') : '<div class="mem-empty">Нет данных</div>'}
        </div>`;
    } catch (e) {
      document.getElementById('memory-content').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async loadMemoryInsights() {
    try {
      const data = await API.request('GET', '/memory_v2/insights');
      const el = document.getElementById('memory-content');
      el.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
          <div class="mem-stat"><div class="mem-stat-label">СООБЩЕНИЙ</div><div class="mem-stat-value">${data.total_messages || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">СЕССИЙ</div><div class="mem-stat-value">${data.total_sessions || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">ФАКТОВ</div><div class="mem-stat-value">${data.total_facts || 0}</div></div>
        </div>
        <div style="margin-bottom:12px">
          <div style="font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px;margin-bottom:8px">АКТИВНЫХ ДНЕЙ</div>
          <div style="font-family:var(--font-hud);font-size:20px;color:var(--text)">${data.active_days || 0}</div>
        </div>
        ${(data.insights || []).map(i => `<div class="mem-item"><div class="mem-item-value">${i}</div></div>`).join('')}`;
    } catch (e) {
      document.getElementById('memory-content').innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async showAgents() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
          <div class="nav-title" style="flex:1">АГЕНТЫ</div>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.agentSpawn()">+ ЗАДАЧА</button>
        </div>
        <div id="agents-list"></div>
      </div>`;
    this.loadAgents();
  },

  async loadAgents() {
    const el = document.getElementById('agents-list');
    try {
      const data = await API.request('GET', '/agents/list');
      const agents = data.agents || [];
      el.innerHTML = agents.length ? agents.map(a => `
        <div class="mem-item">
          <div class="mem-item-header">
            <span class="mem-item-key">${a.name}</span>
            <span class="mem-item-meta">${a.model || ''}</span>
          </div>
          <div class="mem-item-value">${a.description || ''}</div>
          <div style="margin-top:6px;display:flex;gap:4px">
            <button class="file-btn" title="Запустить" onclick="App.agentRun('${a.name}')">▶</button>
          </div>
        </div>
      `).join('') : '<div class="mem-empty">Нет агентов</div>';
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async agentSpawn() {
    const task = prompt('Задача для агента:', '');
    if (!task) return;
    const el = document.getElementById('agents-list');
    el.innerHTML = '<div class="mem-empty">Выполнение...</div>';
    try {
      const data = await API.request('POST', '/agents/spawn', { task });
      if (data.error) throw new Error(data.error);
      el.innerHTML = `
        <div class="mem-item" style="border-color:var(--green)">
          <div class="mem-item-header">
            <span class="mem-item-key" style="color:var(--green)">РЕЗУЛЬТАТ</span>
            <span class="mem-item-meta">${data.agent || ''} | ${data.model || ''} | ${data.iterations || 0} итераций</span>
          </div>
          <div class="mem-item-value">${(data.reply || '').substring(0, 2000)}</div>
          ${data.tool_results?.length ? `<div style="margin-top:6px;font-family:var(--font-mono);font-size:10px;color:var(--text-dim)">Tools: ${data.tool_results.map(t => t.tool).join(', ')}</div>` : ''}
        </div>`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty" style="color:var(--red)">Ошибка: ${e.message}</div>`;
    }
  },

  async agentRun(name) {
    const task = prompt(`Задача для агента "${name}":`, '');
    if (!task) return;
    const el = document.getElementById('agents-list');
    el.innerHTML = '<div class="mem-empty">Выполнение...</div>';
    try {
      const data = await API.request('POST', '/agents/spawn', { agent: name, task });
      if (data.error) throw new Error(data.error);
      el.innerHTML = `
        <div class="mem-item" style="border-color:var(--green)">
          <div class="mem-item-header">
            <span class="mem-item-key" style="color:var(--green)">РЕЗУЛЬТАТ</span>
            <span class="mem-item-meta">${data.agent || name} | ${data.iterations || 0} итераций</span>
          </div>
          <div class="mem-item-value">${(data.reply || '').substring(0, 2000)}</div>
        </div>`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty" style="color:var(--red)">Ошибка: ${e.message}</div>`;
    }
  },

  async showGraph() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
          <div class="nav-title" style="flex:1">ГРАФ ЗНАНИЙ</div>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.graphAddEntity()">+ СУЩНОСТЬ</button>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.graphAddRelation()">+ СВЯЗЬ</button>
          <button class="ctrl-btn" style="width:auto;padding:4px 10px" onclick="App.graphRefresh()">ОБНОВИТЬ</button>
        </div>
        <div id="graph-content"></div>
      </div>`;
    this.loadGraph();
  },

  async loadGraph() {
    const el = document.getElementById('graph-content');
    try {
      const data = await API.request('GET', '/graph/stats');
      el.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin-bottom:16px">
          <div class="mem-stat"><div class="mem-stat-label">СУЩНОСТИ</div><div class="mem-stat-value">${data.entities || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">СВЯЗИ</div><div class="mem-stat-value">${data.relations || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">NODES (NX)</div><div class="mem-stat-value">${data.networkx_nodes || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">EDGES (NX)</div><div class="mem-stat-value">${data.networkx_edges || 0}</div></div>
        </div>
        ${data.entity_types ? `
          <div style="margin-bottom:12px">
            <div style="font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px;margin-bottom:8px">ТИПЫ СУЩНОСТЕЙ</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              ${Object.entries(data.entity_types).map(([k, v]) => `<span class="mem-item" style="padding:4px 10px;display:inline-block"><span class="mem-item-key">${k}</span> <span class="mem-item-meta">${v}</span></span>`).join('')}
            </div>
          </div>` : ''}
        ${data.relation_types ? `
          <div>
            <div style="font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px;margin-bottom:8px">ТИПЫ СВЯЗЕЙ</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              ${Object.entries(data.relation_types).map(([k, v]) => `<span class="mem-item" style="padding:4px 10px;display:inline-block"><span class="mem-item-key">${k}</span> <span class="mem-item-meta">${v}</span></span>`).join('')}
            </div>
          </div>` : ''}`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async graphAddEntity() {
    const id = prompt('ID сущности:', '');
    if (!id) return;
    const type = prompt('Тип:', 'concept');
    if (!type) return;
    const name = prompt('Имя:', id);
    if (!name) return;
    await API.request('POST', '/graph/entity', { id, type, name });
    this.loadGraph();
  },

  async graphAddRelation() {
    const source = prompt('Источник (ID):', '');
    if (!source) return;
    const target = prompt('Цель (ID):', '');
    if (!target) return;
    const relation = prompt('Тип связи:', 'related_to');
    if (!relation) return;
    await API.request('POST', '/graph/relation', { source, target, relation });
    this.loadGraph();
  },

  async graphRefresh() {
    await API.request('POST', '/graph/refresh', {});
    this.loadGraph();
  },

  async showLearning() {
    const workspace = document.getElementById('workspace-panel');
    workspace.innerHTML = `
      <div style="padding:20px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
          <div class="nav-title" style="flex:1">ОБУЧЕНИЕ</div>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:16px">
          <button class="ctrl-btn" onclick="App.loadLearnedCommands()">КОМАНДЫ</button>
          <button class="ctrl-btn" onclick="App.loadLearnSuggestions()">ПРЕДЛОЖЕНИЯ</button>
          <button class="ctrl-btn" onclick="App.loadLearnScores()">МОДЕЛИ</button>
          <button class="ctrl-btn" onclick="App.loadLearnStats()">СТАТИСТИКА</button>
        </div>
        <div id="learning-content"></div>
      </div>`;
    this.loadLearnedCommands();
  },

  async loadLearnedCommands() {
    const el = document.getElementById('learning-content');
    try {
      const data = await API.request('GET', '/learning/commands');
      const cmds = data.commands || [];
      el.innerHTML = `
        <div style="margin-bottom:10px;font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px">ИЗУЧЕННЫЕ КОМАНДЫ</div>
        ${cmds.length ? cmds.map(c => `
          <div class="mem-item">
            <div class="mem-item-header">
              <span class="mem-item-key">${c.phrase || c.pattern_key || ''}</span>
              <span class="mem-item-meta">${c.count || 0}x</span>
            </div>
            <div class="mem-item-value" style="color:var(--green)">${c.command || ''}</div>
          </div>
        `).join('') : '<div class="mem-empty">Нет изученных команд</div>'}`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async loadLearnSuggestions() {
    const el = document.getElementById('learning-content');
    try {
      const data = await API.request('GET', '/learning/suggestions');
      const sugs = data.suggestions || [];
      el.innerHTML = `
        <div style="margin-bottom:10px;font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px">ПРЕДЛОЖЕНИЯ КОМАНД</div>
        ${sugs.length ? sugs.map(s => `
          <div class="mem-item">
            <div class="mem-item-header">
              <span class="mem-item-key">${s.phrase || ''}</span>
              <span class="mem-item-meta">${s.count || 0} повторений</span>
            </div>
            <div class="mem-item-value">${s.suggested_command || s.command || ''}</div>
          </div>
        `).join('') : '<div class="mem-empty">Нет предложений</div>'}`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async loadLearnScores() {
    const el = document.getElementById('learning-content');
    try {
      const data = await API.request('GET', '/learning/scores');
      const scores = data.scores || [];
      el.innerHTML = `
        <div style="margin-bottom:10px;font-family:var(--font-hud);font-size:9px;color:var(--blue);letter-spacing:2px">ПРОИЗВОДИТЕЛЬНОСТЬ МОДЕЛЕЙ</div>
        ${scores.length ? scores.map(s => `
          <div class="mem-item">
            <div class="mem-item-header">
              <span class="mem-item-key">${s.model || ''}</span>
              <span class="mem-item-meta">${s.task_type || ''}</span>
            </div>
            <div class="mem-item-value">успех: ${s.successes || 0} | ошибка: ${s.failures || 0}</div>
          </div>
        `).join('') : '<div class="mem-empty">Нет данных</div>'}`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async loadLearnStats() {
    const el = document.getElementById('learning-content');
    try {
      const data = await API.request('GET', '/learning/stats');
      el.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
          <div class="mem-stat"><div class="mem-stat-label">КОМАНДЫ</div><div class="mem-stat-value">${data.learned_commands || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">МОДЕЛИ</div><div class="mem-stat-value">${data.model_scores || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">ИЗВЛЕЧЕНИЯ</div><div class="mem-stat-value">${data.extractions || 0}</div></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="mem-stat"><div class="mem-stat-label">АВТО ФАКТЫ</div><div class="mem-stat-value">${data.facts_auto || 0}</div></div>
          <div class="mem-stat"><div class="mem-stat-label">РУЧНЫЕ ФАКТЫ</div><div class="mem-stat-value">${data.facts_manual || 0}</div></div>
        </div>`;
    } catch (e) {
      el.innerHTML = `<div class="mem-empty">Ошибка: ${e.message}</div>`;
    }
  },

  async showSettings() {
    const workspace = document.getElementById('workspace-panel');
    let voicesHtml = '';
    try {
      const vData = await API.request('GET', '/tts_bridge/voices');
      const voices = vData.voices || [];
      voicesHtml = voices.map(v => `<option value="${v.id}">${v.name} (${v.engine})</option>`).join('');
    } catch (e) {}

    let sttHtml = '';
    try {
      const sData = await API.request('GET', '/stt/health');
      sttHtml = `<div class="mem-stat"><div class="mem-stat-label">STT</div><div class="mem-stat-value" style="font-size:12px">${sData.model || 'N/A'} | ${sData.loaded ? 'загружена' : 'не загружена'}</div></div>`;
    } catch (e) {}

    let brainHtml = '';
    try {
      const bData = await API.request('GET', '/brain/health');
      const models = bData.models || [];
      brainHtml = `<div class="mem-stat"><div class="mem-stat-label">OLLAMA</div><div class="mem-stat-value" style="font-size:12px">${bData.ollama ? models.join(', ') : 'недоступен'}</div></div>`;
    } catch (e) {}

    let learnHtml = '';
    try {
      const lData = await API.request('GET', '/learning/stats');
      learnHtml = `
        <div class="mem-stat"><div class="mem-stat-label">ОБУЧЕНИЕ</div><div class="mem-stat-value" style="font-size:11px">
          команд: ${lData.learned_commands || 0} | фактов: ${lData.facts_auto || 0}+${lData.facts_manual || 0}
        </div></div>`;
    } catch (e) {}

    let watcherHtml = '';
    try {
      const wData = await API.request('GET', '/watchers/status');
      const disk = wData.disk || {};
      watcherHtml = `
        <div class="mem-stat"><div class="mem-stat-label">ДИСК</div><div class="mem-stat-value" style="font-size:12px">${disk.free_gb || 0}GB free / ${disk.total_gb || 0}GB (${disk.used_pct || 0}% used)</div></div>`;
    } catch (e) {}

    let brainStatsHtml = '';
    try {
      const bsData = await API.request('GET', '/brain/stats');
      brainStatsHtml = `
        <div class="mem-stat"><div class="mem-stat-label">BRAIN</div><div class="mem-stat-value" style="font-size:11px">
          сессий: ${bsData.sessions || 0} | сообщений: ${bsData.messages || 0} | фактов: ${bsData.facts || 0} | паттернов: ${bsData.patterns || 0}
        </div></div>`;
    } catch (e) {}

    let ragStatsHtml = '';
    try {
      const rsData = await API.request('GET', '/rag/health');
      ragStatsHtml = `
        <div class="mem-stat"><div class="mem-stat-label">RAG</div><div class="mem-stat-value" style="font-size:12px">${rsData.documents || 0} документов</div></div>`;
    } catch (e) {}

    workspace.innerHTML = `
      <div style="padding:20px">
        <div class="nav-title" style="margin-bottom:16px">НАСТРОЙКИ</div>
        <div style="max-width:500px;display:flex;flex-direction:column;gap:16px">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            ${sttHtml}
            ${brainHtml}
            ${brainStatsHtml}
            ${ragStatsHtml}
            ${learnHtml}
            ${watcherHtml}
          </div>
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
          <div>
            <label style="font-family:var(--font-hud);font-size:9px;color:var(--blue);display:block;margin-bottom:6px">ГОЛОС TTS</label>
            <select id="settings-tts-voice" style="width:100%;background:var(--bg-deep);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:var(--radius);font-family:var(--font-mono);font-size:12px">
              ${voicesHtml}
            </select>
          </div>
          <button class="ctrl-btn" onclick="App.saveSettings()">СОХРАНИТЬ</button>
        </div>
      </div>`;
  },

  saveSettings() {
    const server = document.getElementById('settings-server')?.value;
    const key = document.getElementById('settings-key')?.value;
    const voice = document.getElementById('settings-tts-voice')?.value;

    document.getElementById('cfg-server').value = server;
    document.getElementById('cfg-key').value = key;
    if (voice) Chat.ttsVoice = voice;

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

    document.addEventListener('click', (e) => {
      if (this._notifOpen && !e.target.closest('.notif-panel') && !e.target.closest('.notif-bell')) {
        this._notifOpen = false;
        const panel = document.getElementById('notif-panel');
        if (panel) panel.style.display = 'none';
      }
    });
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
  },

  _notifOpen: false,

  toggleNotifications() {
    this._notifOpen = !this._notifOpen;
    const panel = document.getElementById('notif-panel');
    if (panel) {
      panel.style.display = this._notifOpen ? 'flex' : 'none';
      if (this._notifOpen) this.loadNotifications();
    }
  },

  async checkNotifications() {
    try {
      const data = await API.request('GET', '/notifications/unread');
      const count = data.count || 0;
      const badge = document.getElementById('notif-badge');
      if (badge) {
        badge.style.display = count > 0 ? 'flex' : 'none';
        badge.textContent = count;
      }
    } catch (e) {}
  },

  async loadNotifications() {
    const el = document.getElementById('notif-list');
    if (!el) return;
    try {
      const data = await API.request('GET', '/notifications/list?limit=20');
      const items = data.notifications || [];
      if (!items.length) {
        el.innerHTML = '<div class="notif-empty">Нет уведомлений</div>';
        return;
      }
      el.innerHTML = items.map(n => `
        <div class="notif-item">
          <div class="notif-item-title">${n.title || 'Уведомление'}</div>
          <div class="notif-item-body">${n.body || ''}</div>
          <div class="notif-item-time">${n.created_at ? new Date(n.created_at).toLocaleString('ru-RU') : ''}</div>
        </div>
      `).join('');
      await API.request('POST', '/notifications/read', {});
      this.checkNotifications();
    } catch (e) {
      el.innerHTML = '<div class="notif-empty">Ошибка загрузки</div>';
    }
  },

  async clearNotifications() {
    await API.request('POST', '/notifications/clear', {});
    const el = document.getElementById('notif-list');
    if (el) el.innerHTML = '<div class="notif-empty">Нет уведомлений</div>';
    this.checkNotifications();
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
