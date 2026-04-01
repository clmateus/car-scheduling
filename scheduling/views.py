from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from .models import Agendamento, Veiculo
from .forms import CadastroVeiculo, AgendamentoForm # Import AgendamentoForm
import json

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

        # Verifica se todos os campos vieram preenchidos
        if all([motorista, dataHoraPartida, dataHoraChegada, destino]):
            
            # Inicia o bloco seguro para o banco de dados
            with transaction.atomic():
                # 1. Busca os IDs dos veículos ocupados nesse horário
                agendamentos_conflitantes = Agendamento.objects.filter(
                    dataPartida__lt=dataHoraChegada,
                    dataChegada__gt=dataHoraPartida
                ).values('veiculo_id')

                # 2. Sorteia um veículo livre e bloqueia a linha no banco (evita double-booking)
                veiculo_escolhido = Veiculo.objects.exclude(
                    id__in=agendamentos_conflitantes
                ).select_for_update(skip_locked=True).order_by('?').first()

                # 3. Se não achar nenhum veículo, devolve o partial de erro
                if not veiculo_escolhido:
                    erro = 'Não há veículos disponíveis para o horário selecionado.'
                    return render(request, 'partials/error.html', {'erro': erro})

                # 4. Se achou, cria o agendamento associando o veículo sorteado
                agendamento = Agendamento.objects.create(
                    veiculo=veiculo_escolhido,
                    motorista=motorista, 
                    dataPartida=dataHoraPartida, 
                    dataChegada=dataHoraChegada, 
                    destino=destino
                )

            # Só chega aqui se o agendamento deu certo
            resposta = render(request, 'partials/success.html', {'agendamento': agendamento})
            resposta['HX-Trigger'] = 'atualizarCalendario'
            return resposta

        else:
            # Erro caso o usuário tenha deixado campos em branco
            erro = 'Por favor, preencha corretamente todos os campos.'
            return render(request, 'partials/error.html', {'erro': erro})
    
    return render(request, 'index.html')

@login_required
def mudar_dia_agendamento(request):
    if request.method == 'POST':
        dados = json.loads(request.body)
        try:
            agendamento = Agendamento.objects.get(id=dados.get('id'))
            agendamento.dataPartida = dados.get('start')
            agendamento.dataChegada = dados.get('end')
            agendamento.save()
            return JsonResponse({'status': 'sucesso'})
        except Agendamento.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': 'Agendamento não encontrado.'})
    return JsonResponse({'status': 'erro'}, status=400)

@login_required
def listar_agendamentos(request):
    agendamentos = Agendamento.objects.all()

    eventos = []

    for agendamento in agendamentos:
        eventos.append({
            'id': agendamento.id,
            'title': agendamento.motorista + ' -> ' + agendamento.destino,
            'start': agendamento.dataPartida.isoformat() if agendamento.dataPartida else None,
            'end': agendamento.dataChegada.isoformat() if agendamento.dataChegada else None,
        })

    return JsonResponse(eventos, safe=False)

@login_required
def remover_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    agendamento.delete() # Isso irá deletar o evento
    response = HttpResponse('')
    response['HX-Trigger'] = 'atualizarCalendario' # Dispara a atualização do calendário
    return response

# Nova view para editar agendamento
@login_required
def editar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)

    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            # Lógica para verificar disponibilidade do veículo pode ser adicionada aqui
            # Se as datas forem alteradas, seria ideal re-verificar se o veículo escolhido
            # ou um novo veículo está disponível. Por simplicidade, estamos apenas salvando.
            form.save()
            response = HttpResponse()
            # Dispara a atualização do calendário e um evento para fechar o modal de edição
            response['HX-Trigger'] = 'atualizarCalendario, closeModalEdicao' 
            return response
        else:
            # Se o formulário for inválido, renderiza o formulário novamente com erros
            return render(request, 'partials/agendamento_form.html', {'form': form, 'agendamento_id': pk})
    else:
        form = AgendamentoForm(instance=agendamento)
    
    return render(request, 'partials/agendamento_form.html', {'form': form, 'agendamento_id': pk})

@login_required
def veiculos(request):
    veiculos = Veiculo.objects.all()

    if request.method == 'POST':
        form = CadastroVeiculo(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('veiculos')

    else:
        form = CadastroVeiculo()

    return render(request, 'veiculos.html', {'veiculos': veiculos, 'form': form})

@login_required
@require_POST
def remover_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    veiculo.delete()
    return HttpResponse('')

@login_required
@require_POST
def editar_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    form = CadastroVeiculo(request.POST, instance=veiculo)

    if form.is_valid():
        form.save()
        resposta = HttpResponse()
        resposta['HX-Refresh'] = 'true'
        return resposta
    
    return HttpResponse('Erro ao validar formulário. Feche e tente novamente.', status=400)

@login_required
def viagens(request):
    proximas_viagens = Agendamento.objects.filter(dataPartida__gt=timezone.now()).order_by('dataPartida')
    return render(request, 'viagens.html', {'proximas_viagens': proximas_viagens})