from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Página inicial
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('tema/<str:nome_tema_slug>/', views.exibir_tema, name='exibir_tema'),

    # Páginas de conteúdo
    path('politicas/', views.politicas, name='politicas'),
    path('termos/', views.termos, name='termos'),

    # Busca
    path('busca/', views.search, name='search'),

    # Seções âncora (podem ser tratadas na mesma view da home)
    path('#sobrenos', views.home, name='sobrenos'),
    path('#temas', views.home, name='temas'),
    path('#depoimentos', views.home, name='depoimentos'),
    path('#contato', views.home, name='contato'),

    # requisicoes ajax
    path('elementor-ajax/', views.elementor_ajax, name='elementor_ajax'),
]
