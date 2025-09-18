"""
Serviço para Parsing de Mensagens do WhatsApp.

Este módulo é responsável por traduzir o payload bruto do webhook do WhatsApp
em um objeto de dados estruturado e normalizado, facilitando o processamento
pelas camadas de serviço e lógica de negócio.
"""

import re
import json
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class ParsedWhatsAppMessage(BaseModel):
    """
    Representa uma mensagem do WhatsApp normalizada e pronta para ser processada.

    Esta estrutura de dados abstrai a complexidade do payload original do webhook,
    fornecendo acesso direto às informações mais relevantes de uma mensagem recebida.
    """
    sender_number: str = Field(..., description="Número de telefone do remetente no formato +5511999999999.")
    sender_id: str = Field(..., description="ID do remetente no WhatsApp (wa_id).")
    profile_name: Optional[str] = Field(None, description="Nome de perfil do usuário no WhatsApp.")
    message_id: str = Field(..., description="ID da mensagem do WhatsApp.")
    message_type: str = Field(..., description="Tipo da mensagem (ex: 'text', 'interactive', 'button').")
    text: Optional[str] = Field(None, description="Conteúdo da mensagem de texto.")
    button_id: Optional[str] = Field(None, description="ID normalizado do botão clicado.")
    button_title: Optional[str] = Field(None, description="Título do botão clicado.")
    raw_message_payload: Dict[str, Any] = Field(..., description="O payload original da mensagem recebida.")


class WhatsAppMessageParser:
    """
    Parser para webhooks do WhatsApp Cloud API.

    A classe centraliza a lógica de extração e normalização de dados
    dos payloads recebidos, lidando com as diferentes estruturas de mensagens
    (texto, botões, interativos, etc.).
    """

    def _get_first(self, lst: Optional[List[Any]]) -> Optional[Any]:
        """Retorna o primeiro elemento de uma lista, se existir."""
        return lst[0] if isinstance(lst, list) and lst else None

    def _normalize_phone_number(self, wa_number: str) -> str:
        """Garante que o número de telefone esteja no formato internacional com '+'"""
        if wa_number and not wa_number.startswith('+'):
            return f"+{wa_number}"
        return wa_number

    def _extract_button_info(self, message: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """
        Extrai o ID e o título de uma mensagem de botão ou interativa.

        Args:
            message: O dicionário da mensagem do WhatsApp.

        Returns:
            Uma tupla contendo (button_id, button_title).
        """
        msg_type = message.get('type')
        raw_btn_id = None
        btn_title = None

        if msg_type == 'interactive':
            interactive = message.get('interactive') or {}
            reply = (interactive.get('button_reply') or interactive.get('list_reply') or {})
            raw_btn_id = (reply.get('id') or '').strip()
            btn_title = (reply.get('title') or '').strip()
        elif msg_type == 'button':  # Legado
            btn = (message.get('button') or {})
            raw_btn_id = (btn.get('payload') or btn.get('id') or '').strip()
            btn_title = (btn.get('text') or '').strip()

        if not raw_btn_id:
            return None, None

        # Normaliza o ID do botão
        btn_id = raw_btn_id
        if btn_id.startswith('{') or btn_id.startswith('['):
            try:
                obj = json.loads(btn_id)
                if isinstance(obj, dict):
                    btn_id = obj.get('id') or obj.get('action') or btn_id
            except json.JSONDecodeError:
                pass
        
        btn_id = str(btn_id or '').strip().lower()
        if ':' in btn_id:
            btn_id = btn_id.split(':', 1)[0]

        return btn_id, btn_title

    def parse(self, body: Dict[str, Any]) -> List[ParsedWhatsAppMessage]:
        """
        Processa o corpo completo do webhook e retorna uma lista de mensagens normalizadas.

        Args:
            body: O corpo JSON completo recebido do webhook do WhatsApp.

        Returns:
            Uma lista de objetos ParsedWhatsAppMessage, um para cada mensagem válida encontrada.
        """
        parsed_messages = []
        try:
            entry = self._get_first(body.get('entry')) or {}
            change = self._get_first(entry.get('changes')) or {}
            value = change.get('value') or {}
            messages = value.get('messages') or []
            contacts = value.get('contacts') or []

            if not messages:
                return []

            contact_obj = self._get_first(contacts) or {}
            profile_name = (contact_obj.get('profile') or {}).get('name')

            for m in messages:
                msg_type = m.get('type')
                if not msg_type:
                    continue

                sender_id = m.get('from')
                message_id = m.get('id')
                
                if not sender_id or not message_id:
                    continue

                normalized_number = self._normalize_phone_number(sender_id)
                text_content = m.get('text', {}).get('body') if msg_type == 'text' else None
                button_id, button_title = self._extract_button_info(m)

                parsed_messages.append(
                    ParsedWhatsAppMessage(
                        sender_number=normalized_number,
                        sender_id=sender_id,
                        profile_name=profile_name,
                        message_id=message_id,
                        message_type=msg_type,
                        text=text_content,
                        button_id=button_id,
                        button_title=button_title,
                        raw_message_payload=m
                    )
                )
        except (AttributeError, KeyError, IndexError) as e:
            print(f"[ERROR][PARSER] Falha ao processar o corpo do webhook: {e}")
            # Retorna lista vazia em caso de estrutura inesperada
            return []

        return parsed_messages
