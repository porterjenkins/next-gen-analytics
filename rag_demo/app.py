"""Streamlit chat interface for the RAG demo."""

import streamlit as st

from rag_demo.rag import ask

st.set_page_config(page_title="Vivint Field Notes RAG", layout="wide")
st.title("Vivint Field Notes — RAG Demo")
st.caption("Ask questions about technician field notes from installation and service visits.")

top_k = st.selectbox("Number of documents to retrieve (k)", options=[1, 3, 5, 10, 20], index=2)
city = st.selectbox(
    "Filter by city",
    options=[None, "Lehi", "Provo", "Salt Lake City"],
    format_func=lambda x: "All cities" if x is None else x,
)

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
            result = ask(user_input, top_k=top_k, city=city)

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
