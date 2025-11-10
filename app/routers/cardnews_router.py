from fastapi import APIRouter, HTTPException
from app.models.cardnews_model import CardNewsRequest, CardNewsResponse
from app.services.cardnews_service import generate_cardnews

router = APIRouter(prefix="/cardnews", tags=["CardNews"])

@router.post("/generate", response_model=CardNewsResponse)
def create_cardnews(request: CardNewsRequest):
    """
    매뉴얼 기반 4컷 만화 카드뉴스 생성
    
    """
    try:
        return generate_cardnews(
            manual_id=request.manual_id,
            tone=request.tone,
            num_slides=request.num_slides
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

