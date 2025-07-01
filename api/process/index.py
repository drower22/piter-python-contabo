import logging
import azure.functions as func
import pandas as pd
import sys
import os
import datetime
from datetime import date, timedelta
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import tempfile

# --- Configuração do Supabase ---
# Na Azure, as variáveis são configuradas no App Service, não em .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Este erro será logado no 'Monitor' da Azure Function
    logging.critical("Erro Crítico: Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não configuradas na Azure.")
    # A função irá falhar se as credenciais não estiverem presentes.
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Constantes de Colunas (exatamente como no script original) ---
COL_STORE_ID = "LOJA_ID"
COL_STORE_NAME = "NOME_DA_LOJA"
COL_BILLING_TYPE = "TIPO_DE_FATURAMENTO"
COL_SALES_CHANNEL = "CANAL_DE_VENDAS"
COL_ORDER_NUMBER = "N°_PEDIDO"
COL_ORDER_ID = "PEDIDO_ID_COMPLETO"
COL_ORDER_DATE = "DATA_DO_PEDIDO_OCORRENCIA"
COL_CONFIRMATION_DATE = "DATA_DE_CONCLUSÃO"
COL_REPASSE_DATE = "DATA_DE_REPASSE"
COL_PAYMENT_ORIGIN = "ORIGEM_DE_FORMA_DE_PAGAMENTO"
COL_PAYMENT_METHOD = "FORMAS_DE_PAGAMENTO"
COL_TOTAL_ORDER_VALUE = "TOTAL_DO_PEDIDO"
COL_ITEMS_VALUE = "VALOR_DOS_ITENS"
COL_DELIVERY_FEE = "TAXA_DE_ENTREGA"
COL_SERVICE_FEE = "TAXA_DE_SERVIÇO"
COL_IFOOD_PROMO = "PROMOCAO_CUSTEADA_PELO_IFOOD"
COL_STORE_PROMO = "PROMOCAO_CUSTEADA_PELA_LOJA"
COL_IFOOD_COMMISSION_PERC = "PERCENTUAL_COMISSAO_IFOOD"
COL_IFOOD_COMMISSION_VALUE = "VALOR_COMISSAO_IFOOD"
COL_PAYMENT_TX_PERC = "PERCENTUAL_PELA_TRANSAÇÃO_DO_PAGAMENTO"
COL_PAYMENT_TX_VALUE = "COMISSAO_PELA_TRANSACAO_DO_PAGAMENTO"
COL_REPASSE_PLAN_PERC = "PERCENTUAL_TAXA_PLANO_DE_REPASSE_EM_1_SEMANA"
COL_REPASSE_PLAN_VALUE = "VALOR_TAXA_PLANO_DE_REPASSE_EM_1_SEMANA"
COL_CALC_BASE = "BASE_DE_CALCULO"
COL_GROSS_VALUE = "VALOR_BRUTO"
COL_DELIVERY_REQUEST = "SOLICITACAO_DE_SERVICOS_DE_ENTREGA_IFOOD"
COL_DELIVERY_DISCOUNT = "DESCONTO_NA_SOLICITACAO_DE_ENTREGA_IFOOD"
COL_NET_VALUE = "VALOR_LIQUIDO"
COL_EVENT_VALUE = "VALOR_OCORRENCIA"
BUCKET_NAME = 'ifood-reports'

# --- Funções Auxiliares (copiadas do script original) ---

def update_file_status(file_record_id: str, status: str, error_message: str = None):
    logging.info(f"-> Atualizando status do arquivo {file_record_id} para '{status}'...")
    if error_message:
        logging.warning(f"   Com a mensagem de erro: {str(error_message)[:200]}...")
    try:
        update_data = {
            'status': status,
            'processed_at': datetime.datetime.now().isoformat(),
            'error_message': error_message
        }
        supabase.table('received_files').update(update_data).eq('id', file_record_id).execute()
    except Exception as e:
        logging.error(f"   ERRO CRÍTICO ao atualizar status do arquivo {file_record_id}: {e}")
        raise

