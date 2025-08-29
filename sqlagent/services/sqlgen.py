import os
from typing import Tuple, Optional, List

# Placeholder: integrate your preferred LLM here (OpenAI, etc.)
# This function returns (sql, rationale)

def generate_sql(question: str, account_id: str, hint_tables: Optional[List[str]] = None) -> Tuple[str, str]:
    # Very naive baseline: map keywords to predefined SQL skeletons
    # Replace with LLM prompt that uses available schemas and tenant filters
    q = question.lower()
    if 'vendas' in q or 'sales' in q:
        sql = """
        select date_trunc('day', created_at) as dia, sum(amount) as total
        from sales
        where account_id = '{account_id}'
        group by 1
        order by 1 desc
        limit 30;
        """.strip().format(account_id=account_id)
        rationale = "Resumo diário de vendas dos últimos 30 registros para a conta."
    else:
        sql = f"select 1 as placeholder where '{account_id}' is not null;"
        rationale = "Placeholder: ajuste o mapeamento ou use o LLM para gerar a query correta."
    return sql, rationale
