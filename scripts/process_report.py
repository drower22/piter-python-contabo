import pandas as pd
import sys
import os
import datetime
from datetime import date, timedelta
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import argparse

# --- Configuração do Supabase ---
# Torna o carregamento do .env à prova de falhas, encontrando o caminho absoluto
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Erro Crítico: Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não foram encontradas.", file=sys.stderr)
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Mapeamento de nomes de colunas para constantes (EXATAMENTE como no cabeçalho da planilha)
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

# --- Funções de Banco de Dados, Storage e Templates ---

def update_file_status(file_record_id: str, status: str, error_message: str = None):
    """Atualiza o status de um arquivo processado na tabela received_files."""
    print(f"-> Atualizando status do arquivo {file_record_id} para '{status}'...")
    if error_message:
        # Limita a mensagem de erro para não poluir o log
        print(f"   Com a mensagem de erro: {str(error_message)[:200]}...")
        
    try:
        update_data = {
            'status': status,
            'processed_at': datetime.datetime.now().isoformat(),
            'error_message': error_message
        }
        response = supabase.table('received_files').update(update_data).eq('id', file_record_id).execute()
        
        if not response.data:
            print(f"   AVISO: Nenhum registro encontrado para o file_record_id {file_record_id} ao tentar atualizar o status.", file=sys.stderr)
        else:
            print(f"   Status do arquivo {file_record_id} atualizado com sucesso no banco.")

    except Exception as e:
        print(f"   ERRO CRÍTICO ao atualizar status do arquivo {file_record_id}: {e}", file=sys.stderr)
        # Re-lança a exceção para que o fluxo principal saiba que algo deu errado.
        raise

def upload_file_to_storage(file_path: str, account_id: str, file_id: str) -> str:
    """Faz o upload de um arquivo para o Supabase Storage com logs detalhados."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo local não encontrado em: {file_path}")

        file_name = os.path.basename(file_path)
        storage_file_path = f"{account_id}/{file_name}"

        with open(file_path, 'rb') as f:
            # O SDK do Supabase espera um objeto de arquivo binário
            response = supabase.storage.from_("ifood-reports").upload(
                path=storage_file_path,
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"} 
            )
        
        return storage_file_path
    except Exception as e:
        # Captura exceções de upload e as propaga
        update_file_status(file_id, 'error', f"Falha no upload: {e}")
        raise IOError(f"Falha ao fazer upload do arquivo para o Supabase Storage: {e}")

def get_message_template(template_name: str, fallback: str) -> str:
    """Busca um template de mensagem no banco de dados."""
    try:
        response = supabase.table('message_templates').select('template_text').eq('template_name', template_name).single().execute()
        return response.data['template_text']
    except Exception as e:
        print(f"Erro ao buscar template '{template_name}', usando fallback: {e}", file=sys.stderr)
        return fallback

def get_kpis_from_db(account_id: str, report_date: date):
    """Busca KPIs de uma data específica no banco de dados."""
    try:
        response = supabase.table('daily_kpis').select('*').eq('account_id', account_id).eq('report_date', report_date.isoformat()).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Erro ao buscar KPIs no DB: {e}", file=sys.stderr)
        return None



def to_iso(val):
    """Converte valor para data e hora em formato ISO 8601, retornando None em caso de falha."""
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val).isoformat()
    except (ValueError, TypeError):
        # Se a conversão falhar, avisa e retorna None para que seja inserido NULL no DB
        print(f"DEBUG: Não foi possível converter '{val}' para data. Será salvo como NULO.")
        return None

def to_float(val):
    """Converte moeda brasileira (ex: 'R$ 1.999,00' ou '2,60%') para float."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip()
        is_percentage = '%' in val
        
        # Remove R$, % e espaços. Troca vírgula de decimal por ponto.
        # Importante: não remove o ponto de milhar ainda.
        cleaned_val = val.replace('R$', '').replace('%', '').strip()
        # Converte o formato brasileiro (1.000,50) para o padrão (1000.50)
        if '.' in cleaned_val and ',' in cleaned_val:
            cleaned_val = cleaned_val.replace('.', '').replace(',', '.')
        else:
            cleaned_val = cleaned_val.replace(',', '.')

        if not cleaned_val:
            return None
        try:
            num = float(cleaned_val)
            if is_percentage:
                return num / 100.0
            return num
        except (ValueError, TypeError):
            print(f"DEBUG: Não foi possível converter '{val}' para float. Será salvo como NULO.")
            return None
    return None

def to_str(val):
    if pd.isna(val) or val == 'nan':
        return None
    return str(val)

