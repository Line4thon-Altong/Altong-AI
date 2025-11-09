from fastapi import FastAPI
from app.routers import manual_router, quiz_router, rag_router, cardnews_router

# FastAPI 앱 생성
app = FastAPI(
    title="Altong AI API",
    version="0.3.0",
    description="RAG 기반 매뉴얼 및 퀴즈/카드뉴스 생성 API"
)

# 라우터 등록
app.include_router(manual_router.router)
app.include_router(quiz_router.router)
app.include_router(rag_router.router)
app.include_router(cardnews_router.router)

@app.get("/")
def root():
    return {"message": "Altong AI FastAPI server is running 🚀"}