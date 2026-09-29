from django import forms
from django.forms import inlineformset_factory

from .models import Equipamento, Frota


class FrotaForm(forms.ModelForm):
	class Meta:
		model = Frota
		fields = ['numero_frota', 'descricao']
		labels = {
			'numero_frota': 'Número da frota',
			'descricao': 'Descrição (opcional)',
		}
		widgets = {
			'numero_frota': forms.TextInput(attrs={'placeholder': 'Ex.: 120128'}),
			'descricao': forms.TextInput(attrs={'placeholder': 'Ex.: Colhedora'}),
		}


class EquipamentoForm(forms.ModelForm):
	class Meta:
		model = Equipamento
		fields = ['nome', 'numero_serie', 'descricao']
		labels = {
			'nome': 'Equipamento',
			'numero_serie': 'Número de série',
			'descricao': 'Descrição (opcional)',
		}
		widgets = {
			'nome': forms.TextInput(attrs={'placeholder': 'Ex.: Monitor X25 Topcon'}),
			'numero_serie': forms.TextInput(attrs={'placeholder': 'Número de série'}),
			'descricao': forms.TextInput(attrs={'placeholder': 'Detalhes opcionais'}),
		}


EquipamentoFormSet = inlineformset_factory(
	Frota,
	Equipamento,
	form=EquipamentoForm,
	extra=1,
	can_delete=True,
)