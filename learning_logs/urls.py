from django.urls import path

from . import views

app_name = "learning_logs"
urlpatterns = [
    #ホームページ
    path('', views.knowledge_list, name='knowledge_list'),
    path('show-others/<str:show_others_flag>/', views.knowledge_list, name='knowledge_list_others'),
    # 詳細ページ用のパス
    path('<int:knowledge_id>/', views.knowledge_detail, name='knowledge_detail'),
    # 新規作成ページ用のパス
    path('new/', views.new_knowledge, name='new_knowledge'),
    
    # 知識タイプ指定付きの新規作成ページ用パス
    path('new/<str:knowledge_type>/', views.new_knowledge, name='new_knowledge_with_type'),

    # 子要素として新規作成ページ用のパス（親IDを渡す）
    path('new/child/<int:parent_id>/', views.new_knowledge, name='new_child_knowledge'),

    # 子要素として新規作成ページ用のパス（親IDとタイプを渡す）
    path('new/child/<int:parent_id>/<str:knowledge_type>/', views.new_knowledge, name='new_child_knowledge_with_type'),
    # 検索結果ページ用のパス
    path('search/', views.search_results, name='search'),
    # タグによるフィルタリング用パス
    path('tag/<str:tag_name>/', views.tag_list, name='tag_list'),
    # タグ一覧ページ用パス
    path('tags/', views.tags_list, name='tags_list'),
    # タグ作成ページ用パス
    path('tags/create/', views.tag_create, name='tag_create'),
    # コメント削除用のパス
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    # 編集ページ用のパス
    path('edit/<int:pk>/', views.edit_knowledge, name='edit_knowledge'),
    # 削除ページ用のパス
    path('delete/<int:pk>/', views.delete_knowledge, name='delete_knowledge'),
    # ユーザープロフィールページ用パス
    path('profile/<str:username>/', views.profile, name='profile'),
]