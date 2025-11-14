from app.core.openai_client import client
from app.core.db import engine
from sqlalchemy import text
import re
import json
import logging

logger = logging.getLogger(__name__)

def chunk_text(manual_json):
    """
    매뉴얼 JSON에서 step-detail 구조를 보존한 채로 chunk를 구성.
    기존처럼 한 줄짜리 flatten이 아니라, JSON 구조로 각 단계를 유지.
    """
    chunks = []

    # goal
    goal = manual_json.get("goal", "")
    if goal:
        chunks.append({"type": "goal", "content": goal})

    # procedure
    for p in manual_json.get("procedure", []):
        step_obj = {}
        if isinstance(p, dict):  # {"step": "...", "details": [...]}
            if "step" in p:
                step_obj["step"] = p["step"]
            if "details" in p:
                step_obj["details"] = p["details"]
        elif isinstance(p, str):  # 만약 단순 문자열 리스트 형태로 들어온 경우
            step_obj["step"] = p
        chunks.append(step_obj)

    # precaution
    for prec in manual_json.get("precaution", []):
        chunks.append({"type": "precaution", "content": prec})

    logger.info(f"[RAG] chunk_text() 완료 | 총 {len(chunks)}개 chunk 생성")
    return chunks

def embed_manual(manual_id: int, manual_json: dict):
    """
    매뉴얼의 각 절차(step, details)를 구조화된 JSON으로 embedding 저장.
    """
    chunks = chunk_text(manual_json)
    logger.info(f"[RAG] 임베딩 시작 | manual_id={manual_id}, chunk_count={len(chunks)}")

    for i, chunk in enumerate(chunks):
        try:
            # JSON 직렬화
            chunk_str = json.dumps(chunk, ensure_ascii=False)
            # OpenAI 임베딩 요청
            emb = client.embeddings.create(
                model="text-embedding-3-small",
                input=chunk_str
            ).data[0].embedding

            # PostgreSQL vector 캐스팅 위해 문자열 변환
            emb_vector_str = "[" + ",".join(str(x) for x in emb) + "]"

            # DB 저장
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO manual_embeddings (manual_id, content, embedding)
                        VALUES (:manual_id, :content, (:embedding)::vector)
                    """),
                    {
                        "manual_id": manual_id,
                        "content": chunk_str,
                        "embedding": emb_vector_str
                    }
                )
                conn.commit()

            logger.info(f"[RAG] {i+1}/{len(chunks)}번 chunk 저장 성공")

        except Exception as e:
            logger.error(f"[RAG] {i+1}번 chunk 저장 실패: {e}")

def retrieve_similar(manual_id: int, query: str, limit: int = 3):
    """
    주어진 manual_id와 query를 기반으로 유사한 절차(chunk)를 반환.
    """
    try:
        # 쿼리 임베딩 생성
        q_emb = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding
        q_emb_str = "[" + ",".join(str(x) for x in q_emb) + "]"

        # DB 검색
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

        result = []
        for r in rows:
            text_content = r._mapping["content"]
            try:
                result.append(json.loads(text_content))
            except json.JSONDecodeError:
                result.append({"text": text_content})

        logger.info(f"[RAG] retrieve_similar() 완료 | {len(result)}개 결과 반환")
        return result

    except Exception as e:
        logger.error(f"[RAG] retrieve_similar() 실패: {e}")
        return []