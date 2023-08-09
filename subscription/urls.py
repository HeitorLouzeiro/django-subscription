from django.urls import path

from . import views
from .views import Register

urlpatterns = [
    path('', views.home, name='home'),
    path('check-mail/', views.check_mail_ajax, name='check-mail'),
    path('register/', Register.as_view(), name='register'),
    path('login/', views.Login.as_view(), name='login'),
]
