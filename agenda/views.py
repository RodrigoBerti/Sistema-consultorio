from django.shortcuts import render


def calendario(request):
    return render(request, 'agenda/calendario.html')