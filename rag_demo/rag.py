"""RAG chain: retrieve context from pgvector, generate answer with Gemini."""

import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_demo.retriever import retrieve

load_dotenv()

SYSTEM_PROMPT = """\
You are an AI assistant for Vivint, a home security company. \
You answer questions using field notes from technician installation and service visits.

Use ONLY the provided field notes to answer the question. \
If the notes don't contain enough information, say so. \
Cite specific notes by their ID when relevant.

Field Notes:
{context}
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
)

chain = prompt | llm | StrOutputParser()


def ask(question: str, top_k: int = 5, city: str | None = None) -> dict:
    results = retrieve(question, top_k=top_k, city=city)

    context = "\n\n".join(
        f"[Note {r['id']}] ({r['datetime']}): {r['text']}" for r in results
    )

    answer = chain.invoke({"context": context, "question": question})

    return {
        "answer": answer,
        "sources": results,
    }
