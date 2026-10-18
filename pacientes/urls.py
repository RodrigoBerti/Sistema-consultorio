
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    path('', views.listar_pacientes, name='listar'),
    path('novo/', views.criar_paciente, name='criar'),
    path('<int:paciente_id>/editar/', views.editar_paciente, name='editar'),
]
