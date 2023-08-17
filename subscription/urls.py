from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('check-mail/', views.check_mail_ajax, name='check-mail'),
    path('register/', views.Register.as_view(), name='register'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.logout, name='logout'),
    path('subcription/', views.subscription, name='subscription'),
    path('callback/', views.callback, name='callback'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('end-subscription/', views.endSubscription, name='endSubscription'),
]
