# Página do Dashboard

Esta é a página principal da aplicação após o login, exibindo uma visão geral dos resultados e métricas de vendas.

## Responsabilidades

- Exibir as métricas de performance mais importantes em `Cards`.
- Apresentar um gráfico de performance de vendas (`PerformanceChart`).
- Permitir a filtragem de visualizações (ex: Performance vs. Financeiro) através do `DashboardFilters`.

## Componentes Utilizados

- `Card` (shared): Para exibir cada métrica individual.
- `DashboardFilters` (local): Para controlar os filtros da página.
- `PerformanceChart` (local): Para exibir o gráfico de performance.
