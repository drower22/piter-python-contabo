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
    logger.log('info', f'Passo 1: Lidas {len(df)} linhas do arquivo Excel.')

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

def _save_conciliation_data(supabase_client, df, account_id, received_file_id, logger):
    """Salva um DataFrame limpo de dados de conciliação no Supabase."""
    try:
        logger.log('info', f'Iniciando salvamento de {len(df)} registros.')
        df['account_id'] = account_id
        df['received_file_id'] = received_file_id
        df['id'] = [uuid.uuid4() for _ in range(len(df))]
        df['raw_data'] = df.apply(lambda row: row.to_json(date_format='iso', force_ascii=False), axis=1)

        records_to_upsert = df.to_dict(orient='records')
        
        batch_size = 200
        for i in range(0, len(records_to_upsert), batch_size):
            batch = records_to_upsert[i:i + batch_size]
            for record in batch:
                for key, value in record.items():
                    if isinstance(value, (datetime.datetime, datetime.date)):
                        record[key] = value.isoformat()
            supabase_client.table(TABLE_CONCILIATION_DATA).insert(batch).execute()
            logger.log('info', f'Lote de {len(batch)} registros salvo com sucesso.')
    except Exception as e:
        logger.log('error', f'Erro ao salvar dados de conciliação: {e}')
        raise # Propaga o erro para o bloco principal

def process_conciliation_file(file_path: str, file_id: str, account_id: str):
    """Orquestra o processo completo de leitura, limpeza e salvamento dos dados de conciliação."""
    logger = SupabaseLogger(account_id, file_id)
    supabase_client = None
    try:
        supabase_client = init_supabase_client(logger)
        logger.set_supabase_client(supabase_client)
        logger.log("INFO", f"Iniciando processamento do arquivo: {file_path}")
        update_file_status(logger, supabase_client, file_id, 'processing')

        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        df = _read_and_prepare_conciliation_df(file_content, logger)
        logger.log('info', f'[DIAGNÓSTICO] Passo 1: {len(df) if df is not None else 0} linhas lidas do Excel.')
        if df is not None and not df.empty:
            logger.log('info', f'[AMOSTRA DADOS] Após leitura inicial:\n{df.head(6).to_string()}')

        if df is None or df.empty:
            logger.log('warning', 'Nenhum dado lido do arquivo. Processamento encerrado.')
            update_file_status(logger, supabase_client, file_id, 'processed', 'Arquivo vazio ou em formato inesperado.')
            return

        df = df.iloc[1:].copy()
        logger.log('info', f'[DIAGNÓSTICO] Passo 2: {len(df)} linhas após remover cabeçalho.')

        # Define os nomes corretos das colunas para alinhar com a tabela do Supabase
        column_names = [
            'competencia', 'data_fato_gerador', 'fato_gerador', 'tipo_lancamento',
            'descricao_lancamento', 'valor', 'base_calculo', 'percentual_taxa',
            'pedido_associado_ifood', 'pedido_associado_ifood_curto', 'pedido_associado_externo',
            'motivo_cancelamento', 'descricao_ocorrencia', 'data_criacao_pedido_associado',
            'data_repasse_esperada', 'valor_transacao', 'loja_id', 'loja_id_curto',
            'loja_id_externo', 'cnpj', 'titulo', 'data_faturamento',
            'data_apuracao_inicio', 'data_apuracao_fim', 'valor_cesta_inicial',
            'valor_cesta_final', 'responsavel_transacao', 'canal_vendas',
            'impacto_no_repasse', 'parcela_pagamento'
        ]
        df.columns = column_names
        logger.log('info', 'Colunas do DataFrame renomeadas para corresponder à tabela.')

        if not df.empty:
            logger.log('info', f'[AMOSTRA DADOS] Após renomear colunas:\n{df.head(6).to_string()}')

        df.dropna(how='all', inplace=True)
        logger.log('info', f'[DIAGNÓSTICO] Passo 3: {len(df)} linhas após remover linhas vazias.')
        if not df.empty:
            logger.log('info', f'[AMOSTRA DADOS] Após remover linhas vazias:\n{df.head(6).to_string()}')

        if df.empty:
            logger.log('warning', 'Nenhum dado restou após a limpeza. Nenhum registro será salvo.')
            update_file_status(logger, supabase_client, file_id, 'processed', 'Nenhum dado válido encontrado após limpeza.')
            return

        df.reset_index(drop=True, inplace=True)
        logger.log('info', f'[DIAGNÓSTICO] Passo 4: {len(df)} registros prontos para salvar.')
        if not df.empty:
            logger.log('info', f'[AMOSTRA DADOS] Antes de salvar:\n{df.head(6).to_string()}')

        _save_conciliation_data(supabase_client, df, account_id, file_id, logger)
        
        update_file_status(logger, supabase_client, file_id, 'processed')
        logger.log("INFO", "Processamento do relatório de conciliação concluído com sucesso.")
        print(json.dumps({"status": "success", "file_id": file_id}))

    except Exception as e:
        error_message = f"Erro inesperado no processamento da conciliação: {e}"
        logger.log('error', error_message, traceback.format_exc())
        if supabase_client:
            update_file_status(logger, supabase_client, file_id, 'error', error_message, traceback.format_exc())
        print(json.dumps({"status": "error", "file_id": file_id, "error": str(e)}))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.log('info', f'Arquivo temporário {file_path} removido.')

# --- Ponto de Entrada para Execução via Linha de Comando ---

def main():
    parser = argparse.ArgumentParser(description="Processa um relatório de conciliação do iFood e salva no Supabase.")
    parser.add_argument('--filepath', required=True, help='Caminho para o arquivo de conciliação .xlsx.')
    parser.add_argument('--account-id', required=True, type=str, help='ID da conta (UUID).')
    parser.add_argument('--file-id', required=True, type=str, help='ID do registro do arquivo (UUID).')
    args = parser.parse_args()

    process_conciliation_file(args.filepath, args.file_id, args.account_id)

if __name__ == "__main__":
    main()
