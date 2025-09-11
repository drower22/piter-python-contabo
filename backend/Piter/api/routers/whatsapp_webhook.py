import os
from fastapi import APIRouter, Request, Query, Body
from fastapi.responses import PlainTextResponse, JSONResponse
from ...infra.supabase import get_supabase
from ...infra.whatsapp import WhatsAppClient
from ...services.flows import DemoFlowsService
from ...services.whatsapp_flow import handle_message, reply_via_whatsapp
from pydantic import BaseModel

router = APIRouter(tags=["WhatsApp"], prefix="/_webhooks/whatsapp")


@router.get("")
async def verify(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    request: Request = None,
):
    # Verificação oficial do Meta WhatsApp Cloud API
    # Fallback: alguns proxies/clients podem enviar sem pontos
    if (hub_mode is None or hub_challenge is None or hub_verify_token is None) and request is not None:
        qp = request.query_params
        hub_mode = hub_mode or qp.get("hub_mode") or qp.get("mode")
        hub_challenge = hub_challenge or qp.get("hub_challenge") or qp.get("challenge")
        hub_verify_token = hub_verify_token or qp.get("hub_verify_token") or qp.get("verify_token")

    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    try:
        print(
            "[WA_VERIFY]",
            {
                "mode": hub_mode,
                "challenge_present": bool(hub_challenge),
                "provided_len": len(hub_verify_token or ""),
                "env_set": bool(verify_token),
                "match": (hub_verify_token == verify_token) if verify_token else False,
            }
        )
    except Exception:
        # Evita que problemas de log quebrem a verificação
        pass
    if hub_mode == "subscribe" and hub_challenge and hub_verify_token == verify_token:
        return PlainTextResponse(content=hub_challenge)
    return PlainTextResponse(status_code=403, content="forbidden")


@router.get("/ _debug/wa-env".replace(" ", ""))
async def debug_wa_env():
    token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    return {
        "env_set": bool(token),
        "len": len(token) if token else 0
    }


def _get_first(lst):
    return lst[0] if isinstance(lst, list) and lst else None


def _ensure_contact(sb, wa_number: str, profile_name: str | None):
    # Busca por número; cria se não existir
    q = sb.table('wa_contacts').select('id').eq('whatsapp_number', wa_number).maybe_single().execute()
    if q.data and q.data.get('id'):
        return q.data['id']
    ins = sb.table('wa_contacts').insert({
        'whatsapp_number': wa_number,
        'profile_name': profile_name,
    }).select('id').single().execute()
    return ins.data['id']


def _ensure_open_conversation(sb, contact_id: str) -> str:
    q = sb.table('wa_conversations').select('id').eq('contact_id', contact_id).eq('status', 'open').order('last_message_at', desc=True).maybe_single().execute()
    if q.data and q.data.get('id'):
        return q.data['id']
    ins = sb.table('wa_conversations').insert({
        'contact_id': contact_id,
        'status': 'open'
    }).select('id').single().execute()
    return ins.data['id']


def _insert_message(sb, conversation_id: str, direction: str, msg_type: str, body: dict, wa_message_id: str | None = None):
    payload = {
        'conversation_id': conversation_id,
        'direction': direction,
        'type': msg_type,
        'json_payload': body,
        'wa_message_id': wa_message_id,
    }
    sb.table('wa_messages').insert(payload).execute()
    # update last_message_at
    sb.table('wa_conversations').update({'last_message_at': 'now()'}).eq('id', conversation_id).execute()


