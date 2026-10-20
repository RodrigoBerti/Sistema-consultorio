
from django.shortcuts import render,redirect, get_object_or_404
from django.db.models import Sum
from django.db.models import DecimalField
from django.db.models.functions import Coalesce

from .models import ContaReceber, Despesa
from .forms import ContaReceberForm
from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange
from datetime import date

from django.db import transaction
from django.contrib import messages
from django.utils import timezone

from .models import ContaReceber, ParcelaReceber, Recebimento
from .forms import GerarParcelasForm, RecebimentoForm


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

def listar_contas_receber(request):
    contas = ContaReceber.objects.select_related(
        'paciente'
    ).prefetch_related(
        'parcelas__recebimentos'
    ).all()

    return render(
        request,
        'financeiro/contas_receber.html',
        {'contas': contas}
    )


def criar_conta_receber(request):
    if request.method == 'POST':
        form = ContaReceberForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Conta a receber cadastrada com sucesso!'
            )
            return redirect('financeiro:contas_receber')
    else:
        form = ContaReceberForm()

    return render(
        request,
        'financeiro/form_conta_receber.html',
        {'form': form, 'titulo': 'Nova conta a receber'}
    )


def editar_conta_receber(request, conta_id):
    conta = get_object_or_404(ContaReceber, pk=conta_id)

    # Não permite alterar uma cobrança depois de registrar
    # parcelas ou recebimentos. Isso evita inconsistências.
    if conta.parcelas.exists():
        messages.error(
            request,
            'Esta conta já possui parcelas. Não é possível '
            'editá-la por esta tela.'
        )
        return redirect('financeiro:contas_receber')

    if request.method == 'POST':
        form = ContaReceberForm(request.POST, instance=conta)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Conta a receber atualizada com sucesso!'
            )
            return redirect('financeiro:contas_receber')
    else:
        form = ContaReceberForm(instance=conta)

    return render(
        request,
        'financeiro/form_conta_receber.html',
        {'form': form, 'titulo': 'Editar conta a receber'}
    )


def gerar_parcelas(request, conta_id):
    conta = get_object_or_404(ContaReceber, pk=conta_id)

    if request.method == 'POST':
        form = GerarParcelasForm(request.POST)

        if form.is_valid():
            quantidade = form.cleaned_data['quantidade']
            primeiro_vencimento = form.cleaned_data['primeiro_vencimento']

            with transaction.atomic():
                conta_bloqueada = ContaReceber.objects.select_for_update().get(
                    pk=conta.pk
                )

                if conta_bloqueada.parcelas.exists():
                    messages.error(
                        request,
                        'Esta conta já possui parcelas cadastradas.'
                    )
                    return redirect(
                        'financeiro:detalhe_conta_receber',
                        conta_id=conta.pk
                    )

                # Converte o total para centavos para evitar
                # diferenças de arredondamento.
                total_centavos = int(
                    (conta_bloqueada.valor_total * 100).quantize(
                        Decimal('1'),
                        rounding=ROUND_HALF_UP
                    )
                )

                valor_base, resto = divmod(total_centavos, quantidade)

                parcelas = []

                for indice in range(quantidade):
                    # Distribui os centavos restantes nas primeiras parcelas.
                    valor_centavos = valor_base + (1 if indice < resto else 0)
                    valor = Decimal(valor_centavos) / Decimal('100')

                    mes_indice = (
                        primeiro_vencimento.month - 1 + indice
                    )
                    ano = primeiro_vencimento.year + mes_indice // 12
                    mes = mes_indice % 12 + 1

                    # Ajusta, por exemplo, dia 31 para o último dia do mês.
                    dia = min(
                        primeiro_vencimento.day,
                        monthrange(ano, mes)[1]
                    )
                    vencimento = date(ano, mes, dia)

                    parcelas.append(
                        ParcelaReceber(
                            conta=conta_bloqueada,
                            numero=indice + 1,
                            valor=valor,
                            data_vencimento=vencimento,
                        )
                    )

                ParcelaReceber.objects.bulk_create(parcelas)

            messages.success(
                request,
                'Parcelas geradas com sucesso!'
            )
            return redirect(
                'financeiro:detalhe_conta_receber',
                conta_id=conta.pk
            )
    else:
        form = GerarParcelasForm()

    return render(
        request,
        'financeiro/gerar_parcelas.html',
        {'conta': conta, 'form': form}
    )


def detalhe_conta_receber(request, conta_id):
    conta = get_object_or_404(
        ContaReceber.objects.prefetch_related(
            'parcelas__recebimentos'
        ).select_related('paciente'),
        pk=conta_id
    )

    return render(
    request,
    'financeiro/detalhe_conta_receber.html',
    {
        'conta': conta,
        'hoje': timezone.localdate(),
    }
)


def registrar_recebimento(request, parcela_id):
    if request.method != 'POST':
        return redirect('financeiro:contas_receber')

    with transaction.atomic():
        parcela = get_object_or_404(
            ParcelaReceber.objects.select_for_update().select_related('conta'),
            pk=parcela_id
        )

        form = RecebimentoForm(request.POST)

        if form.is_valid():
            # Calcula o saldo dentro da transação para validar
            # o pagamento contra os recebimentos já registrados.
            total_recebido = parcela.recebimentos.aggregate(
                total=Sum('valor')
            )['total'] or Decimal('0.00')

            saldo = parcela.valor - total_recebido
            valor_pagamento = form.cleaned_data['valor']

            if valor_pagamento <= 0:
                messages.error(
                    request,
                    'O valor do recebimento deve ser maior que zero.'
                )
            elif valor_pagamento > saldo:
                messages.error(
                    request,
                    f'O recebimento ultrapassa o saldo da parcela '
                    f'(R$ {saldo:.2f}).'
                )
            else:
                recebimento = form.save(commit=False)
                recebimento.parcela = parcela
                recebimento.save()

                messages.success(
                    request,
                    'Recebimento registrado com sucesso!'
                )
        else:
            messages.error(
                request,
                'Confira os dados informados para o recebimento.'
            )

    return redirect(
        'financeiro:detalhe_conta_receber',
        conta_id=parcela.conta_id
    )
