from django.urls import path
from . import views

app_name = "reading_notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("new/", views.note_create, name="create"),
    path("export/", views.note_export_selected, name="export_selected"),
    path("theme-tags/", views.theme_tag_list, name="theme_tag_list"),
    path("theme-tags/new/", views.theme_tag_create, name="theme_tag_create"),
    path("theme-tags/<int:pk>/edit/", views.theme_tag_edit, name="theme_tag_edit"),
    path("theme-tags/<int:pk>/delete/", views.theme_tag_delete, name="theme_tag_delete"),
    path("<int:pk>/", views.note_detail, name="detail"),
    path("<int:pk>/edit/", views.note_edit, name="edit"),
    path("<int:pk>/delete/", views.note_delete, name="delete"),
]
