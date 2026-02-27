from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max


class QuickMemo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quick_memos")
    sequence_id = models.PositiveIntegerField("ID")
    title = models.CharField("タイトル", max_length=200, blank=True)
    body = models.TextField("本文")
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ["-sequence_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "sequence_id"],
                name="unique_sequence_id_per_owner",
            )
        ]

    def __str__(self):
        return f"{self.sequence_id}: {self.title or '(無題)'}"

    def save(self, *args, **kwargs):
        if not self.sequence_id:
            max_sequence_id = (
                QuickMemo.objects.filter(owner=self.owner).aggregate(Max("sequence_id"))[
                    "sequence_id__max"
                ]
                or 0
            )
            self.sequence_id = max_sequence_id + 1

        if not (self.title or "").strip():
            normalized_body = " ".join((self.body or "").split())
            self.title = (normalized_body[:20] or "無題").strip()

        super().save(*args, **kwargs)

