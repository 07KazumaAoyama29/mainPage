from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    path("", views.calendar_view, name="calendar"),
    path("api/events/", views.calendar_events, name="calendar_events"),

    # スケジュール作成用
    path("create-form/", views.schedule_create_form, name="create_form"),
    path("create/", views.schedule_create, name="create"),
    path("edit-form/<int:pk>/", views.schedule_edit_form, name="edit_form"),
    path("update/<int:pk>/", views.schedule_update, name="update"),
    path("delete/<int:pk>/", views.schedule_delete, name="delete"),

    # スケジュール編集用
    path("edit-form/<int:pk>/", views.schedule_edit_form, name="edit_form"),
    path("update/<int:pk>/", views.schedule_update, name="update"),
    path("task/<int:pk>/toggle/", views.toggle_task, name="toggle_task"),
    path("task/edit-form/<int:pk>/", views.task_edit_form, name="task_edit_form"),
    path("task/update/<int:pk>/", views.task_update, name="task_update"),
    path("task/delete/<int:pk>/", views.task_delete, name="task_delete"),
    path("schedule/<int:pk>/", views.schedule_detail, name="schedule_detail"),
    path("api/update_time/", views.schedule_update_time, name="update_schedule_time"),
    path("tasks/reorder/", views.reorder_tasks, name="reorder_tasks"),

    path("action-items/<int:pk>/", views.action_item_detail, name="action_item_detail"),
    path("action-items/<int:pk>/toggle/", views.toggle_action_item_completion, name="toggle_action_item"),
    path("action-items/", views.action_item_list, name="action_item_list"),
    path("action-items/create-form/", views.action_item_create_form, name="action_item_create_form"),
    path("action-items/create/", views.action_item_create, name="action_item_create"),
    path("action-items/edit-form/<int:pk>/", views.action_item_edit_form, name="action_item_edit_form"),
    path("action-items/update/<int:pk>/", views.action_item_update, name="action_item_update"),
    path("action-items/delete/<int:pk>/", views.action_item_delete, name="action_item_delete"),

    # カテゴリ（アクションリスト）管理用
    path("categories/", views.category_list, name="category_list"),
    path("categories/create-form/", views.category_create_form, name="category_create_form"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/edit-form/<int:pk>/", views.category_edit_form, name="category_edit_form"),
    path("categories/update/<int:pk>/", views.category_update, name="category_update"),
    path("categories/delete/<int:pk>/", views.category_delete, name="category_delete"),

    #統計用
    path("summary/", views.weekly_summary, name="weekly_summary"),
    path("summary/monthly/", views.monthly_summary, name="monthly_summary"),

    # 公開用API
    path("api/public-events/", views.public_calendar_events, name="public_calendar_events"),
]