from django.db import models
import os
import zipfile
import json
from django.conf import settings
from django.db import models
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener


if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rejane_site.settings')
    import django
    django.setup()


class Lead(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    mensagem = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} - {self.email}"


register_heif_opener()

# Tipos de imagem aceitos
EXTENSOES_VALIDAS = [
    '.jpg', '.jpeg', '.png', '.gif', '.bmp',
    '.tiff', '.raw', '.dng', '.nef', '.cr2', '.heic'
]

# Tamanho ideal (largura máxima)
LARGURA_MAXIMA = 1280

def validar_imagens_pasta(destino_final):
    """
    Garante que todas as imagens na pasta estejam redimensionadas corretamente,
    rotacionadas corretamente, e renomeadas com sufixo _700x600.jpg
    """
    for nome_arquivo in os.listdir(destino_final):
        caminho = os.path.join(destino_final, nome_arquivo)

        if not os.path.isfile(caminho):
            continue

        try:
            img = Image.open(caminho)

            # Corrige rotação se necessário
            img_corrigida = ImageOps.exif_transpose(img).convert("RGB")

            # Verifica se está com tamanho correto
            if img_corrigida.size != (700, 600):
                img_corrigida = img_corrigida.resize((700, 600), Image.Resampling.LANCZOS)

            # Garante que o nome do arquivo tem _700x600
            nome_base, ext = os.path.splitext(nome_arquivo)
            if not nome_base.endswith('_700x600'):
                nome_base = nome_base + '_700x600'
            nome_final = f"{nome_base}.jpg"

            caminho_final = os.path.join(destino_final, nome_final)

            # Salva novamente se for necessário
            img_corrigida.save(caminho_final, format="JPEG", optimize=True, quality=85)

            # Remove o original se o nome mudou
            if nome_final != nome_arquivo:
                os.remove(caminho)

        except Exception as e:
            print(f"[ERRO] Validação da imagem {nome_arquivo}: {e}")


def criar_ou_atualizar_legendas_json(destino_final, nome_tema):
    """
    Cria ou atualiza o arquivo legendas.json na estrutura compatível com o sistema de edição
    Formato:
    {
        "imagens": [
            {
                "nome": "foto1.jpg",
                "caminho": "/static/images/fotos/PASTA/foto1.jpg",
                "legenda": "Legenda da Foto 1"
            },
            ...
        ],
        "capa": "foto1.jpg"
    }
    """
    json_path = os.path.join(destino_final, 'legendas.json')
    
    # Estrutura padrão do arquivo
    dados = {
        'imagens': [],
        'capa': None
    }
    
    # Se o arquivo já existe, carrega os dados existentes
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
                # Converte estrutura antiga para nova se necessário
                if isinstance(dados, list):
                    dados = converter_estrutura_antiga(dados, nome_tema, destino_final)
        except Exception as e:
            print(f"[ERRO] Ao carregar legendas.json: {e}")
    
    # Nome da pasta em maiúsculas para consistência
    nome_pasta = nome_tema.upper()
    
    # Lista de imagens já registradas
    imagens_registradas = {img['nome'] for img in dados['imagens']}
    
    # Processa as imagens na pasta
    for arquivo in os.listdir(destino_final):
        if arquivo.lower().endswith(('.jpg', '.jpeg', '.png')) and not arquivo.endswith('_700x600.jpg'):
            # Se a imagem não está registrada, adiciona
            if arquivo not in imagens_registradas:
                legenda = os.path.splitext(arquivo)[0].replace('_', ' ').title()
                
                dados['imagens'].append({
                    'nome': arquivo,
                    'caminho': f"/static/images/fotos/{nome_pasta}/{arquivo}",
                    'legenda': legenda
                })
    
    # Define uma capa se não houver
    if not dados['capa'] and dados['imagens']:
        dados['capa'] = dados['imagens'][0]['nome']
    
    # Salva o arquivo JSON
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERRO] Ao salvar legendas.json: {e}")

