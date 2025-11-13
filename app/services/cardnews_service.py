from app.core.openai_client import client
from app.services.rag_service import retrieve_similar
from app.services.image_service import generate_cardnews_image
from app.models.cardnews_model import CardNewsResponse, CardSlide
import json

def flatten_context_chunks(context_chunks):
    """
    RAG 결과를 안전하게 문자열로 변환
    """
    flattened = []
    for c in context_chunks:
        if isinstance(c, dict):
            # step + details 텍스트 합치기
            step = c.get("step", "")
            details = c.get("details", [])
            if isinstance(details, list):
                detail_text = " ".join([str(d) for d in details])
            else:
                detail_text = str(details)
            flattened.append(f"{step} {detail_text}".strip())
        elif isinstance(c, str):
            flattened.append(c)
        else:
            flattened.append(str(c))
    return "\n".join(flattened)

def generate_cardnews(manual_id: int, tone: str, num_slides: int = 4):
    """
    매뉴얼 기반 카드뉴스 생성 (4컷, 동일 인물, 동일 유니폼, 단색 배경)
    """

    # 1️⃣ 핵심 내용 검색 (RAG)
    context_chunks = retrieve_similar(manual_id, "핵심 절차와 주요 포인트", limit=8)
    context = flatten_context_chunks(context_chunks) # flatten 적용 

    # 2️⃣ GPT 카드뉴스 구성 생성
    prompt = f"""
너는 직장인/알바생을 위한 교육 카드뉴스를 만드는 전문가야.
아래 교육 매뉴얼을 읽고, 4개의 카드로 핵심 내용을 요약해줘.

### 교육 매뉴얼
{context}

### 구성
1. 1번 카드: 인사/시작
2. 2~3번 카드: 핵심 절차 및 팁
3. 4번 카드: 마무리/당부

### 출력 형식 (JSON)
{{
  "title": "전체 카드뉴스 제목",
  "slides": [
    {{
      "title": "1. 인사는 밝게!",
      "content": ["손님이 들어오면 먼저 웃으며 인사해요 👋"],
      "scene_description": "검은색 정장을 입은 한국인 직원이 손을 흔드는 장면, 크림색 단색 배경"
    }}
  ]
}}

### 장면 묘사 규칙
- 인물은 반드시 한국인(Korean worker)
- ONE person only / SAME uniform & appearance across all 4 panels
- Solid cream background (completely empty)
- Only facial expression and pose differ
- Simple props OK (calculator, POS, clipboard)
- Props use abstract shapes (short lines, dots, blank rectangles)
- No readable text, numbers, symbols, labels, reflections, or speech bubbles
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "매뉴얼을 읽고 업종을 파악한 뒤 JSON 생성. "
                    "scene_description은 한 명의 한국인 직원, 동일 유니폼과 외형, 단색 크림 배경, "
                    "표정과 포즈만 다르게. 소품은 추상 패턴만 허용, "
                    "글자·숫자·라벨·말풍선 금지."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )

    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(content)
        print("🎨 4컷 카드뉴스 이미지 생성 중...")

        # 3️⃣ 4컷 이미지용 프롬프트 생성
        four_panel_prompt = create_four_panel_prompt(data["slides"])
        single_image_url = generate_cardnews_image(four_panel_prompt)

        # 4️⃣ 슬라이드 구성
        slides = []
        for slide_data in data["slides"]:
            slide = CardSlide(**slide_data)
            slide.image_url = single_image_url
            slides.append(slide)

        return CardNewsResponse(title=data["title"], slides=slides)

    except Exception as e:
        raise ValueError(f"카드뉴스 파싱 실패: {e}\n응답: {content}")


def create_four_panel_prompt(slides: list) -> str:
    """4컷 카드뉴스(2x2)용 영어 프롬프트 생성"""

    scene_descriptions = []
    for i, slide in enumerate(slides, 1):
        desc = slide.get("scene_description", "직원이 일하는 장면")
        title = slide.get("title", f"Panel {i}")
        content = slide.get("content", [""])[0]
        scene_descriptions.append(
            f"Panel {i}: {title} — {content}. Scene: {desc}"
        )

    translation_prompt = f"""
Translate these 4 Korean scene descriptions into English.
Each must clearly describe what happens in each panel.

Scenes:
{chr(10).join(scene_descriptions)}

Each panel = one part of a 4-panel comic (2x2 grid):
- Panel 1 (TOP-LEFT)
- Panel 2 (TOP-RIGHT)
- Panel 3 (BOTTOM-LEFT)
- Panel 4 (BOTTOM-RIGHT)

Rules:
- Exactly 4 lines, one per panel
- All 4 panels must show ONE identical Korean employee (same face, same uniform)
- Each panel shows the specific action described
- Solid cream background, completely empty
- No text, numbers, or symbols in the drawing
"""

    translation_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Translate into concise English. Each panel = one frame of a 4-panel comic. "
                    "Keep all panels consistent with same character and background."
                ),
            },
            {"role": "user", "content": translation_prompt},
        ],
        temperature=0.3,
    )

    panel_prompts = translation_response.choices[0].message.content.strip()

    four_panel_prompt = f"""
Create ONE image containing a 4-panel comic in a 2x2 grid (EXACTLY 4 panels, NOT 9).
Each panel corresponds to the following scenes:

{panel_prompts}

IMPORTANT STRUCTURE:
- Top-left = Panel 1
- Top-right = Panel 2
- Bottom-left = Panel 3
- Bottom-right = Panel 4
- Each panel must show the correct scene based on its description above
- 4 distinct but connected scenes, all within one image
- Same Korean employee appears in all 4 panels

STYLE:
- Flat, clean Korean webtoon style
- Thick black outlines and clear panel borders
- Bold solid colors, minimal shading
- Identical character design in all 4 panels
- Only expression and pose differ

BACKGROUND:
- Solid cream/beige, completely empty
- No furniture or decorations

PROPS:
- Simple work props (calculator, POS, clipboard)
- Props drawn with abstract minimal shapes (short lines, dots, blank rectangles)

FORBIDDEN:
- No readable text, numbers, or letters anywhere
- No sparkle, hearts, reflections, or speech bubbles
"""
    return four_panel_prompt
