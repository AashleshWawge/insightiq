# InsightIQ — AI-Powered Business Intelligence Dashboard

InsightIQ is a full-stack, portfolio-ready business intelligence web application. It enables non-technical users to upload sales CSV datasets, explore automated business metrics in an interactive dashboard, and ask questions in natural language. Powered by Groq LLMs and SQLGlot, it securely translates English questions into PostgreSQL queries, executes approved read-only queries safely, and renders tabular results with plain-English AI explanations.

---

## Architecture Overview

```text
                           USER
                            |
                            v
                   REACT + VITE FRONTEND (Port 5173)
        -------------------------------------------------------------
        | Ask AI (Text-to-SQL) | Analytics Dashboard | Query History |
        | CSV Upload & Preview | Dynamic Visuals     | CSV Export    |
        -------------------------------------------------------------
                            |
                       HTTP / JSON
                            |
                            v
                   PYTHON FASTAPI BACKEND (Port 8000)
        -------------------------------------------------------------
        | Data Ingestion API   | SQLGlot AST Validator              |
        | Dashboard Metric API | Read-Only SQL Execution Engine     |
        | Groq Text-to-SQL API | Query History & Export API         |
        -------------------------------------------------------------
               |                     |                    |
               v                     v                    v
          PANDAS CSV             GROQ API             SQLALCHEMY
          PROCESSING         (qwen/qwen3.8-27b)           |
               |                     |                    |
               |           Structured JSON SQL            |
               |                     |                    |
               v                     v                    v
                       POSTGRESQL DATABASE (Port 5432)
                ----------------------------------------------
                | datasets | sales | query_history           |
                ----------------------------------------------
```

---

## Key Features Built Across All Phases

1. **CSV Ingestion & Pandas Validation (Phase 2)**:
   - Validates required columns: `order_id`, `order_date`, `customer_name`, `city`, `product_name`, `category`, `quantity`, `unit_price`.
   - Filters corrupt rows, non-positive quantities, and negative prices.
   - Saves records into PostgreSQL within an atomic transaction.
2. **Business Analytics Dashboard (Phase 3)**:
   - Real-time SQL aggregations for 5 core KPIs: Gross Revenue, Total Orders, Units Sold, Unique Customers, Average Order Value (AOV).
   - 4 Recharts visualisations: Monthly Revenue Trend, Category Breakdown, City Revenue, and Top 5 Bestselling Products.
3. **Groq Text-to-SQL Engine (Phase 4 & 5)**:
   - Uses Groq SDK with schema grounding and revenue definitions (`SUM(quantity * unit_price)`).
   - Generates structured JSON responses containing SQL, plain-English explanations, and suggested chart types.
   - Refuses out-of-scope questions without hallucinating.
4. **Defense-in-Depth Safe SQL Execution (Phase 6)**:
   - **SQLGlot AST Parsing**: Enforces single statement, `SELECT` only, strictly allowlisted tables (`sales`), and blocks dangerous functions (`pg_sleep`, `dblink`, etc.).
   - **Database-Level Read-Only Mode**: Executes `SET TRANSACTION READ ONLY;` so PostgreSQL aborts any write attempt at the engine level.
   - **Safety Limits**: Automatic `SET LOCAL statement_timeout = 5000;` (5s timeout) and row capping at 100 rows.
5. **Interactive Results & AI Explanation (Phase 7 & 8)**:
   - Explicit user approval before running any query.
   - Dynamic results table with currency and number formatting.
   - Automatic plain-English AI explanations summarizing key findings.
   - Dynamic chart rendering (bar or line charts) directly from query output.
6. **Query History & Export (Phase 9)**:
   - Persistent `query_history` database records for past questions.
   - One-click query re-run.
   - Client-side and server-side CSV export of query results.

---

## Project Structure

