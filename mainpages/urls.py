from django.urls import path, include
from django.contrib import admin

from .views import HomePageView, MePageView

app_name = 'mainpages'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('me/', MePageView.as_view(), name='me'),
    path('admin/', admin.site.urls),
    path('knowledgebase/', include('learning_logs.urls')), 
]
