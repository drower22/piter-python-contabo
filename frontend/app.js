const API_BASE = (window.API_BASE || 'https://api.pitzei.com.br').replace(/\/$/, '');

const logEl = document.getElementById('log');
const healthBtn = document.getElementById('btnHealth');
const healthResult = document.getElementById('healthResult');
const clearBtn = document.getElementById('btnClearLog');
const copyBtn = document.getElementById('btnCopyLog');

const metaPhoneEl = document.getElementById('metaPhone');
const metaLangEl = document.getElementById('metaLang');
const metaTemplateSelect = document.getElementById('metaTemplateSelect');
const metaVariablesEl = document.getElementById('metaVariables');
const btnLoadMeta = document.getElementById('btnLoadMeta');
const btnSendMetaTemplate = document.getElementById('btnSendMetaTemplate');
const metaStatusEl = document.getElementById('metaStatus');
const metaTemplatesListEl = document.getElementById('metaTemplatesList');

const registerNameEl = document.getElementById('registerName');
const registerWhatsappEl = document.getElementById('registerWhatsapp');
const registerResultEl = document.getElementById('registerResult');
const registerDetailsEl = document.getElementById('registerDetails');
const btnRegister = document.getElementById('btnRegister');

const conversationPhoneEl = document.getElementById('conversationPhone');
const adminTokenEl = document.getElementById('adminToken');
const flowStatusEl = document.getElementById('flowStatus');

const btnFlowImportStart = document.getElementById('btnFlowImportStart');
const btnFlowImportSummary = document.getElementById('btnFlowImportSummary');
const btnFlowImportConsumption = document.getElementById('btnFlowImportConsumption');
const btnFlowLowStock = document.getElementById('btnFlowLowStock');
const btnFlowCmv = document.getElementById('btnFlowCmv');

const btnRefreshConversation = document.getElementById('btnRefreshConversation');
const conversationEmptyEl = document.getElementById('conversationEmpty');
const conversationTimelineEl = document.getElementById('conversationTimeline');
const buttonClicksSectionEl = document.getElementById('buttonClicksSection');
const buttonClicksListEl = document.getElementById('buttonClicksList');

const label = document.getElementById('apiBaseLabel');
if (label) label.textContent = API_BASE;

function log(...args) {
  if (!logEl) return;
  const line = args
    .map((v) => (typeof v === 'string' ? v : JSON.stringify(v, null, 2)))
    .join(' ');
  logEl.textContent += `\n${line}`;
  logEl.scrollTop = logEl.scrollHeight;
  if (logEl.textContent.length > 12000) {
    logEl.textContent = logEl.textContent.slice(-9000);
  }
}

function setBadge(el, text, variant) {
  if (!el) return;
  el.textContent = text || '';
  const classes = ['badge'];
  if (variant === 'ok') classes.push('ok');
  if (variant === 'err') classes.push('err');
  el.className = classes.join(' ');
}

function sanitizePhone(raw) {
  return (raw || '').replace(/\D/g, '');
}

function parseVariables(raw) {
  if (!raw) return [];
  return raw
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean);
}

function buildAdminHeaders(required) {
  const token = (adminTokenEl?.value || '').trim();
  if (required && !token) {
    log('[warn] endpoint exige x-admin-token');
  }
  return token ? { 'x-admin-token': token } : {};
}

async function registerUser() {
  const name = (registerNameEl?.value || '').trim();
  const whatsapp = (registerWhatsappEl?.value || '').trim();
  if (!name || !whatsapp) {
    setBadge(registerResultEl, 'Informe nome e WhatsApp', 'err');
    return;
  }

  const body = new URLSearchParams();
  body.append('name', name);
  body.append('whatsapp', whatsapp);

  try {
    const resp = await fetch(`${API_BASE}/forms/signup`, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    });
    const data = await resp.json().catch(() => ({}));

    if (resp.ok) {
      setBadge(registerResultEl, 'Conta criada', 'ok');
      registerDetailsEl.textContent = `account_id: ${data.account_id} • user_id: ${data.user_id}`;
      if (conversationPhoneEl && whatsapp) {
        conversationPhoneEl.value = whatsapp;
      }
      log('[signup][ok]', data);
    } else {
      setBadge(registerResultEl, `ERR ${resp.status}`, 'err');
      registerDetailsEl.textContent = data?.error || 'Falha no cadastro';
      log('[signup][err]', resp.status, data);
    }
  } catch (e) {
    setBadge(registerResultEl, 'Erro', 'err');
    registerDetailsEl.textContent = e.message || String(e);
    log('[signup][error]', e.message || e);
  }
}

