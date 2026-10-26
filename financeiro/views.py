
from django.shortcuts import render,redirect, get_object_or_404
from django.db.models import Sum
from django.db.models import DecimalField
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date

from .models import (
    ContaReceber,
    Despesa,
    PagamentoDespesa,
    ParcelaReceber,
    Recebimento,
)

from .forms import (
    ContaReceberForm,
    DespesaForm,
    PagamentoDespesaForm,
    GerarParcelasForm,
    RecebimentoForm,
)

from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange
from datetime import date

from django.db import transaction
from django.contrib import messages
from django.utils import timezone

from .models import ContaReceber, ParcelaReceber, Recebimento
from .forms import GerarParcelasForm, RecebimentoForm

def inicio_financeiro(request):
    return render(
        request,
        'financeiro/inicio_financeiro.html'
    )

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

    
def painel_financeiro(request):
    hoje = timezone.localdate()

    # Define o período padrão: mês atual.
    inicio_padrao = hoje.replace(day=1)
    fim_padrao = hoje.replace(
        day=monthrange(hoje.year, hoje.month)[1]
    )

    inicio = parse_date(request.GET.get('inicio', '')) or inicio_padrao
    fim = parse_date(request.GET.get('fim', '')) or fim_padrao

    if inicio > fim:
        inicio, fim = fim, inicio

    campo_decimal = DecimalField(
        max_digits=14,
        decimal_places=2
    )

    zero = Decimal('0.00')

    # Valores recebidos dentro do período selecionado.
    total_recebido = Recebimento.objects.filter(
        data_recebimento__range=(inicio, fim)
    ).aggregate(
        total=Coalesce(
            Sum('valor'),
            zero,
            output_field=campo_decimal
        )
    )['total']

    # Despesas efetivamente pagas dentro do período.
    total_pago = PagamentoDespesa.objects.filter(
        data_pagamento__range=(inicio, fim)
    ).aggregate(
        total=Coalesce(
            Sum('valor'),
            zero,
            output_field=campo_decimal
        )
    )['total']

    # Total contratado nas contas a receber.
    total_contas = ContaReceber.objects.aggregate(
        total=Coalesce(
            Sum('valor_total'),
            zero,
            output_field=campo_decimal
        )
    )['total']

    # Total recebido em todas as datas.
    recebimentos_gerais = Recebimento.objects.aggregate(
        total=Coalesce(
            Sum('valor'),
            zero,
            output_field=campo_decimal
        )
    )['total']

    total_a_receber = total_contas - recebimentos_gerais

    # Total de despesas cadastradas.
    total_despesas = Despesa.objects.aggregate(
        total=Coalesce(
            Sum('valor'),
            zero,
            output_field=campo_decimal
        )
    )['total']

    # Total pago em todas as datas.
    pagamentos_gerais = PagamentoDespesa.objects.aggregate(
        total=Coalesce(
            Sum('valor'),
            zero,
            output_field=campo_decimal
        )
    )['total']

    total_a_pagar = total_despesas - pagamentos_gerais

    # Resultado das movimentações do período.
    resultado_periodo = total_recebido - total_pago

    # Quantidade de contas vencidas e ainda não quitadas.
    contas_receber_vencidas = 0

    for conta in ContaReceber.objects.prefetch_related(
        'parcelas__recebimentos'
    ):
        for parcela in conta.parcelas.all():
            recebido_parcela = sum(
                (r.valor for r in parcela.recebimentos.all()),
                zero
            )

            if (
                parcela.data_vencimento < hoje
                and recebido_parcela < parcela.valor
            ):
                contas_receber_vencidas += 1

    despesas_vencidas = 0

    for despesa in Despesa.objects.prefetch_related('pagamentos'):
        if (
            despesa.data_vencimento < hoje
            and despesa.saldo_devedor > 0
        ):
            despesas_vencidas += 1

    return render(
        request,
        'financeiro/painel.html',
        {
            'inicio': inicio,
            'fim': fim,
            'total_recebido': total_recebido,
            'total_pago': total_pago,
            'total_a_receber': total_a_receber,
            'total_a_pagar': total_a_pagar,
            'resultado_periodo': resultado_periodo,
            'total_contas': total_contas,
            'total_despesas': total_despesas,
            'contas_receber_vencidas': contas_receber_vencidas,
            'despesas_vencidas': despesas_vencidas,
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


def listar_contas_pagar(request):
    despesas = Despesa.objects.prefetch_related(
        'pagamentos'
    ).all().order_by('data_vencimento', 'descricao')

    hoje = timezone.localdate()

    for despesa in despesas:
        if despesa.saldo_devedor <= 0:
            despesa.situacao = 'Paga'
        elif despesa.total_pago > 0:
            despesa.situacao = 'Parcial'
        elif despesa.data_vencimento < hoje:
            despesa.situacao = 'Vencida'
        else:
            despesa.situacao = 'Pendente'

    return render(
        request,
        'financeiro/contas_pagar.html',
        {
            'despesas': despesas,
            'hoje': hoje,
        }
    )


def criar_despesa(request):
    if request.method == 'POST':
        form = DespesaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Despesa cadastrada com sucesso!'
            )
            return redirect('financeiro:contas_pagar')
    else:
        form = DespesaForm()

    return render(
        request,
        'financeiro/form_despesa.html',
        {
            'form': form,
            'titulo': 'Nova conta a pagar',
        }
    )


def registrar_pagamento_despesa(request, despesa_id):
    if request.method != 'POST':
        return redirect('financeiro:contas_pagar')

    with transaction.atomic():
        despesa = get_object_or_404(
            Despesa.objects.select_for_update(),
            pk=despesa_id
        )

        form = PagamentoDespesaForm(request.POST)

        if form.is_valid():
            total_pago = despesa.pagamentos.aggregate(
                total=Sum('valor')
            )['total'] or Decimal('0.00')

            saldo = despesa.valor - total_pago
            valor_pagamento = form.cleaned_data['valor']

            if saldo <= 0:
                messages.error(
                    request,
                    'Esta despesa já está totalmente paga.'
                )
            elif valor_pagamento > saldo:
                messages.error(
                    request,
                    f'O pagamento ultrapassa o saldo pendente '
                    f'(R$ {saldo:.2f}).'
                )
            else:
                pagamento = form.save(commit=False)
                pagamento.despesa = despesa
                pagamento.save()

                messages.success(
                    request,
                    'Pagamento registrado com sucesso!'
                )
        else:
            messages.error(
                request,
                'Confira os dados informados para o pagamento.'
            )

    return redirect('financeiro:contas_pagar')
