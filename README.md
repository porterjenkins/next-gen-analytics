# next-gen-analytics

Workshop on modern analytics in the AI era

## Setup

### 0. Change your active directory to `next-gen-analytics`

```
cd next-gen-analytics
```

### 1. Install dependencies

Make sure uv is installed

Mac:

```
curl -LsSf https://astral.sh/uv/install.sh | sh                     
```

Windows  
`powershell -ExecutionPolicy ByPass -c  "irm https://astral.sh/uv/install.ps1 | iex"` 

Now build the environment:

```bash
uv sync
```

### 2. Start the database

Make sure Docker Desktop is running, then:

```bash
docker compose up -d
```

This starts a Postgres 16 container with the pgvector extension on port 5432.

To verify it's running:

```bash
docker compose ps
```

To stop the database:

```bash
docker compose down
```

To stop and delete all data:

```bash
docker compose down -v
```

### 3. Configure environment

Create a .env file to a manage environment variables

```bash
touch .env
```

Now let's add our environment variables:

```
DATABASE_URL=postgresql://rag_user:rag_pass@localhost:5432/rag_demo
GOOGLE_API_KEY=your-api-key-here
```

Set `PYTHONPATH` to the project root so module imports resolve correctly:

```bash
export PYTHONPATH=$(pwd)
```

> Note: Add this to your shell profile (e.g. `~/.zshrc`) or run it each time you open a new terminal.

### 4. Install Atlas

Atlas is used for database schema management:

```bash
curl -sSf https://atlasgo.sh | sh
```

### 5. Enable the pgvector extension

```bash
docker exec rag-postgres psql -U rag_user -d rag_demo -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 6. Run initial migration and insert data

Generate and apply the initial schema:

```bash
./db/scripts/migrate/generate.sh --name initial_schema
./db/scripts/migrate/apply.sh
```

RAG demo data (data/field_notes.csv → notes table). This embeds all 260 documents using `all-MiniLM-L6-v2` (runs locally, no API key needed) and stores them in the `notes` table with pgvector.

```bash
uv run python -m rag_demo.ingest
```

 Agent demo data (data/History_11127185.xlsx → iot table)

```bash
uv run python -m agent_demo.ingest
```

Verify that both insertion jobs worked

To open an interactive psql session:

```bash
docker exec -it rag-postgres psql -U rag_user -d rag_demo
```

Verify out the `notes` table:

```
SELECT * FROM notes LIMIT 2;
```

Verify the iot table:

```
SELECT * FROM iot LIMIT 2;
```

At this point you're ready to run the demo!

# DEMO #1: Retrieval Augmented Generation

### Launch the Streamlit app

```bash
uv run streamlit run rag_demo/app.py
```

### TODO:

- Fill in the postgres query found in `rag_demo.retriever.retriever`
  - `VECTOR_SEARCH_QUERY` and `VECTOR_SEARCH_QUERY_WITH_CITY`
- Change the distance metric:
  - Try cosine similiarity
  - L2 distance
- Change the system prompt, `SYSTEM_PROMPT`, in `rag.py`
- How does the number of documents affect the results?

# DEMO #2: Agent Demo (IoT events)

### Launch the agent Streamlit app

```bash
uv run streamlit run agent_demo/app.py
```

The agent uses Gemini (`gemini-2.5-flash`) with three tools that query the `iot` table:

- `get_counts_by_value` — counts grouped by `device_name`, `device_mapping`, or `event`.
- `get_time_series_by_value` — daily counts over time, optionally filtered to a specific value.
- `get_lagged_events` — for rows matching a filter, shows the prior event via a SQL `LAG` window function.

Each tool returns a markdown table that is fed back to the LLM and also surfaced in a "Tool calls" expander in the UI.

### 4. Add 2-3 new tools to analyze this data!

- Some ideas:
  - Events per day
  - Average value by event?
  - Anomalies?

### 5. Bonus: Multi-agent architecture

- Can you add multiple sub-agents that each solve specialized tasks?

### 6. Deployment

To deploy your app to Databricks, check out this tutorial: [https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent?language=LangGraph](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent?language=LangGraph)