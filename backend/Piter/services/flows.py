from __future__ import annotations

import asyncio
from typing import Dict, Any, List

from ..infrastructure.messaging.whatsapp_client import WhatsAppClient


class DemoFlowsService:
    """
    Serviço centralizador dos fluxos de demonstração (1, 2 e 3).
    Cada fluxo expõe métodos claros e puros para facilitar manutenção.
    """

    def __init__(self, client: WhatsAppClient | None = None) -> None:
        self.client = client or WhatsAppClient()

    # =============
    # Fluxo 1: Importação de vendas concluída
    # =============
    def start_sales_import_flow(self, to: str) -> Dict[str, Any]:
        body = (
            "Olá, aqui é o Piter! Acabamos de receber sua importação de vendas. "
            "Quer ver o resumo agora?"
        )
        buttons = [{"id": "view_summary", "title": "Ver resumo agora"}]
        return self.client.send_buttons(to=to, body_text=body, buttons=buttons)

    def send_sales_summary(self, to: str, summary: Dict[str, Any]) -> Dict[str, Any]:
        # Espera-se que summary já venha calculado pelo chamador
        # Campos esperados: valor_pizzas, qtd_pizzas, valor_bebidas, qtd_bebidas, top_pizzas[], top_bebidas[]
        top_pizzas = summary.get("top_pizzas", [])[:10]
        top_bebidas = summary.get("top_bebidas", [])[:5]
        lines: List[str] = []
        lines.append("Resumo de vendas de hoje\n")
        lines.append("• Total vendido")
        lines.append(f"  - Pizzas: R$ {summary.get('valor_pizzas','0,00')} ({summary.get('qtd_pizzas','0')} un)")
        lines.append(f"  - Bebidas: R$ {summary.get('valor_bebidas','0,00')} ({summary.get('qtd_bebidas','0')} un)\n")
        lines.append("• Top 10 Pizzas")
        for i, item in enumerate(top_pizzas, start=1):
            lines.append(f"  {i}) {item.get('nome','-')} — {item.get('qtd',0)} un")
        lines.append("\n• Top 5 Bebidas")
        for i, item in enumerate(top_bebidas, start=1):
            lines.append(f"  {i}) {item.get('nome','-')} — {item.get('qtd',0)} un")
        text = "\n".join(lines)
        return self.client.send_text(to=to, text=text)

    async def ask_consumption_after_delay(self, to: str, delay_seconds: int = 10) -> Dict[str, Any]:
        await asyncio.sleep(delay_seconds)
        body = (
            "Quer que eu envie a previsão de consumo dos insumos para hoje?"
        )
        buttons = [{"id": "view_consumption", "title": "Ver consumo estimado"}]
        return self.client.send_buttons(to=to, body_text=body, buttons=buttons)

    def send_consumption_list(self, to: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        # items: list[{nome, qtd, unid}]
        top10 = items[:10]
        lines: List[str] = []
        lines.append("Consumo estimado — Top 10 insumos (hoje)\n")
        for i, it in enumerate(top10, start=1):
            lines.append(f"{i}) {it.get('nome','-')} — {it.get('qtd',0)} {it.get('unid','')}")
        lines.append("\nDica: use essa lista para conferir a cozinha e acompanhar o CMV teórico do dia.")
        text = "\n".join(lines)
        return self.client.send_text(to=to, text=text)

    # =============
    # Fluxo 2: Estoque baixo detectado
    # =============
    def start_low_stock_flow(self, to: str) -> Dict[str, Any]:
        body = (
            "Aviso rápido: detectei itens de estoque em níveis críticos. "
            "Quer ver a lista e tomar uma ação agora?"
        )
        buttons = [{"id": "view_low_stock", "title": "Ver itens críticos"}]
        return self.client.send_buttons(to=to, body_text=body, buttons=buttons)

    def send_low_stock_list(self, to: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        # items: list[{insumo, qtd_atual, qtd_min, unid}]
        top = items[:5]
        lines: List[str] = []
        lines.append("Itens críticos de estoque\n")
        for i, it in enumerate(top, start=1):
            lines.append(
                f"{i}) {it.get('insumo','-')} — {it.get('qtd_atual',0)}/{it.get('qtd_min',0)} {it.get('unid','')}"
            )
        lines.append("\nQuer que eu gere uma sugestão de compra?")
        text = "\n".join(lines)
        return self.client.send_buttons(
            to=to,
            body_text=text,
            buttons=[{"id": "make_purchase_list", "title": "Gerar lista de compras"}],
        )

    # =============
    # Fluxo 3: Desvio de CMV
    # =============
    def start_cmv_deviation_flow(self, to: str) -> Dict[str, Any]:
        body = (
            "Identifiquei uma variação no CMV em relação ao esperado. "
            "Quer ver uma análise rápida?"
        )
        buttons = [{"id": "view_cmv_analysis", "title": "Ver análise rápida"}]
        return self.client.send_buttons(to=to, body_text=body, buttons=buttons)

    def send_cmv_analysis(self, to: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # data: {cmv_esperado, cmv_atual, desvio_pct, contribuintes:[{insumo, impacto_pct}]}
        lines: List[str] = []
        lines.append("CMV — Análise rápida\n")
        lines.append(f"• CMV esperado: {data.get('cmv_esperado','-')}%")
        lines.append(f"• CMV atual: {data.get('cmv_atual','-')}%")
        lines.append(f"• Desvio: {data.get('desvio_pct','-')} p.p.\n")
        lines.append("Principais contribuintes")
        for i, it in enumerate(data.get("contribuintes", [])[:3], start=1):
            lines.append(f"{i}) {it.get('insumo','-')} — impacto {it.get('impacto_pct','-')}%")
        lines.append("\nQuer ver ações recomendadas para corrigir hoje?")
        text = "\n".join(lines)
        return self.client.send_buttons(
            to=to,
            body_text=text,
            buttons=[{"id": "view_cmv_actions", "title": "Ver ações recomendadas"}],
        )
