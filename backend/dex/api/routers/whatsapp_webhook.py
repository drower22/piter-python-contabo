import os
from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from ...infra.supabase import get_supabase
from ...infra.whatsapp import WhatsAppClient
from ...services.whatsapp_flow import handle_message, reply_via_whatsapp

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
    }).execute()
    return ins.data[0]['id']


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

        for m in messages:
            wa_from = m.get('from')  # e.g., "5511999999999"
            wa_id = m.get('id')
            msg_type = m.get('type')
            # Normaliza para formato +<cc><number>
            to_number = f"+{wa_from}" if wa_from and not wa_from.startswith('+') else wa_from

            contact_id = _ensure_contact(sb, wa_number=to_number, profile_name=profile_name)
            conversation_id = _ensure_open_conversation(sb, contact_id)

            _insert_message(sb, conversation_id, 'in', msg_type, m, wa_id)

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


@router.post("/send-template")
async def send_template(request: Request):
    """
    Envia um template aprovado da Meta para um número real.
    Segurança: requer header X-Admin-Token igual a ADMIN_TOKEN no ambiente.

    Body JSON exemplos:
    - {"to": "5511999999999", "template": "nome_do_template", "language": "pt_BR", "components": [...]}
    - {"contact_id": "<uuid>", "template": "nome", "language": "pt_BR"}
    """
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and request.headers.get("x-admin-token") != admin_token:
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    body = await request.json()
    to = (body.get("to") or "").strip()
    contact_id = (body.get("contact_id") or "").strip()
    user_id = (body.get("user_id") or "").strip()
    user_number_normalized = (body.get("user_number_normalized") or "").strip()
    template = (body.get("template") or "").strip()
    language = (body.get("language") or "pt_BR").strip()
    components = body.get("components")

    if not template:
        return JSONResponse(status_code=400, content={"error": "template é obrigatório"})

    if not to and not contact_id and not user_id and not user_number_normalized:
        return JSONResponse(status_code=400, content={"error": "informe 'to' ou 'contact_id' ou 'user_id' ou 'user_number_normalized'"})

    sb = None
    if not to and contact_id:
        sb = sb or get_supabase()
        q = sb.table('wa_contacts').select('whatsapp_number').eq('id', contact_id).maybe_single().execute()
        data = q.data or {}
        to = (data.get('whatsapp_number') or '').strip()
        if not to:
            return JSONResponse(status_code=404, content={"error": "contact_id não encontrado ou sem whatsapp_number"})

    if not to and user_id:
        sb = sb or get_supabase()
        q = sb.table('users').select('whatsapp_number_normalized').eq('id', user_id).maybe_single().execute()
        data = q.data or {}
        to = (data.get('whatsapp_number_normalized') or '').strip()
        if not to:
            return JSONResponse(status_code=404, content={"error": "user_id não encontrado ou sem whatsapp_number_normalized"})

    if not to and user_number_normalized:
        to = user_number_normalized

    try:
        client = WhatsAppClient()
        resp = client.send_template(to=to, template=template, language=language, components=components)
        return JSONResponse(status_code=200, content={"ok": True, "to": to, "response": resp})
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.get("/_admin/users")
async def list_users(request: Request):
    """
    Lista usuários com whatsapp_number_normalized preenchido para seleção no frontend.
    Segurança: requer header X-Admin-Token igual a ADMIN_TOKEN.
    """
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and request.headers.get("x-admin-token") != admin_token:
        return JSONResponse(status_code=403, content={"error": "forbidden"})

    sb = get_supabase()
    q = (
        sb.table('users')
        .select('id,user_name,whatsapp_number_normalized')
        .is_('whatsapp_number_normalized', 'not.null')
        .order('created_at', desc=True)
        .limit(200)
        .execute()
    )
    data = q.data or []
    # Filtra nulos por precaução
    data = [
        {
            'id': r.get('id'),
            'user_name': r.get('user_name') or '',
            'whatsapp_number_normalized': r.get('whatsapp_number_normalized') or ''
        }
        for r in data if r.get('whatsapp_number_normalized')
    ]
    return JSONResponse(status_code=200, content={"items": data})
