"""
S3 업로드 서비스
"""
import boto3
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

# S3 클라이언트 생성
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), # 액세스 키  
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'), # 시크릿 키
    region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME') # 버킷이름


def upload_image_to_s3(image_url: str, folder: str = "cardnews") -> str:
    """
    DALL-E 임시 URL의 이미지를 다운로드해서 S3에 업로드
    
    Args:
        image_url: DALL-E가 생성한 임시 이미지 URL
        folder: S3 버킷 내 폴더 (기본: "cardnews")
    
    Returns:
        S3 영구 URL
    """
    try:
        # 이미지 다운로드
        print(f"이미지 다운로드 중: {image_url[:50]}...")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status() # 에러 발생 시 예외 던지기
        
        # S3 업로드용 파일명 생성 (timestamp 기반)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # 20251110_053030 
        filename = f"{folder}/{timestamp}.png" # cardnews/20251110_053030.png 이렇게 파일명 생김
        
        # S3에 업로드
        print(f"S3 업로드 중: {filename}")
        s3_client.upload_fileobj(
            BytesIO(response.content), # 메모리 -> S3로 직접 업로드
            BUCKET_NAME,
            filename,
            ExtraArgs={
                'ContentType': 'image/png',
                'ACL': 'public-read'  # 공개 읽기 권한
            }
        )
        
        # S3 URL 생성
        s3_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION', 'ap-northeast-2')}.amazonaws.com/{filename}"
        
        print(f"S3 업로드 완료: {s3_url}")
        return s3_url
        
    except requests.exceptions.RequestException as e:
        print(f"이미지 다운로드 실패: {e}")
        # 실패 시 원본 URL 반환 (fallback)
        return image_url
        
    except Exception as e:
        print(f"S3 업로드 실패: {e}")
        # 실패 시 원본 URL 반환 (fallback)
        return image_url


def delete_image_from_s3(s3_url: str) -> bool:
    """
    S3에서 이미지 삭제
    
    Args:
        s3_url: S3 이미지 URL
    
    Returns:
        삭제 성공 여부
    """
    try:
        # URL에서 파일명 추출
        # https://bucket-name.s3.region.amazonaws.com/cardnews/20231109_123456.png
        # → cardnews/20231109_123456.png
        filename = s3_url.split(f"{BUCKET_NAME}.s3.")[-1].split('/', 1)[-1]
        
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=filename)
        print(f"S3 삭제 완료: {filename}")
        return True
        
    except Exception as e:
        print(f"S3 삭제 실패: {e}")
        return False
