from django import forms
from .models import *

class CadastroVeiculo(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = ['modelo', 'marca', 'placa', 'foto', 'ano', 'cor', 'chassi', 'renavam', 'versao']
        widgets = {
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'cor': forms.TextInput(attrs={'class': 'form-control'}),
            'chassi': forms.TextInput(attrs={'class': 'form-control'}),
            'renavam': forms.NumberInput(attrs={'class': 'form-control'}),
            'versao': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'modelo': 'Modelo',
            'marca': 'Marca',
            'placa': 'Placa',
            'foto': 'Foto',
            'ano': 'Ano',
            'cor': 'Cor',
            'chassi': 'Chassi',
            'renavam': 'Renavam',
            'versao': 'Versão',
        }
    
    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        if placa:
            return placa.upper()
        return placa


class EdicaoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['motorista', 'dataPartida', 'dataChegada', 'destino', 'passageiros']    
        widgets = {
            'motorista': forms.TextInput(attrs={'class': 'form-control'}),
            'dataPartida': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'dataChegada': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
            'passageiros': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }
        labels = {
            'motorista': 'Nome do motorista',
            'dataPartida': 'Data e hora de Partida',
            'dataChegada': 'Data e hora da Volta',
            'destino': 'Destino',
            'passageiros': 'Passageiros'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dataPartida'].input_formats = ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M')
        self.fields['dataChegada'].input_formats = ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M')


class SeguroForm(forms.ModelForm):
    class Meta:
        model = Seguro
        # Removido o 'apolice' duplicado e garantido que o nome do campo bate com o model
        fields = ['seguro', 'num_apolice', 'apolice', 'inicio_vigencia', 'final_vigencia']
        widgets = {
            'seguro': forms.TextInput(attrs={'class': 'form-control'}),
            'num_apolice': forms.NumberInput(attrs={'class': 'form-control'}),
            'apolice': forms.FileInput(attrs={'class': 'form-control'}), # Campo de Upload
            'inicio_vigencia': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'final_vigencia': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
        labels = {
            'seguro': 'Seguro',
            'num_apolice': 'Nº da Apólice',
            'apolice': 'Arquivo da Apólice (PDF/Imagem)',
            'inicio_vigencia': 'Início da Vigência',
            'final_vigencia': 'Fim da Vigência',
        }

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Seguro 
        fields = ['apolice']

class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        fields = ['categoria', 'marca', 'modelo', 'numero_de_serie', 'conta_google', 'senha_conta_google']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_de_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'conta_google': forms.TextInput(attrs={'class': 'form-control'}),
            'senha_conta_google': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'categoria': 'Categoria',
            'marca': 'Marca',
            'modelo': 'Modelo',
            'numero_de_serie': 'IMEI',
            'conta_google': 'Conta Google (opcional)',
            'senha_conta_google': 'Senha da conta Google (opcional)',
        }

class SolicitarAtivoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoAtivo
        fields = ['usuario', 'categoria', 'justificativa', 'assinatura']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'style': 'resize: none;', 'rows': '2'}),
            'assinatura': forms.HiddenInput(),
        }
        labels = {
            'usuario': 'Solicitante'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['usuario'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['usuario'].disabled = True
        
        if user:
            self.fields['usuario'].initial = user