import json
import os
import re
from typing import Dict, Any, Optional, Tuple

# Providers
try:
    from .providers.openai import OpenAIProvider
except Exception:
    OpenAIProvider = None  # type: ignore

try:
    from .providers.gemini import GeminiProvider
except Exception:
    GeminiProvider = None  # type: ignore

try:
    from .providers.groq import GroqLlamaProvider
except Exception:
    GroqLlamaProvider = None  # type: ignore


INTENT_SCHEMA = {
    "user_query": "",
    "intent": "analytics",  # ex.: analytics|status|finance etc.
    "last_n": 7,
    "last_unit": "days",  # days|weeks|months
    "date_from": None,
    "date_to": None,
    "metrics": ["orders", "revenue"],
    "dimensions": ["day"],
    "filters": [],  # [{"field":"channel","op":"=","value":"ifood"}]
    "table_hint": "v_ifood_order_ledger",
    "preset_candidate": None,  # totais_ultimos_dias|diario_ultimos_dias|status_ultimos_dias
    "limit": 100,
}

PROMPT = (
    "Você é um assistente que EXTRAI parâmetros estruturados de uma pergunta de negócio.\n"
    "Responda EXCLUSIVAMENTE em JSON válido, sem comentários, sem markdown.\n"
    "Campos esperados: {schema_keys}.\n"
    "Regras:\n"
    "- Preencha last_n/last_unit quando a pergunta trouxer um período relativo (ex.: 'últimos 7 dias').\n"
    "- Se trouxer datas absolutas (ex.: 'de 2024-06-01 a 2024-06-10'), use date_from/date_to (YYYY-MM-DD).\n"
    "- metrics e dimensions são listas de termos simples (ex.: ['orders','revenue']).\n"
    "- filters é uma lista de objetos {{field, op, value}}.\n"
    "- table_hint é uma vista ou tabela de leitura (ex.: v_ifood_order_ledger).\n"
    "- preset_candidate pode ser: totais_ultimos_dias | diario_ultimos_dias | status_ultimos_dias.\n"
    "- Se algo não se aplicar, use null ou lista vazia.\n"
    "Pergunta: {question}\n"
)

_JSON_RE = re.compile(r"\{[\s\S]*\}\s*$")


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    # captura o último bloco JSON no texto
    m = _JSON_RE.search(text)
    raw = m.group(0) if m else text
    try:
        data = json.loads(raw)
    except Exception:
        # fallback simples: tenta normalizar aspas
        raw2 = raw.replace("'", '"')
        data = json.loads(raw2)
    return data


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(INTENT_SCHEMA)
    out.update({k: data.get(k, out.get(k)) for k in out.keys()})
    # coerções leves
    if isinstance(out.get("last_n"), str) and out["last_n"].isdigit():
        out["last_n"] = int(out["last_n"])
    if not isinstance(out.get("metrics"), list):
        out["metrics"] = []
    if not isinstance(out.get("dimensions"), list):
        out["dimensions"] = []
    if not isinstance(out.get("filters"), list):
        out["filters"] = []
    if out.get("limit") is None:
        out["limit"] = 100
    return out


def interpret(question: str) -> Tuple[Dict[str, Any], str]:
    """Returns (intent_dict, model_used)."""
    prompt = PROMPT.format(schema_keys=list(INTENT_SCHEMA.keys()), question=question)

    errors = []

    if OpenAIProvider is not None and os.getenv("OPENAI_API_KEY"):
        try:
            txt = OpenAIProvider(model=os.getenv("OPENAI_MODEL")).generate_sql(prompt)
            data = _normalize(_extract_json(txt))
            return data, os.getenv("OPENAI_MODEL", "openai")
        except Exception as e:
            errors.append(f"openai_err: {e}")

    if GeminiProvider is not None and os.getenv("GEMINI_API_KEY"):
        try:
            from .providers.gemini import GeminiProvider as _G
            txt = _G(model=os.getenv("GEMINI_MODEL")).generate_sql(prompt)
            data = _normalize(_extract_json(txt))
            return data, "gemini"
        except Exception as e:
            errors.append(f"gemini_err: {e}")

    if GroqLlamaProvider is not None and os.getenv("GROQ_API_KEY"):
        try:
            txt = GroqLlamaProvider().generate_sql(prompt)
            data = _normalize(_extract_json(txt))
            return data, "llama"
        except Exception as e:
            errors.append(f"llama_err: {e}")

    # fallback mínimo
    return _normalize({"user_query": question, "preset_candidate": "totais_ultimos_dias"}), "fallback"