def read_and_clean_data(file_path: str) -> pd.DataFrame:
    """Lê o arquivo Excel e valida as colunas esperadas."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado no caminho: {file_path}")

    df = pd.read_excel(file_path, engine='openpyxl')

    # Lista de todas as colunas esperadas
    expected_columns = [
        COL_STORE_ID, COL_STORE_NAME, COL_BILLING_TYPE, COL_SALES_CHANNEL,
        COL_ORDER_NUMBER, COL_ORDER_ID, COL_ORDER_DATE, COL_CONFIRMATION_DATE,
        COL_REPASSE_DATE, COL_PAYMENT_ORIGIN, COL_PAYMENT_METHOD,
        COL_TOTAL_ORDER_VALUE, COL_ITEMS_VALUE, COL_DELIVERY_FEE,
        COL_SERVICE_FEE, COL_IFOOD_PROMO, COL_STORE_PROMO,
        COL_IFOOD_COMMISSION_PERC, COL_IFOOD_COMMISSION_VALUE,
        COL_PAYMENT_TX_PERC, COL_PAYMENT_TX_VALUE, COL_REPASSE_PLAN_PERC,
        COL_REPASSE_PLAN_VALUE, COL_CALC_BASE, COL_GROSS_VALUE,
        COL_DELIVERY_REQUEST, COL_DELIVERY_DISCOUNT, COL_NET_VALUE,
        COL_EVENT_VALUE
    ]

    # Verifica se todas as colunas esperadas estão presentes
    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        # Se colunas estiverem faltando, lança um erro claro
        raise ValueError(f"O arquivo não pôde ser processado. As seguintes colunas obrigatórias não foram encontradas: {', '.join(missing_cols)}. Verifique se o relatório exportado está no formato correto.")

    return df

def save_sales_data_to_db(account_id: str, file_record_id: str, df: pd.DataFrame):
    """
    Salva os dados do relatório financeiro na tabela sales_data, ignorando duplicatas.
    Usa a funcionalidade 'upsert' do Supabase para inserir apenas registros novos,
    baseado em uma constraint de unicidade (account_id, pedido_id_completo).
    """
    records_to_insert = []

    for index, row in df.iterrows():
        # Validação para garantir que o ID do pedido não é nulo, o que violaria a constraint
        order_id = to_str(row.get(COL_ORDER_ID))
        if not order_id:
            print(f"DEBUG: Ignorando linha {index + 2} por não ter um 'pedido_id_completo'.")
            continue

        record = {
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
        }
        records_to_insert.append(record)

    if not records_to_insert:
        print("Nenhum registro válido para inserir após o processamento.")
        return

    try:
        print(f"Iniciando inserção de {len(records_to_insert)} registros em lote com de-duplicação...")
        
        # O método 'upsert' com 'ignore_duplicates=True' executa um 'INSERT ... ON CONFLICT DO NOTHING'.
        # 'on_conflict' especifica as colunas da constraint de unicidade.
        response = supabase.table('sales_data').upsert(
            records_to_insert,
            on_conflict='account_id,pedido_id_completo',
            ignore_duplicates=True
        ).execute()
        
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Erro do Supabase ao tentar inserir com de-duplicação: {response.error.message}")
        
        # A resposta de um upsert com ignore_duplicates não retorna as linhas, então apenas logamos o sucesso.
        print(f"Operação de inserção em lote concluída. O banco de dados ignorou os registros duplicados.")

    except Exception as e:
        print(f"Erro ao salvar dados de vendas no DB: {e}", file=sys.stderr)
        if records_to_insert:
            print("DEBUG: Amostra do primeiro registro que seria inserido:")
            print(json.dumps(records_to_insert[0], indent=2, ensure_ascii=False))
        raise e


def generate_summary_message(kpis: dict, account_id: str) -> str:
    """Cria uma mensagem de resumo com base nos KPIs."""
    report_date_str = pd.to_datetime(kpis.get('report_date')).strftime('%d/%m/%Y')
    total_revenue = kpis.get('total_revenue', 0)
    order_count = kpis.get('order_count', 0)
    average_ticket = kpis.get('average_ticket', 0)
    revenue_change = kpis.get('revenue_change_percentage', 0)
    insight = ""
    if revenue_change > 5:
        insight = "🚀 Ótima notícia! Suas vendas cresceram bem em comparação com a semana passada."
    elif revenue_change < -5:
        insight = "📉 Atenção! Suas vendas tiveram uma queda em relação à semana passada. Vale a pena investigar o que aconteceu."
    else:
        insight = "😐 Suas vendas se mantiveram estáveis em comparação com a semana passada."

    template = get_message_template('success_summary', "Resumo: R$ {total_revenue:,.2f} em {order_count} pedidos.")
    message = template.format(
        report_date_str=report_date_str,
        total_revenue=total_revenue,
        order_count=order_count,
        average_ticket=average_ticket,
        revenue_change=revenue_change,
        insight=insight
    ).replace('R$', 'R$ ').replace('.,', ',').replace(',.', '.')

    return message

def update_daily_kpis(account_id: str, df: pd.DataFrame):
    """
    Identifica as datas afetadas no DataFrame e chama a função SQL 
    'recalculate_daily_kpis_for_dates' para recalcular os KPIs diretamente no banco.
    """
    print("Iniciando gatilho para recálculo de KPIs no banco de dados...")

    # Garante que a coluna de data está no formato correto e extrai as datas únicas
    df['kpi_date'] = pd.to_datetime(df[COL_ORDER_DATE], errors='coerce').dt.date
    df.dropna(subset=['kpi_date'], inplace=True)
    
    unique_dates = df['kpi_date'].unique()

    if len(unique_dates) == 0:
        print("Nenhuma data válida encontrada no arquivo para recalcular KPIs.")
        return

    # Converte as datas para o formato string 'YYYY-MM-DD' que a função SQL espera
    dates_to_recalculate = [d.strftime('%Y-%m-%d') for d in unique_dates]
    
    print(f"   - Datas afetadas: {', '.join(dates_to_recalculate)}")
    print(f"   - Chamando a função 'recalculate_daily_kpis_for_dates' no Supabase...")

    try:
        # Chama a função SQL via RPC (Remote Procedure Call)
        supabase.rpc(
            'recalculate_daily_kpis_for_dates',
            {'p_account_id': account_id, 'p_dates': dates_to_recalculate}
        ).execute()
        print("   - Recálculo de KPIs concluído com sucesso no banco de dados.")
    except Exception as e:
        print(f"   ERRO CRÍTICO ao chamar a função de recálculo de KPIs: {e}", file=sys.stderr)
        # Re-lança a exceção para que o bloco principal de tratamento de erros a capture
        raise

def process_financial_report(file_path: str, account_id: str, file_record_id: str):
    print(f"\n--- INICIANDO PROCESSAMENTO DO ARQUIVO ---")
    print(f"  - Arquivo: {os.path.basename(file_path)}")
    print(f"  - Account ID: {account_id}")
    print(f"  - File Record ID: {file_record_id}")
    print(f"-------------------------------------------")
    
    try:
        print("\n[ETAPA 1/5] Atualizando status para 'processing'...")
        update_file_status(file_record_id, 'processing')
        
        print("\n[ETAPA 2/5] Lendo e limpando dados da planilha...")
        df = read_and_clean_data(file_path)
        print(f"  - Leitura concluída. Encontradas {len(df)} linhas.")
        
        print("\n[ETAPA 3/5] Salvando dados de vendas no banco de dados...")
        save_sales_data_to_db(account_id, file_record_id, df)
        
        print("\n[ETAPA 4/5] Calculando e atualizando KPIs diários...")
        update_daily_kpis(account_id, df)
        
        print("\n[ETAPA 5/5] Atualizando status final para 'processed'...")
        update_file_status(file_record_id, 'processed')
        
        print(f"\n--- PROCESSAMENTO CONCLUÍDO COM SUCESSO ---")
        print(json.dumps({"status": "processed", "message": f"Arquivo {os.path.basename(file_path)} processado com sucesso."}))

    except Exception as e:
        error_message = f"Erro no processamento do arquivo {os.path.basename(file_path)}: {e}"
        print(f"\n--- ERRO NO PROCESSAMENTO ---", file=sys.stderr)
        print(f"  - Causa: {error_message}", file=sys.stderr)
        print(f"---------------------------------", file=sys.stderr)
        
        print("\n[ETAPA FINAL - FALHA] Atualizando status para 'error'...")
        update_file_status(file_record_id, 'error', str(e))
        
        print(json.dumps({"status": "error", "message": error_message}))
        sys.exit(1)

def main():
    """
    Função principal SIMPLIFICADA para processar o relatório SEM salvar no banco.
    1. Recebe os argumentos da linha de comando.
    2. Limpa e prepara os dados da planilha.
    3. Gera a mensagem de resumo com os KPIs.
    4. Imprime um JSON com o resumo para o n8n.
    """
    parser = argparse.ArgumentParser(description='Processa relatório financeiro do iFood.')
    parser.add_argument('--filepath', required=True, help='Caminho para o arquivo de relatório .xlsx temporário.')
    parser.add_argument('--account-id', required=True, help='ID da conta do usuário no Supabase.')
    # O número de telefone não é utilizado nesta versão simplificada, mas o argumento é mantido.
    parser.add_argument('--phone-number', required=True, help='Número de telefone do usuário.')
    args = parser.parse_args()

    try:
        # Etapa 1: Limpar e preparar os dados
        print("-> (Modo Simples) Limpando e preparando os dados...")
        df_cleaned = clean_and_prepare_data(args.filepath, args.account_id)
        print("   - Dados limpos com sucesso.")

        # Etapa 2: Gerar a mensagem de resumo
        print("-> (Modo Simples) Gerando mensagem de resumo...")
        # A função generate_summary_message não depende do banco de dados para os cálculos.
        summary_message = generate_summary_message(df_cleaned, args.account_id)
        print("   - Mensagem de resumo gerada.")

        # Etapa 3: Imprimir o resultado final como JSON para o n8n
        print("\n--- SUCESSO (Modo Simples) ---")
        print(json.dumps({
            "status": "success",
            "message": "Relatório processado com sucesso (modo de simulação).",
            "summary": summary_message
        }))

    except Exception as e:
        error_message = f"Erro ao processar o relatório (modo de simulação): {e}"
        print(f"\n--- ERRO CRÍTICO (Modo Simples) ---", file=sys.stderr)
        print(error_message, file=sys.stderr)
        
        # Imprime o JSON de erro final e encerra o script com código de erro
        print(json.dumps({"status": "error", "message": error_message}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()