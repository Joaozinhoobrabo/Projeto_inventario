from urllib.parse import urlencode

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import EquipamentoFormSet, FrotaForm
from .models import Equipamento, Frota, Historico

PERFIS = ('ADMIN', 'USUARIO')


def inicio(request):
	return render(request, 'inventario/inicio.html')


def selecionar_perfil(request):
	if request.method == 'POST':
		perfil = request.POST.get('perfil', '')
		if perfil in PERFIS:
			request.session['perfil_selecionado'] = perfil
			return redirect('painel')
	return redirect('inicio')


def painel(request):
	perfil = request.session.get('perfil_selecionado')
	if perfil not in PERFIS:
		return redirect('inicio')

	consulta = request.GET.get('q', '').strip()
	frota = None
	nao_encontrada = False
	if consulta:
		frota = Frota.objects.prefetch_related('equipamentos').filter(
			numero_frota__iexact=consulta,
		).first()
		nao_encontrada = frota is None

	total_frotas = Frota.objects.count()
	inventariadas = Frota.objects.filter(
		status_inventario=Frota.StatusInventario.INVENTARIADA,
	).count()
	pendentes = total_frotas - inventariadas
	percentual = round(inventariadas * 100 / total_frotas) if total_frotas else 0

	contexto = {
		'perfil': perfil,
		'consulta': consulta,
		'frota': frota,
		'nao_encontrada': nao_encontrada,
		'total_frotas': total_frotas,
		'inventariadas': inventariadas,
		'pendentes': pendentes,
		'percentual': percentual,
		'frotas_pendentes': Frota.objects.filter(
			status_inventario=Frota.StatusInventario.PENDENTE,
		).prefetch_related('equipamentos')[:8],
		'frotas_inventariadas': Frota.objects.filter(
			status_inventario=Frota.StatusInventario.INVENTARIADA,
		).prefetch_related('equipamentos'),
	}
	return render(request, 'inventario/painel.html', contexto)


def frota_nova(request):
	if request.session.get('perfil_selecionado') != 'ADMIN':
		return HttpResponseForbidden('Selecione o perfil ADMIN para gerenciar frotas.')

	frota_form = FrotaForm(request.POST or None)
	equipamento_formset = EquipamentoFormSet(request.POST or None)
	if request.method == 'POST' and frota_form.is_valid() and equipamento_formset.is_valid():
		with transaction.atomic():
			frota = frota_form.save()
			equipamento_formset.instance = frota
			equipamento_formset.save()
		messages.success(request, f'Frota {frota.numero_frota} cadastrada como pendente.')
		return redirect(f'{reverse_painel_query(frota.numero_frota)}')

	return render(request, 'inventario/frota_form.html', {
		'frota_form': frota_form,
		'equipamento_formset': equipamento_formset,
		'titulo': 'Cadastrar frota',
	})


def frota_editar(request, frota_id):
	if request.session.get('perfil_selecionado') != 'ADMIN':
		return HttpResponseForbidden('Selecione o perfil ADMIN para gerenciar frotas.')

	frota = get_object_or_404(Frota, pk=frota_id)
	frota_form = FrotaForm(request.POST or None, instance=frota)
	equipamento_formset = EquipamentoFormSet(request.POST or None, instance=frota)
	if request.method == 'POST' and frota_form.is_valid() and equipamento_formset.is_valid():
		with transaction.atomic():
			frota = frota_form.save()
			equipamento_formset.instance = frota
			equipamento_formset.save()
		messages.success(request, f'Frota {frota.numero_frota} atualizada.')
		return redirect(reverse_painel_query(frota.numero_frota))

	return render(request, 'inventario/frota_form.html', {
		'frota_form': frota_form,
		'equipamento_formset': equipamento_formset,
		'frota': frota,
		'titulo': f'Editar frota {frota.numero_frota}',
	})


def frota_excluir(request, frota_id):
	if request.session.get('perfil_selecionado') != 'ADMIN':
		return HttpResponseForbidden('Selecione o perfil ADMIN para gerenciar frotas.')

	frota = get_object_or_404(Frota, pk=frota_id)
	if request.method == 'POST':
		numero_frota = frota.numero_frota
		frota.delete()
		messages.success(request, f'Frota {numero_frota} excluída.')
		return redirect('painel')
	return render(request, 'inventario/frota_confirm_delete.html', {'frota': frota})


@require_POST
def alternar_inventario(request, frota_id):
	perfil = request.session.get('perfil_selecionado')
	if perfil not in PERFIS:
		return HttpResponseForbidden('Selecione um perfil para registrar o inventário.')

	with transaction.atomic():
		frota = get_object_or_404(Frota.objects.select_for_update(), pk=frota_id)
		if frota.status_inventario == Frota.StatusInventario.PENDENTE:
			acao = 'Inventário concluído'
			frota.status_inventario = Frota.StatusInventario.INVENTARIADA
			frota.data_inventario = timezone.now()
			frota.perfil_inventariado_por = perfil
			mensagem = f'Frota {frota.numero_frota} marcada como inventariada.'
			messages.success(request, mensagem)
		else:
			acao = 'Inventário desfeito'
			frota.status_inventario = Frota.StatusInventario.PENDENTE
			frota.data_inventario = None
			frota.perfil_inventariado_por = ''
			mensagem = f'Inventário da frota {frota.numero_frota} desfeito; ela voltou a pendente.'
			messages.success(request, mensagem)

		frota.save(update_fields=[
			'status_inventario',
			'data_inventario',
			'perfil_inventariado_por',
			'data_atualizacao',
		])
		Historico.objects.create(
			frota=frota,
			numero_frota=frota.numero_frota,
			perfil=perfil,
			acao=acao,
		)

	return HttpResponseRedirect(reverse_painel_query(frota.numero_frota))


@require_POST
def equipamento_remover(request, equipamento_id):
	perfil = request.session.get('perfil_selecionado')
	if perfil not in PERFIS:
		return HttpResponseForbidden('Selecione um perfil para remover o equipamento.')

	with transaction.atomic():
		equipamento = get_object_or_404(
			Equipamento.objects.select_for_update().select_related('frota'),
			pk=equipamento_id,
		)
		frota = equipamento.frota
		if frota.status_inventario != Frota.StatusInventario.INVENTARIADA:
			messages.error(request, 'Só é possível remover itens de uma frota inventariada.')
			return HttpResponseRedirect(reverse_painel_query(frota.numero_frota))

		acao = f'Equipamento removido: {equipamento.nome}'
		if equipamento.numero_serie:
			acao += f' | série: {equipamento.numero_serie}'
		Historico.objects.create(
			frota=frota,
			numero_frota=frota.numero_frota,
			perfil=perfil,
			acao=acao[:100],
		)
		equipamento.delete()
		messages.success(request, f'Equipamento removido da frota {frota.numero_frota}.')

	return HttpResponseRedirect(reverse_painel_query(frota.numero_frota))


def reverse_painel_query(numero_frota):
	return f"{reverse('painel')}?{urlencode({'q': numero_frota})}"
