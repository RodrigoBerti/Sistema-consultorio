
from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import ConsultaForm
from .models import Consulta


def calendario(request):
    hoje = timezone.localdate()

    data_parametro = parse_date(request.GET.get('data', ''))
    data_referencia = data_parametro or hoje

    inicio_semana = data_referencia - timedelta(
        days=data_referencia.weekday()
    )
    fim_semana = inicio_semana + timedelta(days=6)

    consultas = Consulta.objects.filter(
        data__range=(inicio_semana, fim_semana)
    ).select_related('paciente').order_by(
        'data', 'hora_inicio'
    )

    dias = []

    for indice in range(7):
        data_dia = inicio_semana + timedelta(days=indice)

        dias.append({
            'data': data_dia,
            'nome': [
                'Segunda-feira',
                'Terça-feira',
                'Quarta-feira',
                'Quinta-feira',
                'Sexta-feira',
                'Sábado',
                'Domingo',
            ][indice],
            'consultas': [],
        })

    inicio_exibicao = time(8, 0)
    minutos_exibidos = 11 * 60
    pixels_por_hora = 60

    for consulta in consultas:
        minutos_inicio = (
            consulta.hora_inicio.hour * 60
            + consulta.hora_inicio.minute
        )
        minutos_base = (
            inicio_exibicao.hour * 60
            + inicio_exibicao.minute
        )

        topo = (
            minutos_inicio - minutos_base
        ) * pixels_por_hora / 60

        altura = (
            consulta.duracao_minutos
            * pixels_por_hora / 60
        )

        # A grade visual começa às 08h e termina às 18h.
        if topo + altura <= 0 or topo >= minutos_exibidos:
            continue

        topo = max(0, topo)
        altura = min(
            altura,
            minutos_exibidos - topo
        )

        if altura <= 0:
            continue

        dias[consulta.data.weekday()]['consultas'].append({
            'objeto': consulta,
            'topo': topo,
            'altura': altura,
            'cor': {
                Consulta.Status.AGENDADA: '#a9def9',
                Consulta.Status.CONFIRMADA: '#80cbc4',
                Consulta.Status.CONCLUIDA: '#b7e4c7',
                Consulta.Status.CANCELADA: '#e0e0e0',
                Consulta.Status.FALTOU: '#f4a6a6',
            }.get(consulta.status, '#a9def9'),
        })

        horarios = [
            {
                'hora': time(hora, 0),
                'topo': (hora - 8) * 60,
            }
            for hora in range(8, 19)
        ]

    return render(
        request,
        'agenda/calendario.html',
        {
            'hoje': hoje,
            'inicio_semana': inicio_semana,
            'fim_semana': fim_semana,
            'semana_anterior': inicio_semana - timedelta(days=7),
            'proxima_semana': inicio_semana + timedelta(days=7),
            'dias': dias,
            'horarios': horarios,
            'altura_grade': minutos_exibidos,
        }
    )


def nova_consulta(request):
    if request.method == 'POST':
        form = ConsultaForm(request.POST)

        if form.is_valid():
            consulta = form.save()
            messages.success(
                request,
                'Consulta cadastrada com sucesso!'
            )
            return redirect(
                f"/agenda/?data={consulta.data.isoformat()}"
            )
    else:
        data_inicial = request.GET.get('data')
        initial = {}

        if data_inicial and parse_date(data_inicial):
            initial['data'] = parse_date(data_inicial)
        else:
            initial['data'] = timezone.localdate()

        initial['duracao_minutos'] = 30
        initial['status'] = Consulta.Status.AGENDADA

        form = ConsultaForm(initial=initial)

    return render(
        request,
        'agenda/form_consulta.html',
        {
            'form': form,
            'titulo': 'Nova consulta',
        }
    )
