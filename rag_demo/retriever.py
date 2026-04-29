"""Retrieve the most relevant field notes for a query using pgvector."""

from pgvector.psycopg2 import register_vector

from rag_demo.db import get_connection
from rag_demo.embeddings import embed_query


VECTOR_SEARCH_QUERY = """
    SELECT id, datetime, text,
           embedding <=> %s::vector AS distance
    FROM notes
    ORDER BY distance
    LIMIT %s
"""

VECTOR_SEARCH_QUERY_WITH_CITY = """
    SELECT id, datetime, text,
           embedding <=> %s::vector AS distance
    FROM notes
    WHERE city = %s
    ORDER BY distance
    LIMIT %s
"""


def retrieve(query: str, top_k: int = 5, city: str | None = None) -> list[dict]:
    query_embedding = embed_query(query)

    conn = get_connection()
    register_vector(conn)

    with conn.cursor() as cur:
        if city:
            cur.execute(VECTOR_SEARCH_QUERY_WITH_CITY, (query_embedding, city, top_k))
        else:
            cur.execute(VECTOR_SEARCH_QUERY, (query_embedding, top_k))
        rows = cur.fetchall()

    conn.close()

    return [
        {"id": r[0], "datetime": str(r[1]), "text": r[2], "distance": r[3]}
        for r in rows
    ]
