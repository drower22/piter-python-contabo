import os
import sys
import traceback
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
    'competencia': 'sale_date',
    'pedido_associado_ifood': 'order_id',
    'tipo_lancamento': 'transaction_type',
    'descricao_lancamento': 'transaction_description',
    'valor': 'gross_value',
    'valor_transacao': 'transaction_value',
    'data_repasse_esperada': 'payment_date',
    'impacto_no_repasse': 'payment_status',
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
        logger.log('info', 'Iniciando leitura do arquivo Excel (segunda aba).')
        df = pd.read_excel(file_path, sheet_name=1, header=0)
        df = df.replace({np.nan: None})
        logger.log('info', f'{len(df)} linhas lidas do arquivo.')
        
        df.rename(columns=COLUMNS_MAPPING, inplace=True)
        logger.log('info', 'Colunas renomeadas.')
        
        final_columns = list(COLUMNS_MAPPING.values())
        df = df[final_columns]
        logger.log('info', f'DataFrame finalizado com as colunas corretas.')
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
    logger.log('info', f'Iniciando preparação de {len(df)} registros para salvamento.')
    
    df['account_id'] = account_id
    df['received_file_id'] = file_id
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    
    logger.log('info', 'Iniciando serialização segura para JSON (raw_data).')
    df['raw_data'] = df.apply(lambda row: safe_to_json(row, logger), axis=1)
    logger.log('info', 'Serialização concluída.')

    records_to_insert = df.to_dict(orient='records')
    
    batch_size = 100
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i + batch_size]
        try:
            logger.log('info', f'Salvando lote {i // batch_size + 1} com {len(batch)} registros.')
            supabase_client.table(TABLE_CONCILIATION).upsert(batch, on_conflict='id').execute()
        except Exception as e:
            logger.log('error', f'Falha ao salvar lote de dados: {e}')
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
            update_file_status(logger, supabase_client, file_id, 'completed')
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
