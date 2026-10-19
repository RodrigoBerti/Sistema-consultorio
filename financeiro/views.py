
from django.shortcuts import render
from django.db.models import Sum
from django.db.models import DecimalField
from django.db.models.functions import Coalesce

from .models import ContaReceber, Despesa


def painel_financeiro(request):
    total_contas = ContaReceber.objects.aggregate(
        total=Coalesce(
            Sum('valor_total'),
            0,
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )['total']

    total_despesas = Despesa.objects.aggregate(
        total=Coalesce(
            Sum('valor'),
            0,
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )['total']

    return render(
        request,
        'financeiro/painel.html',
        {
            'total_contas': total_contas,
            'total_despesas': total_despesas,
        }
    )
