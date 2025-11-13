from pydantic import BaseModel
from typing import List, Optional

class QuizItem(BaseModel):
    type: str
    question: str
    options: List[str]
    answer: str
    explanation: str

class QuizRequest(BaseModel):
    manual_id: int
    tone: str
    focus: Optional[str] = "procedure"

class QuizResponse(BaseModel):
    quizzes: List[QuizItem]