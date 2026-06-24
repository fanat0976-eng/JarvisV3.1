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
    this.micBtn = document.getElementById('btn-mic');

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
    this.micBtn?.addEventListener('click', () => this.toggleMic());
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

      const body = {
        messages: this.history,
        use_memory: this.memoryEnabled
      };

      if (this.agentMode) {
        think.querySelector('span').textContent = 'АГЕНТ РАБОТАЕТ';
        body.max_iterations = 5;
        const data = await API.request('POST', '/brain/agent', body);
        think.remove();
        if (data.error) throw new Error(data.error);
        const fullText = data.reply || '';
        let info = '';
        if (data.tool_calls > 0) {
          const tools = (data.tool_results || []).map(t => t.tool).join(', ');
          info = ` [${data.model}] tools:${tools} iter:${data.iterations}`;
        }
        bodyEl.innerHTML = this.renderMD(fullText + info);
        this.history.push({ role: 'assistant', content: fullText });
        this.scrollToBottom();
      } else {
        const endpoint = '/brain/chat/stream';
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
      }
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

    if (role === 'ai') {
      const ttsBtn = document.createElement('button');
      ttsBtn.className = 'tts-play-btn';
      ttsBtn.innerHTML = '&#9654;';
      ttsBtn.title = 'Озвучить';
      ttsBtn.addEventListener('click', () => this.speakMessage(body.textContent, ttsBtn));
      wrapper.appendChild(ttsBtn);
    }

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
  },

  async webSearch() {
    const query = this.input.value.trim();
    if (!query) {
      this.appendSystem('Введите запрос для поиска');
      return;
    }
    this.setStreaming(true);
    this.appendMessage('user', '🔍 ' + query);
    const aiEl = this.appendMessage('ai', '');
    const bodyEl = aiEl.querySelector('.msg-body');
    bodyEl.innerHTML = '<span style="color:var(--text-muted)">Поиск в интернете...</span>';

    try {
      const data = await API.request('POST', '/web/search', { query, max_results: 5 });
      const results = data.results || [];
      if (!results.length) {
        bodyEl.innerHTML = '<span style="color:var(--text-muted)">Ничего не найдено</span>';
      } else {
        bodyEl.innerHTML = results.map((r, i) => `
          <div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--border)">
            <div style="font-family:var(--font-hud);font-size:10px;color:var(--blue)">${i + 1}. ${r.title || 'Без заголовка'}</div>
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--text);margin-top:4px">${(r.body || '').substring(0, 200)}</div>
            <div style="font-family:var(--font-mono);font-size:9px;color:var(--text-muted);margin-top:4px">${r.url || ''}</div>
          </div>
        `).join('');
      }
      this.history.push({ role: 'assistant', content: results.map(r => `${r.title}: ${r.body}`).join('\n') });
    } catch (e) {
      bodyEl.innerHTML = `<span style="color:var(--red)">Ошибка: ${e.message}</span>`;
    } finally {
      this.setStreaming(false);
      this.scrollToBottom();
    }
  },

  async speakMessage(text, btn) {
    if (btn.classList.contains('loading')) return;
    btn.classList.add('loading');
    btn.innerHTML = '&#8987;';

    try {
      const voice = this.ttsVoice || 'dmitry';
      const data = await API.request('POST', '/tts_bridge/speak', { text: text.slice(0, 2000), voice });
      if (data.error) throw new Error(data.error);

      const cfg = API.getConfig();
      const audio = new Audio(`${cfg.server}/tts_bridge/audio/${data.filename}`);
      audio.onended = () => {
        btn.classList.remove('loading', 'playing');
        btn.innerHTML = '&#9654;';
      };
      audio.onerror = () => {
        btn.classList.remove('loading', 'playing');
        btn.innerHTML = '&#9654;';
      };
      btn.classList.remove('loading');
      btn.classList.add('playing');
      btn.innerHTML = '&#9632;';
      audio.play();
    } catch (e) {
      btn.classList.remove('loading');
      btn.innerHTML = '&#9654;';
      this.appendSystem('ОШИБКА ОЗВУЧКИ: ' + e.message);
    }
  },

  toggleMic() {
    if (this._mediaRecorder && this._mediaRecorder.state === 'recording') {
      this.stopMic();
    } else {
      this.startMic();
    }
  },

  async startMic() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this._micStream = stream;
      const chunks = [];
      this._mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      this._mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
      this._mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        this.micBtn.classList.remove('recording');
        this.micBtn.textContent = '🎤';
        if (chunks.length === 0) return;
        const blob = new Blob(chunks, { type: 'audio/webm' });
        await this._sendToSTT(blob);
      };
      this._mediaRecorder.start();
      this.micBtn.classList.add('recording');
      this.micBtn.textContent = '⏹';
      this.appendSystem('ЗАПИСЬ ГОЛОСА...');
    } catch (e) {
      this.appendSystem('ОШИБКА МИКРОФОНА: ' + e.message);
    }
  },

  stopMic() {
    if (this._mediaRecorder && this._mediaRecorder.state === 'recording') {
      this._mediaRecorder.stop();
    }
  },

  async _sendToSTT(blob) {
    this.appendSystem('РАСПОЗНАВАНИЕ РЕЧИ...');
    try {
      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        const data = await API.request('POST', '/stt/transcribe/buffer', { audio: base64 });
        if (data.error) {
          this.appendSystem('ОШИБКА STT: ' + data.error);
          return;
        }
        const text = data.text || '';
        if (text.trim()) {
          this.input.value = text;
          this.input.style.height = 'auto';
          this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
          this.appendSystem('РАСПОЗНАНО: ' + text.substring(0, 100));
        } else {
          this.appendSystem('НИЧЕГО НЕ РАСПОЗНАНО');
        }
      };
      reader.readAsDataURL(blob);
    } catch (e) {
      this.appendSystem('ОШИБКА STT: ' + e.message);
    }
  }
};
