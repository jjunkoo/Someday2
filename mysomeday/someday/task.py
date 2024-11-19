# myapp/tasks.py

import logging
from celery import shared_task
from .ml_models import train_and_save_model, load_model_func, MODEL_SAVE_PATH, preprocess_data
import pandas as pd
from .models import CalendarEvent, ModelStatus
from transformers import pipeline
from .ml_models import extract_activity, extract_location, extract_time, get_season, create_sequences, split_into_time_blocks
from datetime import datetime, timedelta

logger = logging.getLogger('myapp')

# 활동 키워드 사전 정의
activity_keywords = {
    '회의': ['회의', '미팅', '회의록'],
    '운동': ['운동', '헬스장', '조깅', '요가'],
    '식사': ['식사', '점심', '저녁', '식당', '밥'],
    '공부': ['공부', '학습', '세미나', '워크숍'],
    '기타': []
}

location_keywords = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기도", "강원도", "충청도", "전라도", "경상도", "제주도"]

@shared_task
def train_model_task():
    """
    모델 학습을 수행하는 Celery 태스크.
    """
    try:
        # 모델 상태를 'training'으로 업데이트
        ModelStatus.objects.update_or_create(id=1, defaults={'status': 'training'})
        
        # MongoDB에서 데이터 로드 (Django ORM 사용)
        events = CalendarEvent.objects.all().order_by('start')
        df = pd.DataFrame(list(events.values()))
        
        if df.empty:
            # 모델 상태를 'not_trained'으로 재설정
            ModelStatus.objects.update_or_create(id=1, defaults={'status': 'not_trained'})
            return '데이터가 없습니다.'
        
        logger.info("데이터 전처리 시작.")
        sequence_df = preprocess_data(df, activity_keywords,location_keywords)
        logger.info("데이터 전처리 완료.")

        # 모델 학습 및 저장
        logger.info("모델 학습 및 저장 시작.")
        train_and_save_model(sequence_df, MODEL_SAVE_PATH)
        logger.info("모델 학습 및 저장 완료.")

        # 모델 로드 (필요 시)
        logger.info("모델 로드 시작.")
        load_model_func(MODEL_SAVE_PATH)
        logger.info("모델 로드 완료.")

        
        # 모델 상태를 'trained'으로 업데이트
        ModelStatus.objects.update_or_create(id=1, defaults={'status': 'trained'})
        
        return '모델 학습 및 저장 완료.'
    
    except Exception as e:
        # 에러 발생 시 모델 상태를 'not_trained'으로 재설정
        ModelStatus.objects.update_or_create(id=1, defaults={'status': 'not_trained'})
        return f'모델 학습 중 오류 발생: {str(e)}'
