from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from learning_logs.models import Knowledge
import time

# Create your models here.
class Todo(models.Model):
    title = models.CharField("タスク名", max_length=50)
    task_type = models.CharField("タスクの種類", max_length=200)
    description = models.TextField("詳細", blank=True)
    text1 = models.CharField("S(何を達成したいのか。)", max_length=200)
    text2 = models.CharField("M(達成できたかどうかを測る定量的な指標)", max_length=200)
    text3 = models.CharField("A(達成するために必要なスキル)", max_length=200)
    text4 = models.CharField("R(関連タスク)", max_length=200)
    deadline = models.DateField("締切(T)")
    int1 = models.IntegerField("基本スコア",default=0)
    int2 = models.IntegerField("タスクの状態",default=0)#Todo=0, Doing=1, Done=2
    int3 = models.IntegerField("タスクのスコア",default=0)
    created_at = models.DateTimeField(default = timezone.now)
    date1 = models.DateTimeField("タスク終了時の時刻",default = timezone.now)
    date2 = models.DateTimeField(default = timezone.now)
    image = models.ImageField(upload_to="")
    owner = models.ForeignKey(User, on_delete=models.CASCADE) 
    knowledge = models.ForeignKey(Knowledge, on_delete=models.SET_NULL, null=True, blank=True) 

    def __str__(self):
        return self.title