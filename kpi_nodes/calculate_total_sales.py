import os
import sys
import psycopg2
from datetime import date

print("=== INÍCIO DO SCRIPT ===", file=sys.stderr)
print(f"Argumentos recebidos: {sys.argv}", file=sys.stderr)

if len(sys.argv) < 8:
    print("ERRO: Argumentos insuficientes. Uso: python calculate_total_sales.py <received_file_id> <account_id> <db_host> <db_name> <db_user> <db_password> <db_port>", file=sys.stderr)
    sys.exit(1)
else:
    received_file_id = sys.argv[1]
    account_id = sys.argv[2]
    db_host = sys.argv[3]
    db_name = sys.argv[4]
    db_user = sys.argv[5]
    db_password = sys.argv[6]
    db_port = sys.argv[7]
    print(f"received_file_id: {received_file_id}", file=sys.stderr)
    print(f"account_id: {account_id}", file=sys.stderr)
    print(f"db_host: {db_host}", file=sys.stderr)
    print(f"db_name: {db_name}", file=sys.stderr)
    print(f"db_user: {db_user}", file=sys.stderr)
    print(f"db_password: {db_password}", file=sys.stderr)
    print(f"db_port: {db_port}", file=sys.stderr)

def calculate_total_sales(received_file_id: str, account_id: str, db_host: str, db_name: str, db_user: str, db_password: str, db_port: str):
    """
    Calcula o total de vendas para um dado received_file_id e account_id
    e atualiza a tabela daily_kpis.
    """
    conn = None
    try:
        # Conexão com o banco de dados
        print("Tentando conectar ao banco...", file=sys.stderr)
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        cur = conn.cursor()

        # 1. Obter as datas únicas e o total de vendas para o received_file_id e account_id
        # Usamos SUM(total_do_pedido) conforme solicitado
        cur.execute("""
            SELECT
                data_do_pedido_ocorrencia::date AS kpi_date,
                SUM(total_do_pedido) AS total_sales_value
            FROM
                public.sales_data
            WHERE
                received_file_id = %s AND account_id = %s
            GROUP BY
                data_do_pedido_ocorrencia::date;
        """, (received_file_id, account_id))

        results = cur.fetchall()

        if not results:
            print(f"Nenhum dado encontrado para received_file_id: {received_file_id} e account_id: {account_id}")
            return

        for kpi_date, total_sales_value in results:
            # 2. Inserir/Atualizar o daily_kpis
            # A função recalculate_daily_kpis_for_dates no schema.sql
            # já lida com o ON CONFLICT. Vamos replicar a lógica aqui.
            # Para este KPI específico, só atualizaremos total_sales.
            cur.execute("""
                INSERT INTO public.daily_kpis (
                    account_id,
                    kpi_date,
                    total_sales,
                    updated_at
                ) VALUES (%s, %s, %s, NOW())
                ON CONFLICT (account_id, kpi_date) DO UPDATE SET
                    total_sales = EXCLUDED.total_sales,
                    updated_at = NOW();
            """, (account_id, kpi_date, total_sales_value))
            conn.commit()

    except Exception as e:
        print(f"ERRO ao executar o script: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            cur.close()
            conn.close()
            print("Conexão com o banco fechada. Fim do script.", file=sys.stderr)

if __name__ == "__main__":
    calculate_total_sales(received_file_id, account_id)
