import datetime
import json
from venv import logger
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import CalendarEvent, ModelStatus
from .task import train_model_task

model = None
tokenizer = None
encoder = None
model_loaded = False

SCOPES = ['https://www.googleapis.com/auth/calendar']


def google_calendar_init_view(request):
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI  # 리디렉션 URI
    )
    
    # 구글 OAuth 인증 URL 생성
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    
    request.session['state'] = state

    # 구글로 리디렉션
    return HttpResponseRedirect(auth_url)
@csrf_exempt
# 인증 후 리디렉트 처리
def google_calendar_redirect_view(request):
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    
    credentials = flow.credentials
    service = build('calendar', 'v3', credentials=credentials)
    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    # 기본 캘린더의 이벤트 가져오기
    events_result = service.events().list(
    calendarId='primary',
    timeMin='2024-01-01T00:00:00Z',
    timeMax='2024-12-31T23:59:59Z',
    maxResults=2500,
    singleEvents=True,
    orderBy='startTime',
    fields='items(id,summary,start,end,description)').execute()
    events = events_result.get('items', [])
    save_events_to_db(events)
    request.session['events'] = events
    model_status = ModelStatus.objects.filter(id=1).first()

    if model_status.status in ['trained', 'training']:
        return HttpResponseRedirect('http://localhost:3000/home')
    else:
        # 모델 학습 트리거
        train_model_task.delay()
        return HttpResponseRedirect('http://localhost:3000/home')
    


def get_events(request):
    events = request.session.get('events', [])
    return JsonResponse(events, safe=False)

