from pydantic import BaseModel
from typing import List

class CardSlide(BaseModel):
    slide_id: int
    title: str
    content: str  # 한 줄 문자열로 변경

class CardNewsResponse(BaseModel):
    title: str
    slides: List[CardSlide]
    image_url: str  # 4컷 이미지 URL 1개