@router.post("")
async def receive_update(request: Request):
    body = await request.json()
    # Estrutura esperada: entry -> changes -> value -> messages
    try:
        entry = _get_first(body.get('entry')) or {}
        change = _get_first(entry.get('changes')) or {}
        value = change.get('value') or {}
        messages = value.get('messages') or []
        contacts = value.get('contacts') or []
        contact_obj = _get_first(contacts) or {}
        profile_name = (contact_obj.get('profile') or {}).get('name')

        if not messages:
            return JSONResponse(status_code=200, content={"skip": True})

        sb = get_supabase()

        flows = DemoFlowsService()
        for m in messages:
            wa_from = m.get('from')  # e.g., "5511999999999"
            wa_id = m.get('id')
            msg_type = m.get('type')
            # Normaliza para formato +<cc><number>
            to_number = f"+{wa_from}" if wa_from and not wa_from.startswith('+') else wa_from

            contact_id = _ensure_contact(sb, wa_number=to_number, profile_name=profile_name)
            conversation_id = _ensure_open_conversation(sb, contact_id)

            _insert_message(sb, conversation_id, 'in', msg_type, m, wa_id)

            # Trata cliques de botões interativos (interactive.button_reply)
            if msg_type == 'interactive':
                interactive = m.get('interactive') or {}
                button_reply = interactive.get('button_reply') or {}
                btn_id = (button_reply.get('id') or '').strip()
                if btn_id:
                    # Persist inbound
                    _insert_message(sb, conversation_id, 'in', 'interactive', m, wa_id)
                    # Roteia pelos fluxos
                    try:
                        if btn_id == 'view_summary':
                            # Dados mock para demo; em produção, consultar Supabase
                            summary = {
                                'valor_pizzas': '4.520,00', 'qtd_pizzas': 180,
                                'valor_bebidas': '1.240,00', 'qtd_bebidas': 210,
                                'top_pizzas': [{'nome': f'Pizza {i}', 'qtd': 30-i} for i in range(1,11)],
                                'top_bebidas': [{'nome': f'Bebida {i}', 'qtd': 50-i} for i in range(1,6)],
                            }
                            flows.send_sales_summary(to_number, summary)
                            import asyncio as _aio
                            _aio.create_task(flows.ask_consumption_after_delay(to_number, 10))
                        elif btn_id == 'view_consumption':
                            items = [{'nome': f'Insumo {i}', 'qtd': 10*i, 'unid': 'un'} for i in range(1,11)]
                            flows.send_consumption_list(to_number, items)
                        elif btn_id == 'view_low_stock':
                            items = [
                                {'insumo': 'Mussarela', 'qtd_atual': 3, 'qtd_min': 8, 'unid': 'kg'},
                                {'insumo': 'Calabresa', 'qtd_atual': 2, 'qtd_min': 6, 'unid': 'kg'},
                                {'insumo': 'Molho', 'qtd_atual': 5, 'qtd_min': 10, 'unid': 'kg'},
                                {'insumo': 'Farinha', 'qtd_atual': 20, 'qtd_min': 35, 'unid': 'kg'},
                                {'insumo': 'Refrigerante Lata', 'qtd_atual': 12, 'qtd_min': 24, 'unid': 'un'},
                            ]
                            flows.send_low_stock_list(to_number, items)
                        elif btn_id == 'make_purchase_list':
                            flows.client.send_text(to_number, 'Ok! Vou gerar a lista de compras sugerida e te envio em instantes.')
                        elif btn_id == 'view_cmv_analysis':
                            data = {
                                'cmv_esperado': 28.0, 'cmv_atual': 32.5, 'desvio_pct': 4.5,
                                'contribuintes': [
                                    {'insumo': 'Mussarela', 'impacto_pct': 1.8},
                                    {'insumo': 'Calabresa', 'impacto_pct': 1.2},
                                    {'insumo': 'Tomate', 'impacto_pct': 0.9},
                                ]
                            }
                            flows.send_cmv_analysis(to_number, data)
                        elif btn_id == 'view_cmv_actions':
                            flows.client.send_text(to_number, 'Ações recomendadas: 1) revisar porcionamento de queijos; 2) ajustar preço das bebidas; 3) auditar perdas na abertura.')
                    except Exception as _e_btn:
                        print('[ERROR] button handler failed:', repr(_e_btn))
                    # Continua para próxima mensagem
                    continue

            # Apenas texto tratado inicialmente
            inbound = {"type": msg_type}
            if msg_type == 'text':
                inbound['text'] = m.get('text')

            conv = {"id": conversation_id, "contact_id": contact_id}
            result = handle_message(conv, inbound)
            if result.reply_text and to_number:
                reply_via_whatsapp(to_number, result)
                # Persist outbound
                _insert_message(sb, conversation_id, 'out', 'text', {"text": {"body": result.reply_text}}, None)

        return JSONResponse(status_code=200, content={"received": True})
    except Exception as e:
        return JSONResponse(status_code=200, content={"received": True, "note": "error, but 200 to avoid retries", "error": str(e)})


