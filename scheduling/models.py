from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    empresa = models.CharField(max_length=255)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Veiculo(models.Model):
    modelo = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    placa = models.CharField(max_length=20, unique=True)
    foto = models.ImageField(upload_to='veiculos/%Y/%m/%d/', blank=True, null=True)
    ano = models.IntegerField(default=2000)
    cor = models.CharField(max_length=100, null=True, blank=True)
    chassi = models.CharField(max_length=50, null=True, blank=True)
    renavam = models.IntegerField(default=1)
    versao = models.CharField(max_length=250, null=True, blank=True)
    
    def __str__(self):
        return f'{self.modelo} - {self.marca} - {self.placa}'

class Agendamento(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    veiculo = models.ForeignKey('Veiculo', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Veículo')
    motorista = models.CharField(max_length=100)
    dataPartida = models.DateTimeField()
    dataChegada = models.DateTimeField()
    destino = models.TextField(blank=True)
    passageiros = models.IntegerField(default=1)

    def __str__(self):
        return f'{self.destino} - {self.motorista} - {self.dataPartida} - {self.dataChegada}'
    
    @property
    def vagas_restantes(self):
        return 5 - self.passageiros
    
class Seguro(models.Model):
    veiculo = models.ForeignKey('Veiculo', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Veículo')
    seguro = models.CharField(max_length=200)
    num_apolice = models.IntegerField(default=1)
    inicio_vigencia = models.DateTimeField()
    final_vigencia = models.DateTimeField()
    # apolice = models.ImageField(upload_to='veiculos/%Y/%m/%d/', blank=True, null=True)
    apolice = models.FileField(upload_to='seguros/', null=True, blank=True)

    def __str__(self):
        return f'{self.seguro} - {self.veiculo}'
    
class Info(models.Model):
    veiculo = models.ForeignKey('Veiculo', on_delete=models.CASCADE, null=True, blank=True)
    mensagem = models.TextField(max_length=350)
    criado_em = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Texto #{self.id} - {self.criado_em.strftime('%d/%m/%Y %H:%M')}"

class Ativo(models.Model):
    class Tipo(models.TextChoices):
        CELULAR = 'Celular'
        TABLET = 'Tablet'
        NOTEBOOK = 'Notebook'
    categoria = models.CharField(max_length=50, choices=Tipo.choices, default=Tipo.CELULAR)
    marca = models.CharField(max_length=100, default='')
    modelo = models.CharField(max_length=100)
    numero_de_serie = models.CharField(max_length=100)
    disponibilidade = models.BooleanField(default=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    conta_google = models.CharField(max_length=255, default='', null=True, blank=True)
    senha_conta_google = models.CharField(max_length=255, default='', null=True, blank=True)

    def __str__(self):
        return f'{self.marca} - {self.modelo}'
    
class SolicitacaoAtivo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    categoria = models.CharField(max_length=50, choices=Ativo.Tipo.choices, default=Ativo.Tipo.CELULAR)
    justificativa = models.TextField(blank=True, null=True)
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_devolucao = models.DateTimeField(null=True, blank=True)
    ativo_entregue = models.ForeignKey(Ativo, on_delete=models.SET_NULL, null=True, blank=True)
    documento = models.FileField(upload_to="documentos/",blank=True, null=True)
    status = models.BooleanField(default=False)
    assinatura = models.CharField(blank=True, null=True)
    
    def __str__(self):
        return f'{self.id} - {self.categoria} - {self.usuario}'