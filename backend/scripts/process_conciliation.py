import os
import sys
import traceback
import hashlib
import uuid
import json

import pandas as pd
import numpy as np
from supabase import Client

# --- Constantes ---
TABLE_CONCILIATION = 'ifood_conciliation'
TABLE_FILES = 'received_files'

# Mapeamento exato das colunas do Excel para as colunas da tabela
COLUMNS_MAPPING = {
    'competencia': 'competence_date',
    'data_fato_gerador': 'event_date',
    'fato_gerador': 'event_trigger',
    'tipo_lancamento': 'transaction_type',
    'descricao_lancamento': 'transaction_description',
    'valor': 'gross_value',
    'base_calculo': 'calculation_base_value',
    'percentual_taxa': 'tax_percentage',
    'pedido_associado_ifood': 'ifood_order_id',
    'pedido_associado_ifood_curto': 'ifood_order_id_short',
    'pedido_associado_externo': 'external_order_id',
    'motivo_cancelamento': 'cancellation_reason',
    'descricao_ocorrencia': 'occurrence_description',
    'data_criacao_pedido_associado': 'order_creation_date',
    'data_repasse_esperada': 'expected_payment_date',
    'valor_transacao': 'transaction_value',
    'loja_id': 'store_id',
    'loja_id_curto': 'store_id_short',
    'loja_id_externo': 'store_id_external',
    'cnpj': 'cnpj',
    'titulo': 'title',
    'data_faturamento': 'billing_date',
    'data_apuracao_inicio': 'settlement_start_date',
    'data_apuracao_fim': 'settlement_end_date',
    'valor_cesta_inicial': 'initial_basket_value',
    'valor_cesta_final': 'final_basket_value',
    'responsavel_transacao': 'transaction_responsible',
    'canal_vendas': 'sales_channel',
    'impacto_no_repasse': 'payment_impact',
    'parcela_pagamento': 'payment_installment',
}

def update_file_status(logger, supabase_client: Client, file_id: str, status: str, details: str = None):
    """Atualiza o status de um arquivo na tabela 'files'."""
    try:
        update_data = {'status': status}
        # A coluna 'details' foi desativada temporariamente para compatibilidade.
        # if details:
        #     update_data['details'] = details
        supabase_client.table(TABLE_FILES).update(update_data).eq('id', file_id).execute()
        logger.log('info', f"Status do arquivo {file_id} atualizado para '{status}'.")
    except Exception as e:
        logger.log('error', f"Falha ao atualizar status do arquivo {file_id}: {e}")

