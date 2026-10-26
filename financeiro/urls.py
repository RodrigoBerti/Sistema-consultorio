
from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.inicio_financeiro, name='painel'),

    path(
        'dashboard/',
        views.painel_financeiro,
        name='dashboard'
    ),
    path(
        'contas-receber/',
        views.listar_contas_receber,
        name='contas_receber'
    ),
    path(
        'contas-receber/nova/',
        views.criar_conta_receber,
        name='criar_conta_receber'
    ),
    path(
        'contas-receber/<int:conta_id>/editar/',
        views.editar_conta_receber,
        name='editar_conta_receber'
    ),

    # Novas rotas de parcelas e recebimentos
    path(
        'contas-receber/<int:conta_id>/',
        views.detalhe_conta_receber,
        name='detalhe_conta_receber'
    ),
    path(
        'contas-receber/<int:conta_id>/gerar-parcelas/',
        views.gerar_parcelas,
        name='gerar_parcelas'
    ),
    path(
        'parcelas/<int:parcela_id>/recebimento/',
        views.registrar_recebimento,
        name='registrar_recebimento'
    ),
    path('contas-receber/nova/',
        views.criar_conta_receber,
        name='criar_conta_receber'
    ),
     path(
        'contas-pagar/',
        views.listar_contas_pagar,
        name='contas_pagar'
    ),
    path(
        'contas-pagar/nova/',
        views.criar_despesa,
        name='criar_despesa'
    ),
    path(
        'contas-pagar/<int:despesa_id>/pagamento/',
        views.registrar_pagamento_despesa,
        name='registrar_pagamento_despesa'
    ),
]
