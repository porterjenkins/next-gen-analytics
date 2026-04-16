"""Streamlit chat interface for the IoT agent demo.

Run: uv run streamlit run agent_demo/app.py
"""

import altair as alt
import pandas as pd
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent_demo.agent import build_agent
from agent_demo.viz import drain_charts

st.set_page_config(page_title="IoT Events Agent", layout="wide")
st.title("IoT Events — Agent Demo")
st.caption(
    "Ask questions about the `iot` events table. The agent has tools for "
    "counts, daily time series, and lagged-event lookups."
)

if "agent" not in st.session_state:
    st.session_state.agent = build_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []


def _render_tool_call(status, tool_call: dict) -> None:
    status.markdown(f"**Call:** `{tool_call['name']}`")
    status.json(tool_call.get("args", {}))


def _render_tool_result(status, msg: ToolMessage) -> None:
    status.markdown("**Result:**")
    status.markdown(msg.content)


def stream_agent(history: list) -> str:
    """Stream agent updates, surfacing each tool call in an st.status box.
    Returns the final assistant text.
    """
    pending_statuses: dict[str, any] = {}
    final_text = ""

    for chunk in st.session_state.agent.stream(
        {"messages": history}, stream_mode="updates"
    ):
        for node_name, update in chunk.items():
            for msg in update.get("messages", []):
                if isinstance(msg, AIMessage):
                    if getattr(msg, "tool_calls", None):
                        for tc in msg.tool_calls:
                            status = st.status(
                                f"🔧 `{tc['name']}`...", expanded=False
                            )
                            _render_tool_call(status, tc)
                            pending_statuses[tc["id"]] = status
                    elif msg.content:
                        final_text = msg.content
                elif isinstance(msg, ToolMessage):
                    status = pending_statuses.pop(msg.tool_call_id, None)
                    if status is not None:
                        _render_tool_result(status, msg)
                        status.update(
                            label=f"✅ `{msg.name}`", state="complete"
                        )

    for status in pending_statuses.values():
        status.update(state="error", label="tool call did not return")

    return final_text


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Ask about iot events..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        drain_charts()  # clear any stale charts before this turn
        history = [
            HumanMessage(content=m["content"]) if m["role"] == "user"
            else AIMessage(content=m["content"])
            for m in st.session_state.messages
        ]
        answer = stream_agent(history)
        st.markdown(answer)

        charts = drain_charts()
        st.caption(f"Charts queued: {len(charts)}")
        for spec in charts:
            df = pd.DataFrame(spec["data"])
            if spec["type"] == "bar":
                chart = (
                    alt.Chart(df)
                    .mark_bar()
                    .encode(
                        x=alt.X(f"{spec['y']}:Q", title=spec["y"]),
                        y=alt.Y(f"{spec['x']}:N", sort="-x", title=spec["x"]),
                        tooltip=list(df.columns),
                    )
                    .properties(title=spec["title"], height=max(200, 22 * len(df)))
                )
                st.altair_chart(chart, use_container_width=True)

    st.session_state.messages.append({"role": "assistant", "content": answer})
