import uuid
from typing import Set
import sqlglot
from sqlglot import exp

ALLOWED_TABLES: Set[str] = {"sales"}
BLOCKED_FUNCTIONS: Set[str] = {
    "pg_sleep",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_write_file",
    "dblink",
    "dblink_exec",
    "query_to_xml",
    "inet_client_addr",
    "version",
}
MAX_QUERY_LIMIT = 100


def validate_and_sanitize_sql(raw_sql: str, dataset_id: uuid.UUID) -> str:
    """
    Parses, validates, and transforms SQL queries to guarantee security:
    1. Rejects invalid syntax or empty queries.
    2. Enforces exactly ONE statement (blocks SQL injection via semicolons).
    3. Requires the statement to be a read-only SELECT.
    4. Restricts table access to only approved tables ('sales').
    5. Blocks dangerous system functions.
    6. Enforces dataset isolation by ensuring 'dataset_id = :dataset_id' is present.
    7. Enforces a maximum result row limit (default: 100 rows).

    Returns sanitized SQL ready for parameterized execution.
    """
    if not raw_sql or not raw_sql.strip():
        raise ValueError("SQL query cannot be empty.")

    clean_sql = raw_sql.strip()
    if clean_sql.endswith(";"):
        clean_sql = clean_sql[:-1].strip()

    # 1. Parse with SQLGlot using the PostgreSQL dialect
    try:
        parsed_expressions = sqlglot.parse(clean_sql, read="postgres")
    except Exception as e:
        raise ValueError(f"Invalid SQL syntax: {str(e)}")

    # 2. Block multiple statements
    if len(parsed_expressions) != 1:
        raise ValueError("Multiple SQL statements are strictly forbidden.")

    statement = parsed_expressions[0]

    # 3. Require SELECT query
    if not isinstance(statement, exp.Select):
        raise ValueError(
            f"Only read-only SELECT queries are allowed. Attempted: {type(statement).__name__}"
        )

    # 4. Restrict tables to allowlist
    tables = {t.name.lower() for t in statement.find_all(exp.Table) if t.name}
    if not tables:
        raise ValueError("Query must specify a target table.")

    unauthorized_tables = tables - ALLOWED_TABLES
    if unauthorized_tables:
        raise ValueError(
            f"Unauthorized table access: {', '.join(unauthorized_tables)}. Only 'sales' is permitted."
        )

    # 5. Block dangerous functions
    anonymous_functions = {
        f.name.lower() for f in statement.find_all(exp.Anonymous) if f.name
    }
    blocked_found = anonymous_functions.intersection(BLOCKED_FUNCTIONS)
    if blocked_found:
        raise ValueError(
            f"Dangerous or restricted functions detected: {', '.join(blocked_found)}"
        )

    # 6. Enforce dataset isolation
    # If the user or model didn't add the dataset_id filter, inject it into the WHERE clause
    sql_text = statement.sql("postgres")
    if ":dataset_id" not in sql_text and "dataset_id" not in sql_text:
        statement = statement.where("dataset_id = :dataset_id", append=True)

    # 7. Enforce maximum row limit
    limit_node = statement.args.get("limit")
    if not limit_node:
        statement = statement.limit(MAX_QUERY_LIMIT)
    else:
        try:
            current_limit = int(limit_node.expression.name)
            if current_limit > MAX_QUERY_LIMIT:
                statement = statement.limit(MAX_QUERY_LIMIT)
        except (ValueError, AttributeError):
            statement = statement.limit(MAX_QUERY_LIMIT)

    # Output formatted PostgreSQL query and normalize named parameter for SQLAlchemy
    final_sql = statement.sql("postgres").replace("%(dataset_id)s", ":dataset_id")
    return final_sql
