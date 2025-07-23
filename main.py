import os
import traceback
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
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

@app.get("/", tags=["Status"], summary="Verifica se a API está online")
def read_root():
    """Endpoint raiz para verificar a saúde da API."""
    return {"status": "ok", "message": "Bem-vindo à API do iFood Sales Concierge!"}

@app.post("/upload/planilha", tags=["Uploads"], summary="Faz upload de uma planilha para o Supabase Storage")
async def upload_planilha(
    file: UploadFile = File(..., description="Arquivo de planilha (xlsx, csv) para upload."),
    user_id: str = Form(..., description="ID do usuário ou conta que está enviando o arquivo."),
    filename: str = Form(..., description="Nome original do arquivo a ser salvo no bucket.")
):
    """
    Recebe um arquivo de planilha via formulário multipart e o envia para o bucket 'financeiro' no Supabase Storage.
    O caminho no bucket será estruturado como: `user_id/filename`.
    """
    try:
        bucket_name = "financeiro"
        path_in_bucket = f"{user_id}/{filename}"

        # Lê o conteúdo do arquivo em bytes
        contents = await file.read()

        # Faz o upload para o Supabase Storage, sobrescrevendo se já existir (upsert=true)
        response = supabase.storage.from_(bucket_name).upload(
            path=path_in_bucket,
            file=contents,
            file_options={"cache-control": "3600", "upsert": "true"}
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "Upload realizado com sucesso!",
                "path": path_in_bucket
            }
        )
    except Exception as e:
        # Em caso de erro, retorna uma resposta com status 500
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro no upload: {str(e)}")

import requests  # Adicionado para download de arquivos via URL

from fastapi import Request, BackgroundTasks
from pydantic import BaseModel
import tempfile
import os

# Importa a lógica de processamento do script
# Este endpoint é EXCLUSIVO para o processamento do relatório financeiro do iFood.
from scripts.process_report import processar_relatorio_financeiro, init_supabase_client as init_processor_supabase, SupabaseLogger


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
        path_in_bucket = f"{user_id}/{filename}"

        # Busca o header Authorization, se enviado
        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header

        # Faz o download do arquivo, repassando o header Authorization se existir
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        contents = response.content

        # Faz o upload para o Supabase Storage, sobrescrevendo se já existir (upsert=true)
        upload_response = supabase.storage.from_(bucket_name).upload(
            path=path_in_bucket,
            file=contents,
            file_options={"cache-control": "3600", "upsert": "true"}
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Upload realizado com sucesso via URL para {tipo}!",
                "path": path_in_bucket
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

class ProcessRequest(BaseModel):
    file_id: str

def run_processing_financeiro(file_id: str):
    """Função que executa o processamento FINANCEIRO em background."""
    # Inicializa um cliente supabase e logger para este processo
    supabase_processor = init_processor_supabase()
    logger = SupabaseLogger(supabase_processor)

    try:
        # 1. Buscar detalhes do arquivo no banco
        response = supabase_processor.table('received_files').select('storage_path, account_id').eq('id', file_id).single().execute()
        record = response.data
        if not record:
            logger.log("ERROR", f"Registro de arquivo com ID {file_id} não encontrado.")
            logger.flush()
            return

        storage_path = record.get('storage_path')
        account_id = record.get('account_id')
        bucket_name = storage_path.split('/')[0]
        path_in_bucket = '/'.join(storage_path.split('/')[1:])

        # 2. Baixar o arquivo do Supabase Storage
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            file_content = supabase_processor.storage.from_(bucket_name).download(path=path_in_bucket)
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name

        # 3. Chamar a função de processamento financeiro
        processar_relatorio_financeiro(supabase_processor, logger, temp_file_path, file_id, account_id)

    except Exception as e:
        error_message = f"Erro no processamento em background para file_id {file_id}: {e}"
        logger.log("CRITICAL", error_message, context={"traceback": traceback.format_exc()})
    finally:
        # 4. Limpar o arquivo temporário e o logger
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        logger.flush()


@app.post("/processar-planilha-financeiro", tags=["Processamento"], summary="Inicia o processamento de uma planilha FINANCEIRA em background")
async def processar_planilha_financeiro_endpoint(process_request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    [FINANCEIRO] Recebe um `file_id` e agenda o processamento da planilha financeira correspondente em background.
    Retorna uma resposta imediata de sucesso.
    """
    background_tasks.add_task(run_processing_financeiro, process_request.file_id)
    return {"message": "Processamento da planilha financeira agendado com sucesso!", "file_id": process_request.file_id}

# Adicione aqui outros endpoints para processar outros tipos de planilha, como conciliação, conforme necessário.
# def processar_relatorio(file_id: str):
#     from scripts.process_report import processar
#     resultado = processar(file_id)
#     return {"resultado": resultado}
