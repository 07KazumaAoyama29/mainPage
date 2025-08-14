from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from learning_logs.models import Knowledge
import time

# Create your models here.
class Schedule(models.Model):
    title = models.CharField("タイトル", max_length=50)
    start_time = models.DateTimeField("開始時刻")
    end_time = models.DateTimeField("終了時刻")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

# --- 子：タスクのモデル ---
class Task(models.Model):
    title = models.CharField("タスク名", max_length=200)
    completed = models.BooleanField("完了フラグ", default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # 親であるScheduleとの関連付け（これが一番重要）
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='tasks')

    def __str__(self):
        return self.title