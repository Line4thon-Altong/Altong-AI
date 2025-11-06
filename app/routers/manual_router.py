from fastapi import APIRouter, HTTPException
from app.models.manual_model import ManualRequest, ManualResponse
from app.services.manual_service import generate_manual

router = APIRouter(prefix="/manual", tags=["Manual"])

@router.post("/generate", response_model=ManualResponse)
def create_manual(request: ManualRequest):
    """
    사장님 입력 기반으로 구조화된 AI 메뉴얼 생성
    """
    try:
        return generate_manual(
            business_type=request.businessType,
            title=request.title,
            goal=request.goal,
            procedure=request.procedure,
            precaution=request.precaution,
            tone=request.tone
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))