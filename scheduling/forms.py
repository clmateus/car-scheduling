from django import forms
from .models import *
from django.contrib.auth.models import User

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
        
        usuarios = User.objects.filter(is_active=True).order_by('first_name')
        choices = [('', 'Selecione um motorista...')] + [(u.get_full_name() or u.username, u.get_full_name() or u.username) for u in usuarios]
        if self.instance and self.instance.motorista and self.instance.motorista not in dict(choices):
            choices.append((self.instance.motorista, f"{self.instance.motorista} (Não registrado)"))
            
        self.fields['motorista'] = forms.ChoiceField(choices=choices, widget=forms.Select(attrs={'class': 'form-control', 'required': True}), label='Nome do motorista')
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
            'categoria': forms.Select(attrs={'class': 'select select-bordered w-full text-base'}),
            'marca': forms.TextInput(attrs={'class': 'input input-bordered w-full text-base'}),
            'modelo': forms.TextInput(attrs={'class': 'input input-bordered w-full text-base'}),
            'numero_de_serie': forms.TextInput(attrs={'class': 'input input-bordered w-full text-base'}),
            'conta_google': forms.TextInput(attrs={'class': 'input input-bordered w-full text-base'}),
            'senha_conta_google': forms.TextInput(attrs={'class': 'input input-bordered w-full text-base'})
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
            'categoria': forms.Select(attrs={'class': 'select select-bordered w-full text-base'}),
            'justificativa': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full text-base', 'style': 'resize: none;', 'rows': '3', 'placeholder': 'Explique brevemente a necessidade deste equipamento...'}),
            'assinatura': forms.HiddenInput(),
        }
        labels = {
            'usuario': 'Solicitante'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['usuario'].widget = forms.TextInput(attrs={'class': 'input input-bordered w-full font-semibold text-base-content/70'})
        self.fields['usuario'].disabled = True
        
        if user:
            self.fields['usuario'].initial = user