from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.storage import FileSystemStorage
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django_q.tasks import async_task
from django.contrib import messages
from .models import *
from .forms import *
from PIL import Image
from django.conf import settings
import json
import io, os
import random

def is_gestor(user):
    return user.groups.filter(name='Gestores').exists() or user.is_superuser

def index(request):
    return render(request, 'index.html')

@login_required
def agendamento(request):
    return render(request, 'transporte/agendamento.html')

@login_required
def agendar(request):
    if request.method == 'POST':
        motorista = request.POST.get('motorista')
        dataHoraPartida = request.POST.get('dataHoraPartida')
        dataHoraChegada = request.POST.get('dataHoraChegada')
        destino = request.POST.get('destino')
        passageiros = request.POST.get('passageiros')

        if not all([motorista, dataHoraPartida, dataHoraChegada, destino, passageiros]):
            erro = 'Por favor, preencha corretamente todos os campos.'
            return render(request, 'partials/error.html', {'erro': erro})

        partida_dt = parse_datetime(dataHoraPartida)
        chegada_dt = parse_datetime(dataHoraChegada)

        # Converte a data do HTML (sem fuso) para uma data compatível com o banco (com fuso)
        if partida_dt and timezone.is_naive(partida_dt):
            partida_dt = timezone.make_aware(partida_dt)
        if chegada_dt and timezone.is_naive(chegada_dt):
            chegada_dt = timezone.make_aware(chegada_dt)

        if partida_dt and chegada_dt and partida_dt >= chegada_dt:
            erro = 'A data da volta deve ser posterior à data de partida.'
            return render(request, 'partials/error.html', {'erro': erro})

        with transaction.atomic():
            # Busca veículos ocupados no intervalo e exclui da seleção
            ids_ocupados = list(
                Agendamento.objects.filter(
                    dataPartida__lt=chegada_dt,
                    dataChegada__gt=partida_dt,
                    veiculo__isnull=False
                ).values_list('veiculo_id', flat=True)
            )
            veiculos_livres = list(Veiculo.objects.exclude(id__in=ids_ocupados))

            if not veiculos_livres:
                erro = 'Não há veículos disponíveis para o horário selecionado.'
                return render(request, 'partials/error.html', {'erro': erro})

            agendamento = Agendamento.objects.create(
                veiculo=random.choice(veiculos_livres),
                motorista=motorista,
                dataPartida=partida_dt,
                dataChegada=chegada_dt,
                destino=destino,
                passageiros=passageiros,
                usuario=request.user
            )

        resposta = render(request, 'partials/success.html', {'agendamento': agendamento})
        resposta['HX-Trigger'] = 'atualizarCalendario'

        async_task(
            send_mail,
            "Agendamento de Viagem",
            (
                f"O seu agendamento com destino a {agendamento.destino} foi realizado com sucesso.\n"
                f"Data e hora de partida: {agendamento.dataPartida.strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"Data e hora de chegada: {agendamento.dataChegada.strftime('%d/%m/%Y %H:%M:%S')}\n"
                "Chegue na expedição com 10 minutos de antecedência.\nDirija com responsabilidade."
            ),
            "lanmax.carscheduling@gmail.com",
            [agendamento.usuario.email],
            fail_silently=False
        )

        return resposta

    return render(request, 'agendamento.html')

@login_required
def mudar_dia_agendamento(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'erro'}, status=400)

    dados = json.loads(request.body)
    try:
        agendamento = Agendamento.objects.get(id=dados.get('id'))
    except Agendamento.DoesNotExist:
        return JsonResponse({'status': 'erro', 'mensagem': 'Agendamento não encontrado.'})

    if not (is_gestor(request.user) or agendamento.usuario == request.user):
        return JsonResponse({'status': 'erro', 'mensagem': 'Você não tem permissão para alterar este agendamento.'}, status=403)

    novo_inicio = parse_datetime(dados.get('start'))
    novo_fim = parse_datetime(dados.get('end')) if dados.get('end') else novo_inicio + (agendamento.dataChegada - agendamento.dataPartida)

    if agendamento.veiculo:
        conflito = Agendamento.objects.filter(
            veiculo=agendamento.veiculo,
            dataPartida__lt=novo_fim,
            dataChegada__gt=novo_inicio
        ).exclude(id=agendamento.id).exists()

        if conflito:
            return JsonResponse({'status': 'erro', 'mensagem': 'O veículo já possui agendamento neste horário.'}, status=400)

    agendamento.dataPartida = novo_inicio
    agendamento.dataChegada = novo_fim
    agendamento.save()
    return JsonResponse({'status': 'sucesso'})

