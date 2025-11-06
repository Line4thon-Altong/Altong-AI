from fastapi import FastAPI
from app.routers import manual_router

# FastAPI 앱 생성
app = FastAPI(
    title="Altong AI API",
    version="0.1.0",
    description="Altong AI 서비스의 메뉴얼 생성용 FastAPI 서버"
)

# 라우터 등록
app.include_router(manual_router.router)

@app.get("/")
def root():
    return {"message": "Altong AI FastAPI server is running 🚀"}