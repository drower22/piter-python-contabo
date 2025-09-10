(() => {
  const API_BASE = (window.API_BASE || 'https://api.pitzei.com.br').replace(/\/$/, '');
  const logEl = document.getElementById('log');
  const healthBtn = document.getElementById('btnHealth');
  const healthResult = document.getElementById('healthResult');
  const sendBtn = document.getElementById('btnSendTemplate');
  const clearBtn = document.getElementById('btnClearLog');

  const label = document.getElementById('apiBaseLabel');
  if (label) label.textContent = API_BASE;

  function log(...args) {
    const line = args.map(v => typeof v === 'string' ? v : JSON.stringify(v, null, 2)).join(' ');
    logEl.textContent += `\n${line}`;
    logEl.scrollTop = logEl.scrollHeight;
  }

  async function checkHealth() {
    try {
      const resp = await fetch(`${API_BASE}/health`);
      const data = await resp.json();
      healthResult.textContent = resp.ok ? 'OK' : `ERR ${resp.status}`;
      healthResult.className = 'badge ' + (resp.ok ? 'ok' : 'err');
      log('[health]', data);
    } catch (e) {
      healthResult.textContent = 'ERR';
      healthResult.className = 'badge err';
      log('[health][error]', e.message || e);
    }
  }

  async function sendTemplate() {
    const to = document.getElementById('to').value.trim();
    const template = document.getElementById('template').value.trim();
    const lang = document.getElementById('lang').value.trim() || 'pt_BR';
    const varsRaw = document.getElementById('vars').value.trim();
    const variables = varsRaw ? varsRaw.split(',').map(s => s.trim()).filter(Boolean) : [];

    if (!to || !template) {
      log('[send-template][warn] preencha To e Template');
      return;
    }

    try {
      const resp = await fetch(`${API_BASE}/_webhooks/whatsapp/send-template`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          // 'x-admin-token': 'SEU_TOKEN', // opcional: defina se exigido no backend
        },
        body: JSON.stringify({
          to,
          template_name: template,
          lang_code: lang,
          variables
        })
      });
      const data = await resp.json().catch(() => ({}));
      log('[send-template]', resp.status, data);
    } catch (e) {
      log('[send-template][error]', e.message || e);
    }
  }

  if (healthBtn) healthBtn.addEventListener('click', checkHealth);
  if (sendBtn) sendBtn.addEventListener('click', sendTemplate);
  if (clearBtn) clearBtn.addEventListener('click', () => (logEl.textContent = ''));
})();
