from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse, HttpResponse
from .models import Agendamento, Veiculo
from .forms import CadastroVeiculo, EdicaoForm
from PIL import Image
import json
import io
import random

def is_gestor(user):
    return user.groups.filter(name='Gestores').exists() or user.is_superuser

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
        passageiros = request.POST.get('passageiros')

        # Verifica se todos os campos vieram preenchidos
        if all([motorista, dataHoraPartida, dataHoraChegada, destino, passageiros]):
            
            partida_dt = parse_datetime(dataHoraPartida)
            chegada_dt = parse_datetime(dataHoraChegada)

            # Converte a data do HTML (sem fuso) para uma data compatível com o Banco de Dados (com fuso)
            if partida_dt and timezone.is_naive(partida_dt):
                partida_dt = timezone.make_aware(partida_dt)
                
            if chegada_dt and timezone.is_naive(chegada_dt):
                chegada_dt = timezone.make_aware(chegada_dt)

            if partida_dt and chegada_dt and partida_dt >= chegada_dt:
                erro = 'A data da volta deve ser posterior à data de partida.'
                return render(request, 'partials/error.html', {'erro': erro})

            # Inicia o bloco seguro para o banco de dados
            with transaction.atomic():
                # 1. Busca os agendamentos conflitantes diretamente
                conflitos = Agendamento.objects.filter(
                    dataPartida__lt=chegada_dt,
                    dataChegada__gt=partida_dt
                )

                # Extrai os IDs dos carros ocupados de forma limpa pelo Python
                ids_ocupados = [ag.veiculo_id for ag in conflitos if ag.veiculo_id]

                # 2. Resgata todos os veículos e retira os ocupados via Python (foge de bugs do SQLite)
                todos_veiculos = Veiculo.objects.all()
                veiculos_livres = [v for v in todos_veiculos if v.id not in ids_ocupados]
                
                veiculo_escolhido = random.choice(veiculos_livres) if veiculos_livres else None

                # 3. Se não achar nenhum veículo, devolve o partial de erro
                if not veiculo_escolhido:
                    erro = 'Não há veículos disponíveis para o horário selecionado.'
                    return render(request, 'partials/error.html', {'erro': erro})

                # 4. Se achou, cria o agendamento associando o veículo sorteado
                agendamento = Agendamento.objects.create(
                    veiculo=veiculo_escolhido,
                    motorista=motorista, 
                    dataPartida=partida_dt, 
                    dataChegada=chegada_dt, 
                    destino=destino,
                    passageiros=passageiros,
                    usuario=request.user
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
            
            if not (is_gestor(request.user) or (hasattr(agendamento, 'usuario') and agendamento.usuario == request.user)):
                return JsonResponse({'status': 'erro', 'mensagem': 'Você não tem permissão para alterar este agendamento.'}, status=403)

            novo_inicio = parse_datetime(dados.get('start'))
            novo_fim = parse_datetime(dados.get('end')) if dados.get('end') else None

            if not novo_fim:
                duracao = agendamento.dataChegada - agendamento.dataPartida
                novo_fim = novo_inicio + duracao

            if agendamento.veiculo:
                conflitos = Agendamento.objects.filter(
                    veiculo=agendamento.veiculo,
                    dataPartida__lt=novo_fim,
                    dataChegada__gt=novo_inicio
                ).exclude(id=agendamento.id)
                
                if conflitos.exists():
                    return JsonResponse({'status': 'erro', 'mensagem': 'O veículo já possui agendamento neste horário.'}, status=400)

            agendamento.dataPartida = novo_inicio
            agendamento.dataChegada = novo_fim
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
            'extendedProps': {
                'pode_editar': is_gestor(request.user) or (hasattr(agendamento, 'usuario') and agendamento.usuario == request.user)
            }
        })

    return JsonResponse(eventos, safe=False)

@login_required
def remover_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    
    if not (is_gestor(request.user) or (hasattr(agendamento, 'usuario') and agendamento.usuario == request.user)):
        return HttpResponse('Você não tem permissão para excluir este agendamento.', status=403)

    agendamento.delete()
    response = HttpResponse('')
    response['HX-Trigger'] = 'atualizarCalendario'
    return response

