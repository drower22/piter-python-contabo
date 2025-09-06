from typing import Tuple, List, Set
import os
import re
import sqlglot
from sqlglot.errors import ParseError


def _get_allowed_tables() -> Set[str]:
    env = os.getenv("SQLAGENT_ALLOWED_TABLES", "")
    parts = [p.strip() for p in env.split(",") if p.strip()]
    return set(parts)


def validate_sql(sql: str) -> Tuple[bool, List[str]]:
    issues: List[str] = []

    # Single statement only
    # crude check: more than one ';' not allowed, and must not end with ';' multiple times
    if sql.count(";") > 1:
        issues.append("Multiple SQL statements are not allowed.")

    try:
        expr = sqlglot.parse_one(sql, read="postgres")
    except ParseError as e:
        return False, [f"parse_error: {e}"]

    lowered = sql.strip().lower()

    # Disallow dangerous statements
    banned = [
        " drop ", " alter ", " create ", " truncate ", " grant ", " revoke ",
        " insert ", " update ", " delete ", " call ", " begin ", " commit ", " rollback ",
    ]
    if any(b in f" {lowered} " for b in banned):
        issues.append("Only SELECT queries are allowed.")

    # Require select root
    if expr and expr.key != "Select":
        issues.append("Root statement must be SELECT.")

    # Allowlist of tables/views
    allowed = _get_allowed_tables()
    if allowed:
        # collect table names from the AST
        try:
            tables = {t.name for t in expr.find_all(sqlglot.expressions.Table)}
        except Exception:
            tables = set()
        for t in tables:
            if t not in allowed:
                issues.append(f"Table not allowed: {t}")

    # LIMIT presence
    if " limit " not in lowered:
        issues.append("Query should include LIMIT to avoid heavy scans.")

    ok = len(issues) == 0
    return ok, issues
