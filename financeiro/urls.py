
from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.painel_financeiro, name='painel'),
]
