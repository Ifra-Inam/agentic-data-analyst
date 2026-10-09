# Agentic Data Analyst

I created an AI-powered data analyst for the AdventureWorks database. A user can ask business questions in natural language and get answers based on the database and business documentation, with validated SQL and charts when useful.

## How It Works

The Streamlit app runs a LangGraph workflow:

1. Retrieve relevant content from the Markdown files in `knowledge/` using Ollama embeddings and Chroma.
2. Decide whether the question can be answered from documentation or needs a database query.
3. For database questions, inspect the PostgreSQL schema, generate SQL, check that it is read-only, and ask the LLM to review it.
4. Run the SQL, check the result, and optionally create a Plotly chart.
5. Ask the LLM to write the final answer.

Groq provides chat completions using `openai/gpt-oss-20b`. Ollama provides the `nomic-embed-text` embedding model. PostgreSQL stores AdventureWorks.

## Graph Nodes

The graph is defined in [`agent/graph.py`](agent/graph.py). This is the node order for database questions. Documentation-only questions finish after `rag`.

| Node       | Implementation                                                       | Responsibility                                                                                                                                               |
| ---------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `rag`      | [`retrieve_documentation.py`](agent/nodes/retrieve_documentation.py) | Retrieves relevant business documentation and routes the question to either a documentation answer or database analysis.                                     |
| `schema`   | [`get_schema.py`](agent/nodes/get_schema.py)                         | Reads the database schema and asks the LLM to select relevant tables and columns.                                                                            |
| `sql`      | [`generate_sql.py`](agent/nodes/generate_sql.py)                     | Generates a PostgreSQL query from the question, documentation, and selected schema.                                                                          |
| `validate` | [`validate_sql.py`](agent/nodes/validate_sql.py)                     | Checks SQL syntax, restricts queries to read-only forms, and asks the LLM whether the query answers the question. Invalid SQL returns to `sql` for revision. |
| `execute`  | [`execute_sql.py`](agent/nodes/execute_sql.py)                       | Executes the query and stores its rows or database error in the workflow state.                                                                              |
| `check`    | [`check_result.py`](agent/nodes/check_result.py)                     | Checks whether the result answers the question. Results that need revision return to `sql`.                                                                  |
| `analyze`  | [`analyze_result.py`](agent/nodes/analyze_result.py)                 | Decides whether a chart would help and, if so, selects its type and fields.                                                                                  |
| `chart`    | [`create_chart.py`](agent/nodes/create_chart.py)                     | Builds the Plotly chart from the selected result columns.                                                                                                    |

## Requirements

- Docker Desktop with Docker Compose
- A valid Groq API key
- Ports `8501`, `5432`, and `11434` available

## Start With Docker

From the repository root in PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace `your_groq_api_key` with an active Groq API key:

```dotenv
GROQ_API_KEY=your_actual_groq_api_key
```

Ollama runs locally in Docker, and the app connects to that service for embeddings.

Build and start the services:

```powershell
docker compose up --build -d
```

Open [http://localhost:8501](http://localhost:8501). On first startup, Compose initializes PostgreSQL from `database/adventureworks.sql` and downloads `nomic-embed-text` into the Ollama volume. The first run can take a few minutes.

Useful commands:

```powershell
docker compose ps
docker compose logs -f app
docker compose down
```

`docker compose down` stops and removes the containers but keeps database and Ollama data. `docker compose down -v` also deletes the volumes, including database contents; use it only when you intentionally want a clean reset.

## Ask Questions

Example questions:

- What is total net revenue?
- What are the top 10 best-selling products by quantity?
- How has the number of customers changed over time?
- Which products generate the most revenue?

Questions asking for large unaggregated result sets can use substantial model tokens. Prefer totals, trends, rankings, or a specific top-N when those answer the question.

## Run Without Docker

Install Python 3.12, PostgreSQL, and Ollama locally. Create and activate a virtual environment, install the dependencies, and ensure the local services are running:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull nomic-embed-text
cd app
streamlit run ui.py
```

Set `GROQ_API_KEY` in the root `.env`. The default local connection settings are PostgreSQL at `localhost:5432` with database `Adventureworks`, user `postgres`, and password `postgres`; Ollama defaults to `http://localhost:11434`. Override these with `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, or `OLLAMA_BASE_URL` as needed. Initialize PostgreSQL with `database/adventureworks.sql` before starting the app.

## Configuration and Data

Compose uses these service addresses inside Docker:

| Service       | Container address | Host port |
| ------------- | ----------------- | --------: |
| Streamlit app | `app:8501`        |    `8501` |
| PostgreSQL    | `postgres:5432`   |    `5432` |
| Ollama        | `ollama:11434`    |   `11434` |

The Compose file uses development database credentials. Do not expose this setup to untrusted networks or reuse these credentials in production. PostgreSQL and Ollama data are stored in named Docker volumes; the knowledge Markdown files are part of the repository.
