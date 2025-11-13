from fastapi import APIRouter, HTTPException
from app.models.cardnews_model import CardNewsResponse
from app.services.cardnews_service import generate_cardnews

router = APIRouter(prefix="/cardnews", tags=["CardNews"])

@router.post("/generate", response_model=CardNewsResponse)
def create_cardnews(manual_id: int):
    """
    매뉴얼 기반 카드뉴스 생성 (4컷 고정)
    - manual_id: 참조할 매뉴얼 ID
    - tone은 DB에서 자동으로 가져옵니다
    """
    try:
        return generate_cardnews(manual_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))