class WhatsAppTemplateRequest(BaseModel):
    to: str | None = None
    contact_id: str | None = None
    user_id: str | None = None
    user_number_normalized: str | None = None
    template_name: str
    lang_code: str
    components: list = []
    # Lista simples de variáveis para o corpo do template ({{1}}, {{2}}, ...)
    variables: list[str] | None = None


async def resolve_recipient(data: WhatsAppTemplateRequest):
    if data.to:
        return data.to
    elif data.contact_id:
        sb = get_supabase()
        q = sb.table('wa_contacts').select('whatsapp_number').eq('id', data.contact_id).maybe_single().execute()
        data = q.data or {}
        return (data.get('whatsapp_number') or '').strip()
    elif data.user_id:
        sb = get_supabase()
        q = sb.table('users').select('whatsapp_number_normalized').eq('id', data.user_id).maybe_single().execute()
        data = q.data or {}
        return (data.get('whatsapp_number_normalized') or '').strip()
    elif data.user_number_normalized:
        return data.user_number_normalized
    else:
        raise Exception("Recipient not found")


@router.post("/send-template")
async def send_template(
    request: Request,
    data: WhatsAppTemplateRequest = Body(...)
):
    try:
        print(f"[DEBUG] Request received: {await request.body()}")
        
        # Verificação do token admin
        admin_token = os.getenv("ADMIN_TOKEN")
        if admin_token and request.headers.get("x-admin-token") != admin_token:
            return JSONResponse(status_code=403, content={"error": "forbidden"})

        # Validação simplificada
        if not data.template_name or not data.lang_code:
            return JSONResponse(
                status_code=422,
                content={"error": "template_name and lang_code are required"}
            )

        # Resolve recipient - aceita qualquer um dos campos
        to_number = await resolve_recipient(data)
        # Normaliza para apenas dígitos (WhatsApp Cloud aceita sem '+')
        import re as _re
        to_number_normalized = _re.sub(r"\D", "", (to_number or "").strip())
        if not to_number_normalized:
            return JSONResponse(status_code=422, content={"error": "invalid recipient"})
        
        # Tenta obter user_name a partir dos identificadores fornecidos
        user_name_val: str | None = None
        try:
            sb = get_supabase()
            if data.user_id:
                q = sb.table('users').select('user_name').eq('id', data.user_id).maybe_single().execute()
                user_name_val = (q.data or {}).get('user_name')
            if not user_name_val and data.user_number_normalized:
                q = sb.table('users').select('user_name').eq('whatsapp_number_normalized', data.user_number_normalized).maybe_single().execute()
                user_name_val = (q.data or {}).get('user_name')
            if not user_name_val and data.to:
                q = sb.table('users').select('user_name').eq('whatsapp_number_normalized', data.to).maybe_single().execute()
                user_name_val = (q.data or {}).get('user_name')
            if not user_name_val and to_number:
                q = sb.table('users').select('user_name').eq('whatsapp_number_normalized', to_number).maybe_single().execute()
                user_name_val = (q.data or {}).get('user_name')
        except Exception as _e:
            # Não falha se não encontrar; apenas segue sem variável automática
            print(f"[DEBUG] Falha ao buscar user_name: {_e}")

        # Envio
        client = WhatsAppClient()
        
        # Adicionando logs para depuração
        components = data.components or []

        # Se não vierem components mas vier uma lista de variables, monta automaticamente
        if not components and (data.variables or []):
            body_params = []
            for v in (data.variables or []):
                # Por padrão enviamos como texto
                body_params.append({"type": "text", "text": str(v)})
            components = [{"type": "body", "parameters": body_params}]

        # Se ainda não houver components e também não houver variables, mas temos user_name,
        # usamos user_name como {{1}}
        if not components and not (data.variables or []):
            if user_name_val:
                components = [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(user_name_val)}]
                }]

        payload = {
            "to": to_number_normalized,
            "template": data.template_name,
            "language": data.lang_code,
            "components": components
        }
        print(f"[DEBUG] WhatsAppClient.send_template PAYLOAD: {payload}")

        try:
            response = client.send_template(
                to=payload["to"],
                template=payload["template"],
                language=payload["language"],
                components=payload["components"]
            )
        except Exception as _e:
            import traceback as _tb
            print("[ERROR] Upstream Meta error:", repr(_e))
            print(_tb.format_exc())
            return JSONResponse(status_code=502, content={"error": "meta_api_error", "details": str(_e)})
        
        print(f"[DEBUG] WhatsApp API response: {response}")
        return JSONResponse(status_code=200, content={"ok": True, "to": to_number_normalized, "response": response})
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in send_template: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500, 
            content={"error": str(e), "traceback": traceback.format_exc()}
        )


