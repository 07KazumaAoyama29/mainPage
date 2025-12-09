from django.urls import path
from . import views

app_name = 'robot_timer'

urlpatterns = [
    path('', views.index, name='index'),
]