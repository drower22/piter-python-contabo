(function(){
  const $ = (id)=>document.getElementById(id);
  const LS_KEY = 'dextester';
  const state = JSON.parse(localStorage.getItem(LS_KEY)||'{}');

  const normalizeBase = (u)=> (u||'').trim().replace(/\/+$/,'');

  const baseUrl = state.baseUrl || 'https://dex-novo-railway-production.up.railway.app';
  const verifyToken = state.verifyToken || '';
  $('baseUrl').value = baseUrl;
  $('verifyToken').value = verifyToken;

  $('saveCfg').onclick = ()=>{
    const cfg = {
      baseUrl: $('baseUrl').value.trim(),
      verifyToken: $('verifyToken').value.trim(),
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
})();
