import os
import sys
import subprocess
import traceback
import re
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

# Ajuste de caminho para permitir importações tanto via 'backend.*' quanto locais
_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_FILE_DIR, '..'))
for _p in (_PROJECT_ROOT, _THIS_FILE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    from backend.Piter.api.routers import health as health_router
    from backend.Piter.api.routers import forms as forms_router
    from backend.Piter.api.routers import whatsapp_webhook as wa_webhook_router
    from backend.Piter.api.routers import logs as logs_router
except ModuleNotFoundError:
    # Fallback quando o pacote raiz 'backend' não está no PYTHONPATH
    from Piter.api.routers import health as health_router
    from Piter.api.routers import forms as forms_router
    from Piter.api.routers import whatsapp_webhook as wa_webhook_router
    from Piter.api.routers import logs as logs_router

# Importa router do SQL Agent (pode não existir em alguns ambientes)
_SQLAGENT_IMPORT_ERR = None
try:
    from sqlagent.api.routes import router as sqlagent_router  # type: ignore
    print("[DEBUG] SQLAgent importado com sucesso.")
except Exception as _e:  # capture and log root cause
    _SQLAGENT_IMPORT_ERR = _e
    sqlagent_router = None  # type: ignore
    import traceback as _tb
    print("[WARN] Falha ao importar SQLAgent: ", repr(_e))
    print(_tb.format_exc())

print("[DEBUG] Iniciando Piter API...")

# Carrega as variáveis de ambiente
# 1) Carrega .env da pasta onde o processo é iniciado (raiz do projeto)
load_dotenv()
# 2) Carrega também backend/.env (baseado no caminho deste arquivo)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ENV = os.path.join(_THIS_DIR, ".env")
load_dotenv(dotenv_path=_BACKEND_ENV, override=False)

# Configuração do Supabase (não-fatal para permitir /health mesmo sem env)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print(f"[DEBUG] SUPABASE_URL: {SUPABASE_URL if SUPABASE_URL else '[NÃO DEFINIDO]'}")
if SUPABASE_KEY:
    print(f"[DEBUG] SUPABASE_KEY: {SUPABASE_KEY[:6]}... (ocultado)")
else:
    print(f"[DEBUG] SUPABASE_KEY: [NÃO DEFINIDO]")

_SUPABASE_READY = bool(SUPABASE_URL and SUPABASE_KEY)
if not _SUPABASE_READY:
    print("[WARN] SUPABASE_URL/SUPABASE_KEY ausentes. Endpoints que dependem de Supabase podem falhar; /health continuará funcionando.")
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # type: ignore[name-defined]
        print("[DEBUG] Cliente Supabase inicializado.")
    except Exception as _sup_e:
        print("[WARN] Falha ao inicializar cliente Supabase no boot:", repr(_sup_e))
        _SUPABASE_READY = False

# Cria a aplicação FastAPI
app = FastAPI(
    title="Piter API",
    description="Agente Piter: consultas SQL no Supabase e notificações via WhatsApp.",
    version="1.0.0"
)
print("[DEBUG] FastAPI inicializado.")

# Habilita CORS para permitir que um frontend local consuma a API (ex.: Railway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

# Fallback de CORS para ambientes onde o proxy/CDN remove cabeçalhos do CORSMiddleware
@app.middleware("http")
async def _ensure_cors_headers(request: Request, call_next):
    # Responde imediatamente a OPTIONS (preflight) com cabeçalhos CORS
    if request.method == "OPTIONS":
        resp = Response(status_code=200)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "*"
        resp.headers["Access-Control-Expose-Headers"] = "*"
        return resp

    response = await call_next(request)
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    response.headers.setdefault("Access-Control-Allow-Headers", "*")
    response.headers.setdefault("Access-Control-Expose-Headers", "*")
    return response

# Inclui routers do agente Piter
app.include_router(health_router.router)
app.include_router(forms_router.router)
app.include_router(wa_webhook_router.router)
app.include_router(logs_router.router)
if sqlagent_router:
    app.include_router(sqlagent_router)
    print("[DEBUG] Router do SQLAgent montado: rotas /qa e /v1/sql habilitadas.")
else:
    print("[WARN] Router do SQLAgent NÃO foi montado. Motivo: ", repr(_SQLAGENT_IMPORT_ERR))

# Servir frontend estático (somente se existir)
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_FRONTEND_DIR = os.path.abspath(os.path.join(_BACKEND_DIR, '..', 'frontend'))
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
    print(f"[DEBUG] Frontend montado em /frontend a partir de {_FRONTEND_DIR}")
else:
    print(f"[WARN] Diretório de frontend não encontrado: {_FRONTEND_DIR}. Rotas estáticas não serão montadas.")

def _ensure_unique_path(supabase_client: Client, bucket: str, user_id: str, filename: str) -> str:
    """Retorna um caminho único dentro do bucket para evitar sobrescrita.

    Se já existir um arquivo com o mesmo nome em `user_id/`, gera um nome com prefixo timestamp.
    """
    import datetime as _dt

    folder = user_id.strip("/")
    base_name = filename.strip("/")

    # Tenta listar arquivos na pasta do usuário e verificar colisão exata do nome
    try:
        entries = supabase_client.storage.from_(bucket).list(path=folder)
        existing_names = {e.get('name') for e in (entries or []) if isinstance(e, dict)}
    except Exception:
        # Se a listagem falhar por qualquer motivo, faz fallback para nome com timestamp
        existing_names = set()

    final_name = base_name
    if base_name in existing_names:
        ts = _dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        # Ex.: 20250809-181010_nome.xlsx
        final_name = f"{ts}_" + base_name

    return f"{folder}/{final_name}"

@app.get("/", tags=["Status"], summary="Verifica se a API está online")
def read_root():
    """Endpoint raiz para verificar a saúde da API."""
    return {"status": "ok", "message": "Bem-vindo à Piter API!"}

@app.post("/upload/planilha", tags=["Uploads"], summary="[Desativado] Upload via bucket")
async def upload_planilha(
    file: UploadFile = File(None),
    data: UploadFile = File(None),
    user_id: str = Form(None),
    account_id: str = Form(None),
    filename: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    return JSONResponse(status_code=410, content={"error": "Endpoint desativado no Piter. O agente opera via consultas SQL, sem upload/buckets."})

# =======================
# Endpoints Frontend Aux
# =======================

@app.post("/frontend/upload/financeiro", tags=["Frontend"], summary="[Desativado] Upload financeiro via script")
async def frontend_upload_financeiro(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    file_id: str = Form(None)
):
    return JSONResponse(status_code=410, content={"error": "Endpoint desativado no Piter. Sem uploads/buckets/scripts."})

@app.post("/frontend/upload-process/conciliacao", tags=["Frontend"], summary="[Desativado] Upload conciliação e processamento")
async def frontend_upload_process_conciliacao(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    account_id: str = Form(...),
    file_id: str = Form(None)
):
    return JSONResponse(status_code=410, content={"error": "Endpoint desativado no Piter. Sem uploads/buckets/scripts."})

import requests  # Adicionado para download de arquivos via URL
from pydantic import BaseModel
import tempfile
import os

"""
Importação OPCIONAL de módulos de scripts legados.
Em muitos ambientes do Piter, esses módulos não existem e os endpoints correspondentes estão desativados.
Portanto, a ausência desses módulos não deve derrubar a API.
"""
try:
    from backend.scripts.process_report import (
        processar_relatorio_financeiro,
        init_supabase_client as init_processor_supabase,
        SupabaseLogger,
    )
    from backend.scripts.process_conciliation import (
        process_conciliation_file,
        update_file_status,
    )
    print("[DEBUG] Módulos backend.scripts.* importados com sucesso.")
except Exception as _e_backend_scripts:
    try:
        from scripts.process_report import (
            processar_relatorio_financeiro,
            init_supabase_client as init_processor_supabase,
            SupabaseLogger,
        )
        from scripts.process_conciliation import (
            process_conciliation_file,
            update_file_status,
        )
        print("[DEBUG] Módulos scripts.* importados com sucesso.")
    except Exception as _e_scripts:
        print("[WARN] Módulos de scripts não encontrados. Endpoints relacionados permanecem desativados.")
        import traceback as _tb
        print(_tb.format_exc())
        # Cria stubs para evitar NameError onde são referenciados mais abaixo (endpoints já retornam 410)
        def processar_relatorio_financeiro(*args, **kwargs):
            raise RuntimeError("processar_relatorio_financeiro indisponível neste build")
        def init_processor_supabase(*args, **kwargs):
            raise RuntimeError("init_processor_supabase indisponível neste build")
        class SupabaseLogger:
            def __init__(self, *a, **k): ...
            def log(self, *a, **k): ...
            def flush(self, *a, **k): ...
        def process_conciliation_file(*args, **kwargs):
            raise RuntimeError("process_conciliation_file indisponível neste build")
        def update_file_status(*args, **kwargs):
            return None

@app.post("/upload/planilha-url", tags=["Uploads"], summary="[Desativado] Upload via URL para Storage")
async def upload_planilha_url(
    request: Request,
    file_url: str = Form(..., description="URL do arquivo de planilha (desativado)."),
    user_id: str = Form(..., description="ID (desativado)."),
    filename: str = Form(..., description="Nome do arquivo (desativado)."),
    tipo: str = Form(..., description="Tipo (desativado).")
):
    return JSONResponse(status_code=410, content={"error": "Endpoint desativado no Piter. Sem uploads/buckets/scripts."})

class ProcessRequest(BaseModel):
    file_id: str
    storage_path: str

class ProcessFinanceiroRequest(BaseModel):
    file_id: str

def run_processing_financeiro(file_id: str):
    """Função que executa o processamento FINANCEIRO em background."""
    # Inicializa um cliente supabase e logger para este processo
    supabase_processor = init_processor_supabase()
    logger = SupabaseLogger(supabase_processor)

    try:
        print(f"[PRINT] Iniciando processamento para file_id: {file_id}")
        # 1. Buscar detalhes do arquivo no banco
        response = supabase_processor.table('received_files').select('storage_path, account_id').eq('id', file_id).single().execute()
        print(f"[PRINT] Resposta do select em received_files: {response}")
        record = response.data
        if not record:
            print(f"[PRINT] Registro de arquivo com ID {file_id} não encontrado.")
            logger.log("ERROR", f"Registro de arquivo com ID {file_id} não encontrado.")
            logger.flush()
            return

        storage_path = record.get('storage_path')
        account_id = record.get('account_id')
        print(f"[PRINT] storage_path do banco: {storage_path}")
        print(f"[PRINT] account_id do banco: {account_id}")
        if not storage_path:
            print(f"[PRINT] storage_path está vazio para file_id {file_id}")
            logger.log("CRITICAL", f"O campo 'storage_path' está vazio no banco para o file_id {file_id}.")
            logger.flush()
            return

        logger.log("INFO", f"[DEBUG] storage_path obtido do banco: '{storage_path}'")
        print(f"[PRINT] [DEBUG] storage_path obtido do banco: '{storage_path}'")

        # Correção para caminhos que possam começar com '/'
        clean_storage_path = storage_path.lstrip('/')
        path_parts = clean_storage_path.split('/')
        print(f"[PRINT] path_parts extraído: {path_parts}")

        if len(path_parts) < 2:
            print(f"[PRINT] storage_path '{storage_path}' é inválido (partes: {path_parts})")
            logger.log("CRITICAL", f"storage_path '{storage_path}' é inválido e não contém bucket/caminho.")
            logger.flush()
            return

        bucket_name = path_parts[0]
        path_in_bucket = '/'.join(path_parts[1:])
        print(f"[PRINT] bucket_name: {bucket_name}")
        print(f"[PRINT] path_in_bucket: {path_in_bucket}")

        logger.log("INFO", f"[DEBUG] Tentando baixar de bucket: '{bucket_name}' com o caminho: '{path_in_bucket}'")
        print(f"[PRINT] [DEBUG] Tentando baixar de bucket: '{bucket_name}' com o caminho: '{path_in_bucket}'")

        # 2. Baixar o arquivo do Supabase Storage
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                print(f"[PRINT] Antes do download do arquivo do Storage...")
                file_content = supabase_processor.storage.from_(bucket_name).download(path=path_in_bucket)
                print(f"[PRINT] Download realizado com sucesso, tamanho: {len(file_content) if file_content else 'NULO'} bytes")
                tmp_file.write(file_content)
                temp_file_path = tmp_file.name
        except Exception as download_exc:
            print(f"[PRINT] ERRO AO BAIXAR ARQUIVO: {download_exc}")
            logger.log("CRITICAL", f"ERRO AO BAIXAR ARQUIVO: {download_exc}", context={"traceback": traceback.format_exc()})
            raise

        # 3. Chamar a função de processamento financeiro
        print(f"[PRINT] Chamando processar_relatorio_financeiro com temp_file_path: {temp_file_path}")
        processar_relatorio_financeiro(supabase_processor, logger, temp_file_path, file_id, account_id)
        print(f"[PRINT] processar_relatorio_financeiro finalizado!")

    except Exception as e:
        error_message = f"Erro no processamento em background para file_id {file_id}: {e}"
        print(f"[PRINT] {error_message}")
        logger.log("CRITICAL", error_message, context={"traceback": traceback.format_exc()})
    finally:
        # 4. Limpar o arquivo temporário e o logger
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            print(f"[PRINT] Removendo arquivo temporário: {temp_file_path}")
            os.remove(temp_file_path)
        logger.flush()


@app.post("/processar-planilha-financeiro", tags=["Processamento"], summary="[Desativado] Processamento financeiro")
async def processar_planilha_financeiro_endpoint(process_request: ProcessFinanceiroRequest, background_tasks: BackgroundTasks):
    return JSONResponse(status_code=410, content={"error": "Processamento via scripts desativado no Piter."})

def run_processing_conciliacao(file_id: str, storage_path: str):
    """Função segura que executa o processamento de CONCILIAÇÃO em background."""
    supabase_processor = None
    logger = None
    temp_file_path = None

    try:
        print(f"[CONCILIATION_TASK] Iniciando para file_id: {file_id}")
        supabase_processor = init_processor_supabase()
        logger = SupabaseLogger(supabase_processor)
        print(f"[CONCILIATION_TASK] Logger inicializado. Buscando account_id...")

        # Busca o ID da conta associado ao arquivo.
        response = supabase_processor.table('received_files').select('account_id').eq('id', file_id).single().execute()
        if not response.data or not response.data.get('account_id'):
            print(f"[CONCILIATION_TASK] ERRO: account_id não encontrado para file_id {file_id}. Resposta: {response.data}")
            raise ValueError(f"Metadados (account_id) para file_id {file_id} não encontrados.")
        account_id = response.data['account_id']
        print(f"[CONCILIATION_TASK] account_id {account_id} encontrado com sucesso.")

        logger.set_context(file_id=file_id, account_id=account_id)

        # Faz o download do arquivo para um local temporário
        logger.log('INFO', f'Iniciando download do arquivo de conciliação: {storage_path}')
        print(f"[CONCILIATION_TASK] Preparando para download. Storage path: {storage_path}")
        path_parts = storage_path.lstrip('/').split('/')
        bucket_name = path_parts[0]
        path_in_bucket = '/'.join(path_parts[1:])
        print(f"[CONCILIATION_TASK] Tentando download do bucket: '{bucket_name}', path: '{path_in_bucket}'")
        
        file_content = supabase_processor.storage.from_(bucket_name).download(path=path_in_bucket)
        print(f"[CONCILIATION_TASK] Download concluído. Bytes recebidos: {len(file_content) if file_content else '0'}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name
        del file_content
        logger.log('INFO', f'Arquivo salvo temporariamente em: {temp_file_path}')

        # Chama diretamente a função de processamento, que agora faz parte da mesma aplicação
        update_file_status(logger, supabase_processor, file_id, 'processing')
        logger.log('INFO', 'Iniciando a execução direta da função de processamento de conciliação.')

        process_conciliation_file(
            logger=logger,
            supabase_client=supabase_processor,
            file_path=temp_file_path,
            file_id=file_id,
            account_id=account_id
        )

        logger.log('INFO', 'Função de processamento de conciliação concluída com sucesso.')

    except Exception as e:
        error_message = f"Erro no orquestrador de processamento de conciliação: {e}"
        tb_str = traceback.format_exc()
        if logger:
            logger.log('CRITICAL', error_message, context={"traceback": tb_str})
            update_file_status(logger, supabase_processor, file_id, 'error', error_message)
        else:
            print(f"ERRO CRÍTICO (logger indisponível): {error_message}", file=sys.stderr)
            print(tb_str, file=sys.stderr)
            
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"INFO: Arquivo temporário {temp_file_path} removido.")
        if logger:
            logger.flush()

@app.post("/processar-planilha-conciliacao", tags=["Processamento"], summary="[Desativado] Processamento conciliação")
async def processar_planilha_conciliacao_endpoint(process_request: ProcessRequest, background_tasks: BackgroundTasks):
    return JSONResponse(status_code=410, content={"error": "Processamento via scripts desativado no Piter."})
