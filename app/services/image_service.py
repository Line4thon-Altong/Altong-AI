from app.core.openai_client import client
from app.services.s3_service import upload_image_to_s3
import os
import logging

logger = logging.getLogger(__name__)


def generate_cardnews_image(prompt: str) -> str:
    """DALL·E 3로 4컷 카드뉴스 이미지 생성 (2x2 grid, identical character, 4 distinct scenes)"""

    enhanced_prompt = f"""
Create ONE image that is a 4-panel comic arranged in a 2x2 grid (EXACTLY 4 panels, NOT 6, NOT 3x2).
Each panel must represent the distinct scenes described below, corresponding to Panel 1–4.
Ensure all 4 panels appear clearly separated with thick black borders.

{prompt}

STRUCTURE:
- Top-left = Panel 1
- Top-right = Panel 2
- Bottom-left = Panel 3
- Bottom-right = Panel 4
- Each panel shows the described action.
- Same Korean employee (same face, hairstyle, uniform) in all 4 panels.
- Only expressions and gestures differ.
- Plain solid cream/beige background for all panels.

STYLE:
- Flat, clean Korean webtoon style.
- Thick black outlines and consistent, clear panel borders.
- Bold solid colors, minimal shading.
- Character proportions identical in all panels.

STRICTLY FORBIDDEN (VERY IMPORTANT):
- No readable text, digits, letters, logos, or signs inside any panel.
- No UI elements, captions, or labels.
- No speech bubbles, sound effects, or decorative marks.
- No sparkles, emojis, or symbols floating in the scene.

The final output must be ONE high-resolution image showing exactly four separate panels (2 on top, 2 on bottom).
"""

    try:
        logger.info("🖼️ [CARDNEWS] DALL-E 카드뉴스 이미지 생성 요청 시작")

        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1792x1024",   # 가로형 4컷 / 2x2에 적당한 고해상도
            quality="hd",       # 고해상도 옵션
            n=1,
        )

        image_url = response.data[0].url
        logger.info(f"✅ [CARDNEWS] 이미지 생성 완료 | url={image_url}")

        use_s3 = os.getenv("USE_S3", "false").lower() == "true"
        if use_s3:
            logger.info("☁️ [CARDNEWS] S3 업로드 시작")
            return upload_image_to_s3(image_url, folder="cardnews")
        else:
            logger.info("⚠️ [CARDNEWS] S3 비활성화 - DALL-E URL 그대로 사용")
            return image_url

    except Exception as e:
        logger.error(f"❌ [CARDNEWS] 이미지 생성 실패: {e}")
        return ""
