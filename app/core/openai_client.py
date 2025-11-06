from openai import OpenAI
from dotenv import load_dotenv
import os

# .env 파일에서 환경변수 로드
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")

# 공통으로 사용할 OpenAI 클라이언트
client = OpenAI(api_key=api_key)