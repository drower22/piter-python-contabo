import pandas as pd
import io
import numpy as np
import sys
import os

# --- Solução Definitiva para o Problema de Módulo ---
# Adiciona o diretório raiz do projeto ao sys.path para que as importações de módulos funcionem
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import datetime
import json
import traceback
import uuid
from supabase import Client
from dotenv import load_dotenv
import argparse

# Importa utilitários do script de relatório, que serve como base
from scripts.process_report import SupabaseLogger, init_supabase_client, update_file_status

# --- Configuração do .env ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Constantes do Schema ---
TABLE_CONCILIATION_DATA = 'conciliation_data'
TABLE_RECEIVED_FILES = 'received_files' # Usado por update_file_status

# --- Funções de Parsing Específicas para Conciliação ---

def parse_brazilian_currency(value):
    if pd.isna(value) or value in ['-', '']:
        return None
    try:
        cleaned_value = str(value).replace('R$', '').strip().replace('.', '').replace(',', '.')
        return float(cleaned_value)
    except (ValueError, TypeError):
        return None

def parse_percent(value):
    if pd.isna(value) or value in ['-', '']:
        return None
    try:
        return str(value).strip()
    except Exception:
        return None

# --- Funções de Processamento de Dados ---

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Converte os nomes das colunas para um formato padronizado."""
    df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]
    return df

def _find_conciliation_sheet(logger: SupabaseLogger, xls: pd.ExcelFile) -> pd.DataFrame:
    """Lê a segunda aba do arquivo (índice 1) e a valida."""
    sheet_names = xls.sheet_names
    logger.log('info', f'Abas encontradas no arquivo: {sheet_names}')
    
    if len(sheet_names) < 2:
        raise ValueError(f"O arquivo precisa ter pelo menos 2 abas, mas só tem {len(sheet_names)}.")

    target_sheet_name = sheet_names[1] # Pega a segunda aba
    logger.log('info', f'Lendo dados da segunda aba: "{target_sheet_name}"')
    df = pd.read_excel(xls, sheet_name=target_sheet_name, dtype=str)
    
    df = _normalize_columns(df)
    logger.log('info', f'Colunas normalizadas da aba "{target_sheet_name}": {list(df.columns)}')
    
    # Adicione aqui uma verificação de colunas essenciais, se necessário
    return df

def read_and_clean_conciliation_data(logger: SupabaseLogger, file_path: str) -> pd.DataFrame:
    """Lê o arquivo Excel, encontra a aba correta, e aplica limpeza inicial."""
    logger.log('info', f"Iniciando leitura e limpeza do arquivo de conciliação: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            file_content_bytes = f.read()
        
        with pd.ExcelFile(io.BytesIO(file_content_bytes), engine='openpyxl') as xls:
            df = _find_conciliation_sheet(logger, xls)

        if df is None or df.empty:
            raise ValueError("Nenhuma aba de conciliação válida foi encontrada ou a aba está vazia.")

        # Aplicar conversões de tipo
        if 'valor' in df.columns:
            df['valor'] = df['valor'].apply(parse_brazilian_currency)
        if 'base_calculo' in df.columns:
            df['base_calculo'] = df['base_calculo'].apply(parse_brazilian_currency)
        if 'percentual_taxa' in df.columns:
            df['percentual_taxa'] = df['percentual_taxa'].apply(parse_percent)
        
        # Converte colunas de data
        date_columns = ['data_fato_gerador', 'data_criacao_pedido_associado', 'data_repasse_esperada', 'data_faturamento', 'data_apuracao_inicio', 'data_apuracao_fim']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        logger.log('info', f'Limpeza e conversão de tipos concluída. {len(df)} linhas prontas para salvar.')
        return df

    except Exception as e:
        logger.log('error', f'Falha ao ler ou limpar os dados de conciliação: {e}')
        raise

def save_conciliation_data(logger: SupabaseLogger, supabase: Client, df: pd.DataFrame, account_id: str, received_file_id: str):
    """Salva os dados de conciliação processados no Supabase."""
    logger.log('info', f'Iniciando salvamento de {len(df)} registros de conciliação.')
    
    df['account_id'] = account_id
    df['received_file_id'] = received_file_id
    df['id'] = [uuid.uuid4() for _ in range(len(df))]
    # Garante que a conversão para JSON lide com erros de codificação nos dados brutos
    df['raw_data'] = df.apply(lambda row: row.to_json(date_format='iso', force_ascii=False), axis=1)

    records_to_upsert = df.to_dict(orient='records')

    if not records_to_upsert:
        logger.log('warning', "Nenhum registro de conciliação válido para inserir.")
        return

    BATCH_SIZE = 200
    logger.log('info', f'Enviando {len(records_to_upsert)} registros em lotes de {BATCH_SIZE}.')

    for i in range(0, len(records_to_upsert), BATCH_SIZE):
        batch = records_to_upsert[i:i+BATCH_SIZE]
        try:
            for record in batch:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (datetime.datetime, datetime.date)):
                        record[key] = value.isoformat()
            
            supabase.table(TABLE_CONCILIATION_DATA).insert(batch).execute()
            logger.log('info', f'Lote de {len(batch)} registros salvo com sucesso.')
        except Exception as e:
            logger.log('error', f'Erro ao salvar lote de conciliação no Supabase: {e}')
            raise

    logger.log('info', 'Salvamento dos dados de conciliação concluído.')

# --- Função Principal de Orquestração ---

def process_conciliation_file(supabase: Client, logger: SupabaseLogger, file_path: str, file_id: str, account_id: str):
    """Função principal que orquestra o processamento do arquivo de conciliação."""
    logger.set_context(file_id=file_id, account_id=account_id)

    try:
        logger.log("INFO", f"Iniciando processamento do arquivo de conciliação: {file_path}")
        update_file_status(logger, supabase, file_id, 'processing')

        df = read_and_clean_conciliation_data(logger, file_path)
        
        save_conciliation_data(logger, supabase, df, account_id, file_id)
        
        update_file_status(logger, supabase, file_id, 'processed')
        logger.log("INFO", "Processamento do relatório de conciliação concluído com sucesso.")
        print(json.dumps({"status": "success", "file_id": file_id}))

    except Exception as e:
        error_message = f"Erro no processamento da conciliação: {e}"
        tb_str = traceback.format_exc()
        logger.log("ERROR", error_message, context={"traceback": tb_str})
        update_file_status(logger, supabase, file_id, 'error', error_message)
        print(json.dumps({"status": "error", "message": str(e), "file_id": file_id}))
    
    finally:
        logger.flush()

# --- Ponto de Entrada para Execução via Linha de Comando ---

def main():
    parser = argparse.ArgumentParser(description="Processa um relatório de conciliação do iFood e salva no Supabase.")
    parser.add_argument('--filepath', required=True, help='Caminho para o arquivo de conciliação .xlsx.')
    parser.add_argument('--account-id', required=True, type=str, help='ID da conta (UUID).')
    parser.add_argument('--file-id', required=True, type=str, help='ID do registro do arquivo (UUID).')
    args = parser.parse_args()

    supabase_client = init_supabase_client()
    logger = SupabaseLogger(supabase_client)
    
    process_conciliation_file(supabase_client, logger, args.filepath, args.file_id, args.account_id)

if __name__ == "__main__":
    main()