# ========================
# Admin demo triggers (Fluxos 1-3)
# ========================
class TriggerRequest(BaseModel):
    to: str


def _normalize_phone(num: str) -> str:
    import re as _re
    return _re.sub(r"\D", "", (num or "").strip())


@router.post("/_admin/demo/trigger/importacao")
async def trigger_importacao(req: TriggerRequest, request: Request):
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and request.headers.get("x-admin-token") != admin_token:
        return JSONResponse(status_code=403, content={"error": "forbidden"})
    to = _normalize_phone(req.to)
    flows = DemoFlowsService()
    resp = flows.start_sales_import_flow(to)
    return JSONResponse(status_code=200, content={"ok": True, "response": resp})


@router.post("/_admin/demo/trigger/estoque_baixo")
async def trigger_estoque_baixo(req: TriggerRequest, request: Request):
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and request.headers.get("x-admin-token") != admin_token:
        return JSONResponse(status_code=403, content={"error": "forbidden"})
    to = _normalize_phone(req.to)
    flows = DemoFlowsService()
    resp = flows.start_low_stock_flow(to)
    return JSONResponse(status_code=200, content={"ok": True, "response": resp})


@router.post("/_admin/demo/trigger/cmv")
async def trigger_cmv(req: TriggerRequest, request: Request):
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and request.headers.get("x-admin-token") != admin_token:
        return JSONResponse(status_code=403, content={"error": "forbidden"})
    to = _normalize_phone(req.to)
    flows = DemoFlowsService()
    resp = flows.start_cmv_deviation_flow(to)
    return JSONResponse(status_code=200, content={"ok": True, "response": resp})


@router.get("/_admin/users")
async def list_users(request: Request):
    try:
        admin_token = os.getenv("ADMIN_TOKEN")
        if admin_token and request.headers.get("x-admin-token") != admin_token:
            return JSONResponse(status_code=403, content={"error": "forbidden"})

        sb = get_supabase()
        
        # Debug: Primeiro descobrir as colunas disponíveis
        debug_q = sb.table('users').select('*').limit(1).execute()
        print(f"[DEBUG] Estrutura da tabela users: {debug_q.data}")
        
        # Query principal usando colunas genéricas
        q = (
            sb.table('users')
            .select('id,whatsapp_number_normalized')
            .not_.eq('whatsapp_number_normalized', None)
            .order('created_at', desc=True)
            .limit(200)
            .execute()
        )
        
        items = []
        for r in q.data or []:
            num = (r.get('whatsapp_number_normalized') or '').strip()
            if num:
                items.append({
                    'id': r.get('id'),
                    'whatsapp_number_normalized': num
                })
        
        return JSONResponse(status_code=200, content={"items": items})
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": "Internal server error", "details": str(e)}
        )
