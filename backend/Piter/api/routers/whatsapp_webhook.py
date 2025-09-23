import os
from fastapi import APIRouter, Request, Query, Body
from fastapi.responses import PlainTextResponse, JSONResponse
from ...infrastructure.database.supabase_client import get_supabase
from ...services.message_parser import WhatsAppMessageParser
from ...services.whatsapp_flow import WhatsAppFlowService
from ...infrastructure.messaging.whatsapp_client import WhatsAppClient
from ...services.flows import DemoFlowsService
from pydantic import BaseModel


router = APIRouter(tags=["WhatsApp"], prefix="/_webhooks/whatsapp")


def _load_catalog_item(sb, item_id: str) -> dict:
    q = (
        sb.table('wa_buttons_catalog')
        .select('id,title,response_type,response_text,next_buttons,template_name,template_lang,template_vars,metadata')
        .eq('id', item_id)
        .maybe_single()
        .execute()
    )
    return q.data or {}


def _apply_defaults(text: str, md: dict) -> str:
    defaults = {}
    try:
        if isinstance(md, str):
            import json as _json
            md = _json.loads(md)
        defaults = (md or {}).get('mock_defaults') or {}
    except Exception:
        defaults = {}
    for k, v in (defaults.items() if isinstance(defaults, dict) else []):
        text = text.replace(f"{{{{{k}}}}}", str(v))
    return text


def _format_summary_text(ms: dict) -> str:
    pizzas = (ms or {}).get('pizzas_top_10') or []
    bebidas = (ms or {}).get('bebidas_top_5') or []
    lines = ["Resumo das vendas de hoje:"]
    if pizzas:
        lines.append("\nTop 10 Pizzas:")
        for i, p in enumerate(pizzas[:10], 1):
            lines.append(f"{i}. {p.get('nome','?')} — {p.get('qtd',0)} un")
    if bebidas:
        lines.append("\nTop 5 Bebidas:")
        for i, b in enumerate(bebidas[:5], 1):
            lines.append(f"{i}. {b.get('nome','?')} — {b.get('qtd',0)} un")
    return "\n".join(lines)


def _format_consumption_text(items: list[dict]) -> str:
    lines = ["Com base nas vendas de hoje, o consumo estimado é:"]
    for it in (items or [])[:50]:
        lines.append(f"- {it.get('insumo','?')}: {it.get('qtd',0)} {it.get('unidade','')}")
    return "\n".join(lines)


class ImportStartBody(BaseModel):
    to: str


@router.post("/_flows/import/start")
async def flow_import_start(req: ImportStartBody):
    """Dispara o início do fluxo de importação usando o item 'import_sales_start'."""
    to = _normalize_phone(req.to)
    sb = get_supabase()
    item = _load_catalog_item(sb, 'import_sales_start')
    if not item:
        return JSONResponse(status_code=404, content={"error": "catalog_item_not_found", "id": "import_sales_start"})
    text = _apply_defaults(item.get('response_text') or '', item.get('metadata') or {})
    buttons = item.get('next_buttons')
    if isinstance(buttons, str):
        try:
            import json as _json
            buttons = _json.loads(buttons)
        except Exception:
            buttons = None
    client = DemoFlowsService().client
    if buttons:
        resp = client.send_buttons(to, text, buttons)
        return {"ok": True, "mode": "text+buttons", "response": resp}
    else:
        resp = client.send_text(to, text)
        return {"ok": True, "mode": "text", "response": resp}


class ImportGenericBody(BaseModel):
    to: str


