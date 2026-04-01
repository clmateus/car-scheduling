from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('agendar/', views.agendar, name='agendar'),
    path('api/eventos', views.listar_agendamentos, name='listar_agendamentos')
]