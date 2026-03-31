from django.db import models

class Veiculo(models.Model):
    modelo = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    placa = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f'{self.modelo} - {self.marca} - {self.placa}'    

class Agendamento(models.Model):
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='agendamentos')
    motorista = models.CharField(max_length=100)
    dataPartida = models.DateTimeField()
    dataChegada = models.DateTimeField()
    destino = models.TextField(blank=True)

    def __str__(self):
        return f'{self.veiculo} - {self.motorista} - {self.dataPartida.date()}'