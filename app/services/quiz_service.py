from app.core.openai_client import client
from app.core.db import engine
from sqlalchemy import text
from app.services.rag_service import retrieve_similar
from app.models.quiz_model import QuizResponse, QuizItem
import json

def generate_quiz(manual_id: int, tone: str, focus: str = "procedure"):
    """
    절차 중심 퀴즈 생성 — step/detail 구조 기반으로 퀴즈를 만듦.
    """
    # 1️. 검색 쿼리 설정
    query_text = (
        "교육 절차 단계별 세부 내용과 순서를 중심으로 요약"
        if focus == "procedure"
        else "교육 매뉴얼 전체 요약"
    )

    # 2️. RAG 검색 수행
    context_chunks = retrieve_similar(manual_id, query_text, limit=5)

    # 3️. fallback (manual 테이블 직접 조회)
    if not context_chunks:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT ai_raw_response FROM manual WHERE id = :id"),
                {"id": manual_id}
            ).fetchone()

        if row:
            try:
                manual_data = json.loads(row._mapping["ai_raw_response"])
                procedure = manual_data.get("procedure", [])
                context = json.dumps(procedure, ensure_ascii=False, indent=2)
            except Exception:
                context = "절차 데이터를 파싱할 수 없습니다."
        else:
            context = "교육 매뉴얼 내용이 없습니다."
    else:
        # 기존: 평문 문자열로 합침
        # context = "\n".join(context_chunks)

        # 수정: 구조 유지(JSON 형태 그대로)
        context = json.dumps(context_chunks, ensure_ascii=False, indent=2)

    # 프롬프트 구성
    prompt = f"""
    너는 소상공인 알바생 교육용 퀴즈를 만드는 전문가야.
    아래 교육 내용을 바탕으로 **절차의 순서와 상황 이해력**을 평가할 수 있는 3문제를 만들어.
    아래의 '절차(procedure)' 데이터를 참고하여 단계별 순서, 조건, 수치, 행동을 평가하는 문제를 만들어라.
    
    ✅ 조건:
    - 1번: OX 문제 (보기는 O, X)
    - 2~3번: 객관식 문제 (보기 2개, 'A)', 'B)' 형식)
    - 각 문제는 반드시 아래 필드 포함:
        • type: "OX" 또는 "MULTIPLE"
        • question: 교육 절차의 의미·이유·주의점을 반영한 구체적 질문
        • options: 보기 배열
        • answer: 정답
        • explanation: tone에 맞는 사장님 말투로, 이유나 실수 사례까지 포함해 작성
    - 모든 문제는 procedure 내부의 step·details를 기반으로 구성
    - 필요시 손님과 알바생의 대화 예시를 한 문항에만 포함해도 됨(단, 대화형 문제도 반드시 절차 단계의 맥락과 연결되어야 함)
        (예: "손님: 'HOT이요.' 알바: (여기에 들어갈 멘트는?)")
    - 절차 순서(예: 시럽 → 토핑 → 포장)를 묻는 문제를 반드시 포함할 것
    - 각 문항은 반드시 절차(procedure)의 순서나 행동 단계와 관련되어야 함.
    - 수치(°C, g, 초 등)나 도구(예: 그라인더, 스팀피처) 관련 내용이 있다면 퀴즈에 1문항 이상 포함할 것

    💬 tone 예시:
    - formal: "~해야 합니다.", "~하지 말아야 합니다."
    - friendly: "~해줘~", "~하자!"
    - dialect: "~하이소~", "~하지 마이소!"
    - expressive: "좋아요! 완벽해요! 👍"

    ⚠️ 주의:
    - 보기 간의 차이를 섬세하게 만들어서 너무 쉽게 맞히지 못하도록 구성
    - JSON 이외의 텍스트는 절대 포함하지 말 것
    - 보기, 정답, 해설 모두 한국어로 작성할 것

    ### tone
    {tone}

    ### 교육 내용
    {context}

    ### 출력 예시 (참고용)
    ※ 예시는 참고용일 뿐, 반드시 위의 매뉴얼 내용을 기반으로 새롭게 생성하세요.
    [
      {{
        "type": "OX",
        "question": "우유는 70°C 이상으로 스팀해야 한다.",
        "options": ["O", "X"],
        "answer": "X",
        "explanation": "65°C를 넘으면 우유 단백질이 파괴돼요! ☕️"
      }},
      {{
        "type": "MULTIPLE",
        "question": "시럽을 뿌린 후 다음에 해야 할 일은?",
        "options": ["A) 토핑 얹기", "B) 손님에게 전달하기"],
        "answer": "A",
        "explanation": "시럽 다음엔 토핑이 필수! 순서 틀리면 모양이 엉망이야~ 🎨"
      }},
      {{
        "type": "MULTIPLE",
        "question": "손님: '저 이거 아이스로 바꿔주세요!' 알바: (여기에 들어갈 멘트는?)",
        "options": ["A) '네, 따뜻한 걸로 바로 드릴게요!'", "B) '네~ 아이스로 변경 도와드릴게요! 😊'"],
        "answer": "B",
        "explanation": "손님 요청은 바로 반영해줘야지! '아이스로 변경 도와드릴게요~' 하면 완벽 👍"
      }}
    ]
    """

    # GPT 호출
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 JSON만 반환하는 한국어 퀴즈 생성기야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9
    )

    content = res.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "")
    try:
        data = json.loads(content)
        quizzes = [QuizItem(**q) for q in data]
        return QuizResponse(quizzes=quizzes)
    except Exception as e:
        raise ValueError(f"퀴즈 파싱 실패: {e}\n응답: {content}")