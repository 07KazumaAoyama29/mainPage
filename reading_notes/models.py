from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ReadingNote(models.Model):
    class Category(models.TextChoices):
        NOVEL = "novel", "小説"
        TECHNICAL = "technical", "専門書"
        READING = "reading", "読み物"
        MAGAZINE = "magazine", "雑誌"
    class Status(models.TextChoices):
        UNREAD = "unread", "未読"
        READING = "reading", "読書中"
        FINISHED = "finished", "読了"

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField("タイトル", max_length=200)
    author = models.CharField("著者名", max_length=200, blank=True)
    page_count = models.IntegerField("ページ数", null=True, blank=True)

    status = models.CharField("ステータス", max_length=20, choices=Status.choices, default=Status.UNREAD)
    finished_at = models.DateField("読了日", null=True, blank=True)

    category = models.CharField("種類", max_length=20, choices=Category.choices, blank=True)

    rating = models.IntegerField(
        "おすすめ度",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    is_public = models.BooleanField("公開する", default=False)
    cover_image = models.ImageField("画像", upload_to="reading_notes/covers/", blank=True, null=True)

    one_line_summary = models.CharField("一言要約", max_length=300, blank=True)
    impression_during = models.TextField("読書中の感想", blank=True)
    impression_after = models.TextField("読了後の感想", blank=True)
    comparison_notes = models.TextField("他作品と比べた感想", blank=True)
    theme_notes = models.TextField("作品のテーマについての感想", blank=True)
    unwritten_notes = models.TextField("書かれていないものについての感想", blank=True)
    era_common_notes = models.TextField("時代の共通点としての感想", blank=True)
    universal_theme_notes = models.TextField("普遍的なテーマとしての感想", blank=True)

    created_at = models.DateTimeField("作成日", auto_now_add=True)
    updated_at = models.DateTimeField("更新日", auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Reading Note"
        verbose_name_plural = "Reading Notes"
        ordering = ["-updated_at"]


class AffiliateLink(models.Model):
    class Kind(models.TextChoices):
        AMAZON = "amazon", "Amazon"
        RAKUTEN = "rakuten", "楽天"

    note = models.ForeignKey(ReadingNote, on_delete=models.CASCADE, related_name="affiliate_links")
    kind = models.CharField("種類", max_length=20, choices=Kind.choices, default=Kind.AMAZON)
    label = models.CharField("ラベル", max_length=100, blank=True)
    url = models.URLField("URL", max_length=500)
    sort_order = models.IntegerField("表示順", default=0)

    def save(self, *args, **kwargs):
        if self.kind == self.Kind.AMAZON:
            self.label = "Amazon"
            self.sort_order = 1
        elif self.kind == self.Kind.RAKUTEN:
            self.label = "楽天"
            self.sort_order = 2
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label or self.get_kind_display()

    class Meta:
        ordering = ["sort_order", "id"]
