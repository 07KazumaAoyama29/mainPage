from django.urls import path
from . import public_views

app_name = "reading_notes_public"

urlpatterns = [
    path("", public_views.recommend_list, name="list"),
    path("<int:pk>/", public_views.recommend_detail, name="detail"),
]