@router.post("/_flows/import/summary")
async def flow_import_summary(req: ImportGenericBody):
    """Envia resumo mock (top pizzas/bebidas) e agenda a pergunta de consumo com botão."""
    to = _normalize_phone(req.to)
    sb = get_supabase()
    item = _load_catalog_item(sb, 'view_summary')
    if not item:
        return JSONResponse(status_code=404, content={"error": "catalog_item_not_found", "id": "view_summary"})
    md = item.get('metadata') or {}
    try:
        if isinstance(md, str):
            import json as _json
            md = _json.loads(md)
    except Exception:
        md = {}
    ms = (md or {}).get('mock_summary') or {}
    text = _format_summary_text(ms)

    client = DemoFlowsService().client
    send1 = client.send_text(to, text)

    # Agenda próxima pergunta com botão 'Ver consumo estimado'
    import asyncio as _aio
    delay_s = int((ms or {}).get('delay_next_seconds') or 3)

    async def _later():
        await _aio.sleep(delay_s)
        client.send_buttons(to, 'Gostaria de ver o consumo estimado para hoje?', [{"id": "view_consumption", "title": "Ver consumo estimado"}])

    _aio.create_task(_later())
    return {"ok": True, "sent": send1, "next_in": delay_s}


@router.post("/_flows/import/consumption")
async def flow_import_consumption(req: ImportGenericBody):
    to = _normalize_phone(req.to)
    sb = get_supabase()
    item = _load_catalog_item(sb, 'view_consumption')
    if not item:
        return JSONResponse(status_code=404, content={"error": "catalog_item_not_found", "id": "view_consumption"})
    md = item.get('metadata') or {}
    try:
        if isinstance(md, str):
            import json as _json
            md = _json.loads(md)
    except Exception:
        md = {}
    items = (md or {}).get('mock_consumption') or []
    text = _format_consumption_text(items)
    resp = DemoFlowsService().client.send_text(to, text)
    return {"ok": True, "response": resp}


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
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    return {
        "verify_token_set": bool(verify_token),
        "verify_token_len": len(verify_token) if verify_token else 0,
        "whatsapp_token_set": bool(os.getenv("WHATSAPP_TOKEN")),
        "whatsapp_phone_id_set": bool(os.getenv("WHATSAPP_PHONE_ID")),
        "whatsapp_waba_id_set": bool(os.getenv("WHATSAPP_WABA_ID")),
        "graph_version": os.getenv("WHATSAPP_GRAPH_VERSION", "v19.0"),
    }


def _get_first(lst):
    return lst[0] if isinstance(lst, list) and lst else None


def _ensure_contact(sb, wa_number: str, profile_name: str | None):
    """
    Garante o ID do contato para abertura de conversa usando a tabela 'perfis'.
    Observação importante: no schema atual, wa_conversations.contact_id referencia perfis(id),
    então não podemos inserir em 'wa_contacts' (view) nem criar um contato novo sem um auth.user.

    Comportamento:
    - Busca em perfis pelo campo 'whatsapp' já normalizado (apenas dígitos)
    - Se encontrar, retorna perfis.id
    - Se não encontrar, retorna None (o caller deve tratar e decidir o que fazer)
    """
    try:
        norm = _normalize_phone(wa_number)
        # Busca direta por igualdade. Caso a base armazene com '+', tentamos as duas formas.
        q = sb.table('perfis').select('id, whatsapp').eq('whatsapp', norm).maybe_single().execute()
        data = getattr(q, 'data', None) or (q.get('data') if isinstance(q, dict) else None) or {}
        if data.get('id'):
            return data['id']

        # Tentativa alternativa com '+' prefixado
        q2 = sb.table('perfis').select('id, whatsapp').eq('whatsapp', f"+{norm}").maybe_single().execute()
        data2 = getattr(q2, 'data', None) or (q2.get('data') if isinstance(q2, dict) else None) or {}
        if data2.get('id'):
            return data2['id']

        # Como última tentativa, buscar por LIKE contendo o final do número (pode haver formatação diferente)
        try:
            q3 = (
                sb.table('perfis')
                .select('id, whatsapp')
                .like('whatsapp', f"%{norm}")
                .limit(1)
                .execute()
            )
            q3data = getattr(q3, 'data', None) or (q3.get('data') if isinstance(q3, dict) else None)
            if q3data and isinstance(q3data, list) and q3data:
                return q3data[0].get('id')
        except Exception:
            pass

        # Não encontrado
        return None
    except Exception as _e:
        print(f"[WARN] _ensure_contact failed: {repr(_e)}")
        return None