@csrf_exempt
def update_event(request):
    if request.method == 'POST':
        try:
            if 'credentials' not in request.session:
                return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
            data = json.loads(request.body)
            if 'id' not in data:
                data = json.loads(request.body)
                title = data.get('title')
                start = data.get('start')
                end = data.get('end')
                description = data.get('description')
                creds_info = request.session['credentials']
                credentials = Credentials(
                    creds_info['token'],
                    refresh_token=creds_info['refresh_token'],
                    token_uri=creds_info['token_uri'],
                    client_id=creds_info['client_id'],
                    client_secret=creds_info['client_secret'],
                    scopes=creds_info['scopes']
                )

                # Google Calendar API 서비스 객체 생성
                service = build('calendar', 'v3', credentials=credentials)

                event_data = {
                    'summary': title,
                    'description': description,
                    'start': {
                        'dateTime': start,  # 예: '2024-11-01T09:00:00+09:00'
                        'timeZone': 'Asia/Seoul',
                    },
                    'end': {
                        'dateTime': end,    # 예: '2024-11-01T10:00:00+09:00'
                        'timeZone': 'Asia/Seoul',
                    }
                }
                # Google Calendar에 이벤트 추가
                service.events().insert(calendarId='primary', body=event_data).execute()
                events_result = service.events().list(
                    calendarId='primary',
                    q = description,
                    timeMin=start,
                    timeMax=end,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                events = events_result.get('items', [])
                print(events)
                save_events_to_db(events)
                return JsonResponse({'status': 'success', 'message': 'Event updated successfully'})
            else:
                event_id = data.get('id')
                title = data.get('title')
                start = data.get('start')
                end = data.get('end')
                description = data.get('description')
                creds_info = request.session['credentials']
                credentials = Credentials(
                    creds_info['token'],
                    refresh_token=creds_info['refresh_token'],
                    token_uri=creds_info['token_uri'],
                    client_id=creds_info['client_id'],
                    client_secret=creds_info['client_secret'],
                    scopes=creds_info['scopes']
                )

                # Google Calendar API 서비스 객체 생성
                service = build('calendar', 'v3', credentials=credentials)

                # 기존 이벤트 가져오기
                event = service.events().get(calendarId='primary', eventId=event_id).execute()
                # 수정/추가할 데이터 업데이트
                event['summary'] = title
                event['description'] = description
                event['start'] = {'dateTime': start, 'timeZone': 'Asia/Seoul'}
                event['end'] = {'dateTime': end, 'timeZone': 'Asia/Seoul'}
                event_body = {
                    'id' : event['id'],
                    'summary': event['summary'],
                    'description': event['description'],
                    'start': {
                        'dateTime': event['start']['dateTime'],  # 예: '2024-11-01T09:00:00+09:00'
                        'timeZone': 'Asia/Seoul',
                    },
                    'end': {
                        'dateTime': event['end']['dateTime'],    # 예: '2024-11-01T10:00:00+09:00'
                        'timeZone': 'Asia/Seoul',
                    }
                }
                # Google Calendar에 이벤트 업데이트
                print(event_body)
                updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
                save_events_to_db(event_body)
                return JsonResponse({'status': 'success', 'message': 'Event updated successfully', 'event' : updated_event})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def delete_event(request):
    if request.method == 'POST':
        try:
            # 세션에 credentials가 있는지 확인
            if 'credentials' not in request.session:
                return JsonResponse({'status': 'error', 'message': '사용자가 인증되지 않았습니다.'}, status=401)
            
            # 클라이언트로부터 전달된 데이터 로드
            data = json.loads(request.body)
            event_id = data.get('id')
            
            if not event_id:
                return JsonResponse({'status': 'error', 'message': '이벤트 ID가 필요합니다.'}, status=400)
            
            # 세션에서 credentials 가져오기
            creds_info = request.session['credentials']
            credentials = Credentials(
                creds_info['token'],
                refresh_token=creds_info.get('refresh_token'),
                token_uri=creds_info['token_uri'],
                client_id=creds_info['client_id'],
                client_secret=creds_info['client_secret'],
                scopes=creds_info['scopes']
            )
            
            # Google Calendar API 서비스 객체 생성
            service = build('calendar', 'v3', credentials=credentials)
            
            # 이벤트 삭제
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            delete_event_from_db(event_id)
            # 삭제 성공 응답
            return JsonResponse({'status': 'success', 'message': '이벤트가 성공적으로 삭제되었습니다.'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': '잘못된 요청 방법입니다.'}, status=400)

@csrf_exempt
def refresh_event(request):
    if request.method == 'POST':
        try:
            # 세션에 credentials가 있는지 확인
            if 'credentials' not in request.session:
                return JsonResponse({'status': 'error', 'message': '사용자가 인증되지 않았습니다.'}, status=401)  
            
            # 세션에서 credentials 가져오기
            creds_info = request.session['credentials']
            credentials = Credentials(
                creds_info['token'],
                refresh_token=creds_info.get('refresh_token'),
                token_uri=creds_info['token_uri'],
                client_id=creds_info['client_id'],
                client_secret=creds_info['client_secret'],
                scopes=creds_info['scopes']
            )
            # Google Calendar API 서비스 객체 생성
            service = build('calendar', 'v3', credentials=credentials)
            events_result = service.events().list(
            calendarId='primary',
            timeMin='2024-01-01T00:00:00Z',
            timeMax='2024-12-31T23:59:59Z',
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime',
            fields='items(id,summary,start,end,description)').execute()
            events = events_result.get('items', [])
            request.session['events'] = events
            # 프론트엔드의 특정 경로로 리디렉션
            return JsonResponse({'status': 'success', 'message': '이벤트가 성공적으로 새로고침 되었습니다'})
        except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': '잘못된 요청 방법입니다.'}, status=400)

def save_events_to_db(events):
    if isinstance(events, dict):
        events = [events]
    elif not isinstance(events, list):
        raise ValueError("events 인자는 리스트 또는 딕셔너리여야 합니다.")
    """
    가져온 이벤트를 Django ORM을 통해 MongoDB에 저장합니다.
    """
    for event in events:
        event_id = event.get('id')
        summary = event.get('summary', 'No Title')
        description = event.get('description', '')
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))

        # 시작 및 종료 시간 파싱
        try:
            if 'dateTime' in event['start']:
                start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                # All-day 이벤트의 경우, 날짜만 제공됨
                start_time = datetime.datetime.strptime(start, '%Y-%m-%d')
            if 'dateTime' in event['end']:
                end_time = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
            else:
                end_time = datetime.datetime.strptime(end, '%Y-%m-%d')
        except ValueError as ve:
            logger.error(f"Date parsing error for event {event_id}: {ve}")
            continue

        # CalendarEvent 객체 생성 또는 업데이트
        CalendarEvent.objects.update_or_create(
            event_id=event_id,
            defaults={
                'summary': summary,
                'description': description,
                'start': start_time,
                'end': end_time,
            }
        )

def delete_event_from_db(event_id):
    try:
        event = CalendarEvent.objects.get(event_id=event_id)
        event.delete()
        return f"이벤트 '{event_id}'가 성공적으로 삭제되었습니다."
    except CalendarEvent.DoesNotExist:
        return f"이벤트 '{event_id}'를 찾을 수 없습니다."
    
@csrf_exempt
def check_model_status(request):
    """
    모델 학습 상태를 확인하는 엔드포인트.
    """
    if request.method == 'GET':
        model_status = ModelStatus.objects.filter(id=1).first()
        if model_status:
            return JsonResponse({'status': model_status.status}, status=200)
        else:
            return JsonResponse({'status': 'unknown'}, status=200)
    
    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)