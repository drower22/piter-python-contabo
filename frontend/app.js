// Module script
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

// -----------------
// Supabase (usuarios)
// -----------------
// Carrega/salva config no localStorage
const sbUrlEl = document.getElementById('sbUrl');
const sbKeyEl = document.getElementById('sbKey');
const btnSaveSupabase = document.getElementById('btnSaveSupabase');
const btnLoadUsers = document.getElementById('btnLoadUsers');
const usersTableBody = document.querySelector('#usersTable tbody');

function loadSupabaseCfg() {
  const url = localStorage.getItem('SB_URL') || '';
  const key = localStorage.getItem('SB_KEY') || '';
  if (sbUrlEl) sbUrlEl.value = url;
  if (sbKeyEl) sbKeyEl.value = key;
}

function saveSupabaseCfg() {
  const url = (sbUrlEl?.value || '').trim();
  const key = (sbKeyEl?.value || '').trim();
  localStorage.setItem('SB_URL', url);
  localStorage.setItem('SB_KEY', key);
  log('[supabase] configuração salva');
}

async function fetchUsers() {
  const url = localStorage.getItem('SB_URL');
  const key = localStorage.getItem('SB_KEY');
  if (!url || !key) {
    log('[supabase][warn] Configure SUPABASE_URL e SUPABASE_ANON_KEY');
    return;
  }
  try {
    const resp = await fetch(`${url.replace(/\/$/, '')}/rest/v1/usuarios?select=id,nome,whatsapp`, {
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
      }
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const items = await resp.json();
    usersTableBody.innerHTML = '';
    for (const r of items) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.id ?? ''}</td><td>${r.nome ?? ''}</td><td>${r.whatsapp ?? ''}</td>`;
      usersTableBody.appendChild(tr);
    }
    log('[supabase][usuarios]', items);
  } catch (e) {
    log('[supabase][error]', e.message || e);
  }
}

// Eventos
if (healthBtn) healthBtn.addEventListener('click', checkHealth);
if (sendBtn) sendBtn.addEventListener('click', sendTemplate);
if (clearBtn) clearBtn.addEventListener('click', () => (logEl.textContent = ''));
if (btnSaveSupabase) btnSaveSupabase.addEventListener('click', saveSupabaseCfg);
if (btnLoadUsers) btnLoadUsers.addEventListener('click', fetchUsers);

// Inicializa
loadSupabaseCfg();