@login_required
def listar_agendamentos(request):
    agendamentos = Agendamento.objects.all()
    eventos = [
        {
            'id': ag.id,
            'title': f'{ag.motorista} -> {ag.destino}',
            'start': ag.dataPartida.isoformat() if ag.dataPartida else None,
            'end': ag.dataChegada.isoformat() if ag.dataChegada else None,
            'extendedProps': {
                'pode_editar': is_gestor(request.user) or ag.usuario == request.user
            }
        }
        for ag in agendamentos
    ]
    return JsonResponse(eventos, safe=False)

@login_required
def remover_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)

    if not (is_gestor(request.user) or agendamento.usuario == request.user):
        return HttpResponse('Você não tem permissão para excluir este agendamento.', status=403)

    agendamento.delete()
    response = HttpResponse('')
    response['HX-Trigger'] = 'atualizarCalendario'

    async_task(
        send_mail,
        "Cancelamento de Viagem",
        f"O seu agendamento com destino a {agendamento.destino} foi cancelado com sucesso.",
        "lanmax.carscheduling@gmail.com",
        [agendamento.usuario.email],
        fail_silently=False
    )

    return response

@login_required
def editar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)

    if not (is_gestor(request.user) or agendamento.usuario == request.user):
        return HttpResponse('Você não tem permissão para editar este agendamento.', status=403)

    if request.method == 'POST':
        form = EdicaoForm(request.POST, instance=agendamento)

        if form.is_valid():
            dataPartida = form.cleaned_data['dataPartida']
            dataChegada = form.cleaned_data['dataChegada']

            if dataPartida >= dataChegada:
                form.add_error(None, 'A data de partida deve ser menor que a data de chegada.')
                return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})

            if agendamento.veiculo:
                conflito = Agendamento.objects.filter(
                    veiculo=agendamento.veiculo,
                    dataPartida__lt=dataChegada,
                    dataChegada__gt=dataPartida
                ).exclude(pk=pk).exists()

                if conflito:
                    form.add_error(None, 'O veículo já possui agendamento neste horário.')
                    return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})

            form.save()
            response = HttpResponse()
            response['HX-Trigger'] = 'atualizarCalendario, closeModalEdicao'

            async_task(
                send_mail,
                "Atualização de Viagem",
                (
                    f"O seu agendamento com destino a {agendamento.destino} foi atualizado com sucesso.\n"
                    f"Data e hora de partida: {agendamento.dataPartida.strftime('%d/%m/%Y %H:%M:%S')}\n"
                    f"Data e hora de chegada: {agendamento.dataChegada.strftime('%d/%m/%Y %H:%M:%S')}\n"
                    "Chegue na expedição com 10 minutos de antecedência.\nDirija com responsabilidade."
                ),
                "lanmax.carscheduling@gmail.com",
                [agendamento.usuario.email],
                fail_silently=False
            )

            return response

        return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})

    form = EdicaoForm(instance=agendamento)
    return render(request, 'edicao_form.html', {'form': form, 'agendamento_id': pk})

@login_required
def veiculos(request):
    if request.method == 'POST':
        form = CadastroVeiculo(request.POST, request.FILES)

        if form.is_valid():
            novo_veiculo = form.save(commit=False)
            foto_enviada = request.FILES.get('foto')

            if foto_enviada:
                img = Image.open(foto_enviada).convert('RGB').resize((250, 200), Image.LANCZOS)
                temp_thumb = io.BytesIO()
                img.save(temp_thumb, format='JPEG', quality=90)
                temp_thumb.seek(0)
                novo_veiculo.foto.save(foto_enviada.name, ContentFile(temp_thumb.read()), save=False)

            novo_veiculo.save()
            return redirect('veiculos')
    else:
        form = CadastroVeiculo()

    return render(request, 'transporte/veiculos.html', {'veiculos': Veiculo.objects.all(), 'form': form})

@login_required
@require_POST
def remover_veiculo(request, pk):
    get_object_or_404(Veiculo, pk=pk).delete()
    return HttpResponse('')

