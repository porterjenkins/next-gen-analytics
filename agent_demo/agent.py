"""Gemini-powered LangChain agent for querying the iot events table."""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from agent_demo.db import get_connection
from agent_demo.tools import *

load_dotenv()

UNIQUE_VALUE_LIMIT = 50


def load_unique_values() -> dict[str, list[str]]:
    """Pull the top UNIQUE_VALUE_LIMIT distinct values (by frequency) for each
    filterable column, so the system prompt can ground the LLM's filter values.
    """
    cols = ("device_name", "device_mapping", "event")
    out: dict[str, list[str]] = {}
    conn = get_connection()
    try:
        for col in cols:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {col} FROM iot WHERE {col} IS NOT NULL "
                    f"GROUP BY {col} ORDER BY COUNT(*) DESC LIMIT %s",
                    (UNIQUE_VALUE_LIMIT,),
                )
                out[col] = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
    return out


def build_values_block(values: dict[str, list[str]]) -> str:
    lines = [
        "Reference values (top values by frequency — use exact strings when "
        "passing a filter_value):"
    ]
    for col, vals in values.items():
        lines.append(f"- {col}: {', '.join(vals)}")
    return "\n".join(lines)

SYSTEM_PROMPT = """\
You are an analytics assistant for a smart-home IoT events dataset.
The data lives in a Postgres table called `iot`, with columns including
`local_time`, `device_id`, `device_name`, `device_mapping`, `event`, and others.

You have the following tools:
  - get_counts_by_value: counts grouped by device_name, device_mapping, or event.
  - plot_counts_by_value: like get_counts_by_value, but renders a bar chart
    in the Streamlit UI. Call this when the user asks for a plot, chart,
    graph, or visualization of counts.
  - get_time_series_by_value: raw (non-aggregated) event records for a
    filter value, ordered by local_time.
  - get_lagged_events: show rows matching a filter with the prior event (LAG).
  - search_field_notes: semantic vector search over a separate `notes` table of
    technician field notes. Use this when the user asks qualitative questions
    ("what issues came up with doorbell cameras?", "problems in Provo"). Pass
    a `city` (Lehi, Provo, or Salt Lake City) only if the user explicitly
    mentions one; otherwise leave it as None.

When the user asks a question:
  1. Decide which column (device_name, device_mapping, or event) best matches
     their intent, and which tool fits the analytical pattern they want.
  2. Call the tool(s).
  3. Summarize the returned markdown table in plain English and include the
     table itself in your reply so the user can see the raw numbers.

If a user asks something the tools cannot answer, say so plainly.
"""

TOOLS = [
    get_counts_by_value,
    plot_counts_by_value,
    get_time_series_by_value,
    get_lagged_events,
    search_field_notes,
]


def build_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0,
    )
    values_block = build_values_block(load_unique_values())
    system_prompt = f"{SYSTEM_PROMPT}\n\n{values_block}"
    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=system_prompt,
    )
