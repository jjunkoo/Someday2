# myapp/tasks.py

from datetime import datetime
import logging
from celery import shared_task
import numpy as np
from .ml_models import get_time_block, predict_lstm, save_lstm_model,MODEL_SAVE_PATH, preprocess_data, split_into_time_blocks, train_lstm_model
import pandas as pd
from .models import CalendarEvent, ModelStatus

logger = logging.getLogger('myapp')

# 활동 키워드 사전 정의
activity_keywords = {
    "저녁식사" : ["저녁","저녁식사","야식"],
    "점심식사" : ["점심","식사","브런치"],
    "운동": ["운동", "헬스", "요가", "필라테스", "홈트", "러닝", "마라톤", "크로스핏", "태권도", "검도", "주짓수"],
    "공부": ["공부", "독서", "강의", "언어", "자격증", "코딩"],
    "스포츠": ["스포츠", "축구", "농구", "배드민턴", "테니스", "등산", "자전거", "클라이밍", "수영", "서핑", "스쿠버","볼링","탁구","야구장","축구장","야구","배구"],
    "관람": ["관람", "연극", "뮤지컬", "콘서트", "전시회", "미술관", "박물관", "영화관", "드라마", "영화", "오페라", "발레"],
    "공원": ["공원", "산책", "피크닉", "캠핑", "숲", "해변", "호수"],
    "실내활동" : ["실내활동","PC방", "노래방", "보드게임", "VR", "방탈출", "만화카페", "당구", "포켓볼", "탁구", "플스방"],
    "기타": []
}

location_keywords = ["강남", "역삼", "삼성동", "신사",
    "압구정", "가로수길", "청담",
    "잠실", "석촌호수",
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
        #events = CalendarEvent.objects.all().order_by('start')
        #df = pd.DataFrame(list(events.values()))
        
        df = pd.read_csv("dataset_with_patterns4.csv")
        df["start"] = pd.to_datetime(df["start"])
        df["end"] = pd.to_datetime(df["end"])

        if df.empty:
            # 모델 상태를 'not_trained'으로 재설정
            ModelStatus.objects.update_or_create(id=1, defaults={'status': 'not_trained'})
            return '데이터가 없습니다.'
        
        logger.info("데이터 전처리 시작.")
        sequence_df = preprocess_data(df, activity_keywords,location_keywords)
        logger.info("데이터 전처리 완료.")
        model, tokenizer, encoder = train_lstm_model(sequence_df)
        # 모델 학습 및 저장
        logger.info("모델 학습 및 저장 시작.")
        save_lstm_model(model, tokenizer,encoder,MODEL_SAVE_PATH)
        logger.info("모델 학습 및 저장 완료.")
        
        # 모델 상태를 'trained'으로 업데이트
        ModelStatus.objects.update_or_create(id=1, defaults={'status': 'trained'})
        
        return '모델 학습 및 저장 완료.'
    
    except Exception as e:
        # 에러 발생 시 모델 상태를 'not_trained'으로 재설정
        ModelStatus.objects.update_or_create(id=1, defaults={'status': 'not_trained'})
        return f'모델 학습 중 오류 발생: {str(e)}'

@shared_task    
def model_predict(time,selected_labels,excluded_labels):
    time_seq = []
    all_results = []
    target = pd.to_datetime(time)
    target_weekday = target.weekday()
    df = pd.read_csv("dataset_with_patterns4.csv")
    df["start"] = pd.to_datetime(df["start"])  # start를 datetime으로 변환
    df["end"] = pd.to_datetime(df["end"])      # end를 datetime으로 변환
    print(selected_labels)
    print(excluded_labels)
    # if(target_weekday == 0):
    #     filtered_df = df[df["start"].dt.weekday == 6]
    # else:
    #     filtered_df = df[df["start"].dt.weekday == target_weekday-1] 
    filtered_df = df[df["start"].dt.weekday == target_weekday]
    recent_events = filtered_df.sort_values(by='start', ascending=False).head(5)
    events = split_into_time_blocks(recent_events)
    seq = events["summary"].head(5).to_numpy()
    seq = np.flip(seq)
    for start_time in events['start']:
        time_s = get_time_block(start_time)
        time_seq.append(time_s)
    time_seq = sorted(time_seq, reverse=True)
    time_sequence = time_seq[:5]
    time_sequence = np.flip(time_sequence)
    result = predict_lstm(MODEL_SAVE_PATH,seq,time_sequence,excluded_labels)
    all_results.append(result["predicted_label"])
    for i in range(15):
        seq = np.concatenate((seq[1:], [result["first_label"]]))
        if time_sequence[4] == 111:
            time_sequence = np.concatenate((time_sequence[1:], [2]))
        else:
            time_sequence = np.concatenate((time_sequence[1:], [time_sequence[4] + 1]))
        result = predict_lstm(MODEL_SAVE_PATH, seq, time_sequence, excluded_labels)
        all_results.append(result["predicted_label"])
    return all_results

    