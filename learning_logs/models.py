from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
# Commentモデルの追加
class Comment(models.Model):
    knowledge = models.ForeignKey(
        'Knowledge',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.knowledge.title}"

class Knowledge(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    title = models.CharField("タイトル", max_length=200)
    content = models.TextField("内容", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True)
    
    # is_publicフィールドを追加
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Knowledge"