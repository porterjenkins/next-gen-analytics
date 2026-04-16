"""Load field_notes.csv into the notes table with embeddings."""

import math

import pandas as pd
from pgvector.psycopg2 import register_vector
from tqdm import tqdm

from rag_demo.db import get_connection
from rag_demo.embeddings import embed_texts

CSV_PATH = "data/field_notes.csv"
BATCH_SIZE = 50


def ingest():
    df = pd.read_csv(CSV_PATH)
    conn = get_connection()
    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM notes")
        count = cur.fetchone()[0]
        if count > 0:
            print(f"Notes table already has {count} rows. Skipping ingest.")
            conn.close()
            return

    texts = df["document_text"].tolist()
    num_batches = math.ceil(len(texts) / BATCH_SIZE)

    for start in tqdm(range(0, len(texts), BATCH_SIZE), total=num_batches, desc="Embedding & inserting"):
        batch_texts = texts[start : start + BATCH_SIZE]
        batch_df = df.iloc[start : start + BATCH_SIZE]
        embeddings = embed_texts(batch_texts)

        with conn.cursor() as cur:
            for (_, row), emb in zip(batch_df.iterrows(), embeddings):
                cur.execute(
                    """
                    INSERT INTO notes (datetime, text, city, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (row["datetime"], row["document_text"], row["city"], emb),
                )
        conn.commit()

    conn.close()
    print("Ingest complete.")


if __name__ == "__main__":
    ingest()
