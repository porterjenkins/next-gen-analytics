"""LangChain tools that query the iot and notes tables and return markdown tables."""

from pickle import NONE
import pandas as pd
from langchain_core.tools import tool
from pgvector.psycopg2 import register_vector

from agent_demo.db import get_connection
from agent_demo.viz import queue_chart
from rag_demo.embeddings import embed_query

ALLOWED_COLUMNS = {"device_name", "device_mapping", "event"}
ALLOWED_CITIES = {"Lehi", "Provo", "Salt Lake City"}


def _validate_column(col: str) -> str:
    if col not in ALLOWED_COLUMNS:
        raise ValueError(
            f"Invalid column '{col}'. Must be one of: {sorted(ALLOWED_COLUMNS)}"
        )
    return col


def _run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


@tool
def get_counts_by_value(group_by: str, limit: int = None) -> str:
    """Return counts of rows in the iot events table grouped by a column.

    Args:
        group_by: Column to group by. Must be one of: 'device_name',
            'device_mapping', 'event'. Infer from the user's question.
        limit: Maximum number of rows to return, ordered by count descending.

    Returns:
        Markdown table with columns [<group_by>, count].
    """
    col = _validate_column(group_by)
    sql = f"""
        SELECT {col} AS {col}, COUNT(*) AS count
        FROM iot
        WHERE {col} IS NOT NULL
        GROUP BY {col}
        ORDER BY count DESC
        LIMIT %s
    """
    df = _run_query(sql, (limit,))
    if df.empty:
        return f"No rows found for `{col}`."
    return df.to_markdown(index=False)


@tool
def get_time_series_by_value(
    filter_column: str, filter_value: str, limit: int = 200
) -> str:
    """Return raw iot event records matching a column value, ordered by local_time.

    This is a raw time series — one row per event, not aggregated. Use it when
    the user wants to see the actual sequence of events over time rather than
    counts.

    Args:
        filter_column: Column to filter on. One of: 'device_name',
            'device_mapping', 'event'. Infer from the user's question.
        filter_value: The value to filter on (e.g. 'Front Door', 'armed_stay').
        limit: Maximum number of rows to return.

    Returns:
        Markdown table with columns [local_time, device_id, device_name,
        event, event_value] sorted by local_time ascending.
    """
    col = _validate_column(filter_column)
    sql = f"""
        SELECT local_time, device_id, device_name, event, event_value
        FROM iot
        WHERE {col} = %s
        ORDER BY local_time
        LIMIT %s
    """
    df = _run_query(sql, (filter_value, limit))
    if df.empty:
        return f"No rows found where `{col}` = `{filter_value}`."
    return df.to_markdown(index=False)


@tool
def get_lagged_events(filter_column: str, filter_value: str, limit: int = 50) -> str:
    """Show iot events matching a filter along with the immediately prior
    event (by local_time) from the full table. Uses a SQL LAG window function
    over (local_time, device_id, event) ordered by local_time.

    Useful for questions like "what happened right before the front door
    opened?" or "what preceded each panel_arming event?".

    Args:
        filter_column: One of: 'device_name', 'device_mapping', 'event'.
            Infer from the user's question.
        filter_value: The value to filter on (e.g. 'Front Door', 'armed_stay').
        limit: Maximum number of rows to return.

    Returns:
        Markdown table with columns [local_time, device_id, event,
        prev_local_time, prev_device_id, prev_event].
    """
    col = _validate_column(filter_column)
    sql = f"""
        WITH with_lag AS (
            SELECT local_time,
                   device_id,
                   event,
                   {col} AS filter_col,
                   LAG(local_time) OVER (ORDER BY local_time) AS prev_local_time,
                   LAG(device_id)  OVER (ORDER BY local_time) AS prev_device_id,
                   LAG(event)      OVER (ORDER BY local_time) AS prev_event
            FROM iot
        )
        SELECT local_time, device_id, event,
               prev_local_time, prev_device_id, prev_event
        FROM with_lag
        WHERE filter_col = %s
        ORDER BY local_time
        LIMIT %s
    """
    df = _run_query(sql, (filter_value, limit))
    if df.empty:
        return f"No rows found where `{col}` = `{filter_value}`."
    return df.to_markdown(index=False)


@tool
def plot_counts_by_value(group_by: str, limit: int = 20) -> str:
    """Render a bar chart of iot event counts grouped by a column.

    Runs the same query as `get_counts_by_value`, converts the result to
    JSON records, and pushes it to the Streamlit session so the app can
    render a bar chart. Use this when the user wants a visualization (not
    just a table) of counts.

    Args:
        group_by: Column to group by. One of: 'device_name',
            'device_mapping', 'event'. Infer from the user's question.
        limit: Maximum number of bars in the chart.

    Returns:
        Short confirmation plus the top-3 rows as markdown (for the LLM
        to reason about). The actual chart is rendered in the Streamlit UI.
    """
    col = _validate_column(group_by)
    sql = f"""
        SELECT {col} AS {col}, COUNT(*) AS count
        FROM iot
        WHERE {col} IS NOT NULL
        GROUP BY {col}
        ORDER BY count DESC
        LIMIT %s
    """
    df = _run_query(sql, (limit,))
    if df.empty:
        return f"No rows found for `{col}`."

    queue_chart({
        "type": "bar",
        "title": f"iot event counts by {col}",
        "x": col,
        "y": "count",
        "data": df.to_dict(orient="records"),
    })

    top = ", ".join(f"{r[col]} ({r['count']})" for _, r in df.head(3).iterrows())
    return (
        f"Rendered a bar chart of `{col}` counts ({len(df)} bars). "
        f"Top values: {top}. Tell the user the chart has been rendered and "
        f"briefly summarize the leaders — do NOT reprint the full table."
    )


@tool
def search_field_notes(
    query: str, city: str | None = None, top_k: int = 5
) -> str:
    """Semantic (vector) search over the `notes` table of technician field notes.

    Embeds the query with all-MiniLM-L6-v2 and finds the nearest neighbors
    using pgvector cosine distance. Optionally restricts to a single city.

    Args:
        query: Natural-language description of what to find in the notes.
        city: Optional city filter. If provided, must be one of
            'Lehi', 'Provo', or 'Salt Lake City'. Pass None to search
            across all cities. Infer from the user's question — only
            set it when they explicitly mention a city.
        top_k: Number of notes to return.

    Returns:
        Markdown table with columns [id, datetime, city, distance, text].
    """
    if city is not None and city not in ALLOWED_CITIES:
        raise ValueError(
            f"Invalid city '{city}'. Must be one of: {sorted(ALLOWED_CITIES)} or None."
        )

    embedding = embed_query(query)

    sql = """
        SELECT id, datetime, city, text,
               embedding <=> %s::vector AS distance
        FROM notes
        WHERE (%s::text IS NULL OR city = %s)
        ORDER BY distance
        LIMIT %s
    """

    conn = get_connection()
    register_vector(conn)
    try:
        df = pd.read_sql(sql, conn, params=(embedding, city, city, top_k))
    finally:
        conn.close()

    if df.empty:
        return "No matching field notes found."
    return df.to_markdown(index=False)



