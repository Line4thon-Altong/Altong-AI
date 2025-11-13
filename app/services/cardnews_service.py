from app.core.openai_client import client
from app.services.rag_service import retrieve_similar
from app.services.image_service import generate_cardnews_image
from app.models.cardnews_model import CardNewsResponse, CardSlide
import json
import logging

# DB 연결을 위한 import
from app.core.db import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


def classify_tone(tone_text: str) -> str:
    """tone 문자열을 기반으로 말투 카테고리 추정 (manual_service와 동일)"""
    if not tone_text:
        return "neutral"

    tone_text = tone_text.lower().strip()

    formal_keywords = [
        "십시오", "하세요", "하십니다", "입니다", "습니다", "주시기", "부탁드립니다",
        "해주세요", "되시길", "감사합니다", "바랍니다", "드리겠습니다", "예요", "세요"
    ]

    casual_keywords = [
        "해", "하자", "해야지", "하네", "하니", "라구", "자", "야지", "했지", "했잖아",
        "하거라", "봐라", "해야겠다", "할게", "할래", "하자꾸나", "하자고", "하라니까"
    ]

    dialect_keywords = [
        "하이소", "데이", "카이", "마이", "이라", "믄", "하모", "하제", "하니껴", "혀",
        "하잉", "허이", "아입니까", "요래", "그라지", "맞나", "하이까", "오이", "카나"
    ]

    friendly_keywords = [
        "요~", "죠~", "아~", "ㅎㅎ", "ㅋㅋ", "^^", "말이야", "있잖아", "같아", "하거든",
        "할 수 있겠지?", "그치?", "좋지?", "느낌이야", "그럼~", "그렇게 해보자~"
    ]

    expressive_keywords = [
        "화이팅", "가보자", "좋구만", "좋다~", "멋지다", "좋아~", "열심히", "힘내자",
        "아자", "가자", "오늘도", "즐겁게", "밝게", "기분좋게"
    ]

    if any(word in tone_text for word in formal_keywords):
        return "formal"
    elif any(word in tone_text for word in dialect_keywords):
        return "dialect"
    elif any(word in tone_text for word in casual_keywords):
        return "casual"
    elif any(word in tone_text for word in friendly_keywords):
        return "friendly"
    elif any(word in tone_text for word in expressive_keywords):
        return "expressive"
    else:
        return "neutral"


def flatten_context_chunks(context_chunks):
    """RAG 결과를 문자열로 변환"""
    flattened = []
    for c in context_chunks:
        if isinstance(c, dict):
            step = c.get("step", "")
            details = c.get("details", [])
            if isinstance(details, list):
                detail_text = " ".join(str(d) for d in details)
            else:
                detail_text = str(details)
            flattened.append(f"{step} {detail_text}".strip())
        elif isinstance(c, str):
            flattened.append(c)
        else:
            flattened.append(str(c))
    return "\n".join(flattened)


def get_manual_tone(manual_id: int) -> str:
    """DB에서 매뉴얼의 tone 가져오기"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT tone FROM manual WHERE id = :manual_id"),
                {"manual_id": manual_id}
            ).fetchone()
            
            if result:
                return result[0] or "친근하지만 꼼꼼한 사장님 말투로"
            return "친근하지만 꼼꼼한 사장님 말투로"
    except Exception as e:
        logger.error(f"❌ [CARDNEWS] tone 조회 실패: {e}")
        return "친근하지만 꼼꼼한 사장님 말투로"


def generate_cardnews(manual_id: int):
    """
    매뉴얼 기반 카드뉴스 생성 (4컷 고정)
    - DB에서 tone 자동 조회
    - tone에 맞는 말투로 텍스트 생성
    - 이모지 제거
    - content는 한 줄로만
    - 4컷 이미지 1장
    """

    # DB에서 tone 가져오기
    tone = get_manual_tone(manual_id)
    logger.info(f"🎨 [CARDNEWS] 카드뉴스 생성 시작 | manual_id={manual_id}, tone={tone}")

    # tone 분류
    tone_type = classify_tone(tone)

    # tone별 말투 지시문
    tone_instruction = {
        "formal": "존댓말 어투로 작성 (예: ~하세요, ~입니다)",
        "casual": "반말 어투로 작성 (예: ~해, ~하자, ~해야지)",
        "dialect": "사투리 느낌으로 작성 (예: ~하이소, ~카이, ~데이)",
        "friendly": "다정하고 부드러운 어투로 작성",
        "expressive": "활기차고 유쾌한 어투로 작성",
        "neutral": "자연스러운 구어체로 작성"
    }[tone_type]

    # 1️⃣ RAG로 매뉴얼 핵심 내용 가져오기
    query = "이 매뉴얼의 핵심 절차와 중요한 주의사항을 교육용으로 요약"
    context_chunks = retrieve_similar(manual_id, query, limit=8)
    context = flatten_context_chunks(context_chunks)

    logger.info(f"🧠 [CARDNEWS] RAG 컨텍스트 준비 완료 | tone_type={tone_type}")

    # 2️⃣ GPT에게 카드뉴스 텍스트 생성 요청 (4컷 고정)
    prompt = f"""
