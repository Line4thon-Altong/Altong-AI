"""
카드뉴스 이미지 생성 서비스
"""
from app.core.openai_client import client
from app.services.s3_service import upload_image_to_s3
import os


def generate_cardnews_image(prompt: str) -> str:
    """
    DALL-E 3로 카드뉴스 이미지 생성
    
    Args:
        prompt: 이미지 프롬프트 (4컷 만화 형식 또는 단일 이미지)
    
    Returns:
        생성된 이미지 URL
    """
    # 캐릭터 일러스트 스타일 강화 프롬프트
    enhanced_prompt = f"""
    {prompt}
    
    CRITICAL STYLE REQUIREMENTS (캐릭터 일러스트 스타일!):
    - Simple LINE DRAWING illustration, NOT photorealistic!
    - Cute kawaii character design with big expressive eyes
    - FLAT COLORS only, no gradients, no shadows, no 3D effects
    - Minimalist clean lines like webtoon or storybook illustration
    - 2D vector art style, NOT realistic rendering
    
    CRITICAL CHARACTER CONSISTENCY (캐릭터 100% 동일 필수!):
    - This is part of a SERIES - character MUST be IDENTICAL in all images
    - FIXED CHARACTER DESIGN: Chibi proportions (head:body = 1:1.5)
    - EXACT SAME facial features: large round brown eyes, 2 white circular highlights, small dot nose, small smile
    - EXACT SAME hair: brown (#8B6F47) wavy ponytail, side-swept bangs, SAME length and style
    - EXACT SAME skin tone: light beige (#FFE4C4)
    - EXACT SAME outfit: orange polo shirt (#FF8C42), orange cap with small icon
    - SAME head-to-body proportions every time
    - Character design is LOCKED - only pose/action changes
    - Think of this as model sheet reference - keep the model EXACTLY the same
    - NO variation in character design allowed!
    
    - Warm orange (#D2691E) and beige (#F5DEB3) color palette
    - White or very light beige background, keep it simple
    - Character-focused composition
    - NO text, NO speech bubbles, NO Korean characters
    - Style reference: children's book illustration, cute mascot design, simple comic style
    """
    
    try:
        # DALL-E 이미지 생성
        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        temp_image_url = response.data[0].url
        print(f"✅ DALL-E 이미지 생성 완료: {temp_image_url[:50]}...")
        
        # S3 업로드 (환경변수로 활성화/비활성화 가능)
        # 개발 시 false로 수정
        # 실서비스에서 true로 수정
        use_s3 = os.getenv('USE_S3', 'false').lower() == 'true' 
        
        if use_s3: # S3에 업로드 하는 코드
            print("☁️  S3 업로드 시작...")
            s3_url = upload_image_to_s3(temp_image_url, folder="cardnews")
            return s3_url # 영구 URL
        else: # S3에 업로드 실패할 경우 임시 URL로 반환
            print("⚠️  S3 비활성화 - 임시 URL 사용 (1시간 후 만료)")
            return temp_image_url
        
    except Exception as e:
        print(f"❌ 이미지 생성 실패: {e}")
        return ""

