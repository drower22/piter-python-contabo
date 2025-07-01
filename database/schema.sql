-- Tabela para representar as contas dos clientes (empresas)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela para os usuários (contatos) associados a cada conta
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    user_name TEXT,
    whatsapp_number VARCHAR(20) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'submitter')), -- 'owner' recebe relatórios, 'submitter' apenas envia
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela para rastrear os arquivos recebidos
CREATE TABLE received_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    submitted_by_user_id UUID REFERENCES users(id), -- Quem enviou
    file_name TEXT,
    status VARCHAR(50) CHECK (status IN ('pending', 'success', 'error')),
    storage_path VARCHAR(512),
    received_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Tabela para armazenar os dados de conciliação financeira do iFood
CREATE TABLE conciliation_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    received_file_id UUID REFERENCES received_files(id),

    competencia VARCHAR(20),
    data_fato_gerador TIMESTAMPTZ,
    fato_gerador TEXT,
    tipo_lancamento TEXT,
    descricao_lancamento TEXT,
    valor DECIMAL(14,2),
    base_calculo DECIMAL(14,2),
    percentual_taxa VARCHAR(20),
    pedido_associado_ifood VARCHAR(50),
    pedido_associado_ifood_curto VARCHAR(50),
    pedido_associado_externo VARCHAR(50),
    motivo_cancelamento TEXT,
    descricao_ocorrencia TEXT,
    data_criacao_pedido_associado TIMESTAMPTZ,
    data_repasse_esperada TIMESTAMPTZ,
    valor_transacao DECIMAL(14,2),
    loja_id VARCHAR(50),
    loja_id_curto VARCHAR(50),
    loja_id_externo VARCHAR(50),
    cnpj VARCHAR(32),
    titulo TEXT,
    data_faturamento TIMESTAMPTZ,
    data_apuracao_inicio TIMESTAMPTZ,
    data_apuracao_fim TIMESTAMPTZ,
    valor_cesta_inicial DECIMAL(14,2),
    valor_cesta_final DECIMAL(14,2),
    responsavel_transacao TEXT,
    canal_vendas TEXT,
    impacto_no_repasse TEXT,
    parcela_pagamento VARCHAR(50),

    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela para armazenar os dados de vendas do relatório financeiro
CREATE TABLE sales_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    received_file_id UUID REFERENCES received_files(id),

    loja_id VARCHAR(50),
    nome_da_loja TEXT,
    tipo_de_faturamento TEXT,
    canal_de_vendas TEXT,
    numero_pedido VARCHAR(50),
    pedido_id_completo TEXT,
    data_do_pedido_ocorrencia TIMESTAMPTZ,
    data_de_conclusao TIMESTAMPTZ,
    data_de_repasse TIMESTAMPTZ,
    origem_de_forma_de_pagamento TEXT,
    formas_de_pagamento TEXT,
    total_do_pedido DECIMAL(14, 2),
    valor_dos_itens DECIMAL(14, 2),
    taxa_de_entrega DECIMAL(14, 2),
    taxa_de_servico DECIMAL(14, 2),
    promocao_custeada_pelo_ifood DECIMAL(14, 2),
    promocao_custeada_pela_loja DECIMAL(14, 2),
    percentual_comissao_ifood DECIMAL(10, 4),
    valor_comissao_ifood DECIMAL(14, 2),
    percentual_pela_transacao_do_pagamento DECIMAL(10, 4),
    comissao_pela_transacao_do_pagamento DECIMAL(14, 2),
    percentual_taxa_plano_repasse_1_semana DECIMAL(10, 4),
    valor_taxa_plano_repasse_1_semana DECIMAL(14, 2),
    base_de_calculo DECIMAL(14, 2),
    valor_bruto DECIMAL(14, 2),
    solicitacao_servicos_entrega_ifood DECIMAL(14, 2),
    desconto_solicitacao_entrega_ifood DECIMAL(14, 2),
    valor_liquido DECIMAL(14, 2),
    valor_ocorrencia DECIMAL(14, 2),

    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT sales_data_unique_order UNIQUE (account_id, pedido_id_completo)
);

-- Tabela para registrar as mensagens enviadas
CREATE TABLE message_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    sent_to_user_id UUID REFERENCES users(id), -- Para quem foi a mensagem
    message_type VARCHAR(50), -- summary, reminder, error
    content TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela para armazenar templates de mensagens (sem alterações)
CREATE TABLE message_templates (
    template_name VARCHAR(50) PRIMARY KEY,
    template_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inserir templates padrão (sem alterações)
INSERT INTO message_templates (template_name, template_text) VALUES
('success_summary', 'Olá! Aqui está o resumo de suas vendas do dia {report_date_str}:\n\n💰 Faturamento Total: R$ {total_revenue:,.2f}\n📦 Número de Pedidos: {order_count}\n🎟️ Ticket Médio: R$ {average_ticket:,.2f}\n\n📊 Variação vs. semana anterior: {revenue_change:+.2f}%\n\n{insight}'),
('daily_reminder', '📢 Bom dia! Ainda não recebi sua planilha de hoje. Assim que você enviar, te mando o resumo rapidinho.'),
('error_invalid_column', '🚫 Não consegui ler sua planilha. Parece que a coluna ''{column_name}'' está faltando. Pode dar uma conferida se exportou no formato correto?'),
('error_generic', '🚫 Oops! Ocorreu um erro inesperado ao processar sua planilha. Minha equipe já foi notificada. Por favor, tente novamente ou aguarde um contato.');

-- Tabela para armazenar KPIs diários calculados
CREATE TABLE daily_kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    kpi_date DATE NOT NULL,

    total_sales DECIMAL(14, 2) DEFAULT 0,
    total_orders_by_channel JSONB,
    total_sales_by_payment_method JSONB,
    free_deliveries_value DECIMAL(14, 2) DEFAULT 0,
    free_deliveries_count INT DEFAULT 0,
    total_store_promo DECIMAL(14, 2) DEFAULT 0,
    total_ifood_promo DECIMAL(14, 2) DEFAULT 0,
    total_commission_and_fees DECIMAL(14, 2) DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT daily_kpis_account_date_unique UNIQUE (account_id, kpi_date)
);

