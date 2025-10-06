from django.urls import path
from . import views

app_name = 'roulette_app'
urlpatterns = [
    # 参加者選択ページ
    path('', views.select_members_view, name='index'),
    # 結果表示ページ
    path('result/', views.result_view, name='result'),
]