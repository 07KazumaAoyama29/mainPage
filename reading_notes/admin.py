from django.contrib import admin
from .models import ReadingNote, AffiliateLink


@admin.register(ReadingNote)
class ReadingNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "category", "rating", "is_public", "finished_at", "updated_at")
    list_filter = ("status", "category", "is_public")
    search_fields = ("title", "author", "one_line_summary")


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "note", "sort_order")
    search_fields = ("label", "note__title")
