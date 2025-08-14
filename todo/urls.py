from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    path("", views.calendar_view, name="calendar"),
    path("api/events/", views.calendar_events, name="calendar_events"),

    # スケジュール作成用
    path("create-form/", views.schedule_create_form, name="create_form"),
    path("create/", views.schedule_create, name="create"),

    # スケジュール編集用
    path("edit-form/<int:pk>/", views.schedule_edit_form, name="edit_form"),
    path("update/<int:pk>/", views.schedule_update, name="update"),
    path("task/<int:pk>/toggle/", views.toggle_task, name="toggle_task"),
    path("schedule/<int:pk>/", views.schedule_detail, name="schedule_detail"),
    path("api/update_time/", views.schedule_update_time, name="update_schedule_time"),
]