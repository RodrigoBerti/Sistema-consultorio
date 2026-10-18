
from django.contrib import admin
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'cpf',
        'telefone',
        'email',
        'ativo',
        'data_cadastro',
    )

    search_fields = ('nome', 'cpf', 'telefone')
    list_filter = ('ativo', 'data_cadastro')
