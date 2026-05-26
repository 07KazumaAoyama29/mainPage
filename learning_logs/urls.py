from django.urls import path

from . import views

app_name = "learning_logs"
urlpatterns = [
    #繝帙・繝繝壹・繧ｸ
    path('', views.knowledge_list, name='knowledge_list'),
    path('show-others/<str:show_others_flag>/', views.knowledge_list, name='knowledge_list_others'),
    # 隧ｳ邏ｰ繝壹・繧ｸ逕ｨ縺ｮ繝代せ
    path('<int:knowledge_id>/', views.knowledge_detail, name='knowledge_detail'),
    path('<int:knowledge_id>/export/', views.export_knowledge_markdown, name='export_knowledge_markdown'),
    # 譁ｰ隕丈ｽ懈・繝壹・繧ｸ逕ｨ縺ｮ繝代せ
    path('new/', views.new_knowledge, name='new_knowledge'),
    
    # 遏･隴倥ち繧､繝玲欠螳壻ｻ倥″縺ｮ譁ｰ隕丈ｽ懈・繝壹・繧ｸ逕ｨ繝代せ
    path('new/<str:knowledge_type>/', views.new_knowledge, name='new_knowledge_with_type'),

    # 蟄占ｦ∫ｴ縺ｨ縺励※譁ｰ隕丈ｽ懈・繝壹・繧ｸ逕ｨ縺ｮ繝代せ・郁ｦｪID繧呈ｸ｡縺呻ｼ・
    path('new/child/<int:parent_id>/', views.new_knowledge, name='new_child_knowledge'),

    # 蟄占ｦ∫ｴ縺ｨ縺励※譁ｰ隕丈ｽ懈・繝壹・繧ｸ逕ｨ縺ｮ繝代せ・郁ｦｪID縺ｨ繧ｿ繧､繝励ｒ貂｡縺呻ｼ・
    path('new/child/<int:parent_id>/<str:knowledge_type>/', views.new_knowledge, name='new_child_knowledge_with_type'),
    # 讀懃ｴ｢邨先棡繝壹・繧ｸ逕ｨ縺ｮ繝代せ
    path('search/', views.search_results, name='search'),
    # 繧ｿ繧ｰ縺ｫ繧医ｋ繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ逕ｨ繝代せ
    path('tag/<str:tag_name>/', views.tag_list, name='tag_list'),
    # 繧ｿ繧ｰ荳隕ｧ繝壹・繧ｸ逕ｨ繝代せ
    path('tags/', views.tags_list, name='tags_list'),
    # 繧ｿ繧ｰ菴懈・繝壹・繧ｸ逕ｨ繝代せ
    path('tags/create/', views.tag_create, name='tag_create'),
    # 繧ｳ繝｡繝ｳ繝亥炎髯､逕ｨ縺ｮ繝代せ
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    # 邱ｨ髮・・繝ｼ繧ｸ逕ｨ縺ｮ繝代せ
    path('edit/<int:pk>/', views.edit_knowledge, name='edit_knowledge'),
    path('edit/<int:pk>/upload-image/', views.upload_knowledge_image, name='upload_knowledge_image'),
    # 蜑企勁繝壹・繧ｸ逕ｨ縺ｮ繝代せ
    path('delete/<int:pk>/', views.delete_knowledge, name='delete_knowledge'),
    # 繝ｦ繝ｼ繧ｶ繝ｼ繝励Ο繝輔ぅ繝ｼ繝ｫ繝壹・繧ｸ逕ｨ繝代せ
    path('profile/<str:username>/', views.profile, name='profile'),
]
