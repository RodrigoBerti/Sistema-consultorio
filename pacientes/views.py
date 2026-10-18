
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from .models import Paciente
from .forms import PacienteForm


def listar_pacientes(request):
    busca = request.GET.get('busca', '').strip()

    pacientes = Paciente.objects.all()

    if busca:
        pacientes = pacientes.filter(
            Q(nome__icontains=busca) |
            Q(cpf__icontains=busca)
        )

    return render(
        request,
        'pacientes/listar.html',
        {
            'pacientes': pacientes,
            'busca': busca,
        }
    )


def criar_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente cadastrado com sucesso!')
            return redirect('pacientes:listar')
    else:
        form = PacienteForm()

    return render(
        request,
        'pacientes/formulario.html',
        {
            'form': form,
            'titulo': 'Novo paciente',
        }
    )


def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)

    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)

        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente atualizado com sucesso!')
            return redirect('pacientes:listar')
    else:
        form = PacienteForm(instance=paciente)

    return render(
        request,
        'pacientes/formulario.html',
        {
            'form': form,
            'titulo': 'Editar paciente',
        }
    )
