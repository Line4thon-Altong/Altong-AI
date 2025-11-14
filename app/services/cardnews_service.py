from app.core.openai_client import client
from app.services.image_service import generate_cardnews_image
from app.models.cardnews_model import CardNewsResponse, CardSlide
import json 
import logging
from app.core.db import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

# 매뉴얼 DB를 참고하여 GPT를 통해 핵심 4가지 매뉴얼 내용을 추출하고
# 영어로 작성한 프롬프팅을 통해 DALL-E-3 AI에게 전달하여 카드뉴스 생성 후 S3에 저장


# 매뉴얼 ID를 받아 카드뉴스를 만들어 주는 함수
def generate_cardnews(manual_id: int):
    """
    매뉴얼 기반 카드뉴스 생성
    - DB에서 전체 매뉴얼 조회
    - 매뉴얼에서 중요한 4개 포인트 추출
    - 이미지 생성
    """

    # DB에서 전체 매뉴얼 데이터 가져오기
    try:
        with engine.connect() as conn:
            # manual 테이블의 ai_raw_response 필드를 가져옴(JSON 원문)
            result = conn.execute(
                text("""
                    SELECT ai_raw_response
                    FROM manual 
                    WHERE id = :manual_id
                """),
                {"manual_id": manual_id}
            ).fetchone() # 하나의 결과만 가져오기
        
        if not result:
            raise ValueError(f"매뉴얼 ID {manual_id}를 찾을 수 없습니다.")
        
        manual_data = json.loads(result[0])
        
    except Exception as e:
        logger.error(f"[CARDNEWS] DB 조회 실패: {e}")
        raise ValueError(f"매뉴얼 조회 실패: {e}")

    logger.info(f"[CARDNEWS] 카드뉴스 생성 시작 | manual_id={manual_id}")

    # 매뉴얼 구조(절차, 목표, 주의사항)
    procedure = manual_data.get("procedure", [])
    goal = manual_data.get("goal", "")
    precaution = manual_data.get("precaution", [])
    
    logger.info(f"[CARDNEWS] 매뉴얼 분석 | 절차 수={len(procedure)}")

    # 매뉴얼 전체에서 핵심 4개 포인트 추출
    # 프롬프팅 영어로 하여 한글 -> 영어 번역 과정을 없앰
    prompt = f"""
You are an expert in creating educational card news for Korean workers.

Analyze the manual below and extract the 4 MOST IMPORTANT points.
Focus on what matters most for education.

### Full Manual Content
**Goal**: {goal}

**Procedures**:
{json.dumps(procedure, ensure_ascii=False, indent=2)}

**Precautions**:
{json.dumps(precaution, ensure_ascii=False, indent=2)}

### Output Format (JSON ONLY)
CRITICAL: You MUST provide EXACTLY 4 key points.

{{
  "title": "Korean title for the card news (5-15 characters)",
  "contents": [
    "First important point in Korean (one clear sentence)",
    "Second important point in Korean (one clear sentence)",
    "Third important point in Korean (one clear sentence)",
    "Fourth important point in Korean (one clear sentence)"
  ]
}}

RULES:
- Each content should be a clear, actionable sentence
- Use natural, friendly Korean
- Focus on practical actions or important reminders
- EXACTLY 4 contents, no more, no less

REMINDER: The contents array MUST contain EXACTLY 4 items.

Generate the JSON now.
"""

    # GPT 모델 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert creating educational card news. You MUST extract EXACTLY 4 key points. Always respond in JSON format only."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(content)
        logger.info("[CARDNEWS] 핵심 포인트 추출 완료")

        # title 추출
        title = data.get("title", "교육 카드뉴스")
        
        # contents 추출
        slides = data.get("contents", [])
        
        # 4개가 아니면 경고 로그
        if len(slides) != 4:
            logger.warning(f"[CARDNEWS] GPT가 {len(slides)}개 포인트 반환 (4개 요청함)")
        
        # 4개 초과 시 앞의 4개만 사용
        if len(slides) > 4:
            slides = slides[:4]
        elif len(slides) < 4:
            while len(slides) < 4: # 4개 이하일 시 부족한 만큼 마지막 내용 복제
                if slides:
                    slides.append(slides[-1])
                else:
                    slides.append("중요한 교육 내용")
        
        # 최종 검증
        assert len(slides) == 4, f"slides는 4개여야 하는데 {len(slides)}개"
        
        logger.info(f"[CARDNEWS] 핵심 포인트 정리 완료 | slides={len(slides)}")

        # contents 기반 이미지 생성
        four_panel_prompt = create_four_panel_prompt_from_contents(slides) # 4컷용 프롬프트 구성을 위한 함수
        logger.info("CARDNEWS] 이미지 생성 시작")
        image_url = generate_cardnews_image(four_panel_prompt)
        logger.info(f"CARDNEWS] 이미지 생성 완료 | url={image_url}")

        # 응답 구성
        return CardNewsResponse(
            title=title,
            slides=slides,
            image_url=image_url
        )

    except Exception as e:
        logger.error(f"[CARDNEWS] 카드뉴스 생성 실패: {e}")
        raise ValueError(f"카드뉴스 생성 실패: {e}\n응답: {content}")


# 4컷 이미지 프롬프트 생성 함수
def create_four_panel_prompt_from_contents(contents: list) -> str:
    """4개 content를 바탕으로 4컷 이미지 프롬프트 생성 """
    
    four_panel_prompt = f"""
**A single 2x2 grid, 4-panel Korean webtoon.**

The image MUST be a single square, clearly divided by thick black borders into four equal quadrants.

- Panel 1 (top-left): A Korean convenience store employee performing the action: "{contents[0]}"
- Panel 2 (top-right): The same employee performing the action: "{contents[1]}"
- Panel 3 (bottom-left): The same employee performing the action: "{contents[2]}"
- Panel 4 (bottom-right): The same employee performing the action: "{contents[3]}"

Style: Clean, simple Korean webtoon art.
CRITICAL: Show the EXACT same character (identical face, hair, uniform) in all 4 panels.
CRITICAL: NO text, NO numbers, NO speech bubbles. **This includes any small, illegible text or numbers in the background or on objects.**
"""
    return four_panel_prompt