# Documento de Especificação: Lógica de Cálculo de KPIs Diários

## 1. Objetivo

Este documento detalha a estrutura e a lógica de cálculo para a tabela `daily_kpis`. O objetivo é criar uma tabela consolidada que sirva como fonte única e precisa para todos os relatórios, utilizando uma **arquitetura de trigger** no banco de dados para garantir cálculos automáticos e em tempo real.

## 2. Arquitetura da Solução

A solução será implementada em três partes, diretamente no Supabase:

1.  **Nova Tabela `daily_kpis`**: Uma tabela redesenhada para armazenar os dados agregados.
2.  **Função PostgreSQL (`calculate_and_upsert_daily_kpi`)**: Uma função que contém toda a lógica de negócio para calcular os KPIs de um único dia para uma única loja.
3.  **Trigger (`on_sales_data_change`)**: Um gatilho que executa a função automaticamente sempre que um novo dado é inserido ou atualizado na tabela `sales_data`.

---

## 3. Novo Schema da Tabela `daily_kpis`

A tabela `daily_kpis` será recriada com a seguinte estrutura para acomodar todos os requisitos.

```sql
CREATE TABLE public.daily_kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    kpi_date DATE NOT NULL,
    store_id VARCHAR(255) NOT NULL,
    store_name VARCHAR(255),
    
    -- Métricas de Vendas Totais
    total_sales NUMERIC(14, 2) DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    
    -- Detalhamento das Vendas (JSONB)
    sales_by_revenue_type JSONB, -- Ex: {"VENDA": 1000.00, "CANCELAMENTO": -50.00}
    sales_by_payment_origin JSONB, -- Ex: {"IFOOD": 800.00, "LOJA": 150.00}
    payment_methods_breakdown JSONB, -- Ex: {"ifood": {"credit_card": 500}, "loja": {"credit_card": 150}}
    
    -- Custos e Taxas
    total_ifood_delivery_fees NUMERIC(14, 2) DEFAULT 0,
    total_commission_and_fees NUMERIC(14, 2) DEFAULT 0,
    commission_percentage NUMERIC(5, 2) DEFAULT 0, -- Percentual médio da comissão
    
    -- Promoções
    total_ifood_promo NUMERIC(14, 2) DEFAULT 0,
    total_store_promo NUMERIC(14, 2) DEFAULT 0,
    
    -- Métricas de Entrega
    free_deliveries_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Constraint de Unicidade: Garante um registro por loja por dia
    UNIQUE (account_id, kpi_date, store_id)
);
```

---

## 4. Lógica da Função de Cálculo (`calculate_and_upsert_daily_kpi`)

A função será acionada pelo trigger e receberá como parâmetros `account_id`, `kpi_date` e `store_id` do registro que foi alterado.

| Coluna KPI (daily_kpis)         | Coluna(s) Fonte (sales_data)        | Lógica de Cálculo e Agregação (Dentro da Função SQL)                                                                                                                                     |
|---------------------------------|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `store_name`                    | `nome_da_loja`                      | `SELECT nome_da_loja ... LIMIT 1` - Pega o nome mais recente.                                                                                                                            |
| `total_sales`                   | `valor_total_do_pedido`             | `SUM(valor_total_do_pedido)`                                                                                                                                                             |
| `total_orders`                  | `pedido_id_completo`                | `COUNT(DISTINCT pedido_id_completo)`                                                                                                                                                     |
| `sales_by_revenue_type`         | `tipo_de_lancamento`, `valor_total_do_pedido` | Agrega a soma por `tipo_de_lancamento` em um objeto JSON.                                                                                                                               |
| `sales_by_payment_origin`       | `origem_forma_de_pagamento`, `valor_total_do_pedido` | Agrega a soma por `origem_forma_de_pagamento` em um objeto JSON.                                                                                                                        |
| `payment_methods_breakdown`     | `formas_de_pagamento` (JSON)        | Itera sobre o JSON de `formas_de_pagamento` de cada pedido, somando os valores por bandeira e por origem (iFood/Loja) em um objeto JSON aninhado.                                           |
| `total_ifood_delivery_fees`     | `solicitacao_de_servicos_entrega_ifood` | `SUM(solicitacao_de_servicos_entrega_ifood)`                                                                                                                                             |
| `total_commission_and_fees`     | `valor_da_comissao`                 | `SUM(valor_da_comissao)`                                                                                                                                                                 |
| `commission_percentage`         | `valor_da_comissao`, `valor_total_do_pedido` | `(SUM(valor_da_comissao) / SUM(valor_total_do_pedido)) * 100`. Tratar divisão por zero.                                                                                                 |
| `total_ifood_promo`             | `promocao_ifood`                    | `SUM(promocao_ifood)`                                                                                                                                                                    |
| `total_store_promo`             | `promocao_da_loja`                  | `SUM(promocao_da_loja)`                                                                                                                                                                  |
| `free_deliveries_count`         | `solicitacao_de_servicos_entrega_ifood` | `COUNT(*) WHERE solicitacao_de_servicos_entrega_ifood = 0`                                                                                                                               |

---

## 5. Definição do Trigger (`on_sales_data_change`)

O trigger será configurado para ser executado `AFTER INSERT OR UPDATE` na tabela `sales_data`, para cada linha (`FOR EACH ROW`). Ele chamará a função de cálculo, passando os dados da linha que foi modificada (`NEW.account_id`, `NEW.data_do_pedido`, `NEW.id_loja`).
