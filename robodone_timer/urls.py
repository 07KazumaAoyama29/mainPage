from django.urls import path
from . import views

app_name = 'robot_timer'

urlpatterns = [
    path('', views.menu, name='menu'),             # トップページ
    path('build/', views.build_timer, name='build_timer'), # 制作タイマー
    path('pair/', views.pair_timer, name='pair_timer'),   # 交代タイマー
]