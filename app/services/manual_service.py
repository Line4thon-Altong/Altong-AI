from app.core.openai_client import client
from app.models.manual_model import ManualResponse
import json

def classify_tone(tone_text: str) -> str:
    """tone 문자열을 기반으로 말투 카테고리 추정"""
    if not tone_text:
        return "neutral"

    tone_text = tone_text.lower().strip()

    # 존댓말 / 격식체
    formal_keywords = [
        "십시오", "하세요", "하십니다", "입니다", "습니다", "주시기", "부탁드립니다",
        "해주세요", "되시길", "감사합니다", "바랍니다", "드리겠습니다", "예요", "세요"
    ]

    # 반말 / 구어체
    casual_keywords = [
        "해", "하자", "해야지", "하네", "하니", "라구", "자", "야지", "했지", "했잖아",
        "하거라", "봐라", "해야겠다", "할게", "할래", "하자꾸나", "하자고", "하라니까"
    ]

    # 사투리 / 지역어
    dialect_keywords = [
        "하이소", "데이", "카이", "마이", "이라", "믄", "하모", "하제", "하니껴", "혀",
        "하잉", "허이", "아입니까", "요래", "그라지", "맞나", "하이까", "오이", "카나"
    ]

    # 친근체 / 부드러운 대화체
    friendly_keywords = [
        "요~", "죠~", "아~", "ㅎㅎ", "ㅋㅋ", "^^", "말이야", "있잖아", "같아", "하거든",
        "할 수 있겠지?", "그치?", "좋지?", "느낌이야", "그럼~", "그렇게 해보자~"
    ]

    # 감정형 / 유쾌·에너지톤
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


def generate_manual(business_type, title, goal, procedure, precaution, tone):
    """사장님 입력을 기반으로 AI가 교육 매뉴얼을 구조화된 JSON 형식으로 생성"""
    
    tone_type = classify_tone(tone)

    # tone_type별 추가 설명 문구
    tone_instruction = {
    "formal": "전체 문장은 존댓말 어투(예: '~하세요', '~입니다')로 작성해. 예의 있고 점잖은 톤이야.",
    "casual": "전체 문장은 반말 어투(예: '~해', '~하자', '~해야지')로 작성해. 친근하고 구어체스럽게 해.",
    "dialect": "전체 문장은 사투리 느낌으로 써. 예: '~하이소', '~카이', '~데이' 같은 지역적 표현을 자연스럽게 섞어 써.",
    "friendly": "전체 문장은 다정하고 부드러운 어투로 써. 존댓말과 반말이 섞여도 괜찮고, 따뜻한 느낌을 주는 대화체야.",
    "expressive": "전체 문장은 활기차고 유쾌한 어투로 써. 긍정적이고 힘나는 문장으로 표현해.",
    "neutral": "기본 자연체로 써. 너무 딱딱하지 않고 자연스러운 구어체로 작성해."
    }[tone_type]

    prompt = f"""
    너는 소상공인 사장님이 직접 알바생에게 교육하는 듯한 말투로 매뉴얼을 작성하는 전문가야.
    아래 tone 정보를 분석해서, 실제 문체에 적극 반영해.
    절대 tone을 참고만 하지 말고, 실제 대사 표현에서도 tone의 스타일을 사용해.
    그리고 문장의 의미에 맞는 이모티콘을 자동으로 넣어줘.
    예를 들어:
    - '인사' 관련 문장에는 👋 😊 🙌
    - '결제'나 '돈' 관련 문장에는 💳 💰 🧾
    - '주의', '조심' 같은 단어에는 ⚠️
    - '경청', '듣기'에는 👂
    - '감사'에는 🙏
    - '밝게', '웃으며'에는 ☀️ 😄
    - 그 외에도 문맥에 어울리는 이모티콘을 자연스럽게 선택해.
    단, 너무 과하게 넣지 말고 전체 문장의 5~10%에만 적절히 추가해.

    ### tone 지시문
    - tone 입력값: "{tone}"
    - tone 분류: {tone_type}
    - tone 반영 규칙: {tone_instruction}

    ### 입력 정보
    업종: {business_type}
    교육 제목: {title}
    교육 목표: {goal}
    교육 절차: {procedure}
    주의할 점: {precaution}

    ### 출력 규칙
    1. 반드시 JSON 형식으로만 출력.
    2. 각 단계 설명(details)과 precaution에도 tone과 의미 기반 이모티콘을 적절히 반영.
    3. goal은 한 문장 요약형 문자열로, procedure와 precaution은 배열로 작성.
    4. Markdown, 불필요한 텍스트, 코드블록 금지.

    ### 출력 예시
    {{
      "title": "주문받고 결제하는 기본 교육",
      "goal": "손님이 기분 좋게 주문하고 결제까지 깔끔하게 끝내기 ☀️",
      "procedure": [
        {{
          "step": "1. 인사는 활짝!",
          "details": [
            "손님 오면 바로 인사하기 — ‘어서오세요!’",
            "밝은 표정이 가장 좋은 시작이에요. 👋"
          ]
        }},
        {{
          "step": "2. 주문 받을 땐 꼼꼼하게",
          "details": [
            "손님이 말 끝낼 때까지 기다리기.",
            "‘HOT이요? ICE요?’ 한 번 더 확인해요."
          ]
        }},
        {{
          "step": "3. 결제 안내 및 영수증 질문",
          "details": [
            "결제 도와드릴게요~ 💳",
            "‘영수증 필요하신가요?’ 자연스럽게 물어보기."
          ]
        }}
      ],
      "precaution": [
        "손님 말 끊지 않기",
        "결제 전 금액 다시 확인하기 ✅",
        "포장 여부 확인 잊지 않기"
      ]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "너는 한국어로 소상공인 알바 교육 매뉴얼을 작성하는 전문가야. 반드시 JSON으로만 응답해."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=1.0
    )

    content = response.choices[0].message.content.strip()

    try:
        # GPT가 ```json ``` 블록으로 감쌀 수 있으므로 제거
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)

        # goal이 리스트면 문자열로 합치기
        if isinstance(data.get("goal"), list):
            data["goal"] = ", ".join(data["goal"])

        # precaution이 문자열이면 리스트로 변환
        if isinstance(data.get("precaution"), str):
            data["precaution"] = [data["precaution"]]

        return ManualResponse(**data)

    except Exception as e:
        raise ValueError(f"AI 응답 파싱 실패: {e}\n응답 내용: {content}")
