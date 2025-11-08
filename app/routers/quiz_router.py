from fastapi import APIRouter, HTTPException
from app.models.quiz_model import QuizRequest, QuizResponse
from app.services.quiz_service import generate_quiz

router = APIRouter(prefix="/quiz", tags=["Quiz"])

@router.post("/generate", response_model=QuizResponse)
def create_quiz(request: QuizRequest):
    try:
        return generate_quiz(request.manual_id, request.tone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))