```text
insightiq/
├── frontend/                     # React 19 + Vite + Tailwind CSS + Recharts
│   ├── src/
│   │   ├── App.jsx               # Main SPA application containing all tabs
│   │   ├── main.jsx              # React DOM entry point
│   │   └── index.css             # Tailwind CSS directives
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── backend/                      # Python 3.13 + FastAPI + SQLAlchemy + Groq
│   ├── app/
│   │   ├── main.py               # Application entry point & router mounting
│   │   ├── config.py             # Centralized settings & environment variables
│   │   ├── database.py           # SQLAlchemy engine, SessionLocal, and get_db dependency
│   │   ├── models/               # SQLAlchemy ORM models (Dataset, Sale, QueryHistory)
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── routes/               # REST API route handlers (health, datasets, dashboard, ai, query_history)
│   │   └── services/             # Business logic (CSV ingestion, Groq client, SQLGlot validator)
│   ├── tests/                    # 27 automated unit tests with Pytest
│   ├── requirements.txt          # Pinned Python dependencies
│   ├── .env.example              # Environment variables template
│   └── .env                      # Local secrets (excluded from Git)
├── sample_data/
│   └── sales_sample.csv          # 180 realistic synthetic sales records for testing
├── .gitignore
└── README.md
```

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL running locally on port 5432

### 2. Backend Setup
In a terminal:
```powershell
cd backend

# 1. Activate Virtual Environment
.\venv\Scripts\Activate.ps1   # (Windows PowerShell)
# or source venv/bin/activate  # (macOS/Linux)

# 2. Configure Environment Variables
# Copy .env.example to .env and configure your PostgreSQL password and Groq API Key:
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/insightiq
# GROQ_API_KEY=your_key_here
# GROQ_MODEL=qwen/qwen3.8-27b

# 3. Run Automated Tests
pytest -v

# 4. Start FastAPI Server
python -m uvicorn app.main:app --reload --port 8000
```
- API Root: `http://localhost:8000/`
- Interactive Swagger UI: `http://localhost:8000/docs`

### 3. Frontend Setup
In a second terminal:
```powershell
cd frontend

# Install dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```
- Open `http://localhost:5173/` in your browser.

---

## API Contract Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Backend service health check |
| `GET` | `/api/health/database` | PostgreSQL connection latency ping |
| `POST` | `/api/datasets/upload` | Upload and validate sales CSV file |
| `GET` | `/api/datasets` | List all imported datasets |
| `GET` | `/api/datasets/{id}` | Get dataset details |
| `GET` | `/api/datasets/{id}/preview` | Preview first N records of dataset |
| `DELETE` | `/api/datasets/{id}` | Delete dataset and cascade-delete its records |
| `GET` | `/api/dashboard/{id}/summary` | Primary business KPIs (Revenue, Orders, Units, Customers, AOV) |
| `GET` | `/api/dashboard/{id}/monthly-revenue` | Monthly chronological revenue metrics |
| `GET` | `/api/dashboard/{id}/category-revenue` | Sales revenue aggregated by category |
| `GET` | `/api/dashboard/{id}/city-revenue` | Sales revenue aggregated by city |
| `GET` | `/api/dashboard/{id}/top-products` | Top N bestselling products by revenue |
| `POST` | `/api/ai/test` | Test Groq API connectivity and latency |
| `POST` | `/api/ai/generate-query` | Convert natural language to read-only SQL |
| `POST` | `/api/ai/execute-query` | Validate and execute read-only SQL safely |
| `POST` | `/api/ai/explain-results` | Explain returned data rows in plain English |
| `GET` | `/api/query-history` | Retrieve past questions and queries |
| `GET` | `/api/query-history/{id}/export` | Export query results as downloadable CSV |
| `DELETE` | `/api/query-history/{id}` | Delete a query history item |

---

## Definition of Done Verification (All 17/17 Complete)

- [x] React frontend starts locally without errors.
- [x] FastAPI backend starts locally without errors.
- [x] PostgreSQL connection works with pooling and ping checks.
- [x] Sample CSV can be uploaded and validated.
- [x] Invalid CSVs produce clear descriptive errors.
- [x] Imported records are associated with a dataset ID for complete isolation.
- [x] Dashboard KPIs are calculated correctly using database-level SQL aggregations.
- [x] Recharts displays monthly, category, city, and top products visualisations.
- [x] Groq API connection works with sub-second latency.
- [x] Natural-language questions generate accurate, read-only SQL.
- [x] Generated SQL is visible for inspection before execution.
- [x] User must explicitly approve execution.
- [x] SQLGlot validation rejects unsafe statements, multi-queries, and unauthorized tables.
- [x] Database execution uses read-only transactions and 5-second timeouts.
- [x] Dataset isolation is enforced at both application and query levels.
- [x] Query results appear in an interactive table with CSV export.
- [x] AI explanations and chart recommendations are grounded in returned results.
- [x] Basic query history and re-run capabilities work.
- [x] API keys and secrets are strictly excluded from Git.
