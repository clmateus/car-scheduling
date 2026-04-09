from celery import shared_task
from django.core.mail import send_mail

@shared_task
def enviar_email(destino, dataPartida, dataChegada, email_usuario):
    send_mail(
        "Agendamento de Viagem",
        f"O seu agendamento com destino a {destino} foi realizado com sucesso.\nData e hora de partida: {dataPartida.strftime('%d/%m/%Y %H:%M:%S')}\nData e hora de chegada: {dataChegada.strftime('%d/%m/%Y %H:%M:%S')}\nChegue na expedição com 10 minutos de antecedência.\nDirija com responsabilidade.",
        "lanmax.carscheduling@gmail.com",
        [email_usuario],
        fail_silently=False
    )