def upload_file_to_storage(file_path: str, account_id: str, file_id: str, original_filename: str) -> str:
    logging.info(f"-> Fazendo upload do arquivo '{original_filename}' para o Supabase Storage...")
    try:
        storage_file_path = f"{account_id}/{original_filename}"
        with open(file_path, 'rb') as f:
            supabase.storage.from_("ifood-reports").upload(
                path=storage_file_path,
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        return storage_file_path
    except Exception as e:
        update_file_status(file_id, 'error', f"Falha no upload: {e}")
        raise IOError(f"Falha ao fazer upload do arquivo para o Supabase Storage: {e}")

def read_and_clean_data(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine='openpyxl')
    expected_columns = [COL_STORE_ID, COL_ORDER_ID, COL_ORDER_DATE]
    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias não encontradas: {', '.join(missing_cols)}.")
    return df

def to_iso(val):
    if pd.isna(val): return None
    try: return pd.to_datetime(val).isoformat()
    except: return None

def to_float(val):
    if pd.isna(val): return None
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        val = val.strip().replace('R$', '').replace('%', '').strip()
        if '.' in val and ',' in val: val = val.replace('.', '').replace(',', '.')
        else: val = val.replace(',', '.')
        try: return float(val)
        except: return None
    return None

def to_str(val):
    if pd.isna(val) or val == 'nan': return None
    return str(val)

def save_sales_data_to_db(account_id: str, file_record_id: str, df: pd.DataFrame):
    records = []
    for _, row in df.iterrows():
        order_id = to_str(row.get(COL_ORDER_ID))
        if not order_id: continue
        records.append({
            'account_id': account_id,
            'received_file_id': file_record_id,
            'loja_id': to_str(row.get(COL_STORE_ID)),
            'nome_da_loja': to_str(row.get(COL_STORE_NAME)),
            'tipo_de_faturamento': to_str(row.get(COL_BILLING_TYPE)),
            'canal_de_vendas': to_str(row.get(COL_SALES_CHANNEL)),
            'numero_pedido': to_str(row.get(COL_ORDER_NUMBER)),
            'pedido_id_completo': order_id,
            'data_do_pedido_ocorrencia': to_iso(row.get(COL_ORDER_DATE)),
            'data_de_conclusao': to_iso(row.get(COL_CONFIRMATION_DATE)),
            'data_de_repasse': to_iso(row.get(COL_REPASSE_DATE)),
            'origem_de_forma_de_pagamento': to_str(row.get(COL_PAYMENT_ORIGIN)),
            'formas_de_pagamento': to_str(row.get(COL_PAYMENT_METHOD)),
            'total_do_pedido': to_float(row.get(COL_TOTAL_ORDER_VALUE)),
            'valor_dos_itens': to_float(row.get(COL_ITEMS_VALUE)),
            'taxa_de_entrega': to_float(row.get(COL_DELIVERY_FEE)),
            'taxa_de_servico': to_float(row.get(COL_SERVICE_FEE)),
            'promocao_custeada_pelo_ifood': to_float(row.get(COL_IFOOD_PROMO)),
            'promocao_custeada_pela_loja': to_float(row.get(COL_STORE_PROMO)),
            'percentual_comissao_ifood': to_float(row.get(COL_IFOOD_COMMISSION_PERC)),
            'valor_comissao_ifood': to_float(row.get(COL_IFOOD_COMMISSION_VALUE)),
            'percentual_pela_transacao_do_pagamento': to_float(row.get(COL_PAYMENT_TX_PERC)),
            'comissao_pela_transacao_do_pagamento': to_float(row.get(COL_PAYMENT_TX_VALUE)),
            'percentual_taxa_plano_repasse_1_semana': to_float(row.get(COL_REPASSE_PLAN_PERC)),
            'valor_taxa_plano_repasse_1_semana': to_float(row.get(COL_REPASSE_PLAN_VALUE)),
            'base_de_calculo': to_float(row.get(COL_CALC_BASE)),
            'valor_bruto': to_float(row.get(COL_GROSS_VALUE)),
            'solicitacao_servicos_entrega_ifood': to_float(row.get(COL_DELIVERY_REQUEST)),
            'desconto_solicitacao_entrega_ifood': to_float(row.get(COL_DELIVERY_DISCOUNT)),
            'valor_liquido': to_float(row.get(COL_NET_VALUE)),
            'valor_ocorrencia': to_float(row.get(COL_EVENT_VALUE)),
            'raw_data': json.dumps(row.astype(str).to_dict(), ensure_ascii=False)
        })
    if records:
        supabase.table('sales_data').upsert(records, on_conflict='account_id,pedido_id_completo', ignore_duplicates=True).execute()

def update_daily_kpis(account_id: str, df: pd.DataFrame):
    df['kpi_date'] = pd.to_datetime(df[COL_ORDER_DATE], errors='coerce').dt.date
    df.dropna(subset=['kpi_date'], inplace=True)
    unique_dates = [d.strftime('%Y-%m-%d') for d in df['kpi_date'].unique()]
    if unique_dates:
        supabase.rpc('recalculate_daily_kpis_for_dates', {'p_account_id': account_id, 'p_dates': unique_dates}).execute()

def orchestrate_report_processing(file_path: str, account_id: str, original_filename: str):
    logging.info(f"--- INICIANDO PROCESSAMENTO DO ARQUIVO {original_filename} ---")
    file_record_id = None
    try:
        logging.info("Etapa 1: Criando registro de rastreamento...")
        insert_response = supabase.table('received_files').insert({
            'account_id': account_id,
            'original_file_name': original_filename,
            'status': 'received',
            'source': 'azure_function'
        }).execute()
        file_record_id = insert_response.data[0]['id']

        logging.info("Etapa 2: Fazendo upload do arquivo para o Storage...")
        upload_file_to_storage(file_path, account_id, file_record_id, original_filename)

        update_file_status(file_record_id, 'processing')
        logging.info("Etapa 3: Lendo e limpando dados da planilha...")
        df = read_and_clean_data(file_path)

        logging.info("Etapa 4: Salvando dados de vendas no banco...")
        save_sales_data_to_db(account_id, file_record_id, df)

        logging.info("Etapa 5: Atualizando KPIs diários...")
        update_daily_kpis(account_id, df)

        update_file_status(file_record_id, 'processed')
        logging.info(f"--- PROCESSAMENTO CONCLUÍDO COM SUCESSO ---")
        return {"status": "success", "message": f"Arquivo {original_filename} processado com sucesso."}

    except Exception as e:
        error_message = f"Erro no processamento: {e}"
        logging.error(error_message, exc_info=True)
        if file_record_id:
            update_file_status(file_record_id, 'error', str(e))
        # Retorna um dicionário de erro que será convertido em JSON
        return {"status": "error", "message": error_message}

# --- Rota Principal (Vercel/Flask) ---
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def handler(path):
    if request.method == 'GET':
        return jsonify({'status': 'ok', 'message': 'Function is ready to receive POST requests.'}), 200

    file_record_id = None
    try:
        # O n8n enviará os dados como 'multipart/form-data'
        post_req = request.form
        account_id = post_req.get('account_id')
        phone_number = post_req.get('phone_number') # Guardado para uso futuro
        
        # Acessa o arquivo enviado
        file = request.files.get('file')

        if not all([account_id, phone_number, file]):
            return jsonify({"status": "error", "message": "Parâmetros ausentes. É necessário 'account_id', 'phone_number' e um arquivo 'file'."}), 400

        # Salva o arquivo em um local temporário para processamento
        original_filename = file.filename
        file_bytes = file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1]) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name

        logging.info(f"Arquivo '{original_filename}' salvo temporariamente em '{temp_file_path}'.")

        # Chama a função principal de orquestração
        result = orchestrate_report_processing(temp_file_path, account_id, original_filename)

        # Limpa o arquivo temporário
        os.remove(temp_file_path)

        # Retorna o resultado como JSON
        return jsonify(result), 200 if result['status'] == 'success' else 500

    except Exception as e:
        logging.error(f"Erro inesperado na função principal: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Erro interno no servidor: {e}"}), 500
