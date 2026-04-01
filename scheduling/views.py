from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from .models import Agendamento

@login_required
def index(request):
    return render(request, 'index.html')
    
@login_required
def agendar(request):
    if request.method == 'POST':
        motorista = request.POST.get('motorista')
        dataHoraPartida = request.POST.get('dataHoraPartida')
        dataHoraChegada = request.POST.get('dataHoraChegada')
        destino = request.POST.get('destino')

        if all([motorista, dataHoraPartida, dataHoraChegada, destino]):
            agendamento = Agendamento.objects.create(motorista=motorista, dataPartida=dataHoraPartida, dataChegada=dataHoraChegada, destino=destino)
            resposta = render(request, 'partials/success.html', {'agendamento': agendamento})
            resposta['HX-Trigger'] = 'atualizarCalendario'
            return resposta
        else:
            erro = 'Por favor, preencha corretamente todos os campos.'
            return render(request, 'partials/error.html', {'erro': erro})
    
    return render(request, 'index.html')

@login_required
def listar_agendamentos(request):
    agendamentos = Agendamento.objects.all()

    eventos = []

    for agendamento in agendamentos:
        eventos.append({
            'id': agendamento.id,
            'title': agendamento.motorista,
            'start': agendamento.dataPartida.isoformat() if agendamento.dataPartida else None,
            'end': agendamento.dataChegada.isoformat() if agendamento.dataChegada else None,
        })

    return JsonResponse(eventos, safe=False)