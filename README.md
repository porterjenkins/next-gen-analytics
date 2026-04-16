# next-gen-analytics

Workshop on modern analytics in the AI era

## Setup

### 1. Install dependencies

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

Copy `.env` and set your Google API key:

```bash
cp .env.example .env
# edit .env and set GOOGLE_API_KEY
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

### 6. Run initial migration

Generate and apply the initial schema:

```bash
./db/scripts/migrate/generate.sh --name initial_schema
./db/scripts/migrate/apply.sh
```

To open an interactive psql session:

```bash
docker exec -it rag-postgres psql -U rag_user -d rag_demo
```

Check out the `notes` table:

```
SELECT * FROM notes LIMIT 2;
```

## Database Management

The project uses [Atlas](https://atlasgo.sh) for database schema management. The `db/` directory contains all database-related files and scripts.

### Schema Declaration

- `**db/schema.pg.hcl**`: HCL-formatted schema declaration file that defines the desired database structure
- Edit this file to make schema changes (add tables, columns, constraints, etc.)

### Migration Scripts

1. **Generate Migration**:
  ```bash
   ./db/scripts/migrate/generate.sh --name <migration_name>
  ```
   Creates a new migration file based on changes to `schema.pg.hcl`. Migration names should be `camel_case`.
  > Note: This command spins up a temporary Docker container as a "dev" database to compute the diff. It does not touch the app database.
2. **Apply Migrations**:
  ```bash
   ./db/scripts/migrate/apply.sh
  ```
   Applies all pending migrations to the database.
3. **Inspect Schema**:
  ```bash
   ./db/scripts/schema/inspect.sh
  ```
   Opens a link to view the database schema graphically in Atlas.

### Workflow

1. Edit `db/schema.pg.hcl` to make desired schema changes
2. Generate a migration: `./db/scripts/migrate/generate.sh --name <descriptive_name>`
3. Review the generated migration file in `db/migrations/`
4. Apply the migration: `./db/scripts/migrate/apply.sh`

# DEMO #1: Retrieval Augmented Generation

### 1. Ingest data

Load the field notes CSV into the database and compute embeddings:

```bash
uv run python -m rag_demo.ingest
```

This embeds all 260 documents using `all-MiniLM-L6-v2` (runs locally, no API key needed) and stores them in the `notes` table with pgvector.

### 2. Launch the Streamlit app

```bash
uv run streamlit run rag_demo/app.py
```

