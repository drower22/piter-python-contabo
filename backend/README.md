# Backend Piter – Arquitetura, Setup e Guia de Operação

Este documento descreve a arquitetura atual do backend, como rodar localmente, variáveis de ambiente necessárias, endpoints disponíveis e o fluxo completo do Webhook do WhatsApp.

---

## Visão Geral

- Linguagem: Python 3.10+
- Framework: FastAPI
- Banco/Storage/Autenticação: Supabase
- Mensageria: WhatsApp Cloud API (Meta Graph)
- Hospedagem: Contabo (deploy via GitHub Actions + SSH), Systemd service `piter-api`

Estrutura por camadas:

```
backend/Piter/
  api/routers/                 # Controladores HTTP (FastAPI)
    whatsapp_webhook.py        # Webhook do WhatsApp – fino; delega processamento
    forms.py                   # Formulários simples (cadastro, upload demo)
    health.py                  # Healthcheck
    logs.py                    # Streaming de logs

  services/                    # Lógica de negócio
    message_parser.py          # Normaliza payload do webhook (texto/botões)
    whatsapp_flow.py           # WhatsAppFlowService: estado + decisões de fluxo
    flows.py                   # Fluxos de demonstração (ex.: sumário, estoque)

  infrastructure/              # Integrações externas (infra)
    database/
      supabase_client.py       # get_supabase() – client do Supabase
    messaging/
      whatsapp_client.py       # WhatsAppClient – envio de texto/template/botões

  core/
    settings.py                # Configurações (env vars)
```

---

## Fluxo do WhatsApp – de ponta a ponta

- `api/routers/whatsapp_webhook.py`
  - Recebe a requisição do Meta.
  - Usa `services/message_parser.py` para normalizar mensagens (`ParsedWhatsAppMessage`).
  - Garante/obtém `wa_contacts` e `wa_conversations` no Supabase.
  - Persiste a mensagem inbound em `wa_messages`.
  - Instancia `WhatsAppFlowService` e chama `process_message()`.

- `services/whatsapp_flow.py` (classe `WhatsAppFlowService`)
  - Recupera o estado corrente da conversa (`wa_state`).
  - Se houver `button_id`, processa via `_handle_button_click()`:
    - Persiste click (`wa_button_clicks`).
    - Consulta catálogo `wa_buttons_catalog` (se ativo) para decidir a resposta:
      - `response_type = text | none | (template/webhook pronto para plug-in)`.
      - Envia resposta via `WhatsAppClient`.
      - Persiste mensagem outbound em `wa_messages`.
      - Atualiza próximo estado (RPC `wa_set_conversation_state`).
    - Fallback para botões de demonstração: `view_summary`, `view_consumption`, `view_low_stock`, `make_purchase_list`, `view_cmv_analysis`, `view_cmv_actions`.
  - Caso não seja botão tratado, segue o fluxo baseado em texto/estado (`welcome`, `menu`, coleta de parâmetros etc.).

- `services/message_parser.py`
  - Extrai de forma robusta `message_type`, `text`, `button_id`, `button_title`, além de `sender_number`, `message_id` e payload bruto.

- `infrastructure/messaging/whatsapp_client.py`
  - `send_text(to, text)`
  - `send_template(to, template, language, components)`
  - `send_buttons(to, body_text, buttons)` – até 3 botões.

---

## Tabelas Supabase relevantes

- `wa_contacts(id, whatsapp_number, profile_name, ...)`
- `wa_conversations(id, contact_id, status, last_message_at, ...)`
- `wa_messages(id, conversation_id, direction, type, json_payload, wa_message_id, ...)`
- `wa_button_clicks(conversation_id, contact_id, wa_message_id, button_id, button_title, raw_payload, ...)`
- `wa_state(conversation_id, step, context)`
- `wa_buttons_catalog(id, active, response_type, response_text, template_name, template_lang, template_vars, next_buttons, next_state, ...)`

---

## Variáveis de Ambiente (.env)

```
# Supabase
SUPABASE_URL=...
SUPABASE_KEY=...              # service_role

# WhatsApp Cloud API
WHATSAPP_PHONE_ID=...
WHATSAPP_TOKEN=...
WHATSAPP_GRAPH_VERSION=v19.0  # opcional
WHATSAPP_VERIFY_TOKEN=...     # usado pelo endpoint GET de verificação

# Admin
ADMIN_TOKEN=...               # para rotas administrativas / templates
```

> Observação: no deploy (Contabo), os secrets/prefixos são configurados no ambiente do servidor e no GitHub Actions.

---

## Como rodar localmente

1) Criar e ativar venv

```
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2) Exportar variáveis de ambiente (ou criar `.env` em `backend/`)

3) Subir API

```
python backend/main.py
# ou
uvicorn backend.Piter.main:app --reload --host 0.0.0.0 --port 8000
```

4) Endpoints úteis

- `GET /health` – healthcheck
- `POST /_webhooks/whatsapp` – webhook do WhatsApp
- `POST /_webhooks/whatsapp/send-template` – envio de template (com `ADMIN_TOKEN`)
- `GET /forms/signup` – formulário de cadastro simples (teste)
- `POST /_admin/debug/simulate-click` – simula clique de botão (teste)

---

## Deploy (Contabo)

- Workflow: `.github/workflows/deploy.yml`
  - Estratégia SSH-first, fallback para HTTPS + `REPO_PAT`.
  - Diretório do app no servidor: `/opt/piter-python-contabo`
  - Cria/atualiza venv e instala dependências.
  - Reinicia Systemd service `piter-api` e recarrega Nginx.

> Secrets necessários no GitHub:
> - `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY` (chave privada)
> - `REPO_PAT` (opcional para fallback HTTPS)

---

## Troubleshooting

- **Webhook 200 mas sem resposta**
  - Verifique logs do servidor e registros em `wa_messages`/`wa_button_clicks`.
  - Confirme `WHATSAPP_PHONE_ID` e `WHATSAPP_TOKEN`.

- **Botões clicados não alteram estado**
  - Veja se `wa_buttons_catalog` possui `next_state`/`next_buttons` corretos.
  - Confirme execução do RPC `wa_set_conversation_state`.

- **Falha ao clonar/atualizar no deploy**
  - Verifique se o servidor tem acesso por SSH ao GitHub.
  - Configure `REPO_PAT` para fallback via HTTPS.

---

## Roadmap curto

- Suporte completo a `response_type = template` e `webhook` no catálogo (já parcialmente preparado em `WhatsAppFlowService`).
- Melhorar persistência padronizada de outbound (usar `_persist_outbound_message` em todos envios).
- Remover pasta antiga `infra/` após confirmar que não há mais importadores.

---

## Créditos

Projeto mantido por `drower22`.

