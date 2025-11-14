from pydantic import BaseModel
from typing import List

class ProcedureItem(BaseModel):
    step: str
    details: List[str]

class ManualRequest(BaseModel):
    businessType: str
    title: str
    goal: List[str]
    procedure: List[str]
    precaution: List[str]
    tone: str

class ManualResponse(BaseModel):
    title: str
    goal: str
    procedure: List[ProcedureItem]
    precaution: List[str]