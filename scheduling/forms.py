from django import forms
from .models import Veiculo, Agendamento

class CadastroVeiculo(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = ['modelo', 'marca', 'placa', 'foto']
        widgets = {
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'modelo': 'Modelo:',
            'marca': 'Marca:',
            'placa': 'Placa:',
            'foto': 'Foto:',
        }
    
    def clean_placa(self):
        placa = self.cleaned_data.get('placa')

        if placa:
            return placa.upper()
        
        return placa

class EdicaoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['motorista', 'dataPartida', 'dataChegada', 'destino']    
        widgets = {
            'motorista': forms.TextInput(attrs={'class': 'form-control'}),
            'dataPartida': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'dataChegada': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'motorista': 'Nome do motorista',
            'dataPartida': 'Data e hora de Partida',
            'dataChegada': 'Data e hora da Volta',
            'destino': 'Destino',
        }