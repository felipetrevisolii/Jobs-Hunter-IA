"""Extrai metadados JobPosting quando publicados como JSON-LD.
Não deduz a cidade a partir do menu/rodapé inteiro do site.
"""
import json
import re
from bs4 import BeautifulSoup


def dados_vaga_estruturados(soup):
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string or tag.get_text() or '{}')
        except (ValueError, TypeError):
            continue
        pilha = [data]
        while pilha:
            item = pilha.pop()
            if isinstance(item, list):
                pilha.extend(item)
            elif isinstance(item, dict):
                tipo = item.get('@type', '')
                if isinstance(tipo, list): tipo = ' '.join(tipo)
                if 'JobPosting' in str(tipo):
                    return item
                pilha.extend(item.values())
    return {}


def extrair_campos(soup):
    dados = dados_vaga_estruturados(soup)
    resultado = {}
    local = dados.get('jobLocation', {})
    if isinstance(local, list): local = local[0] if local else {}
    if isinstance(local, dict):
        endereco = local.get('address', {})
        if isinstance(endereco, dict) and endereco.get('addressLocality'):
            resultado['cidade'] = str(endereco['addressLocality'])
    tipo = dados.get('employmentType')
    if tipo:
        if isinstance(tipo, list): tipo = ', '.join(tipo)
        # FULL_TIME não significa CLT: o vínculo continua a confirmar.
        resultado['tipo_contrato'] = str(tipo)
    if str(dados.get('jobLocationType','')).upper() == 'TELECOMMUTE':
        resultado['modalidade'] = 'Remoto'
    if dados.get('datePosted'):
        resultado['data_publicacao'] = str(dados['datePosted'])
    if dados.get('description'):
        desc = BeautifulSoup(str(dados['description']), 'html.parser').get_text(' ', strip=True)
        resultado['descricao'] = desc[:2200]
        resultado['descricao_confiavel'] = True
    return resultado


def cidade_no_titulo(titulo):
    from services.filtro import identificar_cidade_titulo
    nome = identificar_cidade_titulo(titulo)
    return nome.title() + '/SP' if nome else None


def selecionar_links_na_ordem(soup, dominio, palavras_chave, url_base):
    from urllib.parse import urljoin
    from services.filtro import normalizar_texto
    encontrados = []
    ja_vistos = set()
    for tag in soup.find_all('a', href=True):
        url = urljoin(url_base, tag['href']).split('#')[0].split('?')[0].rstrip('/')
        if dominio not in url.lower() or url in ja_vistos:
            continue
        if any(parte in url.lower() for parte in ('/page/', '/category/', '/tag/', '/author/', '/wp-', '/login', '/politica', '/empresa/')):
            continue
        texto = normalizar_texto(tag.get_text(' ', strip=True) + ' ' + url)
        if not any(re.search(r'\b'+re.escape(item)+r'\b', texto) for item in palavras_chave):
            continue
        # Não retornar páginas de busca ou menus como se fossem anúncios.
        if url.rstrip('/') == url_base.rstrip('/') or url.endswith('/empregos.aspx') or 'vagas-de-emprego-' in url and url.endswith('.aspx') and '/vaga-de-' not in url:
            continue
        ja_vistos.add(url)
        encontrados.append(url)
    return encontrados
