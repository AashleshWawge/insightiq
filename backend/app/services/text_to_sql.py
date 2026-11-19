import json
import time
import uuid
from typing import Dict, Any, Optional

from app.services.ai_service import get_groq_client
from app.config import GROQ_MODEL

SYSTEM_PROMPT = """You are a senior PostgreSQL database analyst for InsightIQ, a business intelligence platform.
Your task is to convert a user's natural language question about sales into a safe, performant PostgreSQL query.

### Target Database Schema:
Table: sales
Columns:
- id: bigint (Primary key)
- dataset_id: uuid (Foreign key referencing datasets)
- order_id: text (Order transaction identifier)
- order_date: date (Date when order was placed, format YYYY-MM-DD)
- customer_name: text (Customer full name)
- city: text (Customer / delivery city)
- product_name: text (Name of product sold)
- category: text (Product category, e.g. Electronics, Furniture)
- quantity: integer (Number of units purchased)
- unit_price: numeric (Price per unit in rupees)

### Critical Business Rules:
1. Revenue is ALWAYS calculated as: SUM(quantity * unit_price).
2. Average Order Value (AOV) is: SUM(quantity * unit_price) / COUNT(DISTINCT order_id).
3. Units sold is: SUM(quantity).
4. Total orders is: COUNT(DISTINCT order_id).
5. Monthly grouping must use: TO_CHAR(order_date, 'YYYY-MM') or DATE_TRUNC('month', order_date).

### Strict Safety & Dialect Rules:
1. Generate PostgreSQL-compliant SQL only.
2. Only generate a SINGLE read-only SELECT statement.
3. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, EXEC, GRANT, or transaction commands.
4. NEVER generate multiple queries separated by semicolons.
5. ALWAYS filter by dataset_id using the exact parameter: `dataset_id = :dataset_id`.
6. Use only the columns listed in the schema. Do not invent columns like 'discount', 'profit', 'cost', 'tax'.
7. If the user's question cannot be answered from the schema (e.g., questions about employee salaries, shipping carriers, profit margins, inventory levels), you MUST set "sql" to null and explain what data is missing in "explanation".

### Response Format:
You must respond ONLY with a valid JSON object matching this schema:
{
  "sql": "SELECT ... FROM sales WHERE dataset_id = :dataset_id ...",
  "explanation": "Clear plain-English explanation of how the query answers the question.",
  "chart_type": "bar" | "line" | "pie" | "table" | null
}
"""


def generate_sql_from_question(
    question: str,
    dataset_id: uuid.UUID,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calls Groq to generate a safe SQL query and explanation for the user's question.
    Returns structured dictionary with:
    - sql: Cleaned SQL query string (or None)
    - explanation: Plain-English explanation
    - chart_type: Recommended visualization
    - can_answer: Boolean
    - latency_ms: Generation time
    """
    client = get_groq_client()
    target_model = model or GROQ_MODEL

    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model=target_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Dataset ID: {dataset_id}\nUser Question: {question}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=600,
    )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    raw_content = response.choices[0].message.content or "{}"

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        raise RuntimeError("Failed to decode model response into valid JSON.")

    raw_sql = parsed.get("sql")
    explanation = parsed.get("explanation", "No explanation provided.")
    chart_type = parsed.get("chart_type")

    # Clean SQL string
    sql = None
    can_answer = False

    if raw_sql and isinstance(raw_sql, str) and raw_sql.strip().lower() != "null":
        clean_sql = raw_sql.strip()
        # Remove trailing semicolons
        if clean_sql.endswith(";"):
            clean_sql = clean_sql[:-1].strip()
        # Ensure :dataset_id placeholder is present for parameter binding
        if ":dataset_id" not in clean_sql and "dataset_id" in clean_sql:
            clean_sql = clean_sql.replace(f"'{dataset_id}'", ":dataset_id").replace(str(dataset_id), ":dataset_id")
        sql = clean_sql
        can_answer = True

    # Validate chart_type against allowlist
    valid_charts = {"bar", "line", "pie", "table"}
    if chart_type and str(chart_type).lower() in valid_charts:
        chart_type = str(chart_type).lower()
    else:
        chart_type = "table" if can_answer else None

    return {
        "dataset_id": dataset_id,
        "question": question,
        "sql": sql,
        "explanation": explanation,
        "chart_type": chart_type,
        "can_answer": can_answer,
        "latency_ms": latency_ms,
    }
