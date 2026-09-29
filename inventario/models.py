from django.db import models

class Frota(models.Model):
	class StatusInventario(models.TextChoices):
		PENDENTE = 'PENDENTE', 'Pendente'
		INVENTARIADA = 'INVENTARIADA', 'Inventariada'

	numero_frota = models.CharField(max_length=50, unique=True)
	descricao = models.CharField(max_length=255, blank=True)
	status_inventario = models.CharField(
		max_length=12,
		choices=StatusInventario.choices,
		default=StatusInventario.PENDENTE,
	)
	data_inventario = models.DateTimeField(null=True, blank=True)
	perfil_inventariado_por = models.CharField(max_length=10, blank=True)
	data_criacao = models.DateTimeField(auto_now_add=True)
	data_atualizacao = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['numero_frota']
		verbose_name = 'frota'
		verbose_name_plural = 'frotas'

	def __str__(self):
		return f'Frota {self.numero_frota}'


class Equipamento(models.Model):
	frota = models.ForeignKey(Frota, on_delete=models.CASCADE, related_name='equipamentos')
	nome = models.CharField(max_length=255)
	numero_serie = models.CharField(max_length=100, blank=True)
	descricao = models.TextField(blank=True)
	data_criacao = models.DateTimeField(auto_now_add=True)
	data_atualizacao = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['nome', 'numero_serie']
		verbose_name = 'equipamento'
		verbose_name_plural = 'equipamentos'

	def __str__(self):
		return f'{self.nome} ({self.frota.numero_frota})'


class Historico(models.Model):
	frota = models.ForeignKey(
		Frota,
		on_delete=models.SET_NULL,
		null=True,
		related_name='historico',
	)
	numero_frota = models.CharField(max_length=50)
	perfil = models.CharField(max_length=10)
	acao = models.CharField(max_length=100)
	data_hora = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-data_hora']
		verbose_name = 'registro de histórico'
		verbose_name_plural = 'históricos'

	def __str__(self):
		return f'{self.acao}: frota {self.numero_frota}'
