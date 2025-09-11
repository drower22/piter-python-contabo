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
    async def log_generator():
        # Comando para seguir os logs do serviço piter-api em tempo real
        cmd = ["journalctl", "-u", "piter-api", "-f", "-n", "0", "--no-pager"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                if process.stdout:
                    line_bytes = await process.stdout.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    # Formata para Server-Sent Events (SSE)
                    yield f"data: {line}\n\n"
                else:
                    await asyncio.sleep(0.1)

        except FileNotFoundError:
            yield "data: ERRO: comando 'journalctl' não encontrado. O serviço de log não pode iniciar.\n\n"
        except Exception as e:
            yield f"data: ERRO: Falha ao ler logs do journalctl: {e}\n\n"
        finally:
            if 'process' in locals() and process.returncode is None:
                process.terminate()
                await process.wait()
    
    return StreamingResponse(log_generator(), media_type="text/event-stream")