def _ensure_open_conversation(sb, contact_id: str) -> str:
    q = sb.table('wa_conversations').select('id').eq('contact_id', contact_id).eq('status', 'open').order('last_message_at', desc=True).maybe_single().execute()
    if q.data and q.data.get('id'):
        return q.data['id']
    ins = sb.table('wa_conversations').insert({
        'contact_id': contact_id,
        'status': 'open'
    }).select('id').single().execute()
    return ins.data['id']




@router.post("")
async def receive_update(request: Request):
    body = await request.json()
    try:
        print("[DEBUG][WA] inbound body:", body)
    except Exception:
        pass

    try:
        parser = WhatsAppMessageParser()
        parsed_messages = parser.parse(body)

        if not parsed_messages:
            return JSONResponse(status_code=200, content={"status": "no valid messages found"})

        sb = get_supabase()
        flow_service = WhatsAppFlowService(supabase_client=sb)

        for msg in parsed_messages:
            try:
                contact_id = _ensure_contact(sb, wa_number=msg.sender_number, profile_name=msg.profile_name)
                if not contact_id:
                    print(f"[WARN] No profile found in 'perfis' for number {msg.sender_number}; skipping message processing.")
                    # Opcional: aqui poderíamos enviar uma mensagem informando que o número não está cadastrado.
                    continue

                conversation_id = _ensure_open_conversation(sb, contact_id)

                # Persiste a mensagem de entrada aqui, antes de processar
                try:
                    payload = {
                        'conversation_id': conversation_id,
                        'direction': 'in',
                        'type': msg.message_type,
                        'json_payload': msg.raw_message_payload,
                        'wa_message_id': msg.message_id,
                    }
                    sb.table('wa_messages').insert(payload).execute()
                    sb.table('wa_conversations').update({'last_message_at': 'now()'}).eq('id', conversation_id).execute()
                except Exception as e:
                    print(f'[WARN] Failed to persist inbound message: {repr(e)}')

                # Delega toda a lógica para o serviço de fluxo
                flow_service.process_message(conversation_id, contact_id, msg)

            except Exception as e:
                print(f'[ERROR] Failed to process message for contact {msg.sender_number}: {repr(e)}')
                # Continua para a próxima mensagem em caso de erro
                continue

        return JSONResponse(status_code=200, content={"received": True})
    except Exception as e:
        import traceback
        print(f"[ERROR] Unhandled exception in receive_update: {repr(e)}")
        print(traceback.format_exc())
        # Retorna 200 para evitar que o WhatsApp faça retentativas
        return JSONResponse(status_code=200, content={"received": True, "error": "internal server error"})


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

        # Nota: endpoint público para facilitar testes e UI.
        # Se desejar restringir, reative o check abaixo.
        # admin_token = os.getenv("ADMIN_TOKEN")
        # if admin_token and request.headers.get("x-admin-token") != admin_token:
        #     return JSONResponse(status_code=403, content={"error": "forbidden"})

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
# Admin: listar templates
# ========================
@router.get("/_admin/meta/templates")
async def list_meta_templates(request: Request, limit: int = 100, after: str | None = None):
    # Público para facilitar consumo pelo frontend

    try:
        import requests as _rq
        waba_id = os.getenv("WHATSAPP_WABA_ID") or ""
        token = os.getenv("WHATSAPP_TOKEN") or ""
        if not waba_id or not token:
            return JSONResponse(status_code=500, content={"error": "missing_waba_or_token"})
        url = f"https://graph.facebook.com/{os.getenv('WHATSAPP_GRAPH_VERSION','v19.0')}/{waba_id}/message_templates"
        params = {"limit": limit}
        if after:
            params["after"] = after
        headers = {"Authorization": f"Bearer {token}"}
        resp = _rq.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Normaliza para um formato simples {name, language, status, category}
        items = []
        for t in (data.get("data") or []):
            items.append({
                "name": t.get("name"),
                "language": t.get("language"),
                "status": t.get("status"),
                "category": t.get("category"),
            })
        return {"items": items, "paging": data.get("paging")}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/_admin/local/templates")
