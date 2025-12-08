from django.contrib import admin
from .models import Schedule, Task, ActionItem, ActionCategory
# Register your models here.
admin.site.register(Schedule)
admin.site.register(Task)
admin.site.register(ActionItem) # もし無ければ追加
admin.site.register(ActionCategory) # ★追加