너는 직장인/알바생을 위한 교육 카드뉴스를 기획하는 전문가야.
아래 교육 매뉴얼 요약을 읽고, **정확히 4개의 카드**로 핵심 내용을 나눠서 설명해.

### 교육 매뉴얼 요약
{context}

### tone 지시문
- tone 입력값: "{tone}"
- tone 분류: {tone_type}
- 말투 규칙: {tone_instruction}
- **모든 문장에 이 말투를 반영해야 함**

### 카드 구성 규칙
1. **정확히 4개의 카드만 생성**
2. 각 카드는:
   - title: 핵심만 담은 짧은 제목 (5~10자, 이모지 없음)
   - content: **딱 한 줄**의 설명 문장 (이모지 없음, tone 반영 필수)
   - scene_description: 이미지에 그릴 장면 묘사 (한국어, 글자/말풍선 묘사 금지)

3. scene_description 작성 규칙:
   - 한 명의 한국인 직원만 등장
   - 행동, 표정, 포즈만 묘사
   - 업종에 맞는 유니폼과 간단한 소품
   - 크림색 단색 배경
   - **절대 금지**: 텍스트, 글자, 숫자, 간판, UI, 말풍선 언급

### 출력 형식 (JSON ONLY)
코드블록 없이 순수 JSON만 출력해.

