from django.contrib import admin

# Register your models here.

from .models import Knowledge, Tag

admin.site.register(Knowledge)
admin.site.register(Tag)
