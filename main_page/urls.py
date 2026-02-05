"""
URL configuration for main_page project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainpages.urls')),
    #todo
    path('schedule/', include('todo.urls')),
    # 学習ノート 
    path('notes/', include('learning_logs.urls')),
    # ユーザー認証 
    path('accounts/', include('accounts.urls')),
    #ルーレット
    path('roulette/', include('roulette_app.urls')),
    #ロボ団タイマー
    path('robodonetimer/', include('robodone_timer.urls')),
    path('reading/', include('reading_notes.urls')),
    path('recommend/', include('reading_notes.public_urls'))
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
