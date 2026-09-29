from django.test import TestCase
from django.urls import reverse

from .models import Equipamento, Frota, Historico


class SelecaoPerfilTests(TestCase):
	def test_inicio_mostra_selecao_com_perfil_ja_escolhido(self):
		session = self.client.session
		session['perfil_selecionado'] = 'ADMIN'
		session.save()

		response = self.client.get(reverse('inicio'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Quem deseja entrar?')

	def test_usuario_seleciona_perfil_sem_login(self):
		response = self.client.post(
			reverse('selecionar_perfil'),
			{'perfil': 'USUARIO'},
		)

		self.assertRedirects(response, reverse('painel'))
		self.assertEqual(self.client.session['perfil_selecionado'], 'USUARIO')

	def test_perfil_invalido_nao_e_aceito(self):
		response = self.client.post(
			reverse('selecionar_perfil'),
			{'perfil': 'DESCONHECIDO'},
		)

		self.assertRedirects(response, reverse('inicio'))
		self.assertNotIn('perfil_selecionado', self.client.session)


class ModelosInventarioTests(TestCase):
	def test_frota_comeca_pendente_e_equipamento_nao_tem_status(self):
		frota = Frota.objects.create(numero_frota='120128')
		equipamento = Equipamento.objects.create(frota=frota, nome='Monitor X25')

		self.assertEqual(frota.status_inventario, Frota.StatusInventario.PENDENTE)
		self.assertEqual(frota.equipamentos.count(), 1)
		self.assertNotIn('status_inventario', {field.name for field in equipamento._meta.fields})

	def test_historico_preserva_numero_se_frota_for_excluida(self):
		frota = Frota.objects.create(numero_frota='120128')
		historico = Historico.objects.create(
			frota=frota,
			numero_frota=frota.numero_frota,
			perfil='USUARIO',
			acao='Inventário concluído',
		)

		frota.delete()
		historico.refresh_from_db()

		self.assertIsNone(historico.frota)
		self.assertEqual(historico.numero_frota, '120128')


class ConsultaFrotaTests(TestCase):
	def setUp(self):
		session = self.client.session
		session['perfil_selecionado'] = 'USUARIO'
		session.save()

	def test_busca_mostra_frota_equipamentos_e_indicadores_do_banco(self):
		frota = Frota.objects.create(numero_frota='120128', descricao='Colhedora')
		Equipamento.objects.create(frota=frota, nome='Monitor X25 Topcon', numero_serie='S-123')

		response = self.client.get(reverse('painel'), {'q': '120128'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Monitor X25 Topcon')
		self.assertContains(response, 'Pendente')
		self.assertEqual(response.context['total_frotas'], 1)
		self.assertEqual(response.context['pendentes'], 1)

	def test_busca_informa_quando_frota_nao_existe(self):
		response = self.client.get(reverse('painel'), {'q': '999999'})

		self.assertContains(response, 'não está cadastrada')
		self.assertTrue(response.context['nao_encontrada'])


class OperacoesFrotaTests(TestCase):
	def escolher_perfil(self, perfil):
		session = self.client.session
		session['perfil_selecionado'] = perfil
		session.save()

	def test_admin_cadastra_frota_e_equipamento_juntos(self):
		self.escolher_perfil('ADMIN')

		response = self.client.post(reverse('frota_nova'), {
			'numero_frota': '117610',
			'descricao': 'Colhedora',
			'equipamentos-TOTAL_FORMS': '1',
			'equipamentos-INITIAL_FORMS': '0',
			'equipamentos-MIN_NUM_FORMS': '0',
			'equipamentos-MAX_NUM_FORMS': '1000',
			'equipamentos-0-nome': 'Monitor X25 Topcon',
			'equipamentos-0-numero_serie': '202406005BR',
			'equipamentos-0-descricao': '',
		})

		frota = Frota.objects.get(numero_frota='117610')
		self.assertRedirects(response, f"{reverse('painel')}?q=117610")
		self.assertEqual(frota.status_inventario, Frota.StatusInventario.PENDENTE)
		self.assertEqual(frota.equipamentos.get().numero_serie, '202406005BR')

	def test_usuario_nao_abre_formulario_de_gestao(self):
		self.escolher_perfil('USUARIO')

		response = self.client.get(reverse('frota_nova'))

		self.assertEqual(response.status_code, 403)

	def test_admin_abre_edicao_da_frota(self):
		self.escolher_perfil('ADMIN')
		frota = Frota.objects.create(numero_frota='117610')

		response = self.client.get(reverse('frota_editar', args=[frota.id]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Editar frota 117610')

	def test_excluir_frota_remove_equipamentos_e_preserva_historico(self):
		self.escolher_perfil('ADMIN')
		frota = Frota.objects.create(numero_frota='117610')
		Equipamento.objects.create(frota=frota, nome='Antena AGS2')
		Historico.objects.create(
			frota=frota,
			numero_frota='117610',
			perfil='ADMIN',
			acao='Registro anterior',
		)

		response = self.client.post(reverse('frota_excluir', args=[frota.id]))

		self.assertRedirects(response, reverse('painel'))
		self.assertFalse(Frota.objects.filter(numero_frota='117610').exists())
		self.assertFalse(Equipamento.objects.filter(nome='Antena AGS2').exists())
		historico = Historico.objects.get(numero_frota='117610')
		self.assertIsNone(historico.frota)

	def test_inventariar_e_desinventariar_preserva_itens_e_registra_historico(self):
		self.escolher_perfil('USUARIO')
		frota = Frota.objects.create(numero_frota='120128')
		equipamento = Equipamento.objects.create(frota=frota, nome='Rádio DEM300')
		url = reverse('alternar_inventario', args=[frota.id])

		primeira_resposta = self.client.post(url)
		frota.refresh_from_db()
		self.assertRedirects(primeira_resposta, f"{reverse('painel')}?q=120128")
		self.assertEqual(frota.status_inventario, Frota.StatusInventario.INVENTARIADA)
		self.assertIsNotNone(frota.data_inventario)
		self.assertEqual(frota.perfil_inventariado_por, 'USUARIO')

		segunda_resposta = self.client.post(url)
		frota.refresh_from_db()
		self.assertRedirects(segunda_resposta, f"{reverse('painel')}?q=120128")
		self.assertEqual(frota.status_inventario, Frota.StatusInventario.PENDENTE)
		self.assertIsNone(frota.data_inventario)
		self.assertEqual(frota.perfil_inventariado_por, '')
		self.assertTrue(Equipamento.objects.filter(pk=equipamento.pk).exists())
		historico = list(Historico.objects.filter(frota=frota).order_by('data_hora'))
		self.assertEqual(len(historico), 2)
		self.assertEqual([evento.acao for evento in historico], [
			'Inventário concluído',
			'Inventário desfeito',
		])
		self.assertTrue(all(evento.perfil == 'USUARIO' for evento in historico))


class ItensInventariadosTests(TestCase):
	def escolher_perfil(self, perfil):
		session = self.client.session
		session['perfil_selecionado'] = perfil
		session.save()

	def criar_frota_inventariada(self, numero_frota='120128'):
		frota = Frota.objects.create(
			numero_frota=numero_frota,
			status_inventario=Frota.StatusInventario.INVENTARIADA,
			data_inventario='2026-09-28T14:32:00Z',
			perfil_inventariado_por='USUARIO',
		)
		return frota

	def test_admin_e_usuario_visualizam_os_itens_inventariados(self):
		frota = self.criar_frota_inventariada()
		Equipamento.objects.create(
			frota=frota,
			nome='Monitor X25 Topcon',
			numero_serie='202406005BR',
		)

		for perfil in ('ADMIN', 'USUARIO'):
			with self.subTest(perfil=perfil):
				self.escolher_perfil(perfil)
				response = self.client.get(reverse('painel'))

				self.assertContains(response, 'Frotas inventariadas')
				self.assertContains(response, 'Monitor X25 Topcon')
				self.assertContains(response, '202406005BR')
				self.assertContains(response, 'Desinventariar frota')

	def test_ambos_perfis_removem_item_inventariado_com_historico(self):
		for perfil in ('ADMIN', 'USUARIO'):
			with self.subTest(perfil=perfil):
				frota = self.criar_frota_inventariada(numero_frota=f'F-{perfil}')
				equipamento = Equipamento.objects.create(
					frota=frota,
					nome='Rádio DEM300',
					numero_serie=f'S-{perfil}',
				)
				outro_equipamento = Equipamento.objects.create(frota=frota, nome='Antena AGS2')
				self.escolher_perfil(perfil)

				response = self.client.post(
					reverse('equipamento_remover', args=[equipamento.id]),
				)

				self.assertRedirects(response, f"{reverse('painel')}?q=F-{perfil}")
				self.assertFalse(Equipamento.objects.filter(pk=equipamento.pk).exists())
				self.assertTrue(Equipamento.objects.filter(pk=outro_equipamento.pk).exists())
				frota.refresh_from_db()
				self.assertEqual(frota.status_inventario, Frota.StatusInventario.INVENTARIADA)
				historico = Historico.objects.get(numero_frota=f'F-{perfil}')
				self.assertEqual(historico.perfil, perfil)
				self.assertIn(f'S-{perfil}', historico.acao)

	def test_nao_remove_item_de_frota_pendente(self):
		self.escolher_perfil('USUARIO')
		frota = Frota.objects.create(numero_frota='P-1')
		equipamento = Equipamento.objects.create(frota=frota, nome='Monitor')

		response = self.client.post(
			reverse('equipamento_remover', args=[equipamento.id]),
		)

		self.assertRedirects(response, f"{reverse('painel')}?q=P-1")
		self.assertTrue(Equipamento.objects.filter(pk=equipamento.pk).exists())
		self.assertFalse(Historico.objects.filter(numero_frota='P-1').exists())
