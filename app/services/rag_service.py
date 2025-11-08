from app.core.openai_client import client
from app.core.db import engine
from sqlalchemy import text
import re

def chunk_text(manual_json):
    chunks = []
    chunks.append(manual_json.get("goal", ""))
    for p in manual_json.get("procedure", []):
        if "step" in p:
            chunks.append(p["step"])
        if "details" in p:
            chunks.extend(p["details"])
    chunks.extend(manual_json.get("precaution", []))
    return [re.sub(r"\s+", " ", c.strip()) for c in chunks if c.strip()]

def embed_manual(manual_id: int, manual_json: dict):
    chunks = chunk_text(manual_json)
    for chunk in chunks:
        emb = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        ).data[0].embedding
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO manual_embeddings (manual_id, content, embedding)
                    VALUES (:manual_id, :content, :embedding)
                """),
                {"manual_id": manual_id, "content": chunk, "embedding": emb}
            )
            conn.commit()

def retrieve_similar(manual_id: int, query: str, limit: int = 3):
    q_emb = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    q_emb_str = "[" + ",".join(str(x) for x in q_emb) + "]"  # JSON string 형태로 변환

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT content
                FROM manual_embeddings
                WHERE manual_id = :manual_id
                ORDER BY embedding <-> (:q_emb)::vector
                LIMIT :limit
            """),
            {"manual_id": manual_id, "q_emb": q_emb_str, "limit": limit}
        ).fetchall()

    return [r._mapping["content"] for r in rows]