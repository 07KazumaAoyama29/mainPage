from django.urls import path

from . import views

app_name = "memo"

urlpatterns = [
    path("", views.memo_list, name="list"),
    path("new/", views.memo_create, name="create"),
    path("<int:pk>/", views.memo_detail, name="detail"),
    path("<int:pk>/edit/", views.memo_edit, name="edit"),
    path("<int:pk>/delete/", views.memo_delete, name="delete"),
    path("<int:pk>/export/", views.memo_export_single, name="export_single"),
    path("export/all/", views.memo_export_all, name="export_all"),
]

