# myapp/ml_model.py
from django.utils import timezone
from datetime import timedelta
import datetime
import logging
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf
import joblib
from transformers import pipeline
import re
from .models import CalendarEvent
logging.basicConfig(
    level=logging.DEBUG,  # 로깅 레벨을 DEBUG로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 콘솔에 로그 출력
        # logging.FileHandler('app.log')  # 파일로 로그 출력 (필요 시 주석 해제)
    ]
)
logger = logging.getLogger('myproject')

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
        hour = 0
        single_time_str = single_time_str.strip()
        
        # '시반'이 포함된 경우, 분 단위를 무시
        if '시반' in single_time_str:
            single_time_str = single_time_str.replace('시반', '시')
        
        # 오전 (AM) 처리: '오전'이 포함된 경우
        if '오전' in single_time_str:
            match = re.search(r'오전\s*(\d+)시', single_time_str)
            if match:
                hour = int(match.group(1))
                if hour == 12:
                    hour = 0
            else:
                print(f"오전 시간 형식 오류: {single_time_str}")
        
        # 오후 (PM) 처리: '오전'이 포함되지 않은 모든 경우를 오후로 처리
        else:
            match = re.search(r'오후\s*(\d+)시', single_time_str)
            if match:
                hour = int(match.group(1))
                if hour != 12:
                    hour += 12
            else:
                # '오전'도 '오후'도 없는 경우, 오후로 간주
                match = re.search(r'(\d+)시', single_time_str)
                if match:
                    hour = int(match.group(1))
                    if hour != 12:
                        hour += 12

        return f"{hour:02d}:00:00"
    except Exception as e:
        print(f"오류 발생: {single_time_str} - {e}")
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
            start_dt = datetime.strptime(f"{date_str} {start_time}", '%Y-%m-%d %H:%M:%S')
            end_dt = start_dt + timedelta(hours=1)
            end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"시간 계산 오류: {start_time} - {e}")
            end_time = f"{date_str} 00:00:00"
        
        start_datetime = f"{date_str} {start_time}"
        end_datetime = end_time
        
        start_datetimes.append(start_datetime)
        end_datetimes.append(end_datetime)
    
    return start_datetimes, end_datetimes

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
        time_seq = seq['time_block'].values
        activity_seq = seq['activity'].values
        location_seq = seq['location'].values
        combined_seq = ' '.join([
            f"{act}:{loc}:{time}" for act, loc, time in zip(activity_seq, location_seq, time_seq)
        ])
        sequences.append(combined_seq)
        label = df.iloc[i + sequence_length]['activity']
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
    logger.debug("extract_time 호출 전.")
    df['extracted_time'] = df['combined_text_summary'].apply(extract_time)
    
    # summary에서 시간이 'Unknown'이면 description에서 추출
    df['extracted_time'] = df.apply(
        lambda row: row['extracted_time'] if row['extracted_time'] != 'Unknown' else extract_time(row['combined_text_description']),
        axis=1
    )
    
    # 여전히 'Unknown'이면 start과 end에서 시간 보완
    df['extracted_time'] = df.apply(
        lambda row: row['extracted_time'] if row['extracted_time'] != 'Unknown' else f"{row['start'].hour} - {row['end'].hour}",
        axis=1
    )
    logger.debug("extract_time 호출 완료.")
    logger.debug(f"추출된 시간 (summary):\n{df['extracted_time'].to_string()}")
    
    # 추출된 시간을 기반으로 start와 end 시간 업데이트
    logger.debug("parse_extracted_time 호출 전.")
    df['parsed_start'], df['parsed_end'] = zip(*df.apply(
        lambda row: parse_extracted_time(row['extracted_time'], row['start'].date()),
        axis=1
    ))
    logger.debug("parse_extracted_time 호출 완료.")
    df = df.explode(['parsed_start', 'parsed_end']).reset_index(drop=True)
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
    df['start'] = pd.to_datetime(df['start'], errors='coerce')
    df['end'] = pd.to_datetime(df['end'], errors='coerce')
    # 2시간 단위로 분할
    logger.debug("split_into_time_blocks 호출 전.")
    logger.debug("DataFrame 'start' 컬럼 내용:\n%s", df['start'].to_string())
    logger.debug("DataFrame 'end' 컬럼 내용:\n%s", df['end'].to_string())
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
    
    # 시퀀스 생성
    sequence_length = 5
    logger.debug(f"create_sequences 호출 전 (sequence_length={sequence_length}).")
    sequence_df = create_sequences(split_df, sequence_length=sequence_length)
    if sequence_df is None:
        logger.error("create_sequences 함수가 None을 반환했습니다.")
        raise ValueError("create_sequences 함수가 None을 반환했습니다.")
    logger.debug(f"create_sequences 호출 완료. 결과 행 수: {len(sequence_df)}")
    
    # 시퀀스 DataFrame 로깅 (선택 사항)
    #logger.debug(f"결과 시퀀스 DataFrame:\n{sequence_df.to_string()}")
    
    logger.info("preprocess_data 함수 완료.")
    return sequence_df

    
    # 모델 학습 및 저장 함수
import os
import joblib
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf

