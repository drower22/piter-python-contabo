// supabase/functions/envia_boas_vindas/index.ts
import { serve } from 'std/server'

serve(async (req) => {
  // Recebe o payload do trigger
  const payload = await req.json();

  // Seu webhook do n8n (Production URL)
  const n8nWebhookUrl = 'https://primary-production-37c2a.up.railway.app/webhook-test/recebe-usuario-supabase';

  // Faz o POST para o n8n
  const n8nResponse = await fetch(n8nWebhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  // Retorna o status
  if (n8nResponse.ok) {
    return new Response(JSON.stringify({ success: true }), { status: 200 });
  } else {
    return new Response(JSON.stringify({ success: false }), { status: 500 });
  }
});