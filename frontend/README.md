# Piter Frontend (Vercel)

Este é um frontend estático simples para interagir com a Piter API hospedada no Contabo.

- API base: https://api.pitzei.com.br
- Recursos:
  - Healthcheck
  - Envio de template do WhatsApp (/_webhooks/whatsapp/send-template)

## Como usar no Vercel

1) No projeto do Vercel, selecione este repositório e configure a raiz do projeto para `frontend/`.
2) Framework Preset: "Other" (ou Static Site).
3) Build Command: vazio (não é necessário)
4) Output Directory: `frontend` (ou deixe Vercel detectar automaticamente como estático)
5) Deploy

## Desenvolvimento local

Abra o arquivo `frontend/index.html` no navegador. Para funcionar com a API em produção, as chamadas usam `https://api.pitzei.com.br`.

Se precisar apontar para outro endpoint, edite `frontend/app.js` e altere a constante `API_BASE`.
