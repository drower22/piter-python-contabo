import os
import sys
import subprocess
import traceback
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv

print("[DEBUG] Iniciando API iFood Sales Concierge...")

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print(f"[DEBUG] SUPABASE_URL: {SUPABASE_URL if SUPABASE_URL else '[NÃO DEFINIDO]'}")
if SUPABASE_KEY:
    print(f"[DEBUG] SUPABASE_KEY: {SUPABASE_KEY[:6]}... (ocultado)")
else:
    print(f"[DEBUG] SUPABASE_KEY: [NÃO DEFINIDO]")

# Validação inicial das variáveis de ambiente
if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERRO] SUPABASE_URL e SUPABASE_KEY são obrigatórios no ambiente.")
    raise ValueError("SUPABASE_URL e SUPABASE_KEY são obrigatórios no ambiente.")
else:
    print("[DEBUG] Variáveis de ambiente carregadas com sucesso.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("[DEBUG] Cliente Supabase inicializado.")

# Cria a aplicação FastAPI
app = FastAPI(
    title="iFood Sales Concierge API",
    description="API para processar e gerenciar planilhas de vendas.",
    version="1.0.0"
)
print("[DEBUG] FastAPI inicializado.")

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
    return {"status": "ok", "message": "Bem-vindo à API do iFood Sales Concierge!"}

@app.post("/upload/planilha", tags=["Uploads"], summary="Faz upload de uma planilha para o Supabase Storage")
async def upload_planilha(
    file: UploadFile = File(None, description="Arquivo de planilha (xlsx, csv) para upload."),
    data: UploadFile = File(None, description="Alias de arquivo (caso a ferramenta envie como 'data')."),
    user_id: str = Form(None, description="ID do usuário/conta."),
    account_id: str = Form(None, description="Alias para ID da conta (equivalente a user_id)."),
    filename: str = Form(..., description="Nome original do arquivo a ser salvo no bucket."),
    background_tasks: BackgroundTasks = None
):
    """
    Recebe um arquivo de planilha via formulário multipart e o envia para o bucket 'financeiro' no Supabase Storage.
    O caminho no bucket será estruturado como: `user_id/filename`.
    """
    try:
        bucket_name = "financeiro"
        # Gera caminho único (evita sobrescrever se já existir arquivo com mesmo nome)
        if file:
            upload_file = file
        elif data:
            upload_file = data
        else:
            raise HTTPException(status_code=400, detail="Nenhum arquivo fornecido.")

        if user_id:
            normalized_user_id = user_id
        elif account_id:
            normalized_user_id = account_id
        else:
            raise HTTPException(status_code=400, detail="Nenhum ID de usuário ou conta fornecido.")

        path_in_bucket = _ensure_unique_path(supabase, bucket_name, normalized_user_id, filename)

        # Lê o conteúdo do arquivo em bytes
        contents = await upload_file.read()

        # Faz o upload para o Supabase Storage SEM sobrescrever automaticamente
        response = supabase.storage.from_(bucket_name).upload(
            path=path_in_bucket,
            file=contents,
            file_options={"cache-control": "3600", "upsert": "false"}
        )

        # Salve o storage_path exatamente como foi salvo (pode ter prefixo de timestamp)
        storage_path = f"{bucket_name}/{path_in_bucket}"

        return JSONResponse(
            status_code=200,
            content={
                "message": "Upload realizado com sucesso!",
                "path": storage_path
            }
        )
    except Exception as e:
        # Em caso de erro, retorna uma resposta com status 500
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro no upload: {str(e)}")

import requests  # Adicionado para download de arquivos via URL
from pydantic import BaseModel
import tempfile
import os

# Importa a lógica de processamento do script
# Este endpoint é EXCLUSIVO para o processamento do relatório financeiro do iFood.
from scripts.process_report import processar_relatorio_financeiro, init_supabase_client as init_processor_supabase, SupabaseLogger
from scripts.process_conciliation import process_conciliation_file, update_file_status

@app.post("/upload/planilha-url", tags=["Uploads"], summary="Faz upload de uma planilha a partir de uma URL para o Supabase Storage")
async def upload_planilha_url(
    request: Request,
    file_url: str = Form(..., description="URL do arquivo de planilha (xlsx, csv) para upload."),
    user_id: str = Form(..., description="ID do usuário ou conta que está enviando o arquivo."),
    filename: str = Form(..., description="Nome original do arquivo a ser salvo no bucket."),
    tipo: str = Form(..., description="Tipo da planilha: financeiro ou conciliacao.")
):
    """
    Faz o download do arquivo da URL fornecida e envia para o bucket 'financeiro' no Supabase Storage.
    O caminho no bucket será estruturado como: `tipo/user_id/filename`, onde tipo pode ser 'financeiro' ou 'conciliacao'.
    Se o header Authorization for enviado, ele será repassado na requisição de download.
    """
    try:
        tipo = tipo.lower().strip()
        if tipo not in ["financeiro", "conciliacao"]:
            return JSONResponse(status_code=400, content={"error": "Tipo inválido. Use 'financeiro' ou 'conciliacao'."})
        bucket_name = tipo  # bucket = financeiro ou conciliacao
        # Gera caminho único para evitar sobrescrita
        path_in_bucket = _ensure_unique_path(supabase, bucket_name, user_id, filename)

        # Busca o header Authorization, se enviado
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header

        # Faz o download do arquivo, repassando o header Authorization se existir
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        contents = response.content

        # Faz o upload para o Supabase Storage SEM sobrescrever automaticamente
        upload_response = supabase.storage.from_(bucket_name).upload(
            path=path_in_bucket,
            file=contents,
            file_options={"cache-control": "3600", "upsert": "false"}
        )

        # O path retornado deve ser o LÓGICO, refletindo o nome final salvo
        storage_path_for_db = f"{tipo}/{path_in_bucket}"

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Upload realizado com sucesso via URL para {tipo}!",
                "path": storage_path_for_db
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

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


@app.post("/processar-planilha-financeiro", tags=["Processamento"], summary="Inicia o processamento de uma planilha FINANCEIRA em background")
async def processar_planilha_financeiro_endpoint(process_request: ProcessFinanceiroRequest, background_tasks: BackgroundTasks):
    """
    [FINANCEIRO] Recebe um `file_id` e agenda o processamento da planilha financeira correspondente em background.
    Retorna uma resposta imediata de sucesso.
    """
    background_tasks.add_task(run_processing_financeiro, process_request.file_id)
    return {"message": "Processamento da planilha financeira agendado com sucesso!", "file_id": process_request.file_id}

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

@app.post("/processar-planilha-conciliacao", tags=["Processamento"], summary="Inicia o processamento de uma planilha de CONCILIAÇÃO em background")
async def processar_planilha_conciliacao_endpoint(process_request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    [CONCILIAÇÃO] Recebe um `file_id` e agenda o processamento da planilha de conciliação correspondente em background.
    Retorna uma resposta imediata de sucesso.
    """
    background_tasks.add_task(run_processing_conciliacao, process_request.file_id, process_request.storage_path)
    return {"message": "Processamento da planilha de conciliação agendado com sucesso!", "file_id": process_request.file_id}