async function checkHealth() {
  try {
    const resp = await fetch(`${API_BASE}/health`);
    const data = await resp.json().catch(() => ({}));
    if (resp.ok) {
      setBadge(healthResult, 'OK', 'ok');
    } else {
      setBadge(healthResult, `ERR ${resp.status}`, 'err');
    }
    log('[health]', data);
  } catch (e) {
    setBadge(healthResult, 'ERR', 'err');
    log('[health][error]', e.message || e);
  }
}

const FLOW_ENDPOINTS = {
  importStart: {
    url: '/_webhooks/whatsapp/_admin/demo/trigger/importacao',
    admin: true,
  },
  importSummary: {
    url: '/_webhooks/whatsapp/_flows/import/summary',
    admin: false,
  },
  importConsumption: {
    url: '/_webhooks/whatsapp/_flows/import/consumption',
    admin: false,
  },
  lowStock: {
    url: '/_webhooks/whatsapp/_admin/demo/trigger/estoque_baixo',
    admin: true,
  },
  cmv: {
    url: '/_webhooks/whatsapp/_admin/demo/trigger/cmv',
    admin: true,
  },
};

async function triggerFlow(kind) {
  const conf = FLOW_ENDPOINTS[kind];
  if (!conf) return;

  const phoneRaw = conversationPhoneEl?.value || '';
  const phone = sanitizePhone(phoneRaw);
  if (!phone) {
    setBadge(flowStatusEl, 'Informe o número destino', 'err');
    return;
  }

  const headers = {
    'content-type': 'application/json',
    ...buildAdminHeaders(conf.admin),
  };

  try {
    const resp = await fetch(`${API_BASE}${conf.url}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ to: phone }),
    });
    const data = await resp.json().catch(() => ({}));
    if (resp.ok) {
      setBadge(flowStatusEl, 'Fluxo disparado', 'ok');
      log(`[flow][${kind}]`, resp.status, data);
      refreshConversation(false, phone);
    } else {
      setBadge(flowStatusEl, `ERR ${resp.status}`, 'err');
      log(`[flow][${kind}][err]`, resp.status, data);
    }
  } catch (e) {
    setBadge(flowStatusEl, 'Erro ao disparar', 'err');
    log(`[flow][${kind}][error]`, e.message || e);
  }
}

function renderMetaTemplates(items) {
  if (!metaTemplatesListEl) return;
  if (!items || !items.length) {
    metaTemplatesListEl.style.display = 'none';
    metaTemplatesListEl.innerHTML = '';
    return;
  }

  metaTemplatesListEl.style.display = '';
  metaTemplatesListEl.innerHTML = items
    .map((item) => {
      const status = item.status ? `<span class=\"badge\">${item.status}</span>` : '';
      const category = item.category ? `<span class=\"badge\">${item.category}</span>` : '';
      const preview = (item.components || [])
        .map((c) => `${c.type || ''}: ${(c.text || '').slice(0, 60)}`)
        .join('<br />');
      return `
        <div class="template-item">
          <strong>${item.name}</strong>
          <div class="muted">${item.language || 'pt_BR'} ${status} ${category}</div>
          ${preview ? `<div class="small">${preview}</div>` : ''}
          <div class="template-actions">
            <button class="btn secondary" data-tpl="${item.name}" data-lang="${item.language || 'pt_BR'}">Enviar</button>
          </div>
        </div>
      `;
    })
    .join('');

  metaTemplatesListEl.querySelectorAll('button[data-tpl]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const tpl = btn.getAttribute('data-tpl');
      const lang = btn.getAttribute('data-lang');
      if (metaTemplateSelect) {
        metaTemplateSelect.value = `${tpl}::${lang}`;
      }
      sendMetaTemplate(tpl, lang);
    });
  });
}