@login_required
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
    hora_viagem = None
    email_criador_do_evento = None

    q = request.GET.get('q', '').strip()
    proximas_viagens = (
        Agendamento.objects.filter(id=q) if q
        else Agendamento.objects.filter(dataPartida__gt=timezone.now()).order_by('dataPartida')
    )

    # Regras de rodízio de São Paulo (dígitos proibidos por dia da semana)
    RODIZIO_SP = {0: ['1', '2'], 1: ['3', '4'], 2: ['5', '6'], 3: ['7', '8'], 4: ['9', '0']}

    for viagem in proximas_viagens:
        email_criador_do_evento = viagem.usuario.email if viagem.usuario else "notfound@gmail.com"
        if viagem.veiculo and viagem.veiculo.placa and viagem.dataPartida:
            placa_final = str(viagem.veiculo.placa)[-1]
            viagem.em_rodizio = placa_final in RODIZIO_SP.get(viagem.dataPartida.weekday(), [])
            hora_viagem = viagem.dataPartida.timestamp()

    return render(request, 'transporte/viagens.html', {
        'proximas_viagens': proximas_viagens,
        'veiculos': Veiculo.objects.all(),
        'hora_atual': hora_atual,
        'hora_viagem': hora_viagem,
        'email_criador_do_evento': email_criador_do_evento,
    })

@login_required
def alterar_veiculo(request, pk):
    if request.method == 'POST':
        agendamento = get_object_or_404(Agendamento, pk=pk)
        agendamento.veiculo_id = request.POST.get('selectVeiculos')
        agendamento.save()
        resposta = HttpResponse()
        resposta['HX-Refresh'] = 'true'
        return resposta

@login_required
def historico(request):
    todas_as_viagens = Agendamento.objects.order_by('-dataPartida')
    return render(request, 'transporte/historico_veiculos.html', {'todas_as_viagens': todas_as_viagens})

@login_required
def carregar_aba(request, aba, veiculo_id):
    """Carrega o conteúdo da aba solicitada via HTMX."""
    veiculo = get_object_or_404(Veiculo, id=veiculo_id)

    templates = {
        'identificacao': 'transporte/tab/identificacao.html',
        'documentacao': 'transporte/tab/documentacao.html',
        'info': 'transporte/tab/info.html',
        'comentarios': 'transporte/tab/comentarios.html',
    }
    context = {'veiculo': veiculo, 'veiculo_id': veiculo_id}

    if aba == 'documentacao':
        context['seguro'] = Seguro.objects.filter(veiculo=veiculo).first()

    if aba == 'comentarios':
        context['observacoes'] = Info.objects.filter(veiculo=veiculo).order_by('-id')

    return render(request, templates.get(aba, 'transporte/tab/identificacao.html'), context)

@login_required
def salvar_aba_identificacao(request, veiculo_id):
    """Salva os dados da aba Identificação."""
    if request.method != 'POST':
        return HttpResponse(status=400)

    veiculo = get_object_or_404(Veiculo, id=veiculo_id)

    veiculo.modelo = request.POST.get('modelo', veiculo.modelo)
    veiculo.marca = request.POST.get('marca', veiculo.marca)
    veiculo.placa = request.POST.get('placa', veiculo.placa)
    veiculo.ano = request.POST.get('ano', veiculo.ano) or None
    veiculo.cor = request.POST.get('cor', veiculo.cor)
    veiculo.chassi = request.POST.get('chassi', veiculo.chassi)
    veiculo.renavam = request.POST.get('renavam', veiculo.renavam)
    veiculo.versao = request.POST.get('versao', veiculo.versao)
    veiculo.save()

    return render(request, 'transporte/tab/identificacao.html', {
        'veiculo': veiculo,
        'veiculo_id': veiculo_id,
        'mensagem_sucesso': 'Dados salvos com sucesso!',
    })

