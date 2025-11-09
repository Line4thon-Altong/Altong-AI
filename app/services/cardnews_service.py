from app.core.openai_client import client
from app.services.rag_service import retrieve_similar
from app.services.image_service import generate_cardnews_image
from app.models.cardnews_model import CardNewsResponse, CardSlide
import json

def generate_cardnews(manual_id: int, tone: str, num_slides: int = 4):
    """
    매뉴얼 기반 카드뉴스 생성 (일관된 스타일 버전)
    
    1. RAG로 핵심 내용 검색
    2. GPT로 카드뉴스 구조 생성
    3. 일관된 스타일로 이미지 생성 (같은 캐릭터, 같은 배경)
    """
    
    # 1. RAG로 핵심 내용 가져오기
    context_chunks = retrieve_similar(manual_id, "핵심 절차와 주요 포인트", limit=8)
    context = "\n".join(context_chunks)
    
    # 2. GPT로 카드뉴스 텍스트 구조 생성
    prompt = f"""
    너는 카드뉴스 디자이너야. 아래 교육 매뉴얼을 바탕으로 {num_slides}장의 카드뉴스를 만들어줘.
    
    ### 중요: 일관된 캐릭터 설정 (모든 카드에서 완전히 동일해야 함!)
    **절대 변하지 않는 캐릭터 고정 요소:**
    - 헤어스타일: 갈색(#8B6F47) 웨이브 포니테일, 앞머리는 살짝 옆으로
    - 얼굴형: 둥근 얼굴, 작고 귀여운 턱선
    - 눈: 큰 갈색 눈, 동그란 하이라이트 2개
    - 피부톤: 밝은 베이지(#FFE4C4)
    - 복장: 주황색(#FF8C42) 폴로셔츠 + 주황색 모자(앞에 작은 아이콘)
    - 얼굴 비율: 눈 크게, 코는 작은 점, 입은 작게
    - 체형: 치비(chibi) 스타일, 머리:몸 비율 1:1.5
    
    **스타일:**
    - 웹툰/캐릭터 일러스트, 단순한 라인 드로잉
    - 플랫 컬러 (그라데이션 NO, 그림자 최소)
    
    **절대 규칙: 위 특징이 모든 이미지에서 100% 동일해야 함!
    오직 포즈와 동작만 바뀌고, 캐릭터 외관은 절대 변경 금지!**
    
    ### 요구사항
    1. 각 카드는 제목(title)과 내용(content), 이미지 프롬프트(image_prompt)로 구성
    2. content는 3-5개의 짧은 문장 배열로 작성
    3. tone에 맞는 말투 사용: {tone}
    4. 이모티콘 적절히 사용
    5. image_prompt는 영어로 작성하되, **반드시 동일한 캐릭터 설명 포함**
       
       기본 템플릿 (캐릭터 일관성 극대화):
       "CONSISTENT CHARACTER: Chibi style female cafe worker, EXACT SAME FACE EVERY TIME - round face with large brown eyes (2 white highlights), small dot nose, small mouth, brown wavy ponytail (#8B6F47), side-swept bangs, light beige skin (#FFE4C4), orange polo shirt (#FF8C42), orange cap with small icon, cute mascot design. [동작 설명]. Simple line art, flat colors, NO gradients, minimal shadows, 2D vector illustration, white background, NO text. CHARACTER MUST BE IDENTICAL IN ALL IMAGES - only pose changes!"
       
       예시:
       - 카드1: "CONSISTENT CHARACTER: Chibi style female cafe worker... cheerfully waving with raised hand..."
       - 카드2: "CONSISTENT CHARACTER: Chibi style female cafe worker... listening carefully, holding notepad..."
       - 카드3: "CONSISTENT CHARACTER: Chibi style female cafe worker... at cashier, pointing gesture..."
       
       중요: 모든 프롬프트 시작은 "CONSISTENT CHARACTER: Chibi style female cafe worker"로 통일!
       
       **주의: 모든 프롬프트에 동일한 캐릭터 묘사를 포함하되, 동작만 바꿔줘!**
       **NO TEXT in image - 이미지에 한글이나 텍스트 넣지 마!**
    
    ### 카드 구성 가이드
    - 1번 카드: 표지 (인사하는 장면)
    - 2~{num_slides-1}번 카드: 핵심 내용 (주문받기, 결제 등 각 절차별 동작)
    - {num_slides}번 카드: 마무리 (미소 짓거나 손가락 하트 등)
    
    ### 교육 내용
    {context}
    
    ### 출력 형식 (JSON)
    {{
      "title": "전체 카드뉴스 제목",
      "slides": [
        {{
          "title": "1. 인사는 활짝!",
          "content": [
            "손님 오면 바로 인사하기 👋",
            "밝은 표정이 첫인상을 좌우해요"
          ],
          "image_prompt": "CONSISTENT CHARACTER: Chibi style female cafe worker, cheerfully waving with raised hand and big smile"
        }},
        {{
          "title": "2. 주문받을 땐 꼼꼼하게",
          "content": [
            "손님 말 끝까지 듣기 👂",
            "HOT? ICE? 한 번 더 확인!"
          ],
          "image_prompt": "CONSISTENT CHARACTER: Chibi style female cafe worker, listening carefully and holding notepad with pen"
        }},
        {{
          "title": "3. 결제는 신중하게",
          "content": [
            "금액 다시 확인하기 💳"
          ],
          "image_prompt": "CONSISTENT CHARACTER: Chibi style female cafe worker, at cashier counter helping with payment"
        }},
        {{
          "title": "4. 마무리는 감사 인사로",
          "content": [
            "감사합니다! 또 오세요 😊"
          ],
          "image_prompt": "CONSISTENT CHARACTER: Chibi style female cafe worker, waving goodbye with happy smile"
        }}
      ]
    }}
    
    중요: 4개 슬라이드의 image_prompt는 모두 "CONSISTENT CHARACTER: Chibi style female cafe worker"로 시작!
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "너는 귀여운 캐릭터 일러스트 스타일의 카드뉴스를 만드는 전문가야. 반드시 JSON 형식으로만 응답하고, 모든 카드에서 같은 캐릭터가 등장하도록 image_prompt를 작성해. 중요: 사진 같은 리얼리즘이 아닌 심플한 라인 드로잉, 웹툰/동화책 같은 2D 일러스트 스타일로!"
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7  # 일관성을 위해 낮춤
    )
    
    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(content)
        
        # 4컷 만화 형식으로 한 번에 이미지 생성
        print(f"🎨 4컷 카드뉴스 이미지 생성 중... (1장에 모두 포함)")
        
        # 4컷 전체 프롬프트 생성
        four_panel_prompt = create_four_panel_prompt(data["slides"])
        single_image_url = generate_cardnews_image(four_panel_prompt)
        
        # 모든 슬라이드에 같은 이미지 URL 할당
        slides = []
        for slide_data in data["slides"]:
            slide = CardSlide(**slide_data)
            slide.image_url = single_image_url  # 전체가 포함된 이미지
            slides.append(slide)
        
        return CardNewsResponse(
            title=data["title"],
            slides=slides
        )
        
    except Exception as e:
        raise ValueError(f"카드뉴스 파싱 실패: {e}\n응답: {content}")


def create_four_panel_prompt(slides: list) -> str:
    """
    4컷 만화 형식 프롬프트 생성
    
    Args:
        slides: 슬라이드 리스트 (각 슬라이드는 dict)
    
    Returns:
        4컷 만화용 통합 프롬프트
    """
    # 각 컷의 설명 추출
    panel_descriptions = []
    for i, slide in enumerate(slides, 1):
        title = slide.get('title', f'{i}번째 장면')
        # image_prompt에서 동작 부분만 추출
        prompt = slide.get('image_prompt', '')
        panel_descriptions.append(f"Panel {i} ({title}): {prompt}")
    
    # 4컷 만화 통합 프롬프트
    four_panel_prompt = f"""
    4-panel comic strip layout (2x2 grid) featuring the SAME CHARACTER in all panels:
    
    Character (consistent in ALL panels):
    - Chibi style female cafe worker
    - Round face, large brown eyes with 2 white highlights, small dot nose, small smile
    - Brown wavy ponytail (#8B6F47), side-swept bangs
    - Light beige skin (#FFE4C4)
    - Orange polo shirt (#FF8C42) and orange cap
    - Head:body ratio 1:1.5
    
    Layout: 2x2 grid with clear borders between panels
    
    {panel_descriptions[0] if len(panel_descriptions) > 0 else 'Panel 1: Character waving'}
    
    {panel_descriptions[1] if len(panel_descriptions) > 1 else 'Panel 2: Character working'}
    
    {panel_descriptions[2] if len(panel_descriptions) > 2 else 'Panel 3: Character smiling'}
    
    {panel_descriptions[3] if len(panel_descriptions) > 3 else 'Panel 4: Character happy'}
    
    Style: Simple line art, flat colors, minimal shadows, 2D vector illustration
    Background: White or light beige
    Important: SAME CHARACTER DESIGN in all 4 panels - only poses change!
    NO text, NO speech bubbles in the image
    Clear panel divisions with thin borders
    """
    
    return four_panel_prompt

