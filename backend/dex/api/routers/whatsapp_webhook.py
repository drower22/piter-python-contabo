from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["WhatsApp"], prefix="/_webhooks/whatsapp")


@router.get("/")
async def verify(hub_mode: str | None = None, hub_challenge: str | None = None, hub_verify_token: str | None = None):
    # Simples verificação (configurar VERIFY_TOKEN no painel Meta e aqui depois)
    if hub_mode == "subscribe" and hub_challenge:
        return PlainTextResponse(content=hub_challenge)
    return PlainTextResponse(status_code=403, content="forbidden")


@router.post("/")
async def receive_update(request: Request):
    # Stub inicial: só lê o JSON e retorna 200
    body = await request.json()
    # Futuro: extrair messages, detectar mídia, baixar via Graph API e inserir em received_files
    return {"received": True, "body_keys": list(body.keys())}
