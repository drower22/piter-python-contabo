import os
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

print(f"[DEBUG] SUPABASE_URL: {SUPABASE_URL}")
print(f"[DEBUG] SUPABASE_KEY: {SUPABASE_KEY[:6]}... (ocultado)")

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

# Adicione aqui outros endpoints para chamar seus outros scripts
# Exemplo:
# @app.post("/processar/relatorio", tags=["Processamento"])
# def processar_relatorio(file_id: str):
#     from scripts.process_report import processar
#     resultado = processar(file_id)
#     return {"resultado": resultado}
