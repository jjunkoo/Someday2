# myapp/ml_model.py
import os
from django.utils import timezone
from datetime import timedelta
import datetime
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
import joblib
import re
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Embedding
from .models import CalendarEvent
import joblib
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pandas as pd
logging.basicConfig(
    level=logging.DEBUG,  # 로깅 레벨을 DEBUG로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 콘솔에 로그 출력
        # logging.FileHandler('app.log')  # 파일로 로그 출력 (필요 시 주석 해제)
    ]
)
logger = logging.getLogger('myproject')

MODEL_SAVE_PATH = './saved_lstm_model'

# 계절별 정의 함수
def get_season(month):
    seasons = {'Spring': [3, 4, 5], 'Summer': [6, 7, 8], 'Autumn': [9, 10, 11], 'Winter': [12, 1, 2]}
    for season, months in seasons.items():
        if month in months:
            return season
    return 'Unknown'

# 활동 추출 함수
def extract_activity(text, activity_keywords):
    for activity, keywords in activity_keywords.items():
        if any(keyword in text for keyword in keywords):
            return activity
    return '기타'

# 장소 추출 함수
def extract_location(text, location_keywords):
    matched_locations = [location for location in location_keywords if location in text]
    return ', '.join(matched_locations) if matched_locations else 'Unknown'

# 시간 추출 함수
def extract_time(text):
    time_patterns = [
        r'\b(오전\s?\d{1,2}시(?:\s?\d{1,2}분)?)\b',          # "오전 2시", "오전 2시 30분"
        r'\b(오후\s?\d{1,2}시(?:\s?\d{1,2}분)?)\b',          # "오후 2시", "오후 2시 30분"
        r'\b[가-힣]+\s(\d{1,2}시(?:\s?\d{1,2}분)?)\b',       # "강남 2시", "강남 2시 30분"
        r'\b(\d{1,2}시반)\b',                                # "2시반"
        r'\b(\d{1,2}시)\b(?=\s*[가-힣]+)',                   # "2시 저녁"
        r'\b(\d{1,2}시)\s?\d{0,2}분\b',                      # "2시 30분"
        r'\b(\d{1,2}시)\b',                                   # "7시"
        r'\b(\d{1,2}):(\d{2})\b'                              # "14:30"
    ]

    times = []
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # 마지막 패턴은 시:분을 별도로 캡처함
            if isinstance(match, tuple):
                if len(match) == 2:
                    # "14:30"과 같은 패턴
                    hour, minute = match
                    times.append(f"{hour}:{minute}")
                else:
                    times.append(match)
            else:
                times.append(match)
    unique_times = list(dict.fromkeys(times))
    
    return ', '.join(unique_times) if times else 'Unknown'

# 시간 문자열을 datetime.time 객체로 파싱하는 함수
def convert_single_time(single_time_str):
    try:
        single_time_str = single_time_str.strip()
        if '시반' in single_time_str:
            single_time_str = single_time_str.replace('시반', '시 30분')
        
        match = re.search(r'(오전|오후)?\s*(\d{1,2})시(?:\s*(\d{1,2})분)?', single_time_str)
        if match:
            period, hour, minute = match.groups()
            hour = int(hour)
            minute = int(minute) if minute else 0

            if period == '오후' and hour != 12:
                hour += 12
            elif period == '오전' and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}:00"
    except Exception as e:
        logger.error(f"시간 변환 오류: {single_time_str} - {e}")
    return "00:00:00"

# 시간 정보 변환 함수
def parse_extracted_time(time_str, date_str):
    start_datetimes = []
    end_datetimes = []
    
    # 쉼표로 분리하여 각각의 시간 정보를 처리
    parts = [part.strip() for part in time_str.split(',')]
    
    for part in parts:
        # 시간 범위가 있는 경우
        if '-' in part:
            range_parts = [p.strip() for p in part.split('-')]
            if len(range_parts) == 2:
                start_str, end_str = range_parts
                start_time = convert_single_time(start_str)
                end_time = convert_single_time(end_str)
                
                # 날짜와 시간 결합
                start_datetime = f"{date_str} {start_time}"  
                end_datetime = f"{date_str} {end_time}"     
                
                start_datetimes.append(start_datetime)
                end_datetimes.append(end_datetime)
            else:
                print(f"시간 범위 형식 오류: {part}")
            continue  # 범위 처리 후 다음으로 넘어감
        
        # 단일 시간 처리
        start_time = convert_single_time(part)
        
        # 끝 시간이 없는 경우 시작 시간에 1시간 더하기
        try:
            start_dt = datetime.datetime.strptime(f"{date_str} {start_time}", '%Y-%m-%d %H:%M:%S')  # 수정
            end_dt = start_dt + timedelta(hours=1)
            end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')  # 수정
        except Exception as e:
            print(f"시간 계산 오류: {start_time} - {e}")
            end_time = f"{date_str} 00:00:00"
        
        start_datetime = f"{date_str} {start_time}"  # 수정
        end_datetime = end_time
        
        start_datetimes.append(start_datetime)
        end_datetimes.append(end_datetime)
    
    return start_datetimes, end_datetimes


