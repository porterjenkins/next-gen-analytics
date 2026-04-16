"""Streamlit chat interface for the RAG demo."""

import streamlit as st

from rag_demo.rag import ask

st.set_page_config(page_title="Vivint Field Notes RAG", layout="wide")
st.title("Vivint Field Notes — RAG Demo")
st.caption("Ask questions about technician field notes from installation and service visits.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Ask a question about field notes..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Searching field notes..."):
            result = ask(user_input)

        st.markdown(result["answer"])

        with st.expander("Retrieved Sources"):
            for src in result["sources"]:
                st.markdown(
                    f"**Note {src['id']}** ({src['datetime']}) — "
                    f"distance: {src['distance']:.4f}\n\n{src['text']}"
                )
                st.divider()

    st.session_state.messages.append(
        {"role": "assistant", "content": result["answer"]}
    )