async function loadMetaTemplates() {
  setBadge(metaStatusEl, 'Carregando...', null);
  try {
    const resp = await fetch(
      `${API_BASE}/_webhooks/whatsapp/_admin/meta/templates?limit=100`,
      {
        headers: {
          ...buildAdminHeaders(true),
        },
      }
    );
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      setBadge(metaStatusEl, `ERR ${resp.status}`, 'err');
      log('[meta][err]', resp.status, data);
      return;
    }

    const items = Array.isArray(data.items) ? data.items : [];
    if (data.warning) {
      setBadge(metaStatusEl, `${items.length} templates demo`, 'ok');
      log('[meta][warn]', data.warning);
    } else {
      setBadge(metaStatusEl, `${items.length} templates`, 'ok');
    }

    if (metaTemplateSelect) {
      const options = ['<option value="">Selecione um template</option>'].concat(
        items.map((item) => `<option value="${item.name}::${item.language}">${item.name} (${item.language})</option>`)
      );
      metaTemplateSelect.innerHTML = options.join('');
    }

    renderMetaTemplates(items);
  } catch (e) {
    setBadge(metaStatusEl, 'Erro ao carregar', 'err');
    log('[meta][error]', e.message || e);
  }
}

async function sendMetaTemplate(templateOverride, langOverride) {
  const phoneRaw = metaPhoneEl?.value || '';
  const phone = sanitizePhone(phoneRaw);
  if (!phone) {
    setBadge(metaStatusEl, 'Informe o número destino', 'err');
    return;
  }

  let templateName = templateOverride;
  let lang = langOverride;

  if (!templateName || !lang) {
    const selected = metaTemplateSelect?.value || '';
    if (!selected) {
      setBadge(metaStatusEl, 'Selecione um template', 'err');
      return;
    }
    const [name, language] = selected.split('::');
    templateName = (name || '').trim();
    lang = (language || '').trim();
  }

  const language = lang || metaLangEl?.value || 'pt_BR';
  const variables = parseVariables(metaVariablesEl?.value || '');

  try {
    const resp = await fetch(`${API_BASE}/_webhooks/whatsapp/send-template`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        ...buildAdminHeaders(true),
      },
      body: JSON.stringify({
        to: phone,
        template_name: templateName,
        lang_code: language,
        variables,
      }),
    });
    const data = await resp.json().catch(() => ({}));
    if (resp.ok) {
      setBadge(metaStatusEl, 'Template enviado', 'ok');
      log('[meta][send][ok]', templateName, language, data);
      refreshConversation(false, phone);
    } else {
      setBadge(metaStatusEl, `ERR ${resp.status}`, 'err');
      log('[meta][send][err]', resp.status, data);
    }
  } catch (e) {
    setBadge(metaStatusEl, 'Erro ao enviar', 'err');
    log('[meta][send][error]', e.message || e);
  }
}

function renderMessage(item) {
  const direction = item.direction === 'out' ? 'message-out' : 'message-in';
  const div = document.createElement('div');
  div.className = `message ${direction}`;

  const meta = document.createElement('div');
  meta.className = 'message-meta';
  const when = item.created_at ? new Date(item.created_at).toLocaleString('pt-BR', { hour12: false }) : '';
  meta.textContent = `${item.direction === 'out' ? 'Piter' : 'Cliente'} • ${item.type || 'unknown'} ${when ? `• ${when}` : ''}`;
  div.appendChild(meta);

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = item.text || '[sem texto]';
  div.appendChild(bubble);

  if (Array.isArray(item.buttons) && item.buttons.length) {
    const btns = document.createElement('div');
    btns.className = 'message-buttons';
    item.buttons.forEach((btn) => {
      const span = document.createElement('span');
      span.textContent = `${btn.title || btn.id || 'botão'}`;
      btns.appendChild(span);
    });
    div.appendChild(btns);
  }

  if (item.button_id && item.direction === 'in') {
    const choice = document.createElement('div');
    choice.className = 'message-buttons';
    const span = document.createElement('span');
    span.textContent = `Botão: ${item.button_title || item.button_id}`;
    choice.appendChild(span);
    div.appendChild(choice);
  }

  return div;
}

