import argparse
import json
import os
import sys
import traceback
import uuid

import pandas as pd
from supabase import Client, create_client

# Adiciona o diretório raiz ao path para resolver importações, se necessário
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- Constantes ---
TABLE_LOGS = 'logs'
TABLE_CONCILIATION = 'ifood_conciliation'
TABLE_FILES = 'received_files'

# Mapeamento exato das colunas do Excel para as colunas da tabela
COLUMNS_MAPPING = {
    'Data da Venda': 'sale_date',
    'ID do Pedido': 'order_id',
    'Tipo de Lançamento': 'transaction_type',
    'Descrição do Lançamento': 'transaction_description',
    'Valor Bruto': 'gross_value',
    'Valor da Entrega': 'delivery_fee',
    'Valor da Transação': 'transaction_value',
    'Valor da Taxa de Serviço': 'service_fee',
    'Valor da Taxa de Pagamento': 'payment_fee',
    'Outros Lançamentos': 'other_fees',
    'Valor Líquido': 'net_value',
    'ID da Transação': 'transaction_id',
    'ID do Lançamento': 'entry_id',
    'Data do Repasse': 'payment_date',
    'Status do Pagamento': 'payment_status',
    'Tipo de Pagamento': 'payment_method',
    'Bandeira do Cartão': 'card_brand'
}

# --- Funções e Classes de Suporte (Isoladas para evitar dependências externas) ---

class SupabaseLogger:
    """Classe de logger para enviar logs para o Supabase de forma isolada."""
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.file_id = None
        self.account_id = None

    def set_context(self, file_id: str, account_id: str):
        self.file_id = file_id
        self.account_id = account_id

    def log(self, level: str, message: str, context: dict = None):
        try:
            payload = {
                "level": level.upper(),
                "message": message,
                "file_id": self.file_id,
                "account_id": self.account_id,
                "context": context or {},
                "source": "process_conciliation"
            }
            print(f"[LOG-{level.upper()}] {message}") # Log local para depuração imediata
            self.supabase.table(TABLE_LOGS).insert(payload).execute()
        except Exception as e:
            print(f"[CRITICAL] Falha ao enviar log para o Supabase: {e}", file=sys.stderr)

def init_supabase_client() -> Client:
    """Inicializa e retorna um cliente Supabase."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.")
    return create_client(url, key)

def update_file_status(logger: SupabaseLogger, supabase_client: Client, file_id: str, status: str, details: str = None):
    """Atualiza o status de um arquivo na tabela 'files'."""
    try:
        update_data = {"status": status}
        if details:
            update_data['details'] = details
        
        supabase_client.table(TABLE_FILES).update(update_data).eq('id', file_id).execute()
        logger.log('info', f"Status do arquivo {file_id} atualizado para '{status}'.")
    except Exception as e:
        logger.log('error', f"Falha ao atualizar status do arquivo {file_id}: {e}")

# --- Funções de Processamento ---

def read_and_clean_data(logger: SupabaseLogger, file_path: str) -> pd.DataFrame:
    """Lê a segunda aba de um arquivo Excel, remove a primeira linha e renomeia as colunas."""
    try:
        logger.log('info', 'Iniciando leitura do arquivo Excel.')
        # sheet_name=1 para ler a segunda aba, header=0 para usar a primeira linha como cabeçalho
        df = pd.read_excel(file_path, sheet_name=1, header=0, engine='openpyxl')
        logger.log('info', f'{len(df)} linhas lidas do arquivo.')
        
        # Renomeia as colunas com base no mapeamento
        df.rename(columns=COLUMNS_MAPPING, inplace=True)
        logger.log('info', 'Colunas renomeadas com sucesso.')
        logger.log('debug', f'Colunas após renomear: {df.columns.tolist()}')
        
        # Garante que apenas as colunas mapeadas existam
        df = df[list(COLUMNS_MAPPING.values())]
        logger.log('info', f'DataFrame finalizado com {len(df.columns)} colunas.')
        return df
    except Exception as e:
        logger.log('error', f'Falha ao ler ou limpar os dados do Excel: {e}')
        raise

def safe_to_json(row, logger):
    """Converte uma linha para JSON de forma segura, tratando erros de encoding."""
    try:
        return row.to_json(date_format='iso', force_ascii=False)
    except Exception as e:
        safe_dict = {}
        for k, v in row.to_dict().items():
            try:
                safe_dict[k] = str(v).encode('utf-8', 'ignore').decode('utf-8')
            except Exception:
                safe_dict[k] = "[DADO ILEGÍVEL]"
        
        error_message = f"Falha de encoding ao serializar linha. Erro: {e}"
        logger.log('warning', error_message, {'problematic_row_data': safe_dict})
        return json.dumps({"error": error_message, "original_data_cleaned": safe_dict})

def save_data_in_batches(logger: SupabaseLogger, supabase_client: Client, df: pd.DataFrame, account_id: str, file_id: str):
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
            supabase_client.table(TABLE_CONCILIATION).upsert(batch, on_conflict='entry_id').execute()
        except Exception as e:
            logger.log('error', f'Falha ao salvar lote de dados: {e}')
            raise
    logger.log('info', 'Todos os lotes foram salvos com sucesso.')

# --- Orquestrador Principal ---

def process_conciliation_file(file_path: str, file_id: str, account_id: str):
    print(f"[PROC_CONCILIATION] Iniciando. file_id={file_id}, account_id={account_id}")
    """Orquestra o processo completo de ponta a ponta."""
    supabase_client = None
    logger = None
    try:
        print("[PROC_CONCILIATION] Inicializando cliente Supabase...")
        supabase_client = init_supabase_client()
        print("[PROC_CONCILIATION] Cliente Supabase inicializado. Inicializando logger...")
        logger = SupabaseLogger(supabase_client)
        print("[PROC_CONCILIATION] Logger inicializado.")
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
        print(details, file=sys.stderr) # Log de erro crítico para o console
        if logger and supabase_client:
            logger.log('critical', error_message, {'traceback': tb_str})
            update_file_status(logger, supabase_client, file_id, 'error', details)
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                if logger:
                    logger.log('info', f'Arquivo temporário {file_path} removido.')
            except OSError as e:
                if logger:
                    logger.log('error', f'Falha ao remover arquivo temporário {file_path}: {e}')

# --- Ponto de Entrada (CLI) ---

import argparse
import json


