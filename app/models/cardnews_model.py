from pydantic import BaseModel
from typing import List

class CardSlide(BaseModel):
    slide_id: int
    title: str
    content: str

class CardNewsResponse(BaseModel):
    title: str
    slides: List[str]  # 각 컷에 대한 한 줄 설명 (4개)
    image_url: str  # 4컷 이미지 URL 1개