from app.core.openai_client import client
from app.services.s3_service import upload_image_to_s3
import os

def generate_cardnews_image(prompt: str) -> str:
    """DALL-E 3로 4컷 카드뉴스 이미지 생성 (2x2 grid, identical character, 4 distinct scenes)"""

    enhanced_prompt = f"""
Create ONE image that is a 4-panel comic arranged in a 2x2 grid (EXACTLY 4 panels, NOT 9).
Each panel must represent the distinct scenes described below, corresponding to Panel 1–4.
Ensure all 4 panels appear clearly separated with thick black borders.

{prompt}

STRUCTURE:
- Top-left = Panel 1
- Top-right = Panel 2
- Bottom-left = Panel 3
- Bottom-right = Panel 4
- Each panel shows the described action
- Same Korean employee (same face, hairstyle, uniform) in all 4 panels
- Only expressions and gestures differ
- Solid cream/beige background for all

STYLE:
- Flat, clean cartoon (Korean webtoon style)
- Thick black outlines and consistent borders
- Bold solid colors, minimal shading
- Character proportions identical in all panels

FORBIDDEN:
- No readable text, digits, labels, or numbers inside panels
- No speech bubbles, reflections, or decorative marks
- No sparkle or symbols

Ensure the final output is ONE image showing four separate panels (2 on top, 2 on bottom).
"""

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        print(f"✅ 이미지 생성 완료: {image_url}")

        use_s3 = os.getenv("USE_S3", "false").lower() == "true"
        if use_s3:
            print("☁️  S3 업로드 중...")
            return upload_image_to_s3(image_url, folder="cardnews")
        else:
            print("⚠️  S3 비활성화 - 임시 URL 사용")
            return image_url

    except Exception as e:
        print(f"❌ 이미지 생성 실패: {e}")
        return ""
