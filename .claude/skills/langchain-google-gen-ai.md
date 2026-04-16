---
name: langchain-google-genai
description: >
  Build LangChain chains and agents powered by Google Gemini models using the
  langchain-google-genai package. Use this skill whenever the user wants to write
  Python code that combines LangChain with Google's Gemini models — including LCEL
  chains, ReAct agents, function-calling tools, RAG pipelines, or embeddings. Trigger
  even if the user says things like "build me a Gemini agent", "use Gemini with
  LangChain", "set up RAG with Google AI", "connect LangChain to Gemini", or asks to
  produce any .py file involving ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings,
  or LangGraph with Gemini. Always produce working, runnable .py files — not just
  snippets — unless the user explicitly asks for a snippet only.
---

# LangChain + Google GenerativeAI Skill

Produce working Python files that wire together LangChain and Google Gemini. Cover
all three major patterns: LCEL chains, agents/tools, and RAG pipelines.

---

## Package & Auth Basics

```bash
uv add langchain langchain-google-genai langchain-community langgraph
```

**Auth (pick one):**

```python
# Option A — env var (preferred)
import os
os.environ["GEMINI_API_KEY"] = "your-key"   # also accepts GOOGLE_API_KEY

# Option B — explicit in constructor
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key="your-key")

# Option C — Vertex AI backend
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "your-project-id"
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
```

> **Note:** `langchain-google-genai >= 4.0.0` uses the unified `google-genai` SDK and
> supports both the Gemini Developer API and Vertex AI via the same class. The legacy
> `ChatVertexAI` class is now deprecated for most use cases.

---

## Current Model IDs (as of April 2026)

| Model | Best for |
|---|---|
| `gemini-2.5-flash` | Fast, cost-efficient, everyday tasks |
| `gemini-2.5-pro` | Complex reasoning, long context |
| `gemini-3.1-pro-preview` | Latest flagship (if access available) |
| `models/gemini-embedding-001` | Embeddings (use with GoogleGenerativeAIEmbeddings) |

Always use the model string exactly as shown above. Do **not** invent model names.

---

## Pattern 1 — LCEL Chains

Read `references/lcel.md` for full patterns. Quick reference:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

chain = (
    ChatPromptTemplate.from_template("Summarize this in one sentence: {text}")
    | llm
    | StrOutputParser()
)

result = chain.invoke({"text": "LangChain is a framework for LLM apps."})
```

Key LCEL operators: `|` pipes runnables. Use `RunnablePassthrough` to forward inputs,
`RunnableParallel` / dict literal for fan-out.

---

## Pattern 2 — Agents & Tools

Read `references/agents.md` for full patterns. Quick reference:

```python
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

@tool
def get_word_length(word: str) -> int:
    """Returns the number of characters in a word."""
    return len(word)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
agent = create_react_agent(llm, tools=[get_word_length])
result = agent.invoke({"messages": [{"role": "user", "content": "How long is 'supercalifragilistic'?"}]})
```

Use `langgraph.prebuilt.create_react_agent` — it is the current idiomatic approach.
The older `initialize_agent` / `AgentExecutor` API still works but is legacy.

---

## Pattern 3 — RAG Pipelines

Read `references/rag.md` for full patterns. Quick reference:

```python
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | ChatPromptTemplate.from_template("Context:\n{context}\n\nQuestion: {question}")
    | llm
    | StrOutputParser()
)

answer = rag_chain.invoke("What is the main topic?")
```

---

## Structured Output

```python
from pydantic import BaseModel

class Summary(BaseModel):
    title: str
    key_points: list[str]

structured_llm = llm.with_structured_output(Summary)
result = structured_llm.invoke("Summarize the history of the internet.")
```

---

## Thinking Models (Gemini 2.5+)

```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    thinking_budget=1024,    # token budget for reasoning; 0 = off, -1 = dynamic
    include_thoughts=True,   # include reasoning in response
)
```

---

## File Generation Rules

1. **Always produce a complete, runnable `.py` file** — include all imports, env setup
   (with a placeholder key), and a `if __name__ == "__main__":` block.
2. **Use `python-dotenv`** for env var loading when the user seems to want production code.
3. **Add type hints and docstrings** to any custom tool or class.
4. **Default model**: use `gemini-2.5-flash` unless the user specifies otherwise.
5. **Never use deprecated APIs**: avoid `LLMChain`, `initialize_agent`, `AgentExecutor`
   from old langchain — prefer LCEL and LangGraph prebuilt.

---

## Reference Files

- `references/lcel.md` — LCEL chains in depth (parallel, branching, streaming, batching)
- `references/agents.md` — Tool definition patterns, LangGraph agent construction
- `references/rag.md` — Full RAG pipeline with document loaders, splitters, vector stores
