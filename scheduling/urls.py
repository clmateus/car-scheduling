from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('agendar/', views.agendar, name='agendar'),
    path('api/eventos', views.listar_agendamentos, name='listar_agendamentos'),
    path('mudar_dia_agendamento/', views.mudar_dia_agendamento, name='mudar_dia_agendamento'),
    path('remover_agendamento/<int:pk>/', views.remover_agendamento, name='remover_agendamento'),
    path('veiculos/', views.veiculos, name='veiculos'),
    path('remover_veiculo/<int:pk>/', views.remover_veiculo, name='remover_veiculo'),
    path('editar_veiculo/<int:pk>/', views.editar_veiculo, name='editar_veiculo'), # Existing
    path('editar_agendamento/<int:pk>/', views.editar_agendamento, name='editar_agendamento'), # New
    path('viagens/', views.viagens, name='viagens'),
    path('historico/', views.historico, name='historico'),
    path('sideBarTEST', views.sideBarTEST, name='sideBarTEST'),
    path('alteral_veiculo/<int:pk>/', views.alterar_veiculo, name='alterar_veiculo')
]