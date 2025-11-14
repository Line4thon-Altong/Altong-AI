from app.core.openai_client import client
from app.services.s3_service import upload_image_to_s3
import os
import logging

logger = logging.getLogger(__name__)

# 카드뉴스용 이미지 만드는 함수
def generate_cardnews_image(prompt: str) -> str:
    """DALL·E 3로 4컷 카드뉴스 이미지 생성"""

    # enhanced_prompt를 사용하지 않고, create_four_panel_prompt_from_contents에서 
    # 생성한 프롬프트를 직접 사용
    # 지시한 내용의 중복을 발생하지 않기위해. AI가 헷갈려할 위험을 줄임

    try:
        logger.info("[CARDNEWS] DALL-E 카드뉴스 이미지 생성 요청 시작")

        # 이미지 생성 API 호출
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )

        # 응답에서 이미지 URL 가져오기
        image_url = response.data[0].url
        logger.info(f"[CARDNEWS] 이미지 생성 완료 | url={image_url}")

        # S3 환경변수 값을 읽어 true시 S3에 업로드
        use_s3 = os.getenv("USE_S3", "false").lower() == "true"
        if use_s3:
            logger.info("[CARDNEWS] S3 업로드 시작")
            return upload_image_to_s3(image_url, folder="cardnews")
        else:
            logger.info("[CARDNEWS] S3 비활성화 - DALL-E URL 그대로 사용")
            return image_url

    except Exception as e:
        logger.error(f"[CARDNEWS] 이미지 생성 실패: {e}")
        return ""