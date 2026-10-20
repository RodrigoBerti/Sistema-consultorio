
from django import forms
from .models import ContaReceber
from decimal import Decimal

from .models import ContaReceber, ParcelaReceber, Recebimento

class ContaReceberForm(forms.ModelForm):
    class Meta:
        model = ContaReceber
        fields = [
            'paciente',
            'tipo',
            'descricao',
            'valor_total',
            'observacoes',
        ]

        widgets = {
            'paciente': forms.Select(attrs={
                'class': 'form-select',
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex.: Restauração dentária',
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0,00',
                'min': '0.01',
                'step': '0.01',
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações opcionais',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['paciente'].queryset = (
            self.fields['paciente'].queryset.filter(ativo=True)
        )

        self.fields['paciente'].empty_label = 'Selecione um paciente'

class GerarParcelasForm(forms.Form):
    quantidade = forms.IntegerField(
        label='Quantidade de parcelas',
        min_value=1,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 120,
        })
    )

    primeiro_vencimento = forms.DateField(
        label='Vencimento da primeira parcela',
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )


class RecebimentoForm(forms.ModelForm):
    class Meta:
        model = Recebimento
        fields = [
            'valor',
            'data_recebimento',
            'forma_pagamento',
            'observacoes',
        ]

        widgets = {
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': '0,00',
            }),
            'data_recebimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'forma_pagamento': forms.Select(attrs={
                'class': 'form-select',
            }),
            'observacoes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações opcionais',
            }),
        }