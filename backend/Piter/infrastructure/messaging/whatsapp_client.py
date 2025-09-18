"""
Cliente para a API do WhatsApp Cloud.

Este módulo encapsula a comunicação com a API Graph do Facebook para envio
de mensagens via WhatsApp, incluindo texto, templates, mídias e botões.
"""

import os
import requests
from typing import Optional, Dict, Any, List

class WhatsAppClient:
    """
    Cliente para interagir com a WhatsApp Cloud API.

    Gerencia a autenticação, a construção de payloads e o envio de requisições
    para os diversos endpoints de mensagens da plataforma.
    """
    def __init__(self, phone_number_id: Optional[str] = None, token: Optional[str] = None, graph_version: Optional[str] = None):
        """
        Inicializa o cliente do WhatsApp.

        Args:
            phone_number_id: O ID do número de telefone registrado na Meta.
            token: O token de acesso permanente para a API Graph.
            graph_version: A versão da API Graph a ser utilizada (ex: 'v19.0').
        """
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_ID")
        self.token = token or os.getenv("WHATSAPP_TOKEN")
        self.graph_version = graph_version or os.getenv("WHATSAPP_GRAPH_VERSION", "v19.0")

        if not self.phone_number_id or not self.token:
            raise ValueError("As variáveis de ambiente WHATSAPP_PHONE_ID e WHATSAPP_TOKEN são obrigatórias.")

        self.base_url = f"https://graph.facebook.com/{self.graph_version}/{self.phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def send_text(self, to: str, text: str, preview_url: bool = False) -> Dict[str, Any]:
        """
        Envia uma mensagem de texto simples.

        Args:
            to: Número do destinatário no formato internacional.
            text: O conteúdo da mensagem.
            preview_url: Se o WhatsApp deve gerar uma pré-visualização de links na mensagem.

        Returns:
            A resposta da API da Meta.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text, "preview_url": preview_url}
        }
        url = f"{self.base_url}/messages"
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def send_template(self, to: str, template: str, language: str = "pt_BR", components: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Envia uma mensagem baseada em um template pré-aprovado.

        Args:
            to: Número do destinatário.
            template: Nome do template.
            language: Código do idioma do template (ex: 'pt_BR').
            components: Componentes dinâmicos do template (variáveis, botões, etc.).

        Returns:
            A resposta da API da Meta.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": language},
                "components": components or []
            }
        }
        url = f"{self.base_url}/messages"
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def send_buttons(self, to: str, body_text: str, buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Envia uma mensagem interativa com botões de resposta rápida.

        Args:
            to: Número do destinatário.
            body_text: O texto principal da mensagem.
            buttons: Uma lista de até 3 dicionários, cada um com 'id' e 'title'.

        Returns:
            A resposta da API da Meta.
        """
        action_buttons = [
            {"type": "reply", "reply": {"id": b['id'], "title": b['title']}}
            for b in buttons[:3]
        ]
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": action_buttons}
            }
        }
        url = f"{self.base_url}/messages"
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
