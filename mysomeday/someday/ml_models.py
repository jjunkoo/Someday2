# myapp/ml_model.py

import logging
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf
import joblib
from transformers import pipeline
import re
from datetime import timedelta, datetime

logger = logging.getLogger('myapp')

MODEL_SAVE_PATH = './saved_transformer_model'

# 계절별 정의 함수
def get_season(month):
    if month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    elif month in [9, 10, 11]:
        return 'Autumn'
    else:
        return 'Winter'

# 활동 추출 함수
def extract_activity(text, activity_keywords):
    for activity, keywords in activity_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return activity
    return '기타'

# 장소 추출 함수
def extract_location(text, location_keywords):
    locations = []
    for location in location_keywords:
        if location in text:
            locations.append(location)
    return ', '.join(locations) if locations else 'Unknown'

# 시간 추출 함수
def extract_time(text):
    time_patterns = [
        r'\b오전\s?\d{1,2}시\b',
        r'\b오후\s?\d{1,2}시\b',
        r'\b\d{1,2}시\s?\d{0,2}분\b',
        r'\b\d{1,2}:\d{2}\b'
    ]
    
    times = []
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            times.append(match)
    
    return ', '.join(times) if times else 'Unknown'

# 시간 문자열을 datetime.time 객체로 파싱하는 함수
def parse_extracted_time(extracted_time_str, event_date):
    """
    extracted_time_str: '오전 10시, 오후 2시' 등의 형식
    event_date: datetime.date 객체
    """
    if extracted_time_str == 'Unknown':
        return None, None
    
    time_patterns = [
        r'오전\s?(\d{1,2})시(?:\s?(\d{0,2})분?)?',
        r'오후\s?(\d{1,2})시(?:\s?(\d{0,2})분?)?',
        r'(\d{1,2})시\s?(\d{0,2})분?',
        r'(\d{1,2}):(\d{2})'
    ]
    
    times = []
    for pattern in time_patterns:
        matches = re.findall(pattern, extracted_time_str)
        for match in matches:
            if len(match) == 2:
                hour, minute = match
                if hour:
                    hour = int(hour)
                else:
                    hour = 0
                minute = int(minute) if minute else 0
                times.append((hour, minute))
    
    # 시간 정보를 오전/오후로 구분
    am_pm_patterns = [
        r'(오전)\s?(\d{1,2})시(?:\s?(\d{0,2})분?)?',
        r'(오후)\s?(\d{1,2})시(?:\s?(\d{0,2})분?)?'
    ]
    
    for pattern in am_pm_patterns:
        matches = re.findall(pattern, extracted_time_str)
        for match in matches:
            period, hour, minute = match
            hour = int(hour)
            minute = int(minute) if minute else 0
            if period == '오후' and hour != 12:
                hour += 12
            elif period == '오전' and hour == 12:
                hour = 0
            times.append((hour, minute))
    
    # 중복된 시간 제거
    times = list(set(times))
    times.sort()
    
    if len(times) == 0:
        return None, None
    elif len(times) == 1:
        start_time = datetime.combine(event_date, datetime.min.time()).replace(hour=times[0][0], minute=times[0][1])
        end_time = start_time + timedelta(hours=2)  # 기본 2시간 추가
        return start_time, end_time
    else:
        start_time = datetime.combine(event_date, datetime.min.time()).replace(hour=times[0][0], minute=times[0][1])
        end_time = datetime.combine(event_date, datetime.min.time()).replace(hour=times[-1][0], minute=times[-1][1])
        return start_time, end_time