# 시간대 라벨링 (0~111)
def get_time_block(dt):
    day_of_week = dt.weekday()  # 0: 월요일, ..., 6: 일요일
    hour = dt.hour
    # 8시부터 12시까지 시간대 설정 (16시간을 16개 블록으로 나눔)
    block = (hour - 8)  # 8시를 시작으로 시간대 계산
    if 0 <= block < 16:  # 8시 ~ 24시 사이의 블록만 처리
        return day_of_week * 16 + block  # 요일별로 16개의 블록
    else:
        return -1  # 유효하지 않은 시간대

# 시퀀스 분할 함수
def split_into_time_blocks(df):
    split_events = []
    for _, row in df.iterrows():
        start_time = row['start']
        end_time = row['end']
        duration = end_time - start_time
        num_blocks = int(duration.total_seconds() // (1 * 3600)) or 1
        for i in range(num_blocks):
            block_start = start_time + timedelta(hours=1 * i)
            block_end = block_start + timedelta(hours=1)
            split_event = row.copy()
            split_event['start'] = block_start
            split_event['end'] = block_end
            split_events.append(split_event)
    split_df = pd.DataFrame(split_events)
    return split_df

    # 모델 학습 및 저장 함수
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
    #logger.debug("DataFrame 'activity' 컬럼 내용:\n%s", df['activity'].to_string())
    
    # 장소 추출
    logger.debug("extract_location 호출 전.")
    df['location'] = df['combined_text_summary'].apply(lambda x: extract_location(x, location_keywords))
    
    # summary에서 장소가 'Unknown'이면 description에서 추출
    df['location'] = df.apply(
        lambda row: row['location'] if row['location'] != 'Unknown' else extract_location(row['combined_text_description'], location_keywords),
        axis=1
    )
    logger.debug("extract_location 호출 완료.")
    # 시간 추출
    # start와 end 컬럼 사용 (간소화된 부분)
    logger.debug("start와 end 컬럼을 바로 사용합니다.")
    df['parsed_start'] = df['start']
    df['parsed_end'] = df['end']
    logger.debug("start와 end 데이터를 parsed_start와 parsed_end로 복사 완료.")
    
    # start와 end를 explode할 필요 없음
    logger.debug("start와 end 컬럼 확인:\n%s", df[['start', 'end']].head().to_string())
    
    # start와 end 컬럼 업데이트 (이미 동일한 값이므로 그대로 둠)
    df['start'] = pd.to_datetime(df['start'], errors='coerce')
    df['end'] = pd.to_datetime(df['end'], errors='coerce')
    logger.debug("start와 end 컬럼 업데이트 완료.")
    
    # 2시간 단위로 분할
    logger.debug("split_into_time_blocks 호출 전.")
    split_df = split_into_time_blocks(df)
    if split_df is None:
        logger.error("split_into_time_blocks 함수가 None을 반환했습니다.")
        raise ValueError("split_into_time_blocks 함수가 None을 반환했습니다.")
    #logger.debug(f"split_into_time_blocks 완료. 결과 행 수: {len(split_df)}")
    #logger.debug(f"결과 DataFrame:\n{split_df.to_string()}")
    
    # 계절 정보 추가
    logger.debug("get_season 호출 전.")
    split_df['season'] = split_df['start'].dt.month.apply(get_season)
    logger.debug("계절 정보 추가 완료.")
    
    # 시간대 라벨링 (0~83)
    logger.debug("get_time_block 호출 전.")
    split_df['time_block'] = split_df['start'].apply(get_time_block)
    logger.debug("get_time_block 호출 완료.")
    
    return split_df

def preprocess_for_lstm(df, sequence_length):
    sequences = []
    labels = []

    df = df.sort_values('start')
    for i in range(len(df) - sequence_length):
        seq = df.iloc[i:i+sequence_length]
        time_seq = seq['time_block'].values
        activity_seq = seq['activity'].values
        combined_seq = [f"{time}:{act}" for time, act in zip(time_seq, activity_seq)]
        sequences.append(combined_seq)
        label = df.iloc[i + sequence_length]['activity']
        labels.append(label)

    return sequences, labels

# 데이터 준비
def prepare_data(df, sequence_length):

    # 1. Preprocess the data for LSTM
    sequences, labels = preprocess_for_lstm(df, sequence_length)
    print("DEBUG: Sequences (raw):", sequences[:5])  # 첫 5개 시퀀스 확인
    print("DEBUG: Labels (raw):", labels[:5])  # 첫 5개 레이블 확인

    # 2. String to integer encoding using Tokenizer
    tokenizer = tf.keras.preprocessing.text.Tokenizer(oov_token = "<OOV>")
    tokenizer.fit_on_texts(sequences)
    encoded_sequences = tokenizer.texts_to_sequences(sequences)
    print("DEBUG: Tokenizer Word Index:", tokenizer.word_index)  # 토크나이저의 단어 사전 확인
    print("DEBUG: Encoded Sequences (first 5):", encoded_sequences[:5])  # 첫 5개 인코딩된 시퀀스 확인

    # 3. Encode labels
    encoder = LabelEncoder()
    encoded_labels = encoder.fit_transform(labels)
    print("DEBUG: Label Classes:", list(encoder.classes_))  # 레이블 클래스 확인
    print("DEBUG: Encoded Labels (first 5):", encoded_labels[:5])  # 첫 5개 인코딩된 레이블 확인

    # 4. Pad the sequences
    padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(encoded_sequences, maxlen=sequence_length)
    print("DEBUG: Padded Sequences (first 5):", padded_sequences[:5])  # 첫 5개 패딩된 시퀀스 확인

    return padded_sequences, encoded_labels, tokenizer, encoder

# LSTM 모델 정의
def build_lstm_model(vocab_size, embedding_dim, input_length, num_classes):
    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=input_length),
        LSTM(128, return_sequences=False),
        Dense(64, activation='relu'),
        Dense(num_classes, activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def train_lstm_model(df, sequence_length=5, embedding_dim=100, batch_size=64, epochs=50, test_size=0.2, random_state=42):

    # 데이터 준비
    padded_sequences, encoded_labels, tokenizer, encoder = prepare_data(df, sequence_length)
    
    # 학습/테스트 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(
        padded_sequences, encoded_labels, test_size=test_size, random_state=random_state
    )
    
    # 모델 정의
    vocab_size = len(tokenizer.word_index) + 1
    num_classes = len(encoder.classes_)
    model = build_lstm_model(vocab_size, embedding_dim, sequence_length, num_classes)
    
    # 모델 학습
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test))
    
    return model, tokenizer, encoder

