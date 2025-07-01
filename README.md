# Concierge de Vendas iFood

Este projeto automatiza o processamento de relatórios de vendas do iFood enviados via WhatsApp, realizando upload seguro para o Supabase Storage, análise de KPIs e atualização de status em banco de dados.

## Fluxo Geral

1. O usuário envia uma planilha de vendas (.xlsx) via WhatsApp.
2. O n8n salva o arquivo localmente e executa o script Python `process_report.py`.
3. O script:
   - Faz upload do arquivo para o Supabase Storage.
   - Processa os dados da planilha.
   - Calcula KPIs (faturamento, ticket médio, etc).
   - Atualiza o status do arquivo e os KPIs no banco de dados.
   - Retorna um resumo para ser enviado ao usuário.

## Requisitos

- Python 3.10+
- Supabase (URL e chave service_role)
- n8n para orquestração
- Variáveis de ambiente configuradas em `.env` na raiz do projeto:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1...
```

## Formato da Planilha Esperada

A planilha deve conter **exatamente** as seguintes colunas (nomes idênticos):

- ID DO PEDIDO
- N° PEDIDO
- DATA
- RESTAURANTE
- ID DO RESTAURANTE
- TAXA DE ENTREGA
- VALOR DOS ITENS
- INCENTIVO PROMOCIONAL DO IFOOD
- INCENTIVO PROMOCIONAL DA LOJA
- TAXA DE SERVIÇO
- TOTAL DO PARCEIRO
- TOTAL DO PEDIDO
- FORMAS DE PAGAMENTO

Outras colunas são ignoradas, mas estas são obrigatórias para o processamento correto.

## Execução Manual do Script

```bash
.venv/bin/python3 scripts/process_report.py \
  --file-path "/caminho/para/arquivo.xlsx" \
  --account-id "<UUID da conta>" \
  --file-id "<UUID do registro na tabela received_files>"
```

## Dicas de Troubleshooting

- **Erro de política de segurança/RLS:** Verifique se a chave SUPABASE_KEY é a `service_role` copiada corretamente do painel do Supabase.
- **Erro de coluna não encontrada:** Confirme que os títulos das colunas na planilha estão idênticos aos listados acima.
- **Arquivo não aparece no bucket:** Verifique logs do script e permissões do bucket no Supabase.

## Próximos Passos Sugeridos

- Implementar notificações automáticas de sucesso/erro via WhatsApp.
- Permitir múltiplos formatos de planilha (ex: CSV).
- Dashboard web para consulta de KPIs históricos.
- Permissões avançadas por usuário.

---

Para dúvidas ou para sugerir melhorias, abra uma issue ou entre em contato com o mantenedor do projeto.
