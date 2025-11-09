from pydantic import BaseModel
from typing import List

class CardSlide(BaseModel):
    """개별 카드 슬라이드"""
    title: str  # 카드 제목
    content: List[str]  # 카드 내용 (여러 줄)
    image_prompt: str  # 이미지 생성을 위한 프롬프트
    image_url: str = ""  # 생성된 4컷 만화 이미지 URL (전체 슬라이드 공통)

class CardNewsRequest(BaseModel):
    """카드뉴스 생성 요청"""
    manual_id: int  # 매뉴얼 ID
    tone: str  # 말투
    num_slides: int = 4  # 생성할 카드 수 (기본 4장)

class CardNewsResponse(BaseModel):
    """카드뉴스 생성 응답"""
    title: str  # 전체 카드뉴스 제목
    slides: List[CardSlide]  # 카드 슬라이드 목록 (모두 같은 image_url 공유)