async def list_local_templates(request: Request):
    """
    Lista templates locais definidos no Supabase.
    Vamos usar a tabela wa_buttons_catalog, lendo metadados de template de meta (jsonb):
      meta.template_name, meta.lang_code, meta.components (opcional)
    Apenas entradas com meta.template_name serão consideradas.
    """
    # Endpoint público: sem necessidade de x-admin-token

    sb = get_supabase()
    q = (
        sb.table('wa_buttons_catalog')
        .select('id,title,response_type,response_text,next_state,next_buttons,template_name,template_lang,template_vars,metadata')
        .eq('active', True)
        .execute()
    )
    items = []
    for r in (q.data or []):
        tname = (r.get('template_name') or '').strip()
        if not tname:
            continue
        items.append({
            'id': r.get('id'),
            'title': r.get('title'),
            'template_name': tname,
            'lang_code': (r.get('template_lang') or 'pt_BR'),
            'components': r.get('template_vars') or [],
        })
    return {"items": items}


@router.get("/_admin/local/catalog")
async def get_full_local_catalog(request: Request):
    """
    Lista completa dos itens ativos do catálogo local (wa_buttons_catalog),
    incluindo campos de resposta (response_type/response_text) mesmo quando não há template.
    """
    sb = get_supabase()
    q = (
        sb.table('wa_buttons_catalog')
        .select('id,title,response_type,response_text,next_state,next_buttons,template_name,template_lang,template_vars,metadata')
        .eq('active', True)
        .execute()
    )
    items = q.data or []
    return {"items": items}


class LocalSendRequest(BaseModel):
    to: str
    id: str