{{
  "title": "전체 카드뉴스 제목",
  "slides": [
    {{
      "title": "짧은 제목",
      "content": "한 줄 설명 문장",
      "scene_description": "직원이 밝게 인사하는 장면, 카페 유니폼, 크림색 배경"
    }},
    {{
      "title": "짧은 제목",
      "content": "한 줄 설명 문장",
      "scene_description": "직원이 주문을 받는 장면, 메모장 들고 경청하는 표정"
    }},
    {{
      "title": "짧은 제목",
      "content": "한 줄 설명 문장",
      "scene_description": "직원이 결제를 도와주는 장면, POS기 앞에서 안내하는 모습"
    }},
    {{
      "title": "짧은 제목",
      "content": "한 줄 설명 문장",
      "scene_description": "직원이 미소 지으며 배웅하는 장면, 손 흔드는 제스처"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "너는 한국어로 교육용 카드뉴스를 설계하는 전문가야. 항상 JSON 형식으로만 응답해."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(content)
        logger.info("🧾 [CARDNEWS] 카드 텍스트 생성 완료")

        # 슬라이드 4개 고정
        slides_data = (data.get("slides") or [])[:4]

        # 4개 미만이면 마지막 슬라이드 복제
        if slides_data and len(slides_data) < 4:
            last = slides_data[-1]
            while len(slides_data) < 4:
                slides_data.append(last)

        logger.info(f"🧩 [CARDNEWS] 슬라이드 정리 완료 | slide_count={len(slides_data)}")

        # 3️⃣ 4컷 이미지 생성
        four_panel_prompt = create_four_panel_prompt(slides_data)
        logger.info("🖼️ [CARDNEWS] 이미지 생성 시작")
        image_url = generate_cardnews_image(four_panel_prompt)
        logger.info(f"🖼️ [CARDNEWS] 이미지 생성 완료 | url={image_url}")

        # 4️⃣ 응답 구성
        slides = []
        for idx, slide_data in enumerate(slides_data, start=1):
            # content가 리스트면 첫 번째 항목만, 문자열이면 그대로
            content_text = slide_data.get("content", "")
            if isinstance(content_text, list):
                content_text = content_text[0] if content_text else ""

            slide = CardSlide(
                slide_id=idx,
                title=slide_data.get("title", f"카드 {idx}"),
                content=content_text
            )
            slides.append(slide)

        return CardNewsResponse(
            title=data.get("title", "교육 카드뉴스"),
            slides=slides,
            image_url=image_url
        )

    except Exception as e:
        logger.error(f"❌ [CARDNEWS] 카드뉴스 파싱 실패: {e}")
        raise ValueError(f"카드뉴스 파싱 실패: {e}\n응답: {content}")


def create_four_panel_prompt(slides: list) -> str:
    """4컷 카드뉴스(2x2)용 영어 프롬프트 생성"""

    # 4개로 고정
    slides = (slides or [])[:4]

    # 4개 미만이면 마지막 슬라이드 복제
    if slides and len(slides) < 4:
        last = slides[-1]
        while len(slides) < 4:
            slides.append(last)

    scene_descriptions = []
    for i, slide in enumerate(slides, 1):
        desc = slide.get("scene_description", "직원이 일하는 장면")
        title = slide.get("title", f"Panel {i}")
        content = slide.get("content", "")
        if isinstance(content, list):
            content = content[0] if content else ""
        scene_descriptions.append(
            f"Panel {i}: {title} — {content}. Scene: {desc}"
        )

    # 한국어 → 영어 번역
    translation_prompt = f"""
Translate these Korean scene descriptions into concise English.
Each line must clearly describe what happens in one panel of a 4-panel comic.

Scenes:
{chr(10).join(scene_descriptions)}

Rules for each panel:
- Describe the action, pose and emotion of a single Korean employee.
- Mention simple props and workplace context if needed (cafe, restaurant, convenience store, etc.).
- Background must be a plain cream-colored solid background.
- Do NOT mention any text, letters, numbers, logos, signs, UI, or speech bubbles.
- Focus only on people, actions, props, and colors.
- Output exactly 4 lines, one for each of the 4 panels.
"""

    translation_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Translate Korean descriptions into simple English prompts for an illustration model. Never mention text or letters inside the image."
            },
            {"role": "user", "content": translation_prompt}
        ],
        temperature=0.3
    )

    panel_prompts = translation_response.choices[0].message.content.strip()

    # 최종 DALL-E 프롬프트
    four_panel_prompt = f"""
Create ONE image containing a 4-panel comic in a 2x2 grid (EXACTLY 4 panels).

Each panel corresponds to the following scene descriptions:

{panel_prompts}

IMPORTANT STRUCTURE:
- Top-left = Panel 1
- Top-right = Panel 2
- Bottom-left = Panel 3
- Bottom-right = Panel 4
- Each panel must show the correct scene based on its description.
- All 4 panels share ONE identical Korean employee (same face, hairstyle, uniform).
- Only facial expressions and poses differ.

STYLE:
- Flat, clean Korean webtoon style.
- Thick black outlines and clearly separated panel borders.
- Bold solid colors, minimal shading.
- Character proportions identical in all panels.

BACKGROUND:
- Plain solid cream/beige background in every panel.
- No furniture or decorations, very minimal environment.

PROPS:
- Simple work props only (calculator, POS terminal, tray, clipboard, coffee cup, etc.).
- Props drawn with simple shapes (lines, dots, rectangles).

STRICTLY FORBIDDEN:
- No readable text, numbers, letters, signs, logos or UI elements anywhere.
- No speech bubbles, sound effects, or decorative symbols (no sparkles, hearts, emojis, etc.).
"""
    return four_panel_prompt