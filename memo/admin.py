from django.contrib import admin

from .models import QuickMemo


@admin.register(QuickMemo)
class QuickMemoAdmin(admin.ModelAdmin):
    list_display = ("owner", "sequence_id", "title", "created_at")
    list_filter = ("owner",)
    search_fields = ("title", "body")