function renderConversationView(data) {
  if (!conversationTimelineEl || !conversationEmptyEl) return;

  const messages = Array.isArray(data?.messages) ? data.messages : [];
  conversationTimelineEl.innerHTML = '';

  if (!messages.length) {
    conversationEmptyEl.style.display = '';
  } else {
    conversationEmptyEl.style.display = 'none';
    messages.forEach((msg) => {
      conversationTimelineEl.appendChild(renderMessage(msg));
    });
  }

  const clicks = Array.isArray(data?.button_clicks) ? data.button_clicks : [];
  if (clicks.length && buttonClicksSectionEl && buttonClicksListEl) {
    buttonClicksSectionEl.style.display = '';
    buttonClicksListEl.innerHTML = '';
    clicks.forEach((item) => {
      const li = document.createElement('li');
      const when = item.clicked_at ? new Date(item.clicked_at).toLocaleString('pt-BR', { hour12: false }) : '';
      li.textContent = `${item.button_title || item.button_id || 'botão'} • ${when}`;
      buttonClicksListEl.appendChild(li);
    });
  } else if (buttonClicksSectionEl) {
    buttonClicksSectionEl.style.display = 'none';
  }
}

async function refreshConversation(manual = false, phoneOverride) {
  const phoneInput = phoneOverride || sanitizePhone(conversationPhoneEl?.value || '');
  if (!phoneInput) {
    if (manual) log('[conversation][warn] informe o número destino');
    renderConversationView({ messages: [], button_clicks: [] });
    return;
  }

  const url = `${API_BASE}/_webhooks/whatsapp/_admin/demo/conversation-log?phone=${encodeURIComponent(phoneInput)}`;
  try {
    const resp = await fetch(url, {
      headers: buildAdminHeaders(false),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      log('[conversation][err]', resp.status, data);
      return;
    }
    renderConversationView(data);
    if (manual) log('[conversation][ok]', data?.messages?.length || 0, 'mensagens');
  } catch (e) {
    log('[conversation][error]', e.message || e);
  }
}

function connectLogStream() {
  try {
    const logStream = new EventSource(`${API_BASE}/_admin/logs/stream`);
    logStream.addEventListener('message', (e) => {
      log('[SERVER]', e.data);
    });
    logStream.addEventListener('error', () => {
      setTimeout(connectLogStream, 6000);
    });
  } catch (e) {
    log('[log-stream][error]', e.message || e);
  }
}

if (btnRegister) btnRegister.addEventListener('click', registerUser);
if (healthBtn) healthBtn.addEventListener('click', checkHealth);
if (clearBtn && logEl) clearBtn.addEventListener('click', () => (logEl.textContent = ''));
if (copyBtn && logEl) {
  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(logEl.textContent || '');
      copyBtn.textContent = 'Copiado!';
      setTimeout(() => (copyBtn.textContent = 'Copiar'), 2000);
    } catch (err) {
      log('[clipboard][error]', err.message || err);
    }
  });
}

if (btnFlowImportStart) btnFlowImportStart.addEventListener('click', () => triggerFlow('importStart'));
if (btnFlowImportSummary) btnFlowImportSummary.addEventListener('click', () => triggerFlow('importSummary'));
if (btnFlowImportConsumption) btnFlowImportConsumption.addEventListener('click', () => triggerFlow('importConsumption'));
if (btnFlowLowStock) btnFlowLowStock.addEventListener('click', () => triggerFlow('lowStock'));
if (btnFlowCmv) btnFlowCmv.addEventListener('click', () => triggerFlow('cmv'));
if (btnRefreshConversation) btnRefreshConversation.addEventListener('click', () => refreshConversation(true));
if (btnLoadMeta) btnLoadMeta.addEventListener('click', loadMetaTemplates);
if (btnSendMetaTemplate) btnSendMetaTemplate.addEventListener('click', () => sendMetaTemplate());

document.addEventListener('DOMContentLoaded', () => {
  connectLogStream();
});
