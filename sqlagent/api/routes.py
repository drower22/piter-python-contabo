from fastapi import APIRouter, Request
from pydantic import BaseModel
from ..services.sqlgen import generate_sql
from ..services.validators import validate_sql
from ..infra.db import list_schemas

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
    sql, rationale = generate_sql(question=body.question, account_id=account_id, hint_tables=body.hint_tables)
    ok, issues = validate_sql(sql)
    return {"sql": sql, "valid": ok, "issues": issues, "rationale": rationale}


class ValidateBody(BaseModel):
    sql: str


@router.post("/v1/sql/validate")
async def post_validate(body: ValidateBody):
    ok, issues = validate_sql(body.sql)
    return {"valid": ok, "issues": issues}
