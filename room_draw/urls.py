from django.urls import path

from . import views


app_name = "room_draw"
urlpatterns = [
    path("", views.index, name="index"),
    path("prepare/", views.prepare, name="prepare"),
    path("draw/", views.draw, name="draw"),
]
