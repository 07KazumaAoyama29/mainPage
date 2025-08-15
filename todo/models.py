from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# --- 1. 新しい「やることリスト」のモデル ---
class ActionItem(models.Model):
    ACTION_TYPE_CHOICES = [
        ('読書', '読書'), ('研究', '研究'), ('バイト', 'バイト'),
        ('娯楽', '娯楽'), ('ジム', 'ジム'), ('その他', 'その他'),
    ]

    title = models.CharField("タイトル", max_length=100)
    action_type = models.CharField("種類", max_length=10, choices=ACTION_TYPE_CHOICES)
    due_date = models.DateField("期日", null=True, blank=True)
    is_scheduled = models.BooleanField("スケジュール済み", default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField("説明", blank=True)
    text1 = models.CharField("目標(Specific)", max_length=200, blank=True)
    text2 = models.CharField("測定可能(Measurable)", max_length=200, blank=True)
    text3 = models.CharField("達成可能(Achievable)", max_length=200, blank=True)
    completed = models.BooleanField("完了フラグ", default=False)

    def __str__(self):
        return self.title

# --- 2. 既存の「スケジュール」モデルの変更 ---
class Schedule(models.Model):
    # ↓ titleフィールドをForeignKeyに変更
    action_item = models.ForeignKey(
        ActionItem, 
        on_delete=models.CASCADE, 
        verbose_name="アクション",
        related_name='schedules' # (推奨) 逆参照名を指定
    )

    # ↓ Scheduleモデル自体が持っていた詳細情報はActionItemに移動したので削除
    # task_type, description, text1, text2, text3, text4, int1 を削除

    start_time = models.DateTimeField("開始時刻")
    end_time = models.DateTimeField("終了時刻")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        if self.action_item:
            return self.action_item.title
        return "(アクション未設定)"

# --- 3. 「タスク」モデルは変更なし ---
class Task(models.Model):
    title = models.CharField("タスク名", max_length=200)
    completed = models.BooleanField("完了フラグ", default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='tasks')
    position = models.IntegerField("表示順", default=0)

    def __str__(self):
        return self.title