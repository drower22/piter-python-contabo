import pandas as pd
import numpy as np
import sys
import os
import datetime
import json
import time
import traceback
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv
import argparse

# --- Configuração do Supabase e .env ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Constantes do Schema ---
TABLE_CONCILIATION_DATA = 'conciliation_data'
TABLE_RECEIVED_FILES = 'received_files'
TABLE_LOGS = 'logs'

# --- Sistema de Logging Centralizado (reutilizado de process_report.py) ---
class SupabaseLogger:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.file_id = None
        self.account_id = None
        self.log_buffer = []

    def set_context(self, file_id: str = None, account_id: str = None):
        if file_id: self.file_id = file_id
        if account_id: self.account_id = account_id

    def log(self, level: str, message: str, context: dict = None):
        payload = {
            "level": level.upper(),
            "message": message,
            "file_id": self.file_id,
            "account_id": self.account_id,
            "context": context
        }
        self.log_buffer.append(payload)
        if level.lower() in ["error", "critical", "warning"]:
            print(f"[{level.upper()}] {message}")

    def flush(self):
        if not self.log_buffer:
            return
        try:
            self.supabase.table(TABLE_LOGS).insert(self.log_buffer).execute()
            self.log_buffer = []
        except Exception as e:
            print(f"[CRITICAL] Falha ao escrever logs no Supabase: {e}", file=sys.stderr)
            print(f"[CRITICAL] Logs perdidos: {self.log_buffer}", file=sys.stderr)

# Colunas esperadas no arquivo de conciliação
EXPECTED_COLUMNS = [
    'competencia', 'data_fato_gerador', 'fato_gerador', 'tipo_lancamento', 
    'descricao_lancamento', 'valor', 'base_calculo', 'percentual_taxa',
    'pedido_associado_ifood', 'pedido_associado_ifood_curto', 'pedido_associado_externo',
    'motivo_cancelamento', 'descricao_ocorrencia', 'data_criacao_pedido_associado',
    'data_repasse_esperada', 'valor_transacao', 'loja_id', 'loja_id_curto',
    'loja_id_externo', 'cnpj', 'titulo', 'data_faturamento', 'data_apuracao_inicio',
    'data_apuracao_fim', 'valor_cesta_inicial', 'valor_cesta_final',
    'responsavel_transacao', 'canal_vendas', 'impacto_no_repasse',
    'parcela_pagamento'
]

def init_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.")
    return create_client(url, key)

def update_file_status(logger: SupabaseLogger, supabase: Client, file_id: str, status: str, error_message: str = None):
    try:
        update_data = {"status": status, "processed_at": datetime.datetime.now().isoformat()}
        if error_message:
            update_data["error_details"] = error_message

        supabase.table(TABLE_RECEIVED_FILES).update(update_data).eq("id", file_id).execute()
        logger.log('info', f"Status do arquivo atualizado para '{status}'.")
    except Exception as e:
        logger.log('error', f"FALHA CRÍTICA ao atualizar status do arquivo: {e}")

def parse_brazilian_currency(value):
    if pd.isna(value) or value in ['-', '']:
        return None
    try:
        # Remove 'R$', espaços, e troca a vírgula por ponto
        cleaned_value = str(value).replace('R$', '').strip().replace('.', '').replace(',', '.')
        return float(cleaned_value)
    except (ValueError, TypeError):
        return None

# percentual_taxa é texto na tabela, então só normaliza/remover espaços

def parse_percent(value):
    if pd.isna(value) or value in ['-', '']:
        return None
    try:
        return str(value).strip()
    except Exception:
        return None

def _normalize_columns(df: pd.DataFrame) -> list:
    """Converte os nomes das colunas para um formato padronizado."""
    return [str(c).lower().strip().replace(' ', '_') for c in df.columns]

def _find_conciliation_sheet(logger: SupabaseLogger, xls: pd.ExcelFile) -> pd.DataFrame:
    """Lê a segunda aba do arquivo (índice 1) e a valida."""
    sheet_names = xls.sheet_names
    logger.log('info', f'Abas encontradas no arquivo: {sheet_names}')

    if len(sheet_names) < 2:
        logger.error(f'O arquivo Excel não contém uma segunda aba (encontradas: {len(sheet_names)}).')
        return None

    try:
        # Lê a segunda aba diretamente pelo índice 1
        second_sheet_name = sheet_names[1]
        logger.log('info', f'Tentando ler a segunda aba do arquivo: "{second_sheet_name}"')
        df = pd.read_excel(xls, sheet_name=1, header=0, dtype=str)

        # Valida as colunas da aba lida
        normalized_columns = _normalize_columns(df)
        found_columns = set(normalized_columns)
        expected_columns = set(EXPECTED_COLUMNS)

        if expected_columns.issubset(found_columns):
            df.columns = normalized_columns
            logger.log('info', f'Sucesso! A segunda aba ("{second_sheet_name}") foi lida e validada.')
            return df
        else:
            missing = expected_columns - found_columns
            logger.error(f'A segunda aba ("{second_sheet_name}") foi lida, mas as colunas não são as esperadas.')
            logger.error(f'Colunas Faltando: {missing}')
            return None
            
    except Exception as e:
        logger.error(f'Falha crítica ao tentar ler a segunda aba do arquivo. Erro: {e}')
        return None

