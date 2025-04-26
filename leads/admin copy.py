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

        # Lê legenda salva (se existir)
        legenda_path = os.path.join(pasta_path, "legendas.json")
        nomes_legendas = []

        # Verifica se o arquivo de legendas existe
        if not os.path.exists(legenda_path):
            # Cria o arquivo de legendas com os nomes das imagens como padrão
            for nome_arquivo in os.listdir(pasta_path):
                if nome_arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                    nome_base = os.path.splitext(nome_arquivo)[0]
                    nomes_legendas.append(nome_base.replace(
                        '_', ' ').title())
            # salva a lista com os nomes das legendas        
            legendas['legendas'] = nomes_legendas
            
            # Salva o arquivo de legendas
            with open(legenda_path, 'w', encoding='utf-8') as f:
                json.dump(legendas, f, ensure_ascii=False, indent=2)
        else:
            # Se o arquivo já existe, carrega as legendas existentes
            with open(legenda_path, 'r', encoding='utf-8') as f:
                legendas = json.load(f)

        # Lista as imagens da pasta
        imagens = []
        for nome_arquivo in os.listdir(pasta_path):
            if nome_arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Verifica se a imagem tem legenda, se não, adiciona o nome base
                if nome_arquivo not in legendas:
                    print(f"[INFO] Adicionando legenda padrão para {legendas}")
                    nome_base = os.path.splitext(nome_arquivo)[0]
                    print('>>>>', nome_base)
                    legendas[nome_arquivo] = nome_base.replace(
                        '_', ' ').title()
                    # Atualiza o arquivo de legendas
                    with open(legenda_path, 'w', encoding='utf-8') as f:
                        json.dump(legendas, f, ensure_ascii=False, indent=2)

                imagens.append({
                    'nome': nome_arquivo,
                    'caminho': f"/static/images/fotos/{folder}/{nome_arquivo}",
                    'legenda': legendas[nome_arquivo]
                })

        # [Restante do código mantido igual...]
        # POST: salvar legenda ou rotacionar imagem
        if request.method == "POST":
            acao = request.POST.get("acao")
            imagem = request.POST.get("imagem")

            if acao == "salvar_legenda":
                legenda = request.POST.get("legenda", "")
                legendas[imagem] = legenda
                with open(legenda_path, 'w', encoding='utf-8') as f:
                    json.dump(legendas, f, ensure_ascii=False, indent=2)
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
                legenda_path = os.path.join(pasta_path, "legendas.json")
                imagem = request.POST.get("imagem")
                try:
                    if os.path.exists(legenda_path):
                        with open(legenda_path, 'r', encoding='utf-8') as f:
                            legendas = json.load(f)
                    else:
                        legendas = {}

                    legendas["__CAPA__"] = imagem

                    with open(legenda_path, 'w', encoding='utf-8') as f:
                        json.dump(legendas, f, ensure_ascii=False, indent=2)

                    messages.success(request, f"Imagem '{imagem}' definida como capa.")
                except Exception as e:
                    messages.error(request, f"Erro ao definir capa: {e}")

            elif acao == "deletar":
                imagem = request.POST.get("imagem")
                if not imagem:
                    messages.error(
                        request, "Imagem não especificada para deleção.")
                    return redirect(f"/admin/galeria/{folder}/editar/")

                caminho = os.path.join(pasta_path, imagem)

                try:
                    os.remove(caminho)
                    # Remove legenda também, se houver
                    if imagem in legendas:
                        del legendas[imagem]
                        with open(legenda_path, 'w', encoding='utf-8') as f:
                            json.dump(
                                legendas, f, ensure_ascii=False, indent=2)
                    messages.success(
                        request, f"Imagem '{imagem}' deletada com sucesso.")
                except Exception as e:
                    messages.error(
                        request, f"Erro ao deletar imagem '{imagem}': {e}")

            return redirect(f"/admin/galeria/{folder}/editar/")

        return render(request, "admin/editar_galeria.html", {
            "pasta": folder,
            "imagens": imagens,
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
