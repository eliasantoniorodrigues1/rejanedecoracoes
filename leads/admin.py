from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.conf import settings
import os
import shutil
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import LinkGaleriaFake, ZipDeFotos
from PIL import Image
import json
import traceback
import time


class CustomAdminSite(admin.AdminSite):
    site_header = "Administração Rejane Decorações"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("galeria/", self.admin_view(self.gerenciar_galeria), name="galeria"),
            path("galeria/renomear/<str:folder>/",
                 self.admin_view(self.renomear_pasta), name="renomear_pasta"),
            path("galeria/deletar/<str:folder>/",
                 self.admin_view(self.deletar_pasta), name="deletar_pasta"),
            path("galeria/<str:folder>/editar/",
                 self.admin_view(self.editar_pasta), name="editar_pasta"),
        ]
        return custom_urls + urls

    def gerenciar_galeria(self, request):
        pasta_base = os.path.join(
            settings.STATICFILES_DIRS[0], "images", "fotos")
        os.makedirs(pasta_base, exist_ok=True)
        pastas = sorted([
            f for f in os.listdir(pasta_base)
            if os.path.isdir(os.path.join(pasta_base, f))
        ])
        return render(request, "admin/galeria_de_fotos.html", {"pastas": pastas})

    def renomear_pasta(self, request, folder):
        pasta_base = os.path.join(
            settings.STATICFILES_DIRS[0], "images", "fotos")
        caminho_atual = os.path.join(pasta_base, folder)
        if request.method == "POST":
            novo_nome = request.POST.get("novo_nome", "").strip().upper()
            novo_caminho = os.path.join(pasta_base, novo_nome)
            if not os.path.exists(novo_caminho):
                os.rename(caminho_atual, novo_caminho)
                messages.success(request, f"Pasta renomeada para {novo_nome}")
            else:
                messages.error(request, "Já existe uma pasta com esse nome.")
            return redirect("/admin/galeria/")
        return render(request, "admin/renomear_pasta.html", {"pasta": folder})

    def deletar_pasta(self, request, folder):
        pasta_base = os.path.join(
            settings.STATICFILES_DIRS[0], "images", "fotos")
        caminho = os.path.join(pasta_base, folder)
        if request.method == "POST":
            shutil.rmtree(caminho)
            messages.success(
                request, f"Pasta '{folder}' deletada com sucesso.")
            return redirect("/admin/galeria/")
        return render(request, "admin/deletar_pasta.html", {"pasta": folder})

    def editar_pasta(self, request, folder):
        pasta_path = os.path.join(
            settings.STATICFILES_DIRS[0], 'images', 'fotos', folder)

        if not os.path.exists(pasta_path):
            messages.error(request, "Pasta não encontrada.")
            return redirect("/admin/galeria/")

        # Caminho para o arquivo de legendas
        legenda_path = os.path.join(pasta_path, "legendas.json")

        # Inicializa a estrutura de dados
        galeria_data = {
            'imagens': [],
            'capa': None
        }

        # Verifica se o arquivo de legendas existe
        if os.path.exists(legenda_path):
            try:
                with open(legenda_path, 'r', encoding='utf-8') as f:
                    galeria_data = json.load(f)
            except json.JSONDecodeError:
                # Se o arquivo estiver corrompido, recria
                galeria_data = {'imagens': [], 'capa': None}

        # Lista as imagens da pasta
        imagens_na_pasta = [f for f in os.listdir(pasta_path)
                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        # Atualiza a lista de imagens no JSON
        imagens_json = []

        # Primeiro, verifica imagens existentes no JSON
        for img_data in galeria_data.get('imagens', []):
            if img_data['nome'] in imagens_na_pasta:
                imagens_json.append(img_data)

        # Depois, adiciona novas imagens que não estão no JSON
        for nome_arquivo in imagens_na_pasta:
            if not any(img['nome'] == nome_arquivo for img in imagens_json):
                nome_base = os.path.splitext(nome_arquivo)[0]
                legenda = nome_base.replace('_', ' ').title()

                imagens_json.append({
                    'nome': nome_arquivo,
                    'caminho': f"/static/images/fotos/{folder}/{nome_arquivo}",
                    'legenda': legenda
                })

        # Atualiza a estrutura de dados
        galeria_data['imagens'] = imagens_json

        # Se não houver capa definida, usa a primeira imagem
        if not galeria_data.get('capa') and imagens_json:
            galeria_data['capa'] = f"/static/images/fotos/{folder}/{imagens_json[0]['nome']}"

        # Salva o arquivo JSON atualizado
        with open(legenda_path, 'w', encoding='utf-8') as f:
            json.dump(galeria_data, f, ensure_ascii=False, indent=2)

        # Prepara a lista de imagens para o template
        imagens_para_template = []
        for img_data in imagens_json:
            imagens_para_template.append({
                'nome': img_data['nome'],
                'caminho': img_data['caminho'],
                'legenda': img_data['legenda'],
                'e_capa': img_data['nome'] == galeria_data.get('capa')
            })

        # Processa requisições POST
        if request.method == "POST":
            acao = request.POST.get("acao")
            imagem = request.POST.get("imagem")

            if acao == "salvar_legenda":
                legenda = request.POST.get("legenda", "")
                # Atualiza a legenda no JSON
                for img_data in galeria_data['imagens']:
                    if img_data['nome'] == imagem:
                        img_data['legenda'] = legenda
                        break

                with open(legenda_path, 'w', encoding='utf-8') as f:
                    json.dump(galeria_data, f, ensure_ascii=False, indent=2)

                messages.success(request, f"Legenda atualizada para {imagem}.")

            elif acao == "rotacionar":
                angulo = int(request.POST.get("angulo", "90"))
                caminho = os.path.join(pasta_path, imagem)

                try:
                    with Image.open(caminho) as img:
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert("RGB")

                        rotated = img.rotate(-angulo, expand=True,
                                             resample=Image.BICUBIC)

                        # Adiciona timestamp ao nome do arquivo temporário
                        timestamp = int(time.time())
                        temp_path = os.path.join(
                            pasta_path, f"temp_rot_{timestamp}_{imagem}")
                        rotated.save(temp_path, format='JPEG',
                                     quality=95, subsampling=0, optimize=True)

                    os.replace(temp_path, caminho)
                    messages.success(
                        request, f"Imagem '{imagem}' rotacionada {angulo}°.")

                    # Redireciona com timestamp para evitar cache
                    return redirect(f"/admin/galeria/{folder}/editar/?t={timestamp}")

                except Exception as e:
                    if 'temp_path' in locals() and os.path.exists(temp_path):
                        os.remove(temp_path)
                    messages.error(request, f"Falha ao rotacionar: {str(e)}")
                    print(f"ERRO DETAIL: {traceback.format_exc()}")
                    return redirect(f"/admin/galeria/{folder}/editar/")

            elif acao == "definir_capa":
                if any(img['nome'] == imagem for img in galeria_data['imagens']):
                    # imagem
                    galeria_data['capa'] = f"/static/images/fotos/{folder}/{imagem}"
                    with open(legenda_path, 'w', encoding='utf-8') as f:
                        json.dump(galeria_data, f,
                                  ensure_ascii=False, indent=2)
                    messages.success(
                        request, f"Imagem '{imagem}' definida como capa.")
                else:
                    messages.error(
                        request, f"Imagem '{imagem}' não encontrada na galeria.")

            elif acao == "deletar":
                if not imagem:
                    messages.error(
                        request, "Imagem não especificada para deleção.")
                    return redirect(f"/admin/galeria/{folder}/editar/")

                caminho = os.path.join(pasta_path, imagem)

                try:
                    os.remove(caminho)
                    # Remove a imagem da lista no JSON
                    galeria_data['imagens'] = [img for img in galeria_data['imagens']
                                               if img['nome'] != imagem]

                    # Se a imagem deletada era a capa, define uma nova capa
                    if galeria_data.get('capa') == imagem and galeria_data['imagens']:
                        # galeria_data['imagens'][0]['nome']
                        galeria_data['capa'] = f"/static/images/fotos/{folder}/{galeria_data['imagens'][0]['nome']}"

                    with open(legenda_path, 'w', encoding='utf-8') as f:
                        json.dump(galeria_data, f,
                                  ensure_ascii=False, indent=2)

                    messages.success(
                        request, f"Imagem '{imagem}' deletada com sucesso.")
                except Exception as e:
                    messages.error(
                        request, f"Erro ao deletar imagem '{imagem}': {e}")

            return redirect(f"/admin/galeria/{folder}/editar/")

        return render(request, "admin/editar_galeria.html", {
            "pasta": folder,
            "imagens": imagens_para_template,
        })

    class Media:
        css = {
            "all": ("leads/css/admin_custom.css",)
        }


class GaleriaLinkAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect("/admin/galeria/")


class ZipDeFotosAdmin(admin.ModelAdmin):
    list_display = ("nome", "enviado_em")

    def save_model(self, request, obj, form, change):
        nome_antigo = obj.nome
        obj.save()
        if obj.nome != nome_antigo:
            messages.warning(
                request, f"O nome da pasta foi alterado para '{obj.nome.upper()}' porque já existia uma pasta com o mesmo nome.")


# Substitui o admin padrão
admin_site = CustomAdminSite(name="custom_admin")
admin_site.register(ZipDeFotos, ZipDeFotosAdmin)