def read_and_clean_data(logger, file_path: str) -> pd.DataFrame:
    """Lê a segunda aba de um arquivo Excel, trata NaNs e renomeia as colunas."""
    try:
        logger.log('info', 'Iniciando leitura e limpeza dos dados do Excel...')
        df = pd.read_excel(file_path, sheet_name=1, header=0)
        df = df.replace({np.nan: None})
        logger.log('info', f'{len(df)} linhas lidas da planilha.')

        df.rename(columns=COLUMNS_MAPPING, inplace=True)
        logger.log('info', 'Colunas renomeadas com sucesso.')

        date_columns = [
            'competence_date', 'event_date', 'order_creation_date', 'expected_payment_date',
            'billing_date', 'settlement_start_date', 'settlement_end_date'
        ]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)

        id_columns = [
            'ifood_order_id', 'ifood_order_id_short', 'external_order_id',
            'store_id', 'store_id_short', 'store_id_external', 'cnpj'
        ]
        for col in id_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('None', None)

        value_columns = [
            'gross_value', 'calculation_base_value', 'tax_percentage', 'transaction_value',
            'initial_basket_value', 'final_basket_value'
        ]
        for col in value_columns:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(r'[^0-9,-]', '', regex=True)
                    .str.replace(',', '.', regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        final_columns = list(COLUMNS_MAPPING.values())
        df = df[final_columns]
        logger.log('info', 'DataFrame finalizado e filtrado com as colunas corretas para o banco.')

        def row_hash(row):
            concat = '|'.join([str(row[col]) if row[col] is not None else '' for col in final_columns])
            return hashlib.sha256(concat.encode('utf-8')).hexdigest()
        df['row_key'] = df.apply(row_hash, axis=1)

        # Remover duplicatas da planilha antes de enviar para o banco
        initial_rows = len(df)
        df.drop_duplicates(subset=['row_key'], keep='first', inplace=True)
        final_rows = len(df)
        if initial_rows > final_rows:
            logger.log('warning', f'{initial_rows - final_rows} linhas duplicadas foram removidas da planilha.')

        # --- Log Explícito dos Dados (10 Primeiras Linhas) ---
        logger.log('info', '>>> INÍCIO DA AMOSTRA DE DADOS PROCESSADOS (10 primeiras linhas) <<<')
        logger.log('info', '\n================ AMOSTRA DAS 10 PRIMEIRAS LINHAS =================')
        for idx, row in df.head(10).iterrows():
            logger.log('info', f'Linha {idx}:')
            for col_name, value in row.items():
                logger.log('info', f'  Coluna: {col_name} | Valor: "{value}" | Tipo: {type(value).__name__}')
        logger.log('info', '===============================================================\n')
        logger.log('info', '>>> FIM DA AMOSTRA DE DADOS <<<')

        return df

    except Exception as e:
        logger.log('error', f'Falha ao ler ou limpar os dados do Excel: {e}')
        raise

def safe_to_json(row, logger):
    """Converte uma linha para JSON de forma segura, tratando erros de encoding."""
    try:
        return row.to_json(date_format='iso', force_ascii=False)
    except Exception as e:
        safe_dict = {k: str(v).encode('utf-8', 'ignore').decode('utf-8') for k, v in row.to_dict().items()}
        logger.log('warning', f"Falha de encoding ao serializar linha: {e}", {'problematic_row_data': safe_dict})
        return json.dumps({"error": f"Falha de encoding: {e}", "original_data_cleaned": safe_dict})

def save_data_in_batches(logger, supabase_client: Client, df: pd.DataFrame, account_id: str, file_id: str):
    """Prepara e salva os dados no Supabase em lotes."""
    logger.log('info', f'Iniciando preparação de {len(df)} registros para salvar no banco de dados.')
    
    logger.log('info', 'Adicionando colunas de metadados (account_id, received_file_id, id).')
    df['account_id'] = account_id
    df['received_file_id'] = file_id
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    
    logger.log('info', 'Iniciando serialização segura para JSON (raw_data).')
    df['raw_data'] = df.apply(lambda row: safe_to_json(row, logger), axis=1)
    logger.log('info', 'Serialização concluída.')

    logger.log('info', f"[DEBUG] Colunas a serem salvas: {df.columns.tolist()}")

    records_to_insert = df.to_dict(orient='records')
    
    batch_size = 100
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i + batch_size]
        try:
            logger.log('info', f'Enviando lote {i//batch_size+1}/{(len(records_to_insert)-1)//batch_size+1} para o Supabase...')
            supabase_client.table(TABLE_CONCILIATION).upsert(batch, on_conflict='row_key').execute()
        except Exception as e:
            logger.log('error', f'Falha ao salvar lote de dados no Supabase: {e}')
            # Log de depuração para inspecionar o primeiro registro do lote que falhou
            if batch:
                logger.log('debug', f'Amostra do primeiro registro do lote que falhou: {json.dumps(batch[0], default=str)}')
            raise
    logger.log('info', 'Todos os lotes foram salvos com sucesso.')

def process_conciliation_file(logger, supabase_client: Client, file_path: str, file_id: str, account_id: str):
    """Orquestra o processo completo de ponta a ponta."""
    try:
        logger.set_context(file_id=file_id, account_id=account_id)
        logger.log('info', f'Iniciando processamento do arquivo de conciliação: {file_path}')
        update_file_status(logger, supabase_client, file_id, 'processing')

        df = read_and_clean_data(logger, file_path)
        
        if df is not None and not df.empty:
            save_data_in_batches(logger, supabase_client, df, account_id, file_id)
            update_file_status(logger, supabase_client, file_id, 'processed')
            logger.log('info', 'Processamento do arquivo concluído com sucesso.')
        else:
            update_file_status(logger, supabase_client, file_id, 'error', 'O arquivo Excel está vazio ou não contém dados na segunda aba.')
            logger.log('warning', 'O DataFrame está vazio após a leitura. Nenhum dado para salvar.')

    except Exception as e:
        error_message = f"Erro fatal no processamento: {e}"
        tb_str = traceback.format_exc()
        details = f"{error_message}\n\nTraceback:\n{tb_str}"
        print(details, file=sys.stderr)
        if logger and supabase_client:
            logger.log('critical', error_message, {'traceback': tb_str})
            update_file_status(logger, supabase_client, file_id, 'error', details)
    finally:
        # A remoção do arquivo temporário é feita no processo principal (main.py)
        pass
