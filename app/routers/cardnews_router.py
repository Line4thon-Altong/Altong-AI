from fastapi import APIRouter, HTTPException
from app.models.cardnews_model import CardNewsRequest, CardNewsResponse
from app.services.cardnews_service import generate_cardnews

router = APIRouter(prefix="/cardnews", tags=["CardNews"])

@router.post("/generate", response_model=CardNewsResponse)
def create_cardnews(request: CardNewsRequest):
    """
    매뉴얼 기반 4컷 만화 카드뉴스 생성
    
    Parameters:
    - manual_id: 매뉴얼 ID
    - tone: 말투 (예: "친근하게~", "존댓말로")
    - num_slides: 생성할 카드 수 (기본 4장, 4컷 만화 형식)
    
    특징:
    - 4컷 만화 형식 (2x2 그리드 레이아웃)
    - 모든 컷에 동일한 캐릭터 등장 (Chibi 스타일 카페 직원)
    - 1장의 이미지에 4개 패널 포함
    - 빠른 생성 (10-15초), 저렴한 비용 ($0.04)
    
    응답:
    - 4개 슬라이드 (각 컷의 제목과 내용 포함)
    - 모든 슬라이드가 동일한 image_url 공유 (4컷 만화 이미지)
    """
    try:
        return generate_cardnews(
            manual_id=request.manual_id,
            tone=request.tone,
            num_slides=request.num_slides
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

