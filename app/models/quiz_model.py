from pydantic import BaseModel
from typing import List

class QuizItem(BaseModel):
    type: str
    question: str
    options: List[str]
    answer: str
    explanation: str

class QuizRequest(BaseModel):
    manual_id: int
    tone: str

class QuizResponse(BaseModel):
    quizzes: List[QuizItem]