import json
import time
from typing import Dict, Any, List

from app.services.ai_service import get_groq_client
from app.config import GROQ_MODEL

EXPLAIN_SYSTEM_PROMPT = """You are a senior data analyst.
Summarize the query results directly in 1-2 concise, factual sentences.

Rules:
1. State findings and key figures directly. Never use filler openers ("Here's what the data shows", "Interestingly", "As we can see", "It's worth noting").
2. No corporate jargon ("deep dive", "unpack", "game-changer", "navigate", "landscape").
3. No passive voice or false agency ("the data tells us", "the numbers reveal"). State the fact directly: e.g. "Laptops produced the highest revenue at ₹12,40,000."
4. Base your summary strictly on the provided rows and columns. Never invent numbers or trends.
5. Recommend the best visual chart:
   - 'line': for time-series data (dates, months, years)
   - 'bar': for categorical rankings (products, categories, cities)
   - 'pie': for small proportion breakdowns (<= 5 categories)
   - 'table': for multi-column details or unaggregated lists
6. Respond ONLY with a valid JSON object matching:
{
  "explanation": "1-2 direct factual sentences stating the primary finding with numbers.",
  "recommended_chart": "bar" | "line" | "pie" | "table"
}
"""


def explain_query_results(
    question: str,
    columns: List[str],
    sample_rows: List[Dict[str, Any]],
    total_row_count: int,
) -> Dict[str, Any]:
    """
    Sends returned data to Groq to generate a plain-English explanation and chart recommendation.
    """
    client = get_groq_client()

    # Cap sample rows to 5 to minimize LLM token consumption
    limited_sample = sample_rows[:5]

    user_content = f"""
User Question: {question}
Total Rows Returned: {total_row_count}
Columns: {', '.join(columns)}
Sample Rows:
{json.dumps(limited_sample, indent=2)}
"""

    start_time = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=250,
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        raw_text = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_text)

        explanation = parsed.get("explanation", "Query returned the requested records.")
        chart = str(parsed.get("recommended_chart", "table")).lower()
        if chart not in {"bar", "line", "pie", "table"}:
            chart = "table"

        return {
            "explanation": explanation,
            "recommended_chart": chart,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        # Fallback in case of model parsing error
        return {
            "explanation": f"Successfully retrieved {total_row_count} records matching your query.",
            "recommended_chart": "table",
            "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
        }
