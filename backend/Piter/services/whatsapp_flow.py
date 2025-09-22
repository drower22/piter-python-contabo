"""
Serviço de Gerenciamento de Fluxo de Conversa do WhatsApp.

Este módulo centraliza toda a lógica de negócio para processar mensagens,
gerenciar o estado da conversa e orquestrar as respostas para o usuário.
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from ..infrastructure.database.supabase_client import get_supabase, SupabaseClient
from ..infrastructure.messaging.whatsapp_client import WhatsAppClient
from .message_parser import ParsedWhatsAppMessage
from .flows import DemoFlowsService # Para manter a lógica de demo por enquanto

class FlowResult:
    """Representa o resultado do processamento de uma etapa do fluxo."""
    def __init__(self, reply_text: Optional[str] = None, new_step: Optional[str] = None, context_patch: Optional[dict] = None):
        self.reply_text = reply_text
        self.new_step = new_step
        self.context_patch = context_patch or {}

class WhatsAppFlowService:
    """
    Orquestra o fluxo de conversa, processando mensagens e gerenciando o estado.
    """
    def __init__(self, supabase_client: Optional[SupabaseClient] = None, whatsapp_client: Optional[WhatsAppClient] = None):
        self.sb = supabase_client or get_supabase()
        self.wa_client = whatsapp_client or WhatsAppClient()
        self.demo_flows = DemoFlowsService(self.wa_client) # Injeta o cliente

    def _get_conversation_state(self, conversation_id: str) -> Tuple[str, dict]:
        """Busca o estado atual da conversa no banco de dados (wa_conversation_state)."""
        resp = self.sb.table('wa_conversation_state').select('state_key, data').eq('conversation_id', conversation_id).maybe_single().execute()
        data = resp.data or {}
        return data.get('state_key') or 'welcome', (data.get('data') or {})

    def _set_conversation_state(self, conversation_id: str, step: str, context: dict) -> None:
        """Salva o novo estado da conversa no banco (RPC wa_set_conversation_state)."""
        try:
            self.sb.rpc('wa_set_conversation_state', {
                'p_conversation_id': str(conversation_id),
                'p_state_key': str(step),
                'p_data': context or None,
            }).execute()
        except Exception as e:
            print(f"[WARN] Failed to set conversation state via RPC: {repr(e)}")

    def _persist_button_click(self, conversation_id: str, contact_id: str, msg: ParsedWhatsAppMessage):
        """Salva o evento de clique de botão para fins de análise."""
        try:
            self.sb.table('wa_button_clicks').insert({
                'conversation_id': conversation_id,
                'contact_id': contact_id,
                'wa_message_id': msg.message_id,
                'button_id': msg.button_id,
                'button_title': msg.button_title,
                'raw_payload': msg.raw_message_payload,
                'clicked_at': 'now()',
            }).execute()
        except Exception as e:
            print(f'[WARN] Failed to persist button click: {repr(e)}')
    
    def _handle_text_based_flow(self, conversation_id: str, msg: ParsedWhatsAppMessage) -> Optional[FlowResult]:
        """Gerencia a lógica de conversa baseada em texto e estado."""
        step, context = self._get_conversation_state(conversation_id)
        text = msg.text

        if step == 'welcome':
            reply = (
                "Olá! Eu sou o Piter. Como posso ajudar?\n"
                "1) Consultas/Conciliação (SQL)\n"
                "2) Relatório Financeiro (SQL)\n"
                "3) Suporte"
            )
            new_step = 'menu'
            self._set_conversation_state(conversation_id, new_step, context)
            return FlowResult(reply_text=reply, new_step=new_step)

        if step == 'menu':
            choice = (text or '').strip()
            if choice.startswith('1'):
                reply = "Perfeito! Para conciliação/consultas via SQL, me informe seu account_id para eu vincular o contexto."
                new_step = 'collect_account_for_conciliation'
            elif choice.startswith('2'):
                reply = "Ótimo! Para relatório financeiro, me diga o período (ex: 2025-08)."
                new_step = 'collect_period_finance'
            elif choice.startswith('3'):
                reply = "Nosso suporte vai te atender. Descreva brevemente seu problema."
                new_step = 'support_wait'
            else:
                reply = "Não entendi. Escolha 1, 2 ou 3."
                new_step = 'menu'
            self._set_conversation_state(conversation_id, new_step, context)
            return FlowResult(reply_text=reply, new_step=new_step)

        # Outros estados (collect_account_for_conciliation, etc.) continuam aqui...

        # Fallback
        self._set_conversation_state(conversation_id, 'welcome', context)
        return FlowResult(reply_text="Voltando ao início...", new_step='welcome')

    def _persist_outbound_message(self, conversation_id: str, msg_type: str, body: dict):
        """Persiste uma mensagem de saída no banco de dados."""
        try:
            payload = {
                'conversation_id': conversation_id,
                'direction': 'out',
                'type': msg_type,
                'json_payload': body,
            }
            self.sb.table('wa_messages').insert(payload).execute()
            self.sb.table('wa_conversations').update({'last_message_at': 'now()'}).eq('id', conversation_id).execute()
        except Exception as e:
            print(f'[WARN] Failed to persist outbound message: {repr(e)}')

    def _send_next_buttons(self, conversation_id: str, to_number: str, catalog_obj: Dict[str, Any]):
        """Envia uma mensagem com os próximos botões, se definidos no catálogo."""
        try:
            next_btns = (catalog_obj or {}).get('next_buttons') or []
            if isinstance(next_btns, str):
                try:
                    next_btns = json.loads(next_btns)
                except json.JSONDecodeError:
                    next_btns = []
            
            if next_btns:
                body_txt = (catalog_obj or {}).get('response_text') or 'Selecione uma opção:'
                self.wa_client.send_buttons(to_number, body_txt, next_btns)
                self._persist_outbound_message(conversation_id, 'interactive', {
                    'interactive': {'type': 'button', 'action': {'buttons': next_btns}, 'body': {'text': body_txt}},
                })
        except Exception as e:
            print(f'[WARN] Next buttons send failed: {repr(e)}')

    def _apply_next_state(self, conversation_id: str, catalog_obj: Dict[str, Any]):
        """Aplica o próximo estado de conversa, se definido no catálogo (direto na tabela)."""
        try:
            next_state = (catalog_obj or {}).get('next_state')
            if next_state:
                self._set_conversation_state(conversation_id, str(next_state), {})
        except Exception as e:
            print(f'[WARN] Next state update failed: {repr(e)}')

    def _handle_button_click(self, conversation_id: str, contact_id: str, msg: ParsedWhatsAppMessage) -> bool:
        """Processa um clique de botão, consultando o catálogo e executando a ação."""
        btn_id = msg.button_id
        to_number = msg.sender_number
        if not btn_id or not to_number:
            return False

        self._persist_button_click(conversation_id, contact_id, msg)

        # 1. Tenta rotear pelo catálogo de botões
        try:
            q_cat = self.sb.table('wa_buttons_catalog').select('*').eq('id', btn_id).eq('active', True).maybe_single().execute()
            cat = q_cat.data if q_cat and q_cat.data else None
        except Exception as e:
            print(f'[WARN] Catalog lookup failed: {repr(e)}')
            cat = None

        if cat:
            rtype = (cat.get('response_type') or 'text').lower()
            if rtype == 'text':
                resp_text = (cat.get('response_text') or '').strip()
                if resp_text:
                    self.wa_client.send_text(to_number, resp_text)
                    self._persist_outbound_message(conversation_id, 'text', {"text": {"body": resp_text}})
                self._send_next_buttons(conversation_id, to_number, cat)
                self._apply_next_state(conversation_id, cat)
                return True
            elif rtype == 'webhook':
                # Executa um webhook externo definido em meta.webhook_url
                try:
                    import requests
                    meta = (cat.get('metadata') or cat.get('meta') or {})
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except json.JSONDecodeError:
                            meta = {}
                    url = (meta.get('webhook_url') or '').strip()
                    method = (meta.get('method') or 'POST').upper()
                    headers = meta.get('headers') or {}
                    payload = {
                        'conversation_id': conversation_id,
                        'contact_id': contact_id,
                        'to': to_number,
                        'button_id': btn_id,
                        'state': self._get_conversation_state(conversation_id)[0],
                    }
                    resp = None
                    if url:
                        if method == 'GET':
                            resp = requests.get(url, params=payload, headers=headers, timeout=10)
                        else:
                            resp = requests.post(url, json=payload, headers=headers, timeout=15)
                    if resp is not None:
                        try:
                            j = resp.json()
                        except Exception:
                            j = {}
                        # Espera-se que o webhook retorne { text?, next_buttons?, next_state? }
                        txt = (j.get('text') or cat.get('response_text') or '').strip()
                        if txt:
                            self.wa_client.send_text(to_number, txt)
                            self._persist_outbound_message(conversation_id, 'text', {"text": {"body": txt}})
                        # Permite que o webhook defina próximos botões/estado, senão usa do catálogo
                        override = {
                            'next_buttons': j.get('next_buttons', cat.get('next_buttons')),
                            'next_state': j.get('next_state', cat.get('next_state')),
                            'response_text': txt or cat.get('response_text'),
                        }
                        self._send_next_buttons(conversation_id, to_number, override)
                        self._apply_next_state(conversation_id, override)
                        return True
                except Exception as e:
                    print(f'[WARN] Webhook execution failed: {repr(e)}')
                # Se falhar, ainda tenta aplicar next do catálogo
                self._send_next_buttons(conversation_id, to_number, cat)
                self._apply_next_state(conversation_id, cat)
                return True
            elif rtype in ('none', 'noop'):
                self._send_next_buttons(conversation_id, to_number, cat)
                self._apply_next_state(conversation_id, cat)
                return True

        # 2. Fallback para a lógica de demonstração hardcoded
        if btn_id == 'view_summary':
            summary = {'valor_pizzas': '4.520,00', 'qtd_pizzas': 180, 'valor_bebidas': '1.240,00', 'qtd_bebidas': 210, 'top_pizzas': [{'nome': f'Pizza {i}', 'qtd': 30-i} for i in range(1,11)], 'top_bebidas': [{'nome': f'Bebida {i}', 'qtd': 50-i} for i in range(1,6)]}
            self.demo_flows.send_sales_summary(to_number, summary)
            # self.demo_flows.ask_consumption_after_delay(to_number, 10) # Asyncio precisa de tratamento especial
            return True
        elif btn_id == 'view_consumption':
            items = [{'nome': f'Insumo {i}', 'qtd': 10*i, 'unid': 'un'} for i in range(1,11)]
            self.demo_flows.send_consumption_list(to_number, items)
            return True
        elif btn_id == 'view_low_stock':
            items = [{'insumo': 'Mussarela', 'qtd_atual': 3, 'qtd_min': 8, 'unid': 'kg'}, {'insumo': 'Calabresa', 'qtd_atual': 2, 'qtd_min': 6, 'unid': 'kg'}, {'insumo': 'Molho', 'qtd_atual': 5, 'qtd_min': 10, 'unid': 'kg'}, {'insumo': 'Farinha', 'qtd_atual': 20, 'qtd_min': 35, 'unid': 'kg'}, {'insumo': 'Refrigerante Lata', 'qtd_atual': 12, 'qtd_min': 24, 'unid': 'un'}]
            self.demo_flows.send_low_stock_list(to_number, items)
            return True
        elif btn_id == 'make_purchase_list':
            self.wa_client.send_text(to_number, 'Ok! Vou gerar a lista de compras sugerida e te envio em instantes.')
            return True
        elif btn_id == 'view_cmv_analysis':
            data = {'cmv_esperado': 28.0, 'cmv_atual': 32.5, 'desvio_pct': 4.5, 'contribuintes': [{'insumo': 'Mussarela', 'impacto_pct': 1.8}, {'insumo': 'Calabresa', 'impacto_pct': 1.2}, {'insumo': 'Tomate', 'impacto_pct': 0.9}]}
            self.demo_flows.send_cmv_analysis(to_number, data)
            return True
        elif btn_id == 'view_cmv_actions':
            self.wa_client.send_text(to_number, 'Ações recomendadas: 1) revisar porcionamento de queijos; 2) ajustar preço das bebidas; 3) auditar perdas na abertura.')
            return True

        return False # Botão não foi tratado nem pelo catálogo, nem pelo fallback

    def process_message(self, conversation_id: str, contact_id: str, msg: ParsedWhatsAppMessage):
        """
        Ponto de entrada principal para processar uma nova mensagem.
        """
        handled = False
        if msg.button_id:
            handled = self._handle_button_click(conversation_id, contact_id, msg)

        if not handled:
            result = self._handle_text_based_flow(conversation_id, msg)
            if result and result.reply_text:
                self.wa_client.send_text(to=msg.sender_number, text=result.reply_text)
                # Persistir resposta outbound
                # _insert_message(self.sb, conversation_id, 'out', 'text', {"text": {"body": result.reply_text}}, None)

