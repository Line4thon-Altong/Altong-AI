from fastapi import APIRouter, HTTPException
from app.services.rag_service import embed_manual

router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/embed")
def create_embeddings(manual_id: int, manual_json: dict):
    try:
        embed_manual(manual_id, manual_json)
        return {"message": f"Manual {manual_id} 임베딩 저장 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
