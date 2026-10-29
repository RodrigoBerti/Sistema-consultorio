
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from pacientes.models import Paciente


class Consulta(models.Model):

    class Status(models.TextChoices):
        AGENDADA = 'AGENDADA', 'Agendada'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        CONCLUIDA = 'CONCLUIDA', 'Concluída'
        CANCELADA = 'CANCELADA', 'Cancelada'
        FALTOU = 'FALTOU', 'Não compareceu'

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='consultas',
        verbose_name='Paciente'
    )

    data = models.DateField(
        verbose_name='Data da consulta'
    )

    hora_inicio = models.TimeField(
        verbose_name='Horário de início'
    )

    duracao_minutos = models.PositiveIntegerField(
        default=30,
        verbose_name='Duração em minutos'
    )

    procedimento = models.CharField(
        max_length=150,
        verbose_name='Procedimento'
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.AGENDADA,
        verbose_name='Status'
    )

    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )

    data_cadastro = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['data', 'hora_inicio']
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'

    def __str__(self):
        return (
            f'{self.paciente.nome} - '
            f'{self.data:%d/%m/%Y} '
            f'{self.hora_inicio:%H:%M}'
        )

    @property
    def hora_fim(self):
        inicio = datetime.combine(
            self.data,
            self.hora_inicio
        )
        fim = inicio + timedelta(
            minutes=self.duracao_minutos
        )
        return fim.time()
    
    @require_POST
    def alterar_status(request, consulta_id):
        consulta = get_object_or_404(Consulta, pk=consulta_id)

        novo_status = request.POST.get('status', '')
        campo_status = Consulta._meta.get_field('status')
        status_validos = dict(campo_status.choices)

        if novo_status not in status_validos:
            messages.error(request, 'Status inválido.')
            return redirect('agenda:calendario')

        consulta.status = novo_status
        consulta.save(update_fields=['status'])

        messages.success(
            request,
            f'Status da consulta atualizado para "{status_validos[novo_status]}".'
        )

        return redirect('agenda:calendario')
    
