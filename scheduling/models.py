from django.contrib.auth.models import User
from django.db import models
from PIL import Image

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
    apolice = models.ImageField(upload_to='veiculos/%Y/%m/%d/', blank=True, null=True)

    def __str__(self):
        return f'{self.seguro} - {self.veiculo}'