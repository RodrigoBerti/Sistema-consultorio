from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('nova/', views.nova_consulta, name='nova_consulta'),
    path(
        '<int:consulta_id>/alterar-status/',
        views.alterar_status,
        name='alterar_status',
    ),
]