@router.post("/_admin/local/send")
async def send_local_item(req: LocalSendRequest, request: Request):
    """
    Envia um item do catálogo local para o número informado.
    - Se houver template_name: envia template via Meta
    - Caso contrário e se response_type == 'text' e houver response_text: envia texto
    """
    to = _normalize_phone(req.to)
    sb = get_supabase()
    # Busca item
    item_q = (
        sb.table('wa_buttons_catalog')
        .select('id,title,response_type,response_text,template_name,template_lang,template_vars,next_buttons,metadata')
        .eq('id', req.id)
        .maybe_single()
        .execute()
    )
    item = item_q.data or {}
    if not item:
        return JSONResponse(status_code=404, content={"error": "catalog_item_not_found"})

    tname = (item.get('template_name') or '').strip()
    lang = (item.get('template_lang') or 'pt_BR').strip()
    if tname:
        # Envia como template
        client = WhatsAppClient()
        components = item.get('template_vars') or []
        try:
            resp = client.send_template(to=to, template=tname, language=lang, components=components)
            return JSONResponse(status_code=200, content={"ok": True, "mode": "template", "response": resp})
        except Exception as _e:
            import traceback as _tb
            print('[ERROR] local send template failed:', repr(_e))
            # incluir corpo retornado pela Meta se disponível
            try:
                import requests as _rq
                if isinstance(_e, _rq.exceptions.HTTPError) and getattr(_e, 'response', None) is not None:
                    return JSONResponse(status_code=502, content={
                        "error": "meta_api_error",
                        "http_status": _e.response.status_code,
                        "meta_body": _e.response.text,
                    })
            except Exception:
                pass
            print(_tb.format_exc())
            return JSONResponse(status_code=502, content={"error": "meta_api_error", "details": str(_e)})

    # Fallback: envia texto (com ou sem botões)
    if (item.get('response_type') or '').strip() == 'text' and (item.get('response_text') or '').strip():
        # Monta texto com placeholders usando metadata.mock_defaults
        text = item.get('response_text') or ''
        md = item.get('metadata') or {}
        defaults = {}
        try:
            if isinstance(md, str):
                import json as _json
                md = _json.loads(md)
            defaults = (md or {}).get('mock_defaults') or {}
        except Exception:
            defaults = {}
        for k, v in (defaults.items() if isinstance(defaults, dict) else []):
            text = text.replace(f"{{{{{k}}}}}", str(v))

        # Decide envio: com botões (interactive) quando next_buttons existir, senão texto simples
        buttons = item.get('next_buttons')
        if isinstance(buttons, str):
            try:
                import json as _json
                buttons = _json.loads(buttons)
            except Exception:
                buttons = None

        client = DemoFlowsService().client  # reusa client WhatsApp
        try:
            if buttons and isinstance(buttons, list) and len(buttons) > 0:
                resp = client.send_buttons(to, text, buttons)
                return JSONResponse(status_code=200, content={"ok": True, "mode": "text+buttons", "response": resp})
            else:
                resp = client.send_text(to, text)
                return JSONResponse(status_code=200, content={"ok": True, "mode": "text", "response": resp})
        except Exception as _e2:
            import traceback as _tb2
            print('[ERROR] local send text/buttons failed:', repr(_e2))
            # incluir corpo retornado pela Meta se disponível
            try:
                import requests as _rq
                if isinstance(_e2, _rq.exceptions.HTTPError) and getattr(_e2, 'response', None) is not None:
                    return JSONResponse(status_code=502, content={
                        "error": "send_text_buttons_failed",
                        "http_status": _e2.response.status_code,
                        "meta_body": _e2.response.text,
                    })
            except Exception:
                pass
            print(_tb2.format_exc())
            return JSONResponse(status_code=500, content={"error": "send_text_buttons_failed", "details": str(_e2)})

    # Webhook: roteia para serviços mockados
    if (item.get('response_type') or '').strip() == 'webhook':
        btn_id = item.get('id') or req.id
        try:
            if btn_id == 'view_summary':
                # reutiliza nosso fluxo mock
                return await flow_import_summary(ImportGenericBody(to=to))
            if btn_id == 'view_consumption':
                return await flow_import_consumption(ImportGenericBody(to=to))
            # fallback por metadata.service
            md = item.get('metadata') or {}
            try:
                if isinstance(md, str):
                    import json as _json
                    md = _json.loads(md)
            except Exception:
                md = {}
            service = (md or {}).get('service')
            if service == 'inventory.low_stock_list' or btn_id == 'view_low_stock':
                flows = DemoFlowsService()
                items = [
                    {'insumo': 'Mussarela', 'qtd_atual': 3, 'qtd_min': 8, 'unid': 'kg'},
                    {'insumo': 'Calabresa', 'qtd_atual': 2, 'qtd_min': 6, 'unid': 'kg'},
                ]
                resp = flows.send_low_stock_list(to, items)
                return JSONResponse(status_code=200, content={"ok": True, "mode": "webhook", "service": service or btn_id, "response": resp})
        except Exception as _e3:
            import traceback as _tb3
            print('[ERROR] local send webhook failed:', repr(_e3))
            print(_tb3.format_exc())
            return JSONResponse(status_code=500, content={"error": "webhook_failed", "details": str(_e3)})

    return JSONResponse(status_code=422, content={"error": "unsupported_catalog_item", "id": req.id})

@router.get("/_admin/local/templates_public")
async def list_local_templates_public(request: Request):
    """
    Espelho público do endpoint de templates locais para evitar bloqueios por token.
    """
    sb = get_supabase()
    q = (
        sb.table('wa_buttons_catalog')
        .select('id,title,response_type,response_text,next_state,next_buttons,template_name,template_lang,template_vars,metadata')
        .eq('active', True)
        .execute()
    )
    items = []
    for r in (q.data or []):
        tname = (r.get('template_name') or '').strip()
        if not tname:
            continue
        items.append({
            'id': r.get('id'),
            'title': r.get('title'),
            'template_name': tname,
            'lang_code': (r.get('template_lang') or 'pt_BR'),
            'components': r.get('template_vars') or [],
        })
    return {"items": items}


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


# ========================
# Admin debug: simular clique de botão
# ========================
class SimulateClickRequest(BaseModel):
    to: str
    btn_id: str


