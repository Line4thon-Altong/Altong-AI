from app.core.openai_client import client
from app.services.rag_service import retrieve_similar
from app.models.quiz_model import QuizResponse, QuizItem
import json

def generate_quiz(manual_id: int, tone: str):
    context_chunks = retrieve_similar(manual_id, "핵심 절차 요약", limit=5)
    context = "\n".join(context_chunks)

    prompt = f"""
    너는 소상공인 알바생 교육용 퀴즈를 만드는 전문가야.
    아래 교육 내용을 바탕으로 3문제를 만들어.
    
    - 1번: OX 문제 (보기는 O, X)
    - 2~3번: 객관식 (보기 2개, A) B) 형식)
    - 각 문제는 질문(question), 보기(options), 정답(answer), 해설(explanation)을 모두 포함해야 해.
    - **해설은 반드시 tone에 맞는 사장님의 말투로 작성해.**
    - tone에 따라 문장 스타일과 어미를 바꿔.
    - 예시:
        * formal: "정확히 해야 합니다.", "주의해야 합니다."
        * friendly: "꼭 확인해줘~", "이 부분은 잊지 말자!"
        * dialect: "이건 꼭 챙기이소~"
        * expressive: "좋아요! 완벽해요! 👍"
    - 반드시 JSON 배열 형식으로만 출력.

    ### tone
    {tone}

    ### 교육 내용
    {context}

    ### 출력 예시
    [
      {{
        "type": "OX",
        "question": "손님이 입장하면 밝게 인사해야 한다.",
        "options": ["O", "X"],
        "answer": "O",
        "explanation": "밝은 인사는 첫인상을 좋게 만들어~ ☀️"
      }},
      {{
        "type": "MULTIPLE",
        "question": "결제 시 꼭 확인해야 할 것은?",
        "options": ["A) 금액", "B) 메뉴 수량"],
        "answer": "A",
        "explanation": "결제 전에 금액 한 번 더 확인하자~ 💳"
      }}
    ]
    """

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