@login_required
def seguro_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    seguro = Seguro.objects.filter(veiculo=veiculo).first()

    if request.method == 'POST':
        form = SeguroForm(request.POST, request.FILES, instance=seguro)
        if form.is_valid():
            novo_seguro = form.save(commit=False)
            novo_seguro.veiculo = veiculo
            novo_seguro.save()

            response = render(request, 'transporte/tab/documentacao.html', {
                'veiculo': veiculo,
                'seguro': novo_seguro,
                'mensagem_sucesso': 'Dados do seguro salvos com sucesso!',
            })
            response['HX-Trigger'] = 'refreshIdentificacao'
            return response

        print("Erros form de seguro:", form.errors)
        return render(request, 'transporte/tab/documentacao.html', {
            'veiculo': veiculo,
            'seguro': seguro,
            'mensagem_erro': 'Erro ao salvar: verifique os campos preenchidos.',
        })

    return render(request, 'transporte/tab/documentacao.html', {'veiculo': veiculo, 'seguro': seguro})

def enviar_texto(request):
    if request.method == 'POST':
        texto = request.POST.get('mensagem')
        veiculo_id = request.POST.get('veiculo_id')

        if texto and veiculo_id:
            veiculo = get_object_or_404(Veiculo, id=veiculo_id)

            Info.objects.create(
                mensagem=texto,
                usuario=request.user,
                veiculo=veiculo
            )

            observacoes = Info.objects.filter(
                veiculo=veiculo
            ).order_by('-criado_em')

            return render(request, 'transporte/tab/comentarios.html', {
                'observacoes': observacoes
            })

    return HttpResponse(status=400)

def upload_arquivos(request):
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('transporte/tab/comentarios.html')
    else:
        form = DocumentoForm()
    return render(request, 'transporte/tab/comentarios.html', {'form': form})

def comentarios(request):
    comentarios = Info.objects.all()
    return render(request, 'transporte/tab/comentarios.html', {'observacoes': comentarios})

def ativos(request):
    return render(request, 'ativos/ativos.html')

def cadastrar_equipamento(request):
    if request.method == 'POST':
        form = AtivoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cadastrar_equipamento')
    else:
        form = AtivoForm()

    return render(request, 'ativos/cadastrar_equipamento.html', {'form': form})

def listar_ativos(request):
    ativos = Ativo.objects.all().order_by('-disponibilidade')

    resumo = [
        {'nome': 'Celulares', 'total': 0, 'disponiveis': 0, 'em_uso': 0, 'icon': 'bi-phone'},
        {'nome': 'Notebooks', 'total': 0, 'disponiveis': 0, 'em_uso': 0, 'icon': 'bi-laptop'},
        {'nome': 'Tablets', 'total': 0, 'disponiveis': 0, 'em_uso': 0, 'icon': 'bi-tablet'},
    ]
    
    for ativo in ativos:
        cat = str(ativo.categoria).lower()
        idx = None
        if 'celular' in cat:
            idx = 0
        elif 'notebook' in cat:
            idx = 1
        elif 'tablet' in cat:
            idx = 2
            
        if idx is not None:
            resumo[idx]['total'] += 1
            if ativo.disponibilidade:
                resumo[idx]['disponiveis'] += 1
            else:
                resumo[idx]['em_uso'] += 1

    return render(request, 'ativos/listar_ativos.html', {'ativos': ativos, 'resumo_ativos': resumo})

@login_required
def detalhes_ativo(request, pk):
    ativo = get_object_or_404(Ativo, id=pk)
    
    solicitacao_ativa = None
    # Se o ativo estiver em uso, buscamos a solicitação mais recente vinculada a ele e ao usuário atual
    if not ativo.disponibilidade and ativo.usuario:
        solicitacao_ativa = SolicitacaoAtivo.objects.filter(
            ativo_entregue=ativo, 
            usuario=ativo.usuario
        ).order_by('-data_solicitacao').first()
        
    return render(request, 'partials/modal_detalhes_ativo.html', {'ativo': ativo, 'solicitacao_ativa': solicitacao_ativa})

@login_required
@user_passes_test(is_gestor, login_url='/')
def editar_ativo(request, pk):
    ativo = get_object_or_404(Ativo, id=pk)
    
    if request.method == 'POST':
        form = AtivoForm(request.POST, instance=ativo)
        if form.is_valid():
            form.save()
            resposta = HttpResponse()
            resposta['HX-Refresh'] = 'true'
            return resposta
    else:
        form = AtivoForm(instance=ativo)
        
    return render(request, 'partials/modal_editar_ativo.html', {'form': form, 'ativo': ativo})

@login_required
@require_POST
def remover_ativo(request, pk):
    ativo = get_object_or_404(Ativo, id=pk)
    ativo.delete()
    resposta = HttpResponse()
    resposta['HX-Refresh'] = 'true'
    return resposta

@login_required
@require_POST
def devolver_ativo(request, pk):
    ativo = get_object_or_404(Ativo, id=pk)

    if ativo.usuario:
        SolicitacaoAtivo.objects.filter(
            ativo_entregue=ativo,
            usuario=ativo.usuario,
            status=True
        ).update(
            status=False,
            data_devolucao=timezone.now()
            )

    ativo.disponibilidade = True
    ativo.usuario = None
    ativo.save()

    resposta = HttpResponse()
    resposta['HX-Refresh'] = 'true'
    return resposta

def solicitar_equipamento(request):
    if request.method == 'POST':
        form = SolicitarAtivoForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('ativos')
    else:
        form = SolicitarAtivoForm(user=(f'{request.user.first_name} {request.user.last_name}'))

    return render(request, 'ativos/solicitar_equipamento.html', {'form': form})

def ver_solicitacoes(request):
    solicitacoes = SolicitacaoAtivo.objects.filter(status=False).order_by('data_solicitacao')
    ativos_disponiveis = Ativo.objects.filter(disponibilidade=True)
    return render(request, 'ativos/ver_solicitacoes.html', {'solicitacoes': solicitacoes, 'ativos_disponiveis': ativos_disponiveis})

def aprovar_solicitacao(request, pk):
    if request.method == "POST":
        solicitacao = get_object_or_404(SolicitacaoAtivo, id=pk)

        ativo_id = request.POST.get('ativo_id')
        documento = request.FILES.get('documento')

        if not ativo_id:
            messages.error(request, 'Você precisa selecionar um ativo disponível para aprovar essa solicitação.')
            return redirect('ver_solicitacoes')

        try:
            with transaction.atomic():
                ativo_escolhido = get_object_or_404(Ativo, id=ativo_id)
                ativo_escolhido.disponibilidade = False
                ativo_escolhido.usuario = solicitacao.usuario
                ativo_escolhido.save()
                solicitacao.ativo_entregue = ativo_escolhido
                solicitacao.status = True

                if documento:
                    solicitacao.documento = documento

                solicitacao.save()
                async_task(
                    send_mail,
                    "Solicitação de ativo aprovada!",
                    (
                        f"A sua solicitação de {solicitacao.categoria} foi aprovada!\n"
                        f"Entre em contato do seu gestor para retirar o seu {solicitacao.ativo_entregue}"
                    ),
                    "lanmax.carscheduling@gmail.com",
                    [ativo_escolhido.usuario.email],
                    fail_silently=False
                )

        except Exception as e:
            messages.error(request, f'Ocorreu o seguinte erro ao tentar salvar: {str(e)}')
        
        return redirect('ativos')
    
    else:
        messages.warning(request, 'Acesso negado.')
        return redirect('ativos')

def meus_itens(request):
    itens_do_usuario = Ativo.objects.filter(usuario = request.user)
    return render(request, 'ativos/meus_itens.html', {'itens_do_usuario': itens_do_usuario})

def menu_veiculos(request):
    return render(request, 'transporte/menu_veiculos.html')

@login_required
def ver_solicitacoes(request):
    solicitacoes = SolicitacaoAtivo.objects.filter(
        status=False
        ).select_related('usuario')

    ativos_por_categoria = {}
    for categoria, _ in Ativo.Tipo.choices:
        ativos_por_categoria[categoria] = list(
            Ativo.objects.filter(categoria=categoria, disponibilidade=True)
            .values('id', 'marca', 'modelo', 'numero_de_serie')
        )

    return render(request, 'ativos/ver_solicitacoes.html', {
        'solicitacoes': solicitacoes,
        'ativos_por_categoria_json': json.dumps(ativos_por_categoria),
    })

def historico_ativo(request):
    solicitacoes_devolvidas = SolicitacaoAtivo.objects.filter(
        status=False,
        ativo_entregue__isnull=False
    ).select_related('usuario', 'ativo_entregue').order_by('data_solicitacao', 'data_devolucao')

    return render(request, 'ativos/historico_ativo.html', {
        'solicitacoes': solicitacoes_devolvidas
    })