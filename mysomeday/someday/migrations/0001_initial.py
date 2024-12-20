# Generated by Django 4.1.13 on 2024-11-08 19:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CalendarEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("event_id", models.CharField(max_length=255, unique=True)),
                ("summary", models.CharField(blank=True, max_length=255, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="calendar_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
