---
name: langchain-streamlit-dataviz
description: >
  Build LangChain-powered Streamlit data visualization apps with tool-calling agents.
  Use this skill whenever the user wants to create a Streamlit dashboard or app that uses
  LangChain tools to (1) load or transform structured data into JSON/DataFrame form and
  (2) render charts (bar, line, scatter, pie, etc.). Trigger when the user mentions
  "langchain", "streamlit", "data visualization", "agent chart", "tool-based chart",
  "visualize data with langchain", or asks to build any data app that combines an LLM
  with pandas, matplotlib, plotly, or altair. Also trigger for queries like "build me
  a dashboard", "make a chart with an agent", "streamlit + langchain", or any request
  to produce a .py app that combines LangChain tool-calling with charting. Always
  produce a complete, runnable app.py — not just snippets.
---

# LangChain + Streamlit Data Visualization Skill

Produce working Streamlit apps that use a LangChain agent with two tools:
- **Data tool** — loads/transforms structured data and returns JSON (via pandas)
- **Chart tool** — renders a chart (bar, line, scatter, etc.) into Streamlit using the JSON

---

## Architecture Overview

```
User prompt (Streamlit input)
        │
        ▼
  LangChain Agent  ──►  Tool 1: get_data()    → returns JSON string
        │                                          (pandas → dict → json)
        │
        └──────────────►  Tool 2: render_chart()  → writes chart to st.session_state
                                                     (plotly or matplotlib)
        │
        ▼
  Streamlit rerenders chart from session_state
```

The agent decides *which* tool(s) to call based on the user's prompt. The chart tool
must use `st.session_state` to pass chart objects back to the main Streamlit thread,
since tool execution happens outside the Streamlit render loop.

---

## Package Setup

```bash
pip install streamlit langchain langchain-openai langchain-community \
            pandas plotly altair matplotlib python-dotenv
```

Or with `uv`:
```bash
uv add streamlit langchain langchain-openai langchain-community \
       pandas plotly altair python-dotenv
```

**Default LLM**: `gpt-4o-mini` via `langchain-openai`. Swap in any provider — see bottom
of this file for non-OpenAI alternatives.

---

## Core Pattern

Read `references/full_app.py` for a complete, runnable example. Key pieces:

### 1. Define the data tool

```python
from langchain_core.tools import tool
import pandas as pd
import json

@tool
def get_data(query: str) -> str:
    """
    Load structured data and return it as a JSON string.
    The query parameter describes what data or filtering is needed.
    Returns a JSON array of objects (list of dicts).
    """
    # --- Replace this block with your real data source ---
    df = pd.DataFrame({
        "month": ["Jan", "Feb", "Mar", "Apr", "May"],
        "revenue": [42000, 51000, 47000, 63000, 58000],
        "expenses": [30000, 33000, 31000, 38000, 35000],
    })
    # --- End data block ---
    return df.to_json(orient="records")
```

**Data source patterns** (pick one, replace the stub above):
- CSV: `df = pd.read_csv("data.csv")`
- SQLite: `df = pd.read_sql("SELECT ...", con)`
- REST API: `df = pd.DataFrame(requests.get(url).json())`
- Hard-coded for demos: inline dict as shown above

### 2. Define the chart tool

```python
import plotly.express as px
import streamlit as st

@tool
def render_chart(json_data: str, chart_type: str, x_col: str, y_col: str) -> str:
    """
    Render a chart from JSON data into the Streamlit app.
    
    Args:
        json_data: JSON array string (output from get_data)
        chart_type: One of 'bar', 'line', 'scatter', 'pie'
        x_col: Column name for the x-axis (or labels for pie)
        y_col: Column name for the y-axis (or values for pie)
    
    Returns a confirmation string. The chart is stored in st.session_state['chart'].
    """
    import json as _json
    records = _json.loads(json_data)
    df = pd.DataFrame(records)
    
    chart_map = {
        "bar":     lambda: px.bar(df, x=x_col, y=y_col),
        "line":    lambda: px.line(df, x=x_col, y=y_col),
        "scatter": lambda: px.scatter(df, x=x_col, y=y_col),
        "pie":     lambda: px.pie(df, names=x_col, values=y_col),
    }
    
    fig = chart_map.get(chart_type, chart_map["bar"])()
    st.session_state["chart"] = fig
    return f"Chart rendered: {chart_type} — {x_col} vs {y_col}"
```

> ⚠️ **Why `st.session_state`?**  
> Streamlit rerenders the page from top to bottom. LangChain tool calls happen in a
> regular Python call stack, so you can't call `st.plotly_chart()` directly inside a
> tool. Instead, store the figure in `st.session_state` and render it *after* the agent
> finishes in the main Streamlit flow.

### 3. Wire the agent

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    model=llm,
    tools=[get_data, render_chart],
    system_prompt=(
        "You are a data visualization assistant. "
        "When the user asks about data, first call get_data to fetch it, "
        "then call render_chart with the JSON to visualize it. "
        "Always infer sensible x_col and y_col from the data structure."
    ),
)
```

### 4. Streamlit UI shell

```python
import streamlit as st

st.title("📊 Data Viz Agent")

if "chart" not in st.session_state:
    st.session_state["chart"] = None
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Chat input
user_input = st.chat_input("Ask about your data...")

if user_input:
    with st.spinner("Thinking..."):
        result = agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })
    
    # Show agent's text reply
    final_text = result["messages"][-1].content
    st.session_state["messages"].append({"role": "assistant", "content": final_text})

# Render chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Render chart if available
if st.session_state["chart"] is not None:
    st.plotly_chart(st.session_state["chart"], use_container_width=True)
```

---

## Multi-chart & Column Selection

To support multiple charts or user-selected columns, extend the session state:

```python
# Store a list of charts
if "charts" not in st.session_state:
    st.session_state["charts"] = []

# In render_chart tool, append instead of overwrite:
st.session_state["charts"].append(fig)

# In UI, render all:
for fig in st.session_state["charts"]:
    st.plotly_chart(fig, use_container_width=True)
```

---

## Environment / Auth

```python
# .env file
OPENAI_API_KEY=sk-...

# In app.py
from dotenv import load_dotenv
load_dotenv()
```

---

## Alternative LLM Providers

Swap the LLM without changing the tools:

```python
# Anthropic Claude
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514")

# Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Local via Ollama
from langchain_community.chat_models import ChatOllama
llm = ChatOllama(model="llama3")
```

Pass the llm object into `create_agent(model=llm, ...)`.

---

## File Generation Rules

1. **Always produce a complete `app.py`** — imports, `.env` loading, tools, agent, full
   Streamlit UI, and `if __name__ == "__main__": ...` is not needed for Streamlit, but
   include a `# Run: streamlit run app.py` comment at the top.
2. **Default model**: `gpt-4o-mini` unless the user specifies otherwise.
3. **Default chart library**: Plotly (`plotly.express`) — it integrates with Streamlit
   via `st.plotly_chart()` with zero config.
4. **Always use `@tool` decorator** from `langchain_core.tools` for tool definitions.
5. **Include docstrings on every tool** — the agent uses these to understand when/how to
   call each tool.
6. **Default data**: include a small hard-coded demo DataFrame so the app runs without
   any data file, and add a comment telling the user where to swap in their real source.
7. **Never use deprecated APIs**: avoid `LLMChain`, `initialize_agent`, `AgentExecutor`.

---

## Reference Files

- `references/full_app.py` — Complete copy-paste starter app (bar + line chart, demo data)
- `references/multi_chart_app.py` — Extended version with column selector and chart history
