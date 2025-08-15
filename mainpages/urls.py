from django.urls import path, include
from django.contrib import admin

from .views import HomePageView

app_name = 'mainpages'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('knowledgebase/', include('learning_logs.urls')), 
]