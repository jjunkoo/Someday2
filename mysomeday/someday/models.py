# myapp/models.py

from django.db import models
from django.contrib.auth.models import User

class CalendarEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    summary = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return self.summary if self.summary else "No Title"

class ModelStatus(models.Model):
    STATUS_CHOICES = [
        ('not_trained', 'Not Trained'),
        ('training', 'Training'),
        ('trained', 'Trained'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_trained')
    last_trained = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'modelstatus'

    def __str__(self):
        return f"Model Status: {self.status}"