from services.fluxo_empregos_ti import distribuir_links
from scrapers.estrutura import extrair_campos, cidade_no_titulo
import os
import re
import time
import unicodedata
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://empregacampinas.com.br"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def normalizar_texto(texto):
    texto = str(texto or "").lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def buscar_soup(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extrair_salario(texto):
    match = re.search(
        r"sal[áa]rio[:\s]+(r\$\s*[\d\.\,]+|a combinar)",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    match = re.search(
        r"r\$\s*[\d\.\,]+",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(0).strip()

    return "Não informado"


def extrair_cidade(texto):
    texto_normalizado = normalizar_texto(texto)

    if "valinhos" in texto_normalizado:
        return "Valinhos/SP"

    if "campinas" in texto_normalizado:
        return "Campinas/SP"

    return "Não informada"


def extrair_empresa(texto):
    match = re.search(
        r"(.+?)\s+est[áa]\s+com\s+\d+\s+vaga",
        texto,
        re.IGNORECASE
    )

    if match:
        empresa = match.group(1).strip()
        return empresa[:80]

    return "Não informada"


def extrair_links_da_busca(soup):
    links = {}

    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "")

        if not href:
            continue

        link = urljoin(BASE_URL, href)
        link_lower = link.lower()
        link_limpo = link.split("?")[0].rstrip("/")

        texto = tag.get_text(" ", strip=True)
        texto_normalizado = normalizar_texto(texto + " " + link)

        # Ignora busca, paginação, categorias, tags e arquivos internos
        itens_para_ignorar = [
            "/page/",
            "?s=",
            "/category/",
            "/tag/",
            "/author/",
            "/wp-content/",
            "/wp-json/",
            "#",
        ]

        if any(item in link_lower for item in itens_para_ignorar):
            continue

        if "empregacampinas.com.br" not in link_lower:
            continue

        palavras_chave = [
            'suporte',
            'informatica',
            'infraestrutura',
            'help desk',
            'service desk',
            'sistemas',
            'ti',
            'tecnologia',
            'redes',
            'noc',
            'automacao',
            'inteligencia artificial',
            'low code',
            'no code',
            'dados',
            'data analyst',
            'analytics',
            'business intelligence',
            'power bi',
            'bi',
            'sap',
            'implantacao',
            'integracoes',
            'integracao',
            'desenvolvedor',
            'desenvolvimento',
            'programador',
            'software',
        ]

        if any(re.search(r"\b" + re.escape(palavra) + r"\b", texto_normalizado) for palavra in palavras_chave):
            links.setdefault(link_limpo, None)

    return links


def extrair_dados_vaga(link):
    try:
        soup = buscar_soup(link)
    except Exception as erro:
        print(f"Erro ao abrir vaga Emprega Campinas: {link}")
        print(erro)
        return None

    texto = soup.get_text("\n", strip=True)

    titulo_tag = soup.find("h1")

    if titulo_tag:
        titulo = titulo_tag.get_text(" ", strip=True)
    else:
        titulo = "Não informado"

    vaga = {
        "titulo": titulo,
        "empresa": extrair_empresa(texto),
        "cidade": cidade_no_titulo(titulo) or extrair_campos(soup).get("cidade", "Não informada"),
        "salario": extrair_salario(texto),
        "descricao": extrair_campos(soup).get("descricao", texto[:1800]),
        "tipo_contrato": extrair_campos(soup).get("tipo_contrato", ""),
        "descricao_confiavel": extrair_campos(soup).get("descricao_confiavel", False),
        "modalidade": extrair_campos(soup).get("modalidade", ""),
        "link": link,
        "fonte": "Emprega Campinas"
    }

    return vaga


def buscar_vagas():
    print("Buscando vagas no Emprega Campinas...")

    cargos = [
        cargo.strip()
        for cargo in os.getenv(
            "CARGOS_BUSCA",
            "Suporte Técnico,Analista de Suporte,Help Desk,Infraestrutura,Assistente de TI,Suporte Sistemas"
        ).split(",")
        if cargo.strip()
    ]

    links_encontrados = {}

    for cargo in cargos:
        termo = quote_plus(cargo)
        url = f"{BASE_URL}/?s={termo}"

        print(f"Consultando: {url}")

        try:
            soup = buscar_soup(url)
            links = extrair_links_da_busca(soup)
            links_encontrados.update({link: None for link in links})
        except Exception as erro:
            print(f"Erro na busca Emprega Campinas: {erro}")

        time.sleep(0.5)

    print(f"Emprega Campinas: links encontrados: {len(links_encontrados)}")

    limite_links = int(os.getenv("MAX_LINKS_EMPREGACAMPINAS", "20"))

    links_para_detalhar = distribuir_links(links_encontrados, limite_links)

    print(f"Emprega Campinas: detalhando apenas {len(links_para_detalhar)} vagas para teste...")

    vagas = []

    for link in links_para_detalhar:
        vaga = extrair_dados_vaga(link)

        if vaga:
            vagas.append(vaga)

        time.sleep(0.3)

    return vagas