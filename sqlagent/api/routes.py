import time
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from ..services.sqlgen import generate_sql
from ..services.presets import list_presets, run_preset
from ..services.validators import validate_sql
from ..infra.db import list_schemas, execute_sql

router = APIRouter()


@router.get("/v1/sql/schemas")
async def get_schemas(request: Request):
    account_id = request.headers.get("x-account-id")
    return {"schemas": list_schemas(account_id)}


class GenerateBody(BaseModel):
    question: str
    hint_tables: list[str] | None = None


@router.post("/v1/sql/generate")
async def post_generate(body: GenerateBody, request: Request):
    account_id = request.headers.get("x-account-id")
    sql, rationale, model = generate_sql(question=body.question, account_id=account_id, hint_tables=body.hint_tables)
    ok, issues = validate_sql(sql)
    return {"sql": sql, "valid": ok, "issues": issues, "rationale": rationale, "model": model}


class ValidateBody(BaseModel):
    sql: str


@router.post("/v1/sql/validate")
async def post_validate(body: ValidateBody):
    ok, issues = validate_sql(body.sql)
    return {"valid": ok, "issues": issues}


class AskBody(BaseModel):
    question: str
    top_k: int | None = None
    date_from: str | None = None
    date_to: str | None = None


@router.post("/qa/ask")
async def post_ask(body: AskBody, request: Request):
    """Recebe pergunta NL, gera SQL (Gemini/Llama), valida, executa e retorna dados.
    """
    t0 = time.time()
    account_id = request.headers.get("x-account-id")

    sql, rationale, model = generate_sql(question=body.question, account_id=account_id)
    ok, issues = validate_sql(sql)
    if not ok:
        raise HTTPException(status_code=400, detail={"message": "Query inválida", "issues": issues, "sql": sql})

    # Execução
    try:
        cols, rows = execute_sql(sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar SQL: {e}")

    timing_ms = int((time.time() - t0) * 1000)
    return {
        "ok": True,
        "model": model,
        "executed_sql": sql,
        "columns": cols,
        "rows": rows,
        "explanation": rationale,
        "timing_ms": timing_ms,
    }


class PresetExecBody(BaseModel):
    preset_id: str
    params: dict | None = None


@router.get("/qa/presets")
async def get_presets():
    return list_presets()


@router.post("/qa/presets/build")
async def post_build_preset(body: PresetExecBody):
    """Somente constroi o SQL do preset sem executar (debug/inspecao)."""
    from ..services.presets import PRESETS  # lazy import for introspection
    if body.preset_id not in PRESETS:
        raise HTTPException(status_code=404, detail="Preset inexistente")
    params = body.params or {}
    try:
        sql = PRESETS[body.preset_id]["sql"](params)
        return {"ok": True, "sql": sql}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/qa/presets/run")
async def post_run_preset(body: PresetExecBody):
    try:
        cols, rows, sql = run_preset(body.preset_id, body.params or {})
        return {"ok": True, "columns": cols, "rows": rows, "executed_sql": sql}
    except Exception as e:
        # inclui o SQL gerado (se conseguir gerar) para facilitar o debug do cliente
        from ..services.presets import PRESETS  # local import
        sql_dbg = None
        try:
            if body.preset_id in PRESETS:
                sql_dbg = PRESETS[body.preset_id]["sql"](body.params or {})
        except Exception:
            pass
        raise HTTPException(status_code=400, detail={"message": str(e), "sql": sql_dbg})