@router.post("/_admin/debug/simulate-click")
async def simulate_click(req: SimulateClickRequest, request: Request):
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and request.headers.get("x-admin-token") != admin_token:
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    to = _normalize_phone(req.to)
    btn_id = (req.btn_id or '').strip()
    print("[DEBUG][WA][SIM] simulate-click:", {"to": to, "btn_id": btn_id})
    flows = DemoFlowsService()
    try:
        if btn_id == 'view_summary':
            summary = {
                'valor_pizzas': '4.520,00', 'qtd_pizzas': 180,
                'valor_bebidas': '1.240,00', 'qtd_bebidas': 210,
                'top_pizzas': [{'nome': f'Pizza {i}', 'qtd': 30-i} for i in range(1,11)],
                'top_bebidas': [{'nome': f'Bebida {i}', 'qtd': 50-i} for i in range(1,6)],
            }
            resp = flows.send_sales_summary(to, summary)
            import asyncio as _aio
            _aio.create_task(flows.ask_consumption_after_delay(to, 10))
            return JSONResponse(status_code=200, content={"ok": True, "routed": btn_id, "resp": resp})
        elif btn_id == 'view_consumption':
            items = [{'nome': f'Insumo {i}', 'qtd': 10*i, 'unid': 'un'} for i in range(1,11)]
            resp = flows.send_consumption_list(to, items)
            return JSONResponse(status_code=200, content={"ok": True, "routed": btn_id, "resp": resp})
        elif btn_id == 'view_low_stock':
            items = [
                {'insumo': 'Mussarela', 'qtd_atual': 3, 'qtd_min': 8, 'unid': 'kg'},
                {'insumo': 'Calabresa', 'qtd_atual': 2, 'qtd_min': 6, 'unid': 'kg'},
                {'insumo': 'Molho', 'qtd_atual': 5, 'qtd_min': 10, 'unid': 'kg'},
                {'insumo': 'Farinha', 'qtd_atual': 20, 'qtd_min': 35, 'unid': 'kg'},
                {'insumo': 'Refrigerante Lata', 'qtd_atual': 12, 'qtd_min': 24, 'unid': 'un'},
            ]
            resp = flows.send_low_stock_list(to, items)
            return JSONResponse(status_code=200, content={"ok": True, "routed": btn_id, "resp": resp})
        elif btn_id == 'make_purchase_list':
            resp = flows.client.send_text(to, 'Ok! Vou gerar a lista de compras sugerida e te envio em instantes.')
            return JSONResponse(status_code=200, content={"ok": True, "routed": btn_id, "resp": resp})
        elif btn_id == 'view_cmv_analysis':
            data = {
                'cmv_esperado': 28.0, 'cmv_atual': 32.5, 'desvio_pct': 4.5,
                'contribuintes': [
                    {'insumo': 'Mussarela', 'impacto_pct': 1.8},
                    {'insumo': 'Calabresa', 'impacto_pct': 1.2},
                    {'insumo': 'Tomate', 'impacto_pct': 0.9},
                ]
            }
            resp = flows.send_cmv_analysis(to, data)
            return JSONResponse(status_code=200, content={"ok": True, "routed": btn_id, "resp": resp})
        elif btn_id == 'view_cmv_actions':
            resp = flows.client.send_text(to, 'Ações recomendadas: 1) revisar porcionamento de queijos; 2) ajustar preço das bebidas; 3) auditar perdas na abertura.')
            return JSONResponse(status_code=200, content={"ok": True, "routed": btn_id, "resp": resp})
        else:
            return JSONResponse(status_code=400, content={"ok": False, "error": "btn_id desconhecido", "btn_id": btn_id})
    except Exception as _e_sim:
        import traceback as _tb
        print('[ERROR][WA][SIM] simulate-click failed:', repr(_e_sim))
        # Se for HTTPError do requests, inclui corpo retornado pela Meta
        try:
            import requests as _rq
            if isinstance(_e_sim, _rq.exceptions.HTTPError) and getattr(_e_sim, 'response', None) is not None:
                meta_status = _e_sim.response.status_code
                meta_body = _e_sim.response.text
                return JSONResponse(status_code=502, content={
                    "ok": False,
                    "http_status": meta_status,
                    "meta_body": meta_body,
                    "error": str(_e_sim),
                })
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"ok": False, "error": str(_e_sim), "traceback": _tb.format_exc()})


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