def converter_estrutura_antiga(dados_antigos, nome_tema, destino_final):
    """
    Converte a estrutura antiga do JSON para a nova estrutura
    Estrutura antiga: [{'nome': ..., 'caminho': ..., 'rota': ...}]
    Estrutura nova: {'imagens': [...], 'capa': ...}
    """
    nome_pasta = nome_tema.upper()
    dados_novos = {
        'imagens': [],
        'capa': None
    }
    
    # Encontra a primeira imagem na pasta para ser a capa
    imagem_capa = None
    for arquivo in os.listdir(destino_final):
        if arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
            imagem_capa = arquivo
            break
    
    # Converte os dados antigos
    for item in dados_antigos:
        if isinstance(item, dict) and 'nome' in item:
            dados_novos['imagens'].append({
                'nome': os.path.basename(item.get('caminho', '')),
                'caminho': f"/static/images/fotos/{nome_pasta}/{os.path.basename(item.get('caminho', ''))}",
                'legenda': item.get('nome', '').title()
            })
    
    # Define a capa
    dados_novos['capa'] = imagem_capa
    
    return dados_novos

class ZipDeFotos(models.Model):
    nome = models.CharField(max_length=100, blank=True, editable=False)
    arquivo_zip = models.FileField(upload_to='temp_zip/')
    enviado_em = models.DateTimeField(auto_now_add=True)

    def gerar_nome_unico(self, base_nome):
        base_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'fotos')
        nome_final = base_nome
        contador = 1
        while os.path.exists(os.path.join(base_path, nome_final.upper())):
            nome_final = f"{base_nome}_{contador}"
            contador += 1
        return nome_final

    def save(self, *args, **kwargs):
        # Define nome antes de salvar
        nome_base = os.path.splitext(os.path.basename(self.arquivo_zip.name))[0]
        nome_base = nome_base.replace('_', ' ').replace('-', ' ').title()
        nome_final = self.gerar_nome_unico(nome_base)
        self.nome = nome_final

        super().save(*args, **kwargs)

        nome_pasta = self.nome.upper()
        destino_final = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'fotos', nome_pasta)
        os.makedirs(destino_final, exist_ok=True)

        zip_path = self.arquivo_zip.path

        if zipfile.is_zipfile(zip_path):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    filename = os.path.basename(member.filename)
                    print('[INFO] Extraindo:', filename)

                    if not filename:  # pula diretórios dentro do zip
                        continue

                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in EXTENSOES_VALIDAS:
                        continue

                    try:
                        with zip_ref.open(member) as file:
                            img = Image.open(file)
                            # Redimensionar se necessário
                            if img.width > LARGURA_MAXIMA:
                                altura = int((LARGURA_MAXIMA / img.width) * img.height)
                                img = img.resize((LARGURA_MAXIMA, altura), Image.Resampling.LANCZOS)

                            # corrigir rotacao
                            img = ImageOps.exif_transpose(img).convert("RGB")

                            # Definir nome final
                            nome_arquivo_final = os.path.splitext(filename)[0] + "_700x600.jpg"
                            caminho_destino = os.path.join(destino_final, nome_arquivo_final)

                            img.save(caminho_destino, format="JPEG", optimize=True, quality=85)

                    except Exception as e:
                        print(f"[ERRO] Falha ao extrair {filename}: {e}")
        
        # Cria ou atualiza o arquivo legendas.json
        criar_ou_atualizar_legendas_json(destino_final, self.nome)
        
        # valida imagens_pasta(destino_final)                
        # validar_imagens_pasta(destino_final)
        # Remove o zip
        print('[INFO] Removendo arquivo: ', zip_path)
        os.remove(zip_path)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "📦 Enviar fotos (.zip)"
        verbose_name_plural = "📦 Enviar fotos (.zip)"


class LinkGaleriaFake(models.Model):
    class Meta:
        managed = False
        verbose_name = "📁 Galeria de Fotos"
        verbose_name_plural = "Acessar Galeria"