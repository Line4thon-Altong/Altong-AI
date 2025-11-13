from fastapi import APIRouter, HTTPException
from app.models.manual_model import ManualRequest, ManualResponse
from app.services.manual_service import generate_manual
from app.services.rag_service import embed_manual

router = APIRouter(prefix="/manual", tags=["Manual"])

@router.post("/generate", response_model=ManualResponse)
def create_manual(request: ManualRequest):
    """
    사장님 입력 기반으로 구조화된 AI 메뉴얼 생성
    """
    try:
        # 메뉴얼 생성
        return generate_manual(
            business_type=request.businessType,
            title=request.title,
            goal=request.goal,
            procedure=request.procedure,
            precaution=request.precaution,
            tone=request.tone
        )
    
        # 메뉴얼 생성 후 자동 임베딩
        try:
            embed_manual(
                manual_id=getattr(request, "manual_id", 0),  # Spring에서는 별도 전달 안 해도 됨
                manual_json=manual.model_dump()
            )
            print("RAG 임베딩 자동 저장 완료")
        except Exception as e:
            print(f"임베딩 저장 실패 (무시하고 계속 진행): {e}")

        return manual
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))