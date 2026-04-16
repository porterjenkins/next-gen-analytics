"""Thread-safe chart queue shared between tools and the Streamlit app.

Tools call `queue_chart(...)` to enqueue a chart spec. The Streamlit app
calls `drain_charts()` after the agent finishes to collect and render them.
Using a module-level list (instead of st.session_state) avoids issues when
LangGraph executes tool calls outside the main Streamlit script thread.
"""

import threading

_lock = threading.Lock()
_queue: list[dict] = []


def queue_chart(spec: dict) -> None:
    with _lock:
        _queue.append(spec)


def drain_charts() -> list[dict]:
    with _lock:
        out = _queue[:]
        _queue.clear()
    return out
