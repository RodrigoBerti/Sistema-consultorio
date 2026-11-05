from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML

from pacientes.models import Paciente


def gerar_ficha_anamnese(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)

    html = render_to_string(
        'documentos/ficha_anamnese.html',
        {'paciente': paciente}
    )

    pdf = HTML(
        string=html,
        base_url=request.build_absolute_uri('/')
    ).write_pdf()

    response = HttpResponse(
        pdf,
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'inline; filename="anamnese_{paciente.id}.pdf"'
    )

    return response