(function(){
  const $ = (id)=>document.getElementById(id);
  const LS_KEY = 'dextester';
  const state = JSON.parse(localStorage.getItem(LS_KEY)||'{}');

  const normalizeBase = (u)=> (u||'').trim().replace(/\/+$/,'');

  const baseUrl = state.baseUrl || 'https://dex-novo-railway-production.up.railway.app';
  const verifyToken = state.verifyToken || '';
  const adminToken = state.adminToken || '';
  const tplName = state.tplName || 'whatsapp_verification';
  const tplLang = state.tplLang || 'pt_BR';
  $('baseUrl').value = baseUrl;
  $('verifyToken').value = verifyToken;
  const adminTokenEl = $('adminToken'); if (adminTokenEl) adminTokenEl.value = adminToken;
  const tplNameEl = $('tplName'); if (tplNameEl) tplNameEl.value = tplName;
  const tplLangEl = $('tplLang'); if (tplLangEl) tplLangEl.value = tplLang;

  $('saveCfg').onclick = ()=>{
    const cfg = {
      baseUrl: $('baseUrl').value.trim(),
      verifyToken: $('verifyToken').value.trim(),
      adminToken: ($('adminToken')?.value||'').trim(),
      tplName: ($('tplName')?.value||'').trim(),
      tplLang: ($('tplLang')?.value||'').trim(),
    };
    localStorage.setItem(LS_KEY, JSON.stringify(cfg));
    alert('Config salva');
  };

  $('btnHealth').onclick = async ()=>{
    $('outHealth').textContent = '...';
    try {
      const base = normalizeBase($('baseUrl').value);
      const res = await fetch(`${base}/`);
      const txt = await res.text();
      $('outHealth').textContent = `${res.status} ${res.statusText}\n\n${txt}`;
    } catch(e){
      $('outHealth').textContent = `ERR: ${e}`;
    }
  };

  $('btnVerify').onclick = async ()=>{
    $('outVerify').textContent = '...';
    const challenge = encodeURIComponent(($('challenge').value||'123456').trim());
    const token = encodeURIComponent(($('verifyToken').value||'').trim());
    const base = normalizeBase($('baseUrl').value);
    const url = `${base}/_webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=${token}&hub.challenge=${challenge}`;
    try {
      const res = await fetch(url);
      const txt = await res.text();
      $('outVerify').textContent = `${res.status} ${res.statusText}\n\n${txt}`;
    } catch(e){
      $('outVerify').textContent = `ERR: ${e}`;
    }
  };

  $('btnSimulate').onclick = async ()=>{
    $('outSim').textContent = '...';
    let body;
    try{ body = JSON.parse($('payload').value); }
    catch{ $('outSim').textContent = 'JSON inválido no payload'; return; }
    try {
      const base = normalizeBase($('baseUrl').value);
      const res = await fetch(`${base}/_webhooks/whatsapp`,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(body)
      });
      const txt = await res.text();
      $('outSim').textContent = `${res.status} ${res.statusText}\n\n${txt}`;
    } catch(e){
      $('outSim').textContent = `ERR: ${e}`;
    }
  };

  // ==== Admin: Listar usuários e enviar template ====
  const usersList = $('usersList');
  const outTpl = $('outTpl');
  const btnReloadUsers = $('btnReloadUsers');
  const btnSendTemplate = $('btnSendTemplate');

  async function reloadUsers(){
    if (!btnReloadUsers) return;
    outTpl.textContent = '';
    btnReloadUsers.disabled = true; btnReloadUsers.textContent = 'Carregando...';
    try{
      const base = normalizeBase($('baseUrl').value);
      const res = await fetch(`${base}/_webhooks/whatsapp/_admin/users`,{
        headers: { 'X-Admin-Token': ($('adminToken')?.value||'').trim() }
      });
      const data = await res.json().catch(()=>({}));
      usersList.innerHTML = '';
      if (res.ok && data.items){
        for (const u of data.items){
          const opt = document.createElement('option');
          opt.value = u.whatsapp_number_normalized;
          opt.textContent = `${u.user_name || u.id} — ${u.whatsapp_number_normalized}`;
          usersList.appendChild(opt);
        }
      } else {
        outTpl.textContent = `${res.status} ${res.statusText}\n\n${JSON.stringify(data)}`;
      }
    } catch(e){
      outTpl.textContent = `ERR: ${e}`;
    } finally {
      btnReloadUsers.disabled = false; btnReloadUsers.textContent = 'Listar usuários';
    }
  }

  async function sendTemplate(){
    outTpl.textContent = '...';
    const base = normalizeBase($('baseUrl').value);
    const admin = ($('adminToken')?.value||'').trim();
    const name = ($('tplName')?.value||'').trim() || 'whatsapp_verification';
    const lang = ($('tplLang')?.value||'').trim() || 'pt_BR';
    const manual = ($('manualNumber')?.value||'').trim();
    const selected = usersList && usersList.value ? usersList.value : '';
    const body = { template: name, language: lang };
    if (manual){ body.to = manual; }
    else if (selected){ body.user_number_normalized = selected; }
    else { outTpl.textContent = 'Escolha um usuário ou informe um número.'; return; }

    try{
      const res = await fetch(`${base}/_webhooks/whatsapp/send-template`,{
        method:'POST',
        headers:{ 'Content-Type':'application/json', 'X-Admin-Token': admin },
        body: JSON.stringify(body)
      });
      const txt = await res.text();
      outTpl.textContent = `${res.status} ${res.statusText}\n\n${txt}`;
    } catch(e){
      outTpl.textContent = `ERR: ${e}`;
    }
  }

  if (btnReloadUsers) btnReloadUsers.onclick = reloadUsers;
  if (btnSendTemplate) btnSendTemplate.onclick = sendTemplate;
})();
