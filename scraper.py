from bs4 import BeautifulSoup
import json


def coletar_avaliacoes(html_path, json_path):
    with open(html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Extraindo uma vez apenas
    nomes = [nome.get_text(strip=True) for nome in soup.find_all('div', class_='Vpc5Fe')]
    notas = [nota.get('aria-label') for nota in soup.find_all('div', class_='dHX2k')]
    comentarios = [comentario.get_text(strip=True) for comentario in soup.find_all('div', class_='OA1nbd')]

    # Garante que o número de elementos seja o mesmo
    total = min(len(nomes), len(notas), len(comentarios))

    avaliacoes = []

    for i in range(total):
        avaliacoes.append({
            'nome': nomes[i].lower().title(),
            'nota': notas[i],
            'comentario': comentarios[i]
        })

    # Salvando em JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(avaliacoes, f, ensure_ascii=False, indent=2)

    print(f"[INFO] {len(avaliacoes)} avaliações coletadas e salvas em {json_path}")


coletar_avaliacoes('scraper_avaliacoes.html', 'avaliacoes.json')
