
from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from pacientes.models import Paciente
from .models import Consulta


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = [
            'paciente',
            'data',
            'hora_inicio',
            'duracao_minutos',
            'procedimento',
            'status',
            'observacoes',
        ]

        widgets = {
            'paciente': forms.Select(attrs={
                'class': 'form-select',
            }),
            'data': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'hora_inicio': forms.TimeInput(
                format='%H:%M',
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                }
            ),
            'duracao_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'step': 15,
            }),
            'procedimento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex.: limpeza, avaliação, restauração',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        data = cleaned_data.get('data')
        hora_inicio = cleaned_data.get('hora_inicio')
        duracao = cleaned_data.get('duracao_minutos')
        consulta_id = self.instance.pk

        if not data or not hora_inicio or not duracao:
            return cleaned_data

        if duracao < 15 or duracao > 480:
            self.add_error(
                'duracao_minutos',
                'A duração deve ser entre 15 e 480 minutos.'
            )
            return cleaned_data

        inicio = datetime.combine(data, hora_inicio)
        fim = inicio + timedelta(minutes=duracao)

        if fim.date() != data:
            self.add_error(
                'duracao_minutos',
                'A consulta deve terminar no mesmo dia.'
            )
            return cleaned_data

        # Consultas canceladas não bloqueiam o horário.
        consultas_do_dia = Consulta.objects.filter(
            data=data
        ).exclude(
            status=Consulta.Status.CANCELADA
        )

        if consulta_id:
            consultas_do_dia = consultas_do_dia.exclude(
                pk=consulta_id
            )

        for existente in consultas_do_dia:
            inicio_existente = datetime.combine(
                existente.data,
                existente.hora_inicio
            )
            fim_existente = inicio_existente + timedelta(
                minutes=existente.duracao_minutos
            )

            if inicio < fim_existente and fim > inicio_existente:
                raise forms.ValidationError(
                    'Esse horário conflita com outra consulta '
                    f'({existente.hora_inicio:%H:%M} - '
                    f'{fim_existente:%H:%M}). Escolha outro horário.'
                )

        return cleaned_data
