from django.shortcuts import render
import os
from django.conf import settings
from PIL import Image, ImageOps
from django.db.models import Q
from .models import Lead, ZipDeFotos  # Importando os modelos que você tem
from django.core.paginator import Paginator
from django.templatetags.static import static
from django.http import JsonResponse


FOTOS_DIR = os.path.join(settings.BASE_DIR, 'static/images', 'fotos')

# utils


def redimensionar_salvar_imagem(caminho_imagem):
    """
    Corrige a orientação com base no EXIF, redimensiona para 700x600,
    e salva a nova imagem no mesmo diretório com sufixo '_700x600'.

    Args:
        caminho_imagem (str): Caminho completo do arquivo de imagem original.

    Returns:
        str: Caminho da imagem redimensionada ou original (se erro).
    """
    try:
        if not os.path.exists(caminho_imagem):
            print(f"[ERRO] Arquivo não encontrado: {caminho_imagem}")
            return caminho_imagem  # Evita retornar None

        with Image.open(caminho_imagem) as img:
            # Corrige a orientação com base nos dados EXIF
            img_corrigida = ImageOps.exif_transpose(img).convert("RGB")

            nova_resolucao = (700, 600)
            imagem_redimensionada = img_corrigida.resize(
                nova_resolucao, Image.Resampling.LANCZOS)

            diretorio, nome_arquivo = os.path.split(caminho_imagem)
            nome_base, extensao = os.path.splitext(nome_arquivo)

            novo_nome_arquivo = f"{nome_base}_700x600{extensao.lower()}"
            novo_caminho_imagem = os.path.join(diretorio, novo_nome_arquivo)

            imagem_redimensionada.save(
                novo_caminho_imagem, format="JPEG", optimize=True, quality=85)

            print(f"[OK] Imagem salva em: {novo_caminho_imagem}")
            return novo_caminho_imagem

    except Exception as e:
        print(f"[ERRO] Falha ao processar {caminho_imagem}: {e}")
        return caminho_imagem  # Em vez de None, retorna original para evitar quebra


def home(request):
    dados_temas = []

    if not os.path.exists(FOTOS_DIR):
        os.makedirs(FOTOS_DIR)

    for nome_tema in os.listdir(FOTOS_DIR):
        caminho_tema = os.path.join(FOTOS_DIR, nome_tema)
        if not os.path.isdir(caminho_tema):
            continue

        imagem_redimensionada = None

        for nome_arquivo in os.listdir(caminho_tema):
            caminho_arquivo = os.path.join(caminho_tema, nome_arquivo)
            if not os.path.isfile(caminho_arquivo):
                continue

            # Aceita .jpg e .jpeg
            if nome_arquivo.lower().endswith('_700x600.jpg') or nome_arquivo.lower().endswith('_700x600.jpeg'):
                imagem_redimensionada = os.path.join(
                    'static', 'images', 'fotos', nome_tema, nome_arquivo
                ).replace('\\', '/')
                break

        if imagem_redimensionada:
            dados_temas.append({
                'nome': nome_tema.strip().title(),
                'caminho': imagem_redimensionada,
                'rota': f'/tema/{nome_tema.lower().replace(" ", "-")}/'
            })

    context = {'temas': dados_temas}
    return render(request, 'home.html', context)


def exibir_tema(request, nome_tema_slug):
    print(f"[INFO] Acessando tema: {nome_tema_slug}")
    nome_tema = nome_tema_slug.replace('-', ' ').title()
    caminho_tema = os.path.join(FOTOS_DIR, nome_tema)
    print(f"[INFO] Acessando tema: {nome_tema}---{caminho_tema}")
    imagens_tema = []
    if os.path.exists(caminho_tema) and os.path.isdir(caminho_tema):
        for nome_arquivo in os.listdir(caminho_tema):
            # if nome_arquivo.endswith('_700x600.jpg'):
            #    continue  # Pula para a próxima iteração

            caminho_arquivo = os.path.join(caminho_tema, nome_arquivo)
            if os.path.isfile(caminho_arquivo):
                caminho_relativo = os.path.join('static', 'images', 'fotos',
                                                nome_tema.upper(),
                                                nome_arquivo).replace('\\', '/')
                # imagens_tema.append(
                #   {'caminho': caminho_relativo, 'nome': nome_arquivo})
                imagens_tema.append({'thumbnail': caminho_relativo,
                                     'original': caminho_relativo,
                                     'nome': nome_arquivo})

    context = {'nome_tema': nome_tema, 'imagens': imagens_tema}
    return render(request, 'pagina_tema.html', context)


def politicas(request):
    return render(request, 'politicas.html')


def termos(request):
    return render(request, 'termos.html')


def search(request):
    termo = request.GET.get('q', '').strip().lower()
    dados_temas = []

    if termo and os.path.exists(FOTOS_DIR):
        for nome_tema in os.listdir(FOTOS_DIR):
            if termo in nome_tema.lower():
                caminho_tema = os.path.join(FOTOS_DIR, nome_tema)
                if not os.path.isdir(caminho_tema):
                    continue

                imagem_redimensionada = None

                for nome_arquivo in os.listdir(caminho_tema):
                    if nome_arquivo.lower().endswith('_700x600.jpg') or nome_arquivo.lower().endswith('_700x600.jpeg'):
                        imagem_redimensionada = static(os.path.join(
                            'images', 'fotos', nome_tema, nome_arquivo))
                        break

                if imagem_redimensionada:
                    dados_temas.append({
                        'nome': nome_tema.strip().title(),
                        'caminho': imagem_redimensionada,
                        'rota': f'/tema/{nome_tema.lower().replace(" ", "-")}/'
                    })
    print('[INFO] Dados temas:', dados_temas)
    paginator = Paginator(dados_temas, 10)  # 10 temas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'resultados_busca.html', {
        'temas': page_obj,
        'termo': termo,
        'page_obj': page_obj
    })


def elementor_ajax(request):
    # Implemente a lógica de AJAX conforme necessário
    return JsonResponse({'status': 'success'})

