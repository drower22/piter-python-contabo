import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


class OpenAIProvider:
    """Simple wrapper for OpenAI Chat Completions-style text generation.
    Accepts any model via env OPENAI_MODEL (default: gpt-4o-mini). If you want to use
    an experimental model like 'gpt-5-nano', set OPENAI_MODEL=gpt-5-nano in the service env.
    """

    def __init__(self, model: Optional[str] = None):
        if OpenAI is None:
            raise RuntimeError("openai sdk não instalado")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY não definido")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_sql(self, prompt: str) -> str:
        # Keep the response concise; we only want SQL text.
        system = (
            "Você é um assistente que gera exclusivamente SQL PostgreSQL válido. "
            "Responda APENAS com o SQL bruto, sem comentários, explicações nem markdown."
        )
        # Use responses.create for the new SDK
        kwargs = {}
        temp = os.getenv("OPENAI_TEMPERATURE")
        if temp:
            try:
                kwargs["temperature"] = float(temp)
            except Exception:
                pass
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            **kwargs,
        )
        text = resp.choices[0].message.content or ""
        text = text.strip()
        # Remove cercas de código se vierem
        if text.startswith("```"):
            text = text.strip("`\n ")
            if text.lower().startswith("sql"):
                text = text[3:].lstrip("\n")
        return text.strip()

    def generate_text(self, history: list[dict]) -> str:
        """history: list of {role, content}. Returns assistant text."""
        system_default = (
            "Você é um assistente útil. Responda de forma objetiva."
        )
        messages = []
        # Prepend system if not present
        if not history or history[0].get("role") != "system":
            messages.append({"role": "system", "content": system_default})
        messages.extend(history)
        kwargs = {}
        temp = os.getenv("OPENAI_TEMPERATURE")
        if temp:
            try:
                kwargs["temperature"] = float(temp)
            except Exception:
                pass
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **kwargs,
        )
        return (resp.choices[0].message.content or "").strip()