def read_and_clean_conciliation_data(logger: SupabaseLogger, file_path: str) -> pd.DataFrame:
    logger.log('info', f"Iniciando leitura e limpeza do arquivo de conciliação: {file_path}")
    try:
        xls = pd.ExcelFile(file_path)
        df = _find_conciliation_sheet(logger, xls)

        if df is None:
            raise ValueError("Nenhuma aba de conciliação válida foi encontrada. Verifique se o arquivo é o correto e se a aba 'Relatório de Conciliação' existe com os cabeçalhos na primeira linha.")

        logger.log('info', f'Colunas normalizadas: {list(df.columns)}')

        # Validação de colunas
        missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colunas esperadas não encontradas no arquivo: {', '.join(missing_cols)}")

        df['raw_data'] = df.apply(lambda row: json.dumps(row.to_dict()), axis=1)

        # Limpeza e conversão de tipos
        numeric_cols = ['valor', 'base_calculo', 'valor_transacao', 'valor_cesta_inicial', 'valor_cesta_final']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        date_cols = [
            'data_fato_gerador', 'data_criacao_pedido_associado', 'data_repasse_esperada',
            'data_faturamento', 'data_apuracao_inicio', 'data_apuracao_fim'
        ]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        df = df.replace({np.nan: None})
        logger.log('info', 'Limpeza e normalização dos dados concluídas.')
        return df

    except Exception as e:
        logger.log('error', f"Falha ao ler ou limpar os dados do arquivo de conciliação: {e}")
        raise

def save_conciliation_data(logger: SupabaseLogger, supabase: Client, df: pd.DataFrame, account_id: str, received_file_id: str):
    logger.log('info', f'Iniciando o salvamento de {len(df)} registros de conciliação.')
    
    # Adiciona IDs de conta e arquivo para rastreabilidade
    df['account_id'] = account_id
    df['received_file_id'] = received_file_id

    # Função para criar uma chave única para o upsert (ajuste se quiser usar para evitar duplicidade)
    def create_upsert_key(row):
        key_parts = [
            str(row.get('pedido_associado_ifood', '')),
            str(row.get('data_fato_gerador', '')),
            str(row.get('descricao_lancamento', '')),
            str(row.get('valor', ''))
        ]
        key_string = "-".join(key_parts)
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, key_string))
    df['id'] = df.apply(lambda row: uuid.uuid4(), axis=1)  # Gera um UUID para cada linha
    df['raw_data'] = df.apply(lambda row: row.to_json(), axis=1)
    # Adiciona coluna upsert_key se desejar evitar duplicidade (opcional)
    # df['upsert_key'] = df.apply(create_upsert_key, axis=1)

    # Converte o DataFrame para uma lista de dicionários para o upsert
    records_to_upsert = df.to_dict(orient='records')

    if not records_to_upsert:
        logger.log('warning', "Nenhum registro de conciliação válido para inserir.")
        return

    BATCH_SIZE = 200
    logger.log('info', f'Enviando {len(records_to_upsert)} registros em lotes de {BATCH_SIZE}.')

    for i in range(0, len(records_to_upsert), BATCH_SIZE):
        batch = records_to_upsert[i:i+BATCH_SIZE]
        try:
            # Assegura que todos os dados no batch são JSON serializáveis
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

    logger.log('info', 'Salvamento dos dados de conciliação concluído.')

def processar_relatorio_conciliacao(supabase: Client, logger: SupabaseLogger, file_path: str, received_file_id: str, account_id: str):
    logger.set_context(file_id=received_file_id, account_id=account_id)

    try:
        logger.log("INFO", f"Iniciando processamento do arquivo de conciliação: {file_path}")
        update_file_status(logger, supabase, received_file_id, 'processing')

        df = read_and_clean_conciliation_data(logger, file_path)
        if df is None or df.empty:
            raise ValueError("A leitura e limpeza dos dados de conciliação falhou. O DataFrame está vazio.")

        save_conciliation_data(logger, supabase, df, account_id, received_file_id)
        
        update_file_status(logger, supabase, received_file_id, 'processed')
        logger.log("INFO", "Processamento do relatório de conciliação concluído com sucesso.")
        print(json.dumps({"status": "success", "file_id": received_file_id}))

    except Exception as e:
        error_message = f"Erro no processamento da conciliação: {e}"
        tb_str = traceback.format_exc()
        logger.log("ERROR", error_message, context={"traceback": tb_str})
        update_file_status(logger, supabase, received_file_id, 'error', error_message)
        print(json.dumps({"status": "error", "message": str(e), "file_id": received_file_id}))
    
    finally:
        logger.flush()

def main():
    parser = argparse.ArgumentParser(description="Processa um relatório de conciliação do iFood e salva no Supabase.")
    parser.add_argument('--filepath', required=True, help='Caminho para o arquivo de conciliação .xlsx.')
    parser.add_argument('--account-id', required=True, type=str, help='ID da conta (UUID).')
    parser.add_argument('--received-file-id', required=True, type=str, help='ID do registro do arquivo (UUID).')
    args = parser.parse_args()

    supabase_client = init_supabase_client()
    logger = SupabaseLogger(supabase_client)
    
    processar_relatorio_conciliacao(supabase_client, logger, args.filepath, args.received_file_id, args.account_id)

if __name__ == "__main__":
    main()

