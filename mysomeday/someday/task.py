# myapp/tasks.py

import logging
from celery import shared_task
from .ml_models import create_combined_seq, get_previous_five_events, predicted_data, train_and_save_model, load_model_func, MODEL_SAVE_PATH, preprocess_data
import pandas as pd
from .models import CalendarEvent, ModelStatus
from transformers import pipeline
from .ml_models import extract_activity, extract_location, extract_time, get_season, create_sequences, split_into_time_blocks
from datetime import datetime, timedelta

logger = logging.getLogger('myapp')

# 활동 키워드 사전 정의
activity_keywords = {
    "식사": ["요리", "외식", "맛집","아침","점심","저녁","모임"],
    "운동": ["헬스", "요가", "필라테스", "홈트"],
    "공부": ["독서", "강의", "언어", "자격증", "회의","시험","기말","중간"],
    "스포츠": ["축구", "농구", "배드민턴", "테니스", "등산", "자전거", "클라이밍", "수영", "서핑", "스쿠버","볼링","탁구","야구장","축구장","야구","배구"],
    "관람": ["연극", "뮤지컬", "콘서트", "전시회", "미술관", "박물관", "영화관", "드라마","영화"],
    "공원": ["산책", "피크닉", "캠핑", "숲"],
    "실내활동" : ["PC방", "노래방", "보드게임", "VR", "방탈출", "만화카페", "당구", "포켓볼", "탁구", "플스방"],
    "기타": []
}

location_keywords = ["강남", "역삼", "삼성동", "신사",
    "압구정", "가로수길", "청담",
    "잠실", "롯데월드", "석촌호수",
    "홍대", "연남동", "합정", "망원", "상수",
    "종로", "인사동", "삼청동", "서촌", "북촌",
    "을지로", "을지로3가",
    "혜화", "대학로",
    "동대문", "동대문디자인플라자(DDP)",
    "건대", "커먼그라운드",
    "왕십리", "한양대",
    "성수", "서울숲",
    "신촌", "연세대학교", "이대",
    "마포", "공덕",
    "상암", "DMC", "월드컵공원",
    "양재", "양재 꽃시장",
    "서초", "교대역", "예술의전당",
    "사당", "방배동",
    "노원", "불암산",
    "수유", "북한산",
    "미아", "미아사거리"]

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

@shared_task    
def model_predict():
    #events = get_previous_five_events()
    #print(events)
    #combined_seq = create_combined_seq(events)
    seq = pd.DataFrame({
    'activity': ['회의', '외식', '회의', '회의', '회의'],
    'location': ['강남','강남','강남','강남','강남'], #지역으로 바꿔야함
    'time_block': [4, 5, 6, 7, 8]
    })
    #combined_seq = '운동:헬스장:4 외식:식당:5 영화:영화관:6 독서:도서관:7 운동:헬스장:8'
    predicted_data(seq)