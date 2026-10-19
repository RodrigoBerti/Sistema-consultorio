
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def inicio(request):
    return HttpResponse("""
        <h1>Sistema do Consultório Odontológico</h1>
        <p>Bem-vindo ao sistema de gestão!</p>
        <ul>
            <li><a href="/admin/">Administração</a></li>
            <li><a href="/pacientes/">Pacientes</a></li>
            <li><a href="/financeiro/">Financeiro</a></li>
        </ul>
    """)


urlpatterns = [
    path('', inicio, name='inicio'),
    path('admin/', admin.site.urls),
    path('pacientes/', include('pacientes.urls')),
    path('financeiro/', include('financeiro.urls')),
]