-- Função para recalcular os KPIs diários para um determinado conjunto de datas
ALTER TABLE public.daily_kpis
ADD COLUMN IF NOT EXISTS commission_percentage numeric;

CREATE OR REPLACE FUNCTION public.recalculate_daily_kpis_for_dates(p_account_id uuid, p_dates date[])
RETURNS void
LANGUAGE sql
AS $$
    INSERT INTO public.daily_kpis (
        account_id,
        kpi_date,
        total_sales,
        total_orders_by_channel,
        total_sales_by_payment_method,
        free_deliveries_count,
        free_deliveries_value,
        total_store_promo,
        total_ifood_promo,
        total_commission_and_fees,
        commission_percentage,
        updated_at
    )
    WITH daily_data AS (
        SELECT
            sd.account_id,
            sd.data_do_pedido_ocorrencia::date as kpi_date,
            (CASE
                WHEN TRIM(UPPER(sd.tipo_de_faturamento)) = 'PEDIDO' THEN 1
                WHEN TRIM(UPPER(sd.tipo_de_faturamento)) IN ('PEDIDO CANCELADO', 'ESTORNO POR CANCELAMENTO DE PEDIDO') THEN -1
                ELSE 0
            END) as multiplier,
            sd.total_do_pedido,
            sd.canal_de_vendas,
            sd.formas_de_pagamento,
            (CASE WHEN sd.taxa_de_entrega = 0 AND TRIM(UPPER(sd.tipo_de_faturamento)) = 'PEDIDO' THEN 1 ELSE 0 END) as free_delivery_flag,
            sd.promocao_custeada_pela_loja,
            sd.promocao_custeada_pelo_ifood,
            sd.valor_comissao_ifood,
            sd.comissao_pela_transacao_do_pagamento,
            sd.valor_taxa_plano_repasse_1_semana
        FROM public.sales_data as sd
        WHERE sd.account_id = p_account_id AND sd.data_do_pedido_ocorrencia::date = ANY(p_dates)
    ),
    aggregated_by_day AS (
        SELECT
            kpi_date,
            SUM(total_do_pedido * multiplier) as total_sales,
            SUM(free_delivery_flag) as free_deliveries_count,
            SUM(promocao_custeada_pela_loja * multiplier) as total_store_promo,
            SUM(promocao_custeada_pelo_ifood * multiplier) as total_ifood_promo,
            SUM((valor_comissao_ifood + comissao_pela_transacao_do_pagamento) * multiplier) as total_commission_and_fees
        FROM daily_data
        GROUP BY kpi_date
    ),
    orders_by_channel_agg AS (
        SELECT
            kpi_date,
            jsonb_object_agg(canal_de_vendas, order_count) FILTER (WHERE canal_de_vendas IS NOT NULL) as total_orders_by_channel
        FROM (
            SELECT kpi_date, canal_de_vendas, SUM(multiplier) as order_count
            FROM daily_data
            WHERE multiplier != 0
            GROUP BY kpi_date, canal_de_vendas
        ) sub
        GROUP BY kpi_date
    ),
    sales_by_payment_agg AS (
        SELECT
            kpi_date,
            jsonb_object_agg(formas_de_pagamento, sales_total) FILTER (WHERE formas_de_pagamento IS NOT NULL) as total_sales_by_payment_method
        FROM (
            SELECT kpi_date, formas_de_pagamento, SUM(total_do_pedido * multiplier) as sales_total
            FROM daily_data
            WHERE multiplier != 0
            GROUP BY kpi_date, formas_de_pagamento
        ) sub
        GROUP BY kpi_date
    )
    SELECT
        p_account_id,
        d.kpi_date,
        d.total_sales,
        o.total_orders_by_channel,
        s.total_sales_by_payment_method,
        d.free_deliveries_count,
        0.00::numeric as free_deliveries_value,
        d.total_store_promo,
        d.total_ifood_promo,
        d.total_commission_and_fees,
        CASE WHEN d.total_sales IS NULL OR d.total_sales = 0 THEN NULL
             ELSE ABS(d.total_commission_and_fees) / d.total_sales * 100
        END AS commission_percentage,
        NOW()
    FROM aggregated_by_day d
    LEFT JOIN orders_by_channel_agg o ON d.kpi_date = o.kpi_date
    LEFT JOIN sales_by_payment_agg s ON d.kpi_date = s.kpi_date
    ON CONFLICT (account_id, kpi_date)
    DO UPDATE SET
        total_sales = EXCLUDED.total_sales,
        total_orders_by_channel = EXCLUDED.total_orders_by_channel,
        total_sales_by_payment_method = EXCLUDED.total_sales_by_payment_method,
        free_deliveries_count = EXCLUDED.free_deliveries_count,
        free_deliveries_value = EXCLUDED.free_deliveries_value,
        total_store_promo = EXCLUDED.total_store_promo,
        total_ifood_promo = EXCLUDED.total_ifood_promo,
        total_commission_and_fees = EXCLUDED.total_commission_and_fees,
        commission_percentage = EXCLUDED.commission_percentage,
        updated_at = NOW();
$$;

