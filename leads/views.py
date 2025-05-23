from django.shortcuts import render
import os
from django.conf import settings
from PIL import Image, ImageOps
from django.db.models import Q
from .models import Lead, ZipDeFotos  # Importando os modelos que você tem
from django.core.paginator import Paginator
from django.templatetags.static import static
from django.http import JsonResponse
import json
from bs4 import BeautifulSoup


FOTOS_DIR = os.path.join(settings.BASE_DIR, 'static/images', 'fotos')
TEMPLATE_DIR = os.path.join(settings.BASE_DIR, 'templates')

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

    for nome_tema in sorted(os.listdir(FOTOS_DIR)):
        caminho_tema = os.path.join(FOTOS_DIR, nome_tema)
        if not os.path.isdir(caminho_tema):
            continue

        imagem_capa = None

        # Tenta carregar a legenda e pegar o valor da chave "capa"
        legenda_path = os.path.join(caminho_tema, 'legendas.json')
        if os.path.exists(legenda_path):
            try:
                with open(legenda_path, 'r', encoding='utf-8') as f:
                    legendas = json.load(f)
                    imagem_capa = legendas.get("capa")
            except Exception as e:
                print(f"[ERRO] Lendo legendas.json em {nome_tema}: {e}")

        # Fallback: se não encontrou capa, usa a primeira imagem válida redimensionada
        if not imagem_capa:
            for nome_arquivo in os.listdir(caminho_tema):
                if nome_arquivo.lower().endswith('_700x600.jpg') or nome_arquivo.lower().endswith('_700x600.jpeg'):
                    imagem_capa = os.path.join(
                        'static', 'images', 'fotos', nome_tema, nome_arquivo
                    ).replace('\\', '/')
                    break

        if imagem_capa:
            dados_temas.append({
                'nome': nome_tema.strip().title(),
                'caminho': imagem_capa,
                'rota': f'/tema/{nome_tema.lower().replace(" ", "-")}/'
            })

    # trata as avaliacoes
    avaliacoes = coletar_avaliacoes(
        os.path.join('leads', 'templates', 'leads', 'scraper_avaliacoes.html'),
        'avaliacao_google.json'
    )

    context = {'temas': dados_temas, 'avaliacoes': avaliacoes}

    return render(request, 'home.html', context)



def exibir_tema(request, nome_tema_slug):
    print(f"[INFO] Acessando tema: {nome_tema_slug}")
    nome_tema = nome_tema_slug.replace('-', ' ').title()
    print(f"[INFO] Caminho padrao das imagens: {FOTOS_DIR}")
    caminho_tema = os.path.join(FOTOS_DIR, nome_tema.upper())
    print(f"[INFO] Caminho do tema: {caminho_tema}")
    imagens_tema = []
    if os.path.exists(caminho_tema) and os.path.isdir(caminho_tema):
        print(f"[INFO] Tema encontrado: {caminho_tema}")
        for nome_arquivo in os.listdir(caminho_tema):
            # if nome_arquivo.endswith('_700x600.jpg'):
            #    continue  # Pula para a próxima iteração
            caminho_arquivo = os.path.join(caminho_tema, nome_arquivo)
            print(f"[INFO] Verificando arquivo: {caminho_arquivo}")
            if os.path.isfile(caminho_arquivo):
                caminho_relativo = os.path.join('static', 'images', 'fotos',
                                                nome_tema.upper(),
                                                nome_arquivo).replace('\\', '/')

                # imagens_tema.append(
                #   {'caminho': caminho_relativo, 'nome': nome_arquivo})
                imagens_tema.append({'thumbnail': caminho_relativo,
                                     'original': caminho_relativo,
                                     'nome': nome_arquivo})

    # carrega as avaliacoes
    avaliacoes = json.load(
        open('avaliacao_google.json', 'r', encoding='utf-8'))

    print(f"[INFO] Imagens do tema {nome_tema}: {imagens_tema}")
    context = {'nome_tema': nome_tema,
               'imagens': imagens_tema, 'avaliacoes': avaliacoes}
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


def coletar_avaliacoes(html_path, json_path):
    with open(html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Extraindo uma vez apenas
    nomes = [nome.get_text(strip=True)
             for nome in soup.find_all('div', class_='Vpc5Fe')]
    notas = [nota.get('aria-label')
             for nota in soup.find_all('div', class_='dHX2k')]
    comentarios = [comentario.get_text(
        strip=True) for comentario in soup.find_all('div', class_='OA1nbd')]

    # Garante que o número de elementos seja o mesmo
    total = min(len(nomes), len(notas), len(comentarios))

    avaliacoes = []

    for i in range(total):
        avaliacoes.append({
            'nome': nomes[i],
            'nota': notas[i],
            'comentario': comentarios[i]
        })

    # Salvando em JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(avaliacoes, f, ensure_ascii=False, indent=2)

    print(
        f"[INFO] {len(avaliacoes)} avaliações coletadas e salvas em {json_path}")

    return avaliacoes
