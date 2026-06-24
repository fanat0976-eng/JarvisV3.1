const API = {
  getConfig() {
    return {
      server: document.getElementById('cfg-server')?.value?.trim() || 'http://127.0.0.1:8003',
      key: document.getElementById('cfg-key')?.value?.trim() || 'jarvis-v3.1'
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