# 모델 저장
def save_lstm_model(model, tokenizer, encoder, path):
    os.makedirs(path, exist_ok=True)
    
    # 모델 저장 (디렉터리 내부에 .keras 파일로 저장)
    model_file = os.path.join(path, "model.keras")
    model.save(model_file)
    with open(f"{path}/tokenizer.pkl", "wb") as f:
        joblib.dump(tokenizer, f)
    with open(f"{path}/label_encoder.pkl", "wb") as f:
        joblib.dump(encoder, f)

# 모델 로드
def load_lstm_model(path):
    model_path = os.path.join(path, "model.keras")
    # 모델 로드
    model = tf.keras.models.load_model(model_path)
    with open(f"{path}/tokenizer.pkl", "rb") as f:
        tokenizer = joblib.load(f)
    with open(f"{path}/label_encoder.pkl", "rb") as f:
        encoder = joblib.load(f)
    return model, tokenizer, encoder

def predict_lstm(path,sequence,time_sequence, excluded_labels):
    model, tokenizer, encoder = load_lstm_model(path)
    
    # 시퀀스 결합 (시간 + 활동)
    combined_sequence = [f"{time}:{act}" for time, act in zip(time_sequence, sequence)]
    print("Combined Sequence:", combined_sequence)  # 디버깅용
    
    # 시퀀스 토큰화
    tokenized_sequence = tokenizer.texts_to_sequences([combined_sequence])
    print("Tokenized Sequence:", tokenized_sequence)  # 디버깅용
    
    # 시퀀스 패딩
    padded_sequence = tf.keras.preprocessing.sequence.pad_sequences(tokenized_sequence, maxlen=5)
    print("Padded Sequence:", padded_sequence)  # 디버깅용
    
    # 모델 예측
    predictions = model.predict(padded_sequence)
    print("Predictions (Raw):", predictions)  # 디버깅용
    
    # 확률 분포 계산
    probabilities = predictions[0]
    class_probabilities = {encoder.classes_[i]: float(prob) for i, prob in enumerate(probabilities)}
    
    # 가장 높은 확률의 클래스 반환
    predicted_class_idx = np.argmax(predictions, axis=1)
    predicted_label = encoder.inverse_transform(predicted_class_idx)
    
    # 최종 레이블 선택
    sorted_classes = sorted(class_probabilities.items(), key=lambda x: x[1], reverse=True)
    highest_label, highest_probability = sorted_classes[0]
    for label, prob in sorted_classes:
        if label not in excluded_labels and label != "기타":  # 특정 레이블 및 "기타" 제외 조건
            final_label = label
            final_probability = prob
            break
    else:
        final_label = None
        final_probability = None

    
    return {
        "first_label" : highest_label,
        "predicted_label": final_label,
        "probabilities": class_probabilities,
        "selected_probability": final_probability
    }