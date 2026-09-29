"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from inventario import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('painel/', views.painel, name='painel'),
    path('perfil/', views.selecionar_perfil, name='selecionar_perfil'),
    path('frotas/nova/', views.frota_nova, name='frota_nova'),
    path('frotas/<int:frota_id>/editar/', views.frota_editar, name='frota_editar'),
    path('frotas/<int:frota_id>/excluir/', views.frota_excluir, name='frota_excluir'),
    path('frotas/<int:frota_id>/alternar-inventario/', views.alternar_inventario, name='alternar_inventario'),
    path('equipamentos/<int:equipamento_id>/remover/', views.equipamento_remover, name='equipamento_remover'),
]