# 시간대 라벨링 (0~83)
def get_time_block(dt):
    day_of_week = dt.weekday()  # 0: 월요일, ..., 6: 일요일
    hour = dt.hour
    block = (day_of_week * 12) + (hour // 2)
    return block

# 시퀀스 및 레이블 생성 함수
def create_sequences(df, sequence_length=5):
    sequences = []
    labels = []
    
    df = df.sort_values('start')
    for i in range(len(df) - sequence_length):
        seq = df.iloc[i:i+sequence_length]
        label = df.iloc[i+sequence_length]['time_block']
        # 시퀀스에 포함할 피처 선택 (activity, location)
        activity_seq = ' '.join(seq['activity'].values)
        location_seq = ' '.join(seq['location'].values)
        combined_seq = activity_seq + " " + location_seq
        sequences.append(combined_seq)
        labels.append(label)
    
    # 시퀀스과 레이블을 DataFrame으로 변환
    sequence_df = pd.DataFrame({
        'sequence': sequences,
        'label': labels
    })
    
    return sequence_df

# 시퀀스 분할 함수
def split_into_time_blocks(df):
    split_events = []
    for _, row in df.iterrows():
        start_time = row['start']
        end_time = row['end']
        duration = end_time - start_time
        num_blocks = int(duration.total_seconds() // (2 * 3600)) or 1
        for i in range(num_blocks):
            block_start = start_time + timedelta(hours=2 * i)
            block_end = block_start + timedelta(hours=2)
            split_event = row.copy()
            split_event['start'] = block_start
            split_event['end'] = block_end
            split_events.append(split_event)
    split_df = pd.DataFrame(split_events)
    return split_df

# 데이터 전처리 함수
def preprocess_data(df, activity_keywords, location_keywords):
    logger.info("preprocess_data 함수 시작.")
    # combined_text_summary와 combined_text_description 두 개의 컬럼 생성
    logger.debug("combined_text 생성 중.")
    df['combined_text_summary'] = df['summary'].fillna('')
    df['combined_text_description'] = df['description'].fillna('')
    logger.debug("combined_text 생성 완료.")
    
    # NER Pipeline 초기화
    logger.debug("NER Pipeline 초기화 중.")
    # 활동 추출
    logger.debug("extract_activity 호출 전.")
    df['activity'] = df['combined_text_summary'].apply(lambda x: extract_activity(x, activity_keywords))
    # summary에서 활동이 추출되지 않으면 description에서 추출
    df['activity'] = df.apply(
        lambda row: row['activity'] if row['activity'] != '기타' else extract_activity(row['combined_text_description'], activity_keywords),
        axis=1
    )
    logger.debug("extract_activity 호출 완료.")
    
    # 장소 추출
    logger.debug("extract_location 호출 전.")
    df['location'] = df['combined_text_summary'].apply(lambda x: extract_location(x,location_keywords))
    # summary에서 장소가 'Unknown'이면 description에서 추출
    df['location'] = df.apply(
        lambda row: row['location'] if row['location'] != 'Unknown' else extract_location(row['combined_text_description'], location_keywords),
        axis=1
    )
    logger.debug("extract_location 호출 완료.")
    
    # 시간 추출
    logger.debug("extract_time 호출 전.")
    df['extracted_time'] = df['combined_text_summary'].apply(extract_time)
    # summary에서 시간이 'Unknown'이면 description에서 추출
    df['extracted_time'] = df.apply(
        lambda row: row['extracted_time'] if row['extracted_time'] != 'Unknown' else extract_time(row['combined_text_description']),
        axis=1
    )
    # 여전히 'Unknown'이면 start과 end에서 시간 보완
    df['extracted_time'] = df.apply(
        lambda row: row['extracted_time'] if row['extracted_time'] != 'Unknown' else f"{row['start'].hour}:{row['start'].minute} - {row['end'].hour}:{row['end'].minute}",
        axis=1
    )
    logger.debug("extract_time 호출 완료.")
    
    # 추출된 시간을 기반으로 start와 end 시간 업데이트
    logger.debug("parse_extracted_time 호출 전.")
    df['parsed_start'], df['parsed_end'] = zip(*df.apply(
        lambda row: parse_extracted_time(row['extracted_time'], row['start'].date()),
        axis=1
    ))
    logger.debug("parse_extracted_time 호출 완료.")
    
    # parsed_start와 parsed_end가 존재하면 이를 start와 end로 사용
    logger.debug("start와 end 시간 업데이트 중.")
    df['start'] = df.apply(
        lambda row: row['parsed_start'] if row['parsed_start'] else row['start'],
        axis=1
    )
    df['end'] = df.apply(
        lambda row: row['parsed_end'] if row['parsed_end'] else row['end'],
        axis=1
    )
    logger.debug("start와 end 시간 업데이트 완료.")
    
    # 2시간 단위로 분할
    logger.debug("split_into_time_blocks 호출 전.")
    split_df = split_into_time_blocks(df)
    if split_df is None:
        logger.error("split_into_time_blocks 함수가 None을 반환했습니다.")
        raise ValueError("split_into_time_blocks 함수가 None을 반환했습니다.")
    logger.debug(f"split_into_time_blocks 완료. 결과 행 수: {len(split_df)}")
    logger.debug(f"결과값 : {split_df}")
    
    # 계절 정보 추가
    logger.debug("get_season 호출 전.")
    split_df['season'] = split_df['start'].dt.month.apply(get_season)
    logger.debug("계절 정보 추가 완료.")
    
    # 시간대 라벨링 (0~83)
    logger.debug("get_time_block 호출 전.")
    split_df['time_block'] = split_df['start'].apply(get_time_block)
    logger.debug("get_time_block 호출 완료.")
    
    # 시퀀스 생성
    sequence_length = 5
    logger.debug(f"create_sequences 호출 전 (sequence_length={sequence_length}).")
    sequence_df = create_sequences(split_df, sequence_length=sequence_length)
    if sequence_df is None:
        logger.error("create_sequences 함수가 None을 반환했습니다.")
        raise ValueError("create_sequences 함수가 None을 반환했습니다.")
    logger.debug(f"create_sequences 호출 완료. 결과 행 수: {len(sequence_df)}")
    
    logger.info("preprocess_data 함수 완료.")
    return sequence_df
    
    # 모델 학습 및 저장 함수
def train_and_save_model(df, model_save_path=MODEL_SAVE_PATH):
        # 레이블 인코딩
        encoder = LabelEncoder()
        y = encoder.fit_transform(df['label'])
        y_cat = tf.keras.utils.to_categorical(y)
        
        # 시퀀스 텍스트 토큰화
        tokenizer = AutoTokenizer.from_pretrained("beomi/KcELECTRA-base")
        
        def tokenize_texts(texts, tokenizer, max_length=128):
            return tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors='tf'
            )
        
        encodings = tokenize_texts(df['sequence'].tolist(), tokenizer, max_length=128)
        
        # TensorFlow 데이터셋 생성
        dataset = tf.data.Dataset.from_tensor_slices((
            {
                'input_ids': encodings['input_ids'],
                'attention_mask': encodings['attention_mask']
            },
            y_cat
        ))
        
        # 배치 크기 설정
        batch_size = 16
        dataset = dataset.shuffle(buffer_size=10000).batch(batch_size)
        
        # 모델 정의
        transformer_model = TFAutoModelForSequenceClassification.from_pretrained("beomi/KcELECTRA-base", num_labels=len(encoder.classes_))
        
        # 컴파일
        optimizer = tf.keras.optimizers.Adam(learning_rate=2e-5)
        loss = tf.keras.losses.CategoricalCrossentropy(from_logits=False)
        metric = tf.keras.metrics.CategoricalAccuracy('accuracy')
        
        transformer_model.compile(optimizer=optimizer, loss=loss, metrics=[metric])
        
        # 학습
        epochs = 3
        transformer_model.fit(dataset, epochs=epochs)
        
        # 모델 저장
        transformer_model.save_pretrained(model_save_path)
        tokenizer.save_pretrained(model_save_path)
        
        # 레이블 인코더 저장
        joblib.dump(encoder, os.path.join(model_save_path, 'label_encoder.pkl'))
        
        print(f"모델과 토크나이저, 레이블 인코더가 '{model_save_path}'에 저장되었습니다.")
    
    # 모델 로드 함수
def load_model_func(model_load_path=MODEL_SAVE_PATH):
        from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
        
        model = TFAutoModelForSequenceClassification.from_pretrained(model_load_path)
        tokenizer = AutoTokenizer.from_pretrained(model_load_path)
        encoder = joblib.load(os.path.join(model_load_path, 'label_encoder.pkl'))
        
        print(f"모델, 토크나이저, 레이블 인코더가 '{model_load_path}'에서 로드되었습니다.")
        
        return model, tokenizer, encoder 
