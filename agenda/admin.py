from django.contrib import admin
from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = (
        'paciente',
        'data',
        'hora_inicio',
        'duracao_minutos',
        'procedimento',
        'status',
    )

    list_filter = ('status', 'data')
    search_fields = ('paciente__nome', 'procedimento')
    date_hierarchy = 'data'