def train_and_save_model(df, model_save_path='MODEL_SAVE_PATH'):
    # 레이블 인코딩 (정수 레이블 사용)
    encoder = LabelEncoder()
    y = encoder.fit_transform(df['label'])
    
    # 시퀀스 텍스트 토큰화
    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
    
    def tokenize_texts(texts, tokenizer, max_length=128):
        return tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors='tf'
        )
    
    encodings = tokenize_texts(df['sequence'].tolist(), tokenizer, max_length=128)
    
    # TensorFlow 데이터셋 생성 (정수 레이블 사용)
    dataset = tf.data.Dataset.from_tensor_slices((
        {
            'input_ids': encodings['input_ids'],
            'attention_mask': encodings['attention_mask']
        },
        y  # 정수 레이블
    ))
    
    # 배치 크기 설정
    batch_size = 16
    dataset = dataset.shuffle(buffer_size=10000).batch(batch_size)
    
    # GPU 설정 (가능한 경우)
    physical_devices = tf.config.list_physical_devices('GPU')
    if physical_devices:
        try:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
        except:
            pass  # GPU 설정 실패 시 무시
    
    # 분산 전략 설정 (필요 시)
    strategy = tf.distribute.get_strategy()
    
    with strategy.scope():
        # 모델 정의
        transformer_model = TFAutoModelForSequenceClassification.from_pretrained(
            "xlm-roberta-base",
            num_labels=len(encoder.classes_)
        )
        
        # 컴파일 (손실 함수와 메트릭 수정)
        optimizer = tf.keras.optimizers.Adam(learning_rate=2e-5)
        loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')
        
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
#모델 예측값을 위한 2시간 단위로 자르기
def generate_time_blocks(start_hour, end_hour, interval):
    time_blocks = []
    current_hour = start_hour
    while current_hour < end_hour:
        block_start = current_hour
        block_end = current_hour + interval
        time_blocks.append((block_start, block_end))
        current_hour += interval
    return time_blocks

# time_blocks = generate_time_blocks()
# print("예측할 시간대:", time_blocks)

def create_combined_seq(seq):
    time_seq = seq['time_block'].values
    activity_seq = seq['activity'].values
    location_seq = seq['location'].values
    combined_seq = ' '.join([
        f"{act}:{loc}:{time}" for act, loc, time in zip(activity_seq, location_seq, time_seq)
    ])
    return combined_seq

def number_to_time_object(number):
    # 숫자를 시간 객체로 변환
    hours = int(number)
    minutes = int((number - hours) * 60)
    return datetime.time(hour=hours, minute=minutes)

def predicted_data(df_sequence):
    predicted_schedule = []
    activity_to_location = {
    '운동': '헬스장',
    '공부': '도서관',
    '식사': '식당',
    '회의': '회의실',
    '기타': 'Unknown'
    } #지역으로 바꿔야함함
    time_blocks = generate_time_blocks(8,24,2) #요일만 선택하면 되므로 시간대는 이렇게 고정하자 아니면 시간대도 선택 가능하게 해도됨
    model , tokenizer , encoder = load_model_func(MODEL_SAVE_PATH)
    print("레이블 인코더 클래스:", encoder.classes_)
    print("모델의 클래스 수:", model.config.num_labels)
    print("레이블 인코더의 클래스 수:", len(encoder.classes_))
    time_block = 9
    combined_seq = create_combined_seq(df_sequence)
    for block_start, block_end in time_blocks:
        # 시퀀스 토큰화
        encodings = tokenizer(
            [combined_seq],
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors='tf'
        )
        
        # 모델 예측
        predictions = model(encodings['input_ids'], encodings['attention_mask'], training=False)
        
        # 예측된 로짓을 확률로 변환
        probabilities = tf.nn.softmax(predictions.logits, axis=-1).numpy()
        
        print(f"Time Block {block_start}:00 - {block_end}:00 - Probabilities: {probabilities}")

        # 가장 높은 확률을 가진 클래스 인덱스
        predicted_class_idx = probabilities.argmax(axis=-1)[0]
        
        print(f"예측된 클래스 인덱스: {predicted_class_idx}")

        # 인덱스를 레이블로 변환
        if predicted_class_idx >= len(encoder.classes_):
            predicted_label = "Unknown_Label_Index"
            print(f"예측된 클래스 인덱스 {predicted_class_idx}가 레이블 인코더 범위를 벗어났습니다.")
        else:
            predicted_label = encoder.inverse_transform([predicted_class_idx])[0]
            print(f"예측된 레이블: {predicted_label}")
        
        # 활동에 따른 장소 할당
        predicted_location = activity_to_location.get(predicted_label, 'Unknown')
        
        # 예측 결과 저장
        predicted_schedule.append({
            'time_block': f"{block_start}:00 - {block_end}:00",
            'predicted_activity': predicted_label,
            'predicted_location': predicted_location
        })
        
        print(f"예측된 활동 for {block_start}:00 - {block_end}:00: {predicted_label} at {predicted_location}")
        time_block = time_block + 1
        # 시퀀스 업데이트 (활동과 장소 추가)
        new_row = {
            'activity': predicted_label,
            'location': predicted_location,
            'time_block': time_block
        }
        df_sequence = pd.concat([df_sequence, pd.DataFrame([new_row])], ignore_index=True)
        # 시퀀스 길이 유지 (최근 5개)
        if len(df_sequence) > 5:
            df_sequence = df_sequence.iloc[-5:].reset_index(drop=True)
        
        # 업데이트된 시퀀스 텍스트 생성
        combined_seq = create_combined_seq(df_sequence)

def get_previous_five_events():
    # 현재 시간을 기준으로 조회 (timezone-aware)
    given_time = timezone.now()

    # 특정 시간 이전의 이벤트를 start 시간 기준으로 내림차순 정렬 후 상위 5개 가져오기
    previous_events_qs = CalendarEvent.objects.filter(start__lt=given_time).order_by('-start')[:5]

    # QuerySet을 리스트의 딕셔너리로 변환
    previous_events_list = list(previous_events_qs.values())

    # 리스트를 오름차순으로 정렬 (가장 오래된 이벤트가 먼저)
    previous_events_sorted = sorted(previous_events_list, key=lambda x: x['start'])

    # Pandas DataFrame으로 변환
    df = pd.DataFrame(previous_events_sorted)

    return df