from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django_q.tasks import async_task
from .models import Agendamento, Veiculo, Seguro
from .forms import CadastroVeiculo, EdicaoForm, SeguroForm
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

    return render(request, 'index.html')


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

    return render(request, 'veiculos.html', {'veiculos': Veiculo.objects.all(), 'form': form})


@login_required
@user_passes_test(is_gestor, login_url='/')
@require_POST
def remover_veiculo(request, pk):
    get_object_or_404(Veiculo, pk=pk).delete()
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

    return render(request, 'viagens.html', {
        'proximas_viagens': proximas_viagens,
        'veiculos': Veiculo.objects.all(),
        'hora_atual': hora_atual,
        'hora_viagem': hora_viagem,
        'email_criador_do_evento': email_criador_do_evento,
    })


@login_required
@user_passes_test(is_gestor, login_url='/')
def alterar_veiculo(request, pk):
    if request.method == 'POST':
        agendamento = get_object_or_404(Agendamento, pk=pk)
        agendamento.veiculo_id = request.POST.get('selectVeiculos')
        agendamento.save()
        resposta = HttpResponse()
        resposta['HX-Refresh'] = 'true'
        return resposta


@login_required
@user_passes_test(is_gestor, login_url='/')
def historico(request):
    todas_as_viagens = Agendamento.objects.order_by('-dataPartida')
    return render(request, 'historico.html', {'todas_as_viagens': todas_as_viagens})


@login_required
def carregar_aba(request, aba, veiculo_id):
    """Carrega o conteúdo da aba solicitada via HTMX."""
    veiculo = get_object_or_404(Veiculo, id=veiculo_id)

    templates = {
        'identificacao': 'tab/identificacao.html',
        'documentacao': 'tab/documentacao.html',
        'info': 'tab/info.html',
        'mecanica': 'tab/mecanica.html',
    }

    context = {'veiculo': veiculo, 'veiculo_id': veiculo_id}

    if aba == 'documentacao':
        context['seguro'] = Seguro.objects.filter(veiculo=veiculo).first()

    return render(request, templates.get(aba, 'tab/identificacao.html'), context)


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

    return render(request, 'tab/identificacao.html', {
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

            response = render(request, 'tab/documentacao.html', {
                'veiculo': veiculo,
                'seguro': novo_seguro,
                'mensagem_sucesso': 'Dados do seguro salvos com sucesso!',
            })
            response['HX-Trigger'] = 'refreshIdentificacao'
            return response

        print("Erros form de seguro:", form.errors)
        return render(request, 'tab/documentacao.html', {
            'veiculo': veiculo,
            'seguro': seguro,
            'mensagem_erro': 'Erro ao salvar: verifique os campos preenchidos.',
        })

    return render(request, 'tab/documentacao.html', {'veiculo': veiculo, 'seguro': seguro})