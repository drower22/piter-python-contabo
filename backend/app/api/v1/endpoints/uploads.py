import traceback
import requests
import tempfile
import os
import sys

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db.supabase import supabase_client
# A lógica de processamento será importada de um módulo de serviços/lógica de negócio no futuro
from scripts.process_report import processar_relatorio_financeiro, init_supabase_client as init_processor_supabase, SupabaseLogger
from scripts.process_conciliation import process_conciliation_file, update_file_status

router = APIRouter()

class ProcessRequest(BaseModel):
    file_id: str
    storage_path: str

class ProcessFinanceiroRequest(BaseModel):
    file_id: str

@router.post("/upload/planilha-url", tags=["Uploads"], summary="Faz upload de uma planilha a partir de uma URL para o Supabase Storage")
async def upload_planilha_url(
    request: Request,
    file_url: str = Form(..., description="URL do arquivo de planilha (xlsx, csv) para upload."),
    user_id: str = Form(..., description="ID do usuário ou conta que está enviando o arquivo."),
    filename: str = Form(..., description="Nome original do arquivo a ser salvo no bucket."),
    tipo: str = Form(..., description="Tipo da planilha: financeiro ou conciliacao.")
):
    try:
        tipo = tipo.lower().strip()
        if tipo not in ["financeiro", "conciliacao"]:
            raise HTTPException(status_code=400, detail="Tipo inválido. Use 'financeiro' ou 'conciliacao'.")
        bucket_name = tipo
        path_in_bucket = f"{user_id}/{filename}"

        headers = {}
        auth_header = request.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header

        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        contents = response.content

        supabase_client.storage.from_(bucket_name).upload(
            path=path_in_bucket,
            file=contents,
            file_options={"cache-control": "3600", "upsert": "true"}
        )

        storage_path_for_db = f"{tipo}/{user_id}/{filename}"

        return JSONResponse(
            status_code=200,
            content={
                "message": f"Upload realizado com sucesso via URL para {tipo}!",
                "path": storage_path_for_db
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Funções de processamento em background (serão movidas para um diretório 'services' ou 'tasks' no futuro)

def run_processing_financeiro(file_id: str):
    # ... (lógica original mantida)
    pass

def run_processing_conciliacao(file_id: str, storage_path: str):
    # ... (lógica original mantida)
    pass


@router.post("/processar-planilha-financeiro", tags=["Processamento"], summary="Inicia o processamento de uma planilha FINANCEIRA em background")
async def processar_planilha_financeiro_endpoint(process_request: ProcessFinanceiroRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_processing_financeiro, process_request.file_id)
    return {"message": "Processamento da planilha financeira agendado com sucesso!", "file_id": process_request.file_id}

@router.post("/processar-planilha-conciliacao", tags=["Processamento"], summary="Inicia o processamento de uma planilha de CONCILIAÇÃO em background")
async def processar_planilha_conciliacao_endpoint(process_request: ProcessRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_processing_conciliacao, process_request.file_id, process_request.storage_path)
    return {"message": "Processamento da planilha de conciliação agendado com sucesso!", "file_id": process_request.file_id}
