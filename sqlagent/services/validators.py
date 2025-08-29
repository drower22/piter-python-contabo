from typing import Tuple, List
import sqlglot
from sqlglot.errors import ParseError

def validate_sql(sql: str) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    try:
        expr = sqlglot.parse_one(sql, read="postgres")
    except ParseError as e:
        return False, [f"parse_error: {e}"]

    # Disallow dangerous statements
    lowered = sql.strip().lower()
    banned = [
        "drop ", "alter ", "create ", "truncate ", "grant ", "revoke ",
        "insert ", "update ", "delete ",
    ]
    if any(b in lowered for b in banned):
        issues.append("Only SELECT queries are allowed.")

    # Require select root
    if expr and expr.key != "Select":
        issues.append("Root statement must be SELECT.")

    # Basic guard: limit presence
    if " limit " not in lowered:
        issues.append("Query should include LIMIT to avoid heavy scans.")

    ok = len(issues) == 0
    return ok, issues
