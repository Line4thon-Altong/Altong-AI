# 베이스 이미지 설정
FROM python:3.12-slim

# 작업 디렉토리
WORKDIR /app

# 의존성 파일 복사 & 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 전체 복사
COPY . .

# 컨테이너가 열어야 할 포트
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]