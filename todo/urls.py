from django.urls import path
from . import views
from .views import TodoUpdate, TodoDelete

urlpatterns = [
    # Todoのリストと作成
    path("", views.taskList, name="tasklist"),
    path("create/", views.create, name="create"),

    # Todoの更新と削除
    path("update/<int:pk>", TodoUpdate.as_view(), name="update"),
    path("delete/<int:pk>", TodoDelete.as_view(), name="delete"),
    
    # Todoの状態変更
    path("state/<int:pk>", views.state, name="state"),
]