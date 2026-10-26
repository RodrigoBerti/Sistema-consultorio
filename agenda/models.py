
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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
