from __future__ import annotations
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import logging
from typing import Optional

router = APIRouter(tags=["Logs"])

# ==============================
# In-process async logging queue
# ==============================
_LOG_QUEUE: asyncio.Queue[str] | None = None


class _QueueHandler(logging.Handler):
    """Logging handler that pushes formatted log records to an asyncio.Queue."""

    def __init__(self, queue_supplier):
        super().__init__()
        self._queue_supplier = queue_supplier

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            q = self._queue_supplier()
            if q is not None:
                # Put nowait; drop if full to avoid blocking the app
                try:
                    q.put_nowait(msg)
                except Exception:
                    pass
        except Exception:
            # Never raise from logging
            pass


def _ensure_log_queue() -> asyncio.Queue[str]:
    global _LOG_QUEUE
    if _LOG_QUEUE is None:
        _LOG_QUEUE = asyncio.Queue(maxsize=1000)
        # Attach handler to root logger once
        root = logging.getLogger()
        handler = _QueueHandler(lambda: _LOG_QUEUE)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        root.addHandler(handler)
        # If root has no level set, default to INFO so we capture prints wrapped as logging elsewhere
        if root.level == logging.NOTSET:
            root.setLevel(logging.INFO)
    return _LOG_QUEUE


async def _journalctl_stream(service_name: str):
    """Yield journalctl lines as SSE messages. Requires systemd access."""
    cmd = [
        "journalctl",
        "-u",
        service_name,
        "-f",
        "-n",
        "0",
        "--no-pager",
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        while True:
            if process.stdout is None:
                await asyncio.sleep(0.2)
                continue
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8", errors="ignore").strip()
            yield f"data: {line}\n\n"
    except FileNotFoundError:
        yield "data: WARN: journalctl não disponível neste ambiente. Usando logs internos da aplicação.\n\n"
    except Exception as e:
        yield f"data: ERRO: Falha no journalctl: {e}\n\n"


async def _inprocess_stream():
    """Yield messages from the in-process async logging queue as SSE messages."""
    q = _ensure_log_queue()
    # Emit a header message immediately (helps CDNs like Cloudflare keep the connection open)
    yield "data: [startup] Streaming de logs internos iniciado.\n\n"
    while True:
        try:
            msg = await asyncio.wait_for(q.get(), timeout=2.5)
            yield f"data: {msg}\n\n"
        except asyncio.TimeoutError:
            # Heartbeat para manter conexão viva
            yield "data: [heartbeat]\n\n"


@router.get("/_admin/logs/stream")
async def stream_logs(request: Request, source: Optional[str] = None):
    """
    Stream de logs via SSE.
    - Por padrão (source != 'journal'): usa uma fila interna assíncrona que coleta logs da aplicação.
    - Se source == 'journal': tenta usar journalctl na unidade informada via query ?unit=piter-api (default: piter-api).
    """

    async def log_generator():
        # Escolha da fonte
        if source == "journal":
            unit = request.query_params.get("unit", "piter-api")
            async for line in _journalctl_stream(unit):
                yield line
        else:
            async for line in _inprocess_stream():
                yield line

    headers = {
        # Prevent buffering at reverse proxies
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        # For some reverse proxies like nginx
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(log_generator(), media_type="text/event-stream", headers=headers)


@router.post("/_admin/logs/ping")
async def logs_ping():
    """Gera uma linha de log imediatamente para validar o stream in-process."""
    q = _ensure_log_queue()
    logging.getLogger("piter.logs").info("[ping] teste de log pelo endpoint /_admin/logs/ping")
    # Também tenta empurrar uma linha direta, caso o handler ainda não esteja ligado
    try:
        q.put_nowait("[ping] linha enviada diretamente para a fila de logs")
    except Exception:
        pass
    return {"ok": True}
