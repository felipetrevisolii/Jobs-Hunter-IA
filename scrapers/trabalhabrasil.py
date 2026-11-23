from services.fluxo_empregos_ti import distribuir_links
from scrapers.estrutura import extrair_campos, cidade_no_titulo
import os
import re
import time
import unicodedata
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.trabalhabrasil.com.br"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def slugify(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    texto = texto.strip("-")
    return texto


def buscar_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.Timeout:
        print(f"Tempo esgotado ao acessar: {url}")
        return None
    except requests.exceptions.RequestException as erro:
        print(f"Erro ao acessar {url}")
        print(erro)
        return None
    except Exception as erro:
        print(f"Erro inesperado ao acessar {url}")
        print(erro)
        return None


def montar_urls_busca():
    cidades = [
        cidade.strip()
        for cidade in os.getenv("CIDADES", "Campinas,Valinhos").split(",")
        if cidade.strip()
    ]

    cargos = [
        cargo.strip()
        for cargo in os.getenv(
            "CARGOS_BUSCA",
            "Suporte Técnico,Analista de Suporte,Help Desk,Infraestrutura,Assistente de TI,Suporte Sistemas"
        ).split(",")
        if cargo.strip()
    ]

    paginas_por_busca = int(os.getenv("PAGINAS_POR_BUSCA", "3"))

    urls = []

    for cidade in cidades:
        cidade_slug = slugify(cidade)

        for cargo in cargos:
            cargo_slug = slugify(cargo)

            url_base = f"{BASE_URL}/vagas-de-emprego-em-{cidade_slug}-sp/{cargo_slug}"

            for pagina in range(1, paginas_por_busca + 1):
                if pagina == 1:
                    urls.append(url_base)
                else:
                    urls.append(f"{url_base}?Pagina={pagina}")

    return urls


def extrair_links_vagas(soup):
    links = {}

    for tag in soup.find_all("a", href=True):
        href = tag.get("href")

        if not href:
            continue

        link = urljoin(BASE_URL, href)
        link = link.split("?")[0]

        padrao_vaga = r"/vagas-(de-emprego|empregos)-em-[^/]+/.+/\d+/?$"

        if re.search(padrao_vaga, link):
            links.setdefault(link, None)

    return links


def limpar_linhas(texto):
    return [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]


def extrair_titulo(soup, texto):
    h1 = soup.find("h1")

    if h1:
        titulo = h1.get_text(strip=True)
        titulo = re.sub(r"^Vaga de\s+", "", titulo, flags=re.IGNORECASE)
        return titulo.strip()

    match = re.search(r"Vaga de\s+(.+)", texto, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return "Não informado"


def extrair_salario(texto):
    match = re.search(
        r"Sal[áa]rio\s*(R\$\s*[\d\.\,]+(?:\s*por\s*(?:m[eê]s|dia))?|A combinar)",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    match = re.search(
        r"Sal[áa]rio:\s*(R\$\s*[\d\.\,]+|A combinar)",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return "Não informado"


def extrair_cidade_pela_url(url):
    match = re.search(r"vagas-(?:de-emprego|empregos)-em-([a-z-]+)-sp", url)

    if not match:
        return "Não informada"

    cidade_slug = match.group(1)
    cidade = cidade_slug.replace("-", " ").title()

    return f"{cidade}/SP"


def extrair_empresa(linhas, titulo):
    termos_ignorar = [
        "copiar id",
        "id copiado",
        "id copiado com sucesso",
        "me candidatar",
        "informações da vaga",
        "informacoes da vaga",
        "dados da vaga",
        "salário",
        "salario"
    ]

    for index, linha in enumerate(linhas):
        linha_normalizada = linha.lower()

        if "copiar id" in linha_normalizada or "id copiado" in linha_normalizada:
            proximas_linhas = linhas[index + 1:index + 10]

            for candidata in proximas_linhas:
                candidata_limpa = candidata.strip()
                candidata_normalizada = candidata_limpa.lower()

                if not candidata_limpa:
                    continue

                if candidata_normalizada == titulo.lower():
                    continue

                if any(termo in candidata_normalizada for termo in termos_ignorar):
                    continue

                if "/sp" in candidata_normalizada:
                    continue

                if len(candidata_limpa) > 100:
                    continue

                return candidata_limpa

    return "Não informada"


def extrair_descricao(texto):
    match = re.search(
        r"Descrição da vaga\s*(.+?)\s*Me candidatar",
        texto,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        return ""

    descricao = match.group(1).strip()
    descricao = re.sub(r"\s+", " ", descricao)

    return descricao[:500]


def extrair_dados_vaga(link):
    soup = buscar_soup(link)

    if not soup:
        return None

    texto = soup.get_text("\n", strip=True)
    linhas = limpar_linhas(texto)

    titulo = extrair_titulo(soup, texto)
    salario = extrair_salario(texto)
    cidade = cidade_no_titulo(titulo) or extrair_campos(soup).get("cidade") or extrair_cidade_pela_url(link)
    empresa = extrair_empresa(linhas, titulo)
    descricao = extrair_descricao(texto)

    return {
    "titulo": titulo,
    "empresa": empresa,
    "cidade": cidade,
    "salario": salario,
    "descricao": extrair_campos(soup).get("descricao", descricao),
    "tipo_contrato": extrair_campos(soup).get("tipo_contrato", ""),
        "descricao_confiavel": extrair_campos(soup).get("descricao_confiavel", False),
    "modalidade": extrair_campos(soup).get("modalidade", ""),
    "link": link,
    "fonte": "Trabalha Brasil"
}


def buscar_vagas():
    print("Buscando vagas no Trabalha Brasil...")

    urls_busca = montar_urls_busca()
    links_encontrados = {}

    for url in urls_busca:
        print(f"Consultando: {url}")

        soup = buscar_soup(url)

        if not soup:
            continue

        links = extrair_links_vagas(soup)
        links_encontrados.update({link: None for link in links})

        time.sleep(1)

    print(f"Links de vagas encontrados: {len(links_encontrados)}")

    limite_links = int(os.getenv("MAX_LINKS_TRABALHABRASIL", "40"))

    links_para_detalhar = distribuir_links(links_encontrados, limite_links)

    print(f"Detalhando apenas {len(links_para_detalhar)} vagas para teste...")

    vagas = []

    for link in links_para_detalhar:
        vaga = extrair_dados_vaga(link)

        if vaga:
            vagas.append(vaga)

        time.sleep(0.5)

    print(f"Vagas coletadas antes do filtro: {len(vagas)}")

    return vagas