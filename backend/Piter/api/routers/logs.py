from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import os

router = APIRouter(tags=["Logs"])

@router.get("/_admin/logs/stream")
async def stream_logs():
    """
    Stream dos logs do sistema em tempo real
    """
    log_file = "/var/log/piter-api.log"  # Ajuste para o caminho real dos seus logs
    
    async def log_generator():
        with open(log_file, 'r') as f:
            f.seek(0, 2)  # Vai para o final do arquivo
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                yield f"data: {line}\n\n"
    
    return StreamingResponse(log_generator(), media_type="text/event-stream")
