📌전체적인 프로젝트 설명
- 구글 캘린더의 데이터를 받아와 RNN 모델을 튜닝하여 사용자의 생활 패턴을 학습하고 이에 맞는 맞춤 활동을 추천해 주는 웹 
📌코드 설명
📍mysomeday/myproject
- 모델 학습의 비동기 처리를 위해 사용한 celery와 redis에 대한 설정 및 전체적인 프로젝트에 대한 설정
📍mysomeday/someday
models.py
- 몽고db에 캘린더 데이터를 저장하기 위한 model
- 모델이 학습되었는지를 확인하기 위한 model
ml_models.py
- 딥러닝 모델 튜닝을 위한 전체적인 코드
- get_season , extract_activity , extract_location , extract_time 함수는 캘린더의 데이터를 받아와 필요한 정보인 계절, 활동, 장소에 대한 정보만 추출하여 저장
  정보 추출을 위해 RNN 모델을 튜닝 하는 것은 비효율적이라 생각하여 몇가지의 형식을 작성하여 데이터 추출 진행
- parse_extracted_time , get_time_block , create_sequences , split_into_time_blocks , preprocess_data 함수는 모델 학습을 위해 데이터를 전처리 하는 함
  시간 정보를 토대로 사용자가 선호하는 활동을 학습하는 방식을 사용하였기에 2시간 단위의 time block을 생성하여 활동 , 장소 , 시간을 토대로 시퀀스 생성
- train_and_save_model 함수는 이미 학습되어있는 한글 텍스트 처리 모델을 파인튜닝을 하는 함수
- load_model_func 학습이 끝난 모델을 불러와 사용하는 함수