@login_required
def editar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)

    if not (is_gestor(request.user) or (hasattr(agendamento, 'usuario') and agendamento.usuario == request.user)):
        return HttpResponse('Você não tem permissão para editar este agendamento.', status=403)

    if request.method == 'POST':
        form = EdicaoForm(request.POST, instance=agendamento)
        
        if form.is_valid():
            dataPartida = form.cleaned_data['dataPartida']
            dataChegada = form.cleaned_data['dataChegada']

            if dataPartida >= dataChegada:
                form.add_error(None, 'A data de partida deve ser menor que a data de chegada.')
                return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})

            # Verifica se o novo horário ou novo veículo conflita com outro agendamento já existente
            if agendamento.veiculo:
                conflitos = Agendamento.objects.filter(
                    veiculo=agendamento.veiculo,
                    dataPartida__lt=dataChegada,
                    dataChegada__gt=dataPartida
                ).exclude(pk=pk) # Exclui a verificação de conflito consigo mesmo
            
                if conflitos.exists():
                    form.add_error(None, 'O veículo já possui agendamento neste horário.')
                    return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})
            
            form.save()
            response = HttpResponse()
            response['HX-Trigger'] = 'atualizarCalendario, closeModalEdicao' 
            return response
        else:
            return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})
    else:
        form = EdicaoForm(instance=agendamento)
    
    return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})

@login_required
@user_passes_test(is_gestor, login_url='/')
def veiculos(request):
    todos_veiculos = Veiculo.objects.all()

    if request.method == 'POST':
        form = CadastroVeiculo(request.POST, request.FILES)
        
        if form.is_valid():
            novo_veiculo = form.save(commit=False)
            
            foto_enviada = request.FILES.get('foto')
            
            if foto_enviada:
                img = Image.open(foto_enviada)
                
                img = img.convert('RGB')                
                img = img.resize((250, 200), Image.LANCZOS)
                
                temp_thumb = io.BytesIO()
                img.save(temp_thumb, format='JPEG', quality=90)
                temp_thumb.seek(0)

                novo_veiculo.foto.save(foto_enviada.name, ContentFile(temp_thumb.read()), save=False)
            

            novo_veiculo.save()
            return redirect('veiculos')

    else:
        form = CadastroVeiculo()

    return render(request, 'veiculos.html', {'veiculos': todos_veiculos, 'form': form})

@login_required
@user_passes_test(is_gestor, login_url='/')
@require_POST
def remover_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    veiculo.delete()
    return HttpResponse('')

@login_required
@user_passes_test(is_gestor, login_url='/')
@require_POST
def editar_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    form = CadastroVeiculo(request.POST, request.FILES, instance=veiculo)

    if form.is_valid():
        form.save()
        resposta = HttpResponse()
        resposta['HX-Refresh'] = 'true'
        return resposta
    
    return HttpResponse('Erro ao validar formulário. Feche e tente novamente.', status=400)

@login_required
def viagens(request):
    hora_atual = timezone.now().timestamp()

    q = request.GET.get('q', '').strip()
    if q:
        proximas_viagens = Agendamento.objects.filter(id=q)
    else:
        proximas_viagens = Agendamento.objects.filter(dataPartida__gt=timezone.now()).order_by('dataPartida')

    veiculos = Veiculo.objects.all()

    for viagem in proximas_viagens:
        email_criador_do_evento = viagem.usuario.email if viagem.usuario else "notfound@gmail.com"
        if viagem.veiculo and viagem.veiculo.placa and viagem.dataPartida:
            placa_final = str(viagem.veiculo.placa)[-1]
            dia_semana = viagem.dataPartida.weekday() # 0 = Segunda, 6 = Domingo
            
            # Regras de rodízio de São Paulo
            rodizio_sp = {
                0: ['1', '2'], # Segunda-feira
                1: ['3', '4'], # Terça-feira
                2: ['5', '6'], # Quarta-feira
                3: ['7', '8'], # Quinta-feira
                4: ['9', '0'], # Sexta-feira
            }
            
            placas_proibidas = rodizio_sp.get(dia_semana, [])
            viagem.em_rodizio = placa_final in placas_proibidas

            hora_viagem = viagem.dataPartida.timestamp()

    return render(request, 'viagens.html', {'proximas_viagens': proximas_viagens, 'veiculos': veiculos, 'hora_atual': hora_atual, 'hora_viagem': hora_viagem, 'email_criador_do_evento': email_criador_do_evento})

@login_required
@user_passes_test(is_gestor, login_url='/')
def alterar_veiculo(request, pk):
    if request.method == 'POST':
        veiculo_id = request.POST.get('selectVeiculos')
        
        agendamento = get_object_or_404(Agendamento, pk=pk)
        agendamento.veiculo_id = veiculo_id
        agendamento.save()

        resposta = HttpResponse()
        resposta['HX-Refresh'] = 'true'
        return resposta

@login_required
@user_passes_test(is_gestor, login_url='/')
def historico(request):
    todas_as_viagens = Agendamento.objects.all().order_by('dataPartida').reverse()        

    return render(request, 'historico.html', {'todas_as_viagens': todas_as_viagens})