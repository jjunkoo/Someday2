# myproject/celery.py

from __future__ import absolute_import, unicode_literals
import os
import sys
from celery import Celery

# Django의 설정 모듈을 Celery에 알려줍니다.
sys.path.append('/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Django 설정을 Celery에 로드
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱의 tasks.py 파일을 자동으로 발견하도록 설정
app.autodiscover_tasks()
