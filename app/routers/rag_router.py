from fastapi import APIRouter, HTTPException
from app.services.rag_service import embed_manual
from app.models.rag_model import RagEmbedRequest

router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/embed")
def create_embeddings(request: RagEmbedRequest):
    try:
        embed_manual(request.manual_id, request.manual_json)
        return {"message": f"Manual {request.manual_id} 임베딩 저장 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
