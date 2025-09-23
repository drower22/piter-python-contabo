async function loadLocalCatalog() {
  try {
    const resp = await fetch(`${API_BASE}/_webhooks/whatsapp/_admin/local/templates`);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${JSON.stringify(data)}`);
    const items = (data.items||[]);
    if (localSelect) {
      localSelect.innerHTML = '<option value="">Selecione um item</option>' +
        items.map(x => {
          const tname = x.template_name;
          const lang = x.lang_code || 'pt_BR';
          return `<option value="${tname}::${lang}">${x.title || tname} (${lang})</option>`;
        }).join('');
    }
    log('[local-catalog]', resp.status, items.length);
  } catch (e) {
    log('[local-catalog][error]', e.message || e);
  }
}

async function sendLocalSelected() {
  const to = (toTemplateEl?.value || '').trim();
  if (!to) return log('[local-send][warn] preencha To');
  const val = localSelect?.value || '';
  if (!val) return log('[local-send][warn] selecione um item');
  const [templateName, langCode] = val.split('::');
  try {
    const resp = await fetch(`${API_BASE}/_webhooks/whatsapp/send-template`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ to, template_name: templateName, lang_code: langCode || 'pt_BR', variables: [] })
    });
    const data = await resp.json().catch(() => ({}));
    log('[local-send]', resp.status, data);
  } catch (e) {
    log('[local-send][error]', e.message || e);
  }
}
// Module script
const API_BASE = (window.API_BASE || 'https://api.pitzei.com.br').replace(/\/$/, '');
const logEl = document.getElementById('log');
const healthBtn = document.getElementById('btnHealth');
const healthResult = document.getElementById('healthResult');
const sendBtn = document.getElementById('btnSendTemplate');
const clearBtn = document.getElementById('btnClearLog');
const btnLoadMeta = document.getElementById('btnLoadMeta');
const metaTemplatesEl = document.getElementById('metaTemplates');
const btnLoadMetaSelect = document.getElementById('btnLoadMetaSelect');
const templateSelect = document.getElementById('templateSelect');
const localSelect = document.getElementById('localTemplateSelect');
const btnLoadLocalSelect = document.getElementById('btnLoadLocalSelect');
const btnSendLocal = document.getElementById('btnSendLocal');

const label = document.getElementById('apiBaseLabel');
if (label) label.textContent = API_BASE;
// Inputs
const toTemplateEl = document.getElementById('to');

// Novo botão de copiar
const copyBtn = document.getElementById('copyLog');
if (copyBtn) {
  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(logEl.textContent)
      .then(() => {
        copyBtn.textContent = 'Copiado!';
        setTimeout(() => copyBtn.textContent = 'Copiar Log', 2000);
      })
      .catch(err => console.error('Failed to copy:', err));
  });
}

// ===============
// Templates: Utils
// ===============
function renderTemplatesList(el, items, sourceLabel) {
  if (!el) return;
  if (!items || !items.length) {
    el.innerHTML = '<div class="muted">Nenhum template encontrado.</div>';
    return;
  }
  const html = items.map((t) => {
    const tname = t.name || t.template_name;
    const lang = t.language || t.lang_code || 'pt_BR';
    const status = t.status ? `<span class="badge">${t.status}</span>` : '';
    const category = t.category ? `<span class="badge">${t.category}</span>` : '';
    return `
      <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; border:1px solid var(--border); border-radius:10px; padding:8px; margin:6px 0;">
        <div style="font-size:13px">
          <div><strong>${tname}</strong> <span class="badge">${lang}</span> ${status} ${category}</div>
          <div class="muted">${sourceLabel}</div>
        </div>
        <button class="btn" data-tname="${tname}" data-lang="${lang}">Enviar</button>
      </div>`;
  }).join('');
  el.innerHTML = html;
  el.querySelectorAll('button[data-tname]').forEach(btn => {
    btn.addEventListener('click', () => {
      const tn = btn.getAttribute('data-tname');
      const lg = btn.getAttribute('data-lang');
      sendTemplateQuick(tn, lg);
    });
  });
}

async function sendTemplateQuick(templateName, langCode, toOverride) {
  const to = (toOverride || toTemplateEl?.value || '').trim();
  if (!to || !templateName || !langCode) {
    log('[send-quick][warn] preencha To/Template/Lang');
    return;
  }
  try {
    const resp = await fetch(`${API_BASE}/_webhooks/whatsapp/send-template`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ to, template_name: templateName, lang_code: langCode, variables: [] })
    });
    const data = await resp.json().catch(() => ({}));
    log('[send-quick]', templateName, langCode, resp.status, data);
    // no-op
  } catch (e) {
    log('[send-quick][error]', e.message || e);
  }
}

async function loadMetaTemplates() {
  try {
    const resp = await fetch(`${API_BASE}/_webhooks/whatsapp/_admin/meta/templates?limit=100`);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${JSON.stringify(data)}`);
    renderTemplatesList(metaTemplatesEl, data.items || [], 'Meta');
    log('[meta-templates]', resp.status, (data.items||[]).length);

    // Preenche o select de templates Meta
    if (templateSelect) {
      const items = data.items || [];
      templateSelect.innerHTML = '<option value="">Selecione um template</option>' +
        items.map(t => `<option value="${t.name}::${t.language}">${t.name} (${t.language})</option>`).join('');
    }
  } catch (e) {
    log('[meta-templates][error]', e.message || e);
  }
}

function log(...args) {
  const line = args.map(v => typeof v === 'string' ? v : JSON.stringify(v, null, 2)).join(' ');
  logEl.textContent += `\n${line}`;
  logEl.scrollTop = logEl.scrollHeight;
  
  // Limita o tamanho do log para evitar consumo excessivo de memória
  if (logEl.textContent.length > 10000) {
    logEl.textContent = logEl.textContent.slice(-8000);
  }
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
  const to = toTemplateEl.value.trim();
  // Lê do dropdown (formato name::lang). Se vazio, usa campos manuais
  const selVal = templateSelect?.value || '';
  let template = '';
  let lang = '';
  if (selVal) {
    const parts = selVal.split('::');
    template = (parts[0] || '').trim();
    lang = (parts[1] || '').trim();
  } else {
    template = (document.getElementById('template')?.value || '').trim();
    lang = (document.getElementById('lang')?.value || 'pt_BR').trim();
  }
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
    // no-op
  } catch (e) {
    log('[send-template][error]', e.message || e);
  }
}

// Novo: Conexão SSE para logs do servidor
function connectLogStream() {
  const logStream = new EventSource(`${API_BASE}/_admin/logs/stream`);
  
  logStream.addEventListener('message', (e) => {
    log('[SERVER]', e.data);
  });

  logStream.addEventListener('error', (e) => {
    console.error('Log stream error:', e);
    setTimeout(connectLogStream, 5000); // Reconecta após 5 segundos
  });
}

// Inicia quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  connectLogStream();
});

// Eventos
if (healthBtn) healthBtn.addEventListener('click', checkHealth);
if (sendBtn) sendBtn.addEventListener('click', sendTemplate);
if (clearBtn) clearBtn.addEventListener('click', () => (logEl.textContent = ''));
if (btnLoadMeta) btnLoadMeta.addEventListener('click', loadMetaTemplates);
if (btnLoadMetaSelect) btnLoadMetaSelect.addEventListener('click', loadMetaTemplates);
if (btnLoadLocalSelect) btnLoadLocalSelect.addEventListener('click', loadLocalCatalog);
if (btnSendLocal) btnSendLocal.addEventListener('click', sendLocalSelected);

// Inicializa
// no extra setup
