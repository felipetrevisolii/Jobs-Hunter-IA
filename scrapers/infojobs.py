from services.fluxo_empregos_ti import distribuir_links
from scrapers.estrutura import extrair_campos, cidade_no_titulo
import os
import re
import time
import unicodedata
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.infojobs.com.br"

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
        r"R\$\s*[\d\.\,]+(?:\s*a\s*R\$\s*[\d\.\,]+)?",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(0).strip()

    if "a combinar" in normalizar_texto(texto):
        return "A combinar"

    return "Não informado"


def extrair_cidade(texto):
    texto_normalizado = normalizar_texto(texto)

    if "valinhos" in texto_normalizado:
        return "Valinhos/SP"

    if "campinas" in texto_normalizado:
        return "Campinas/SP"

    return "Não informada"


def extrair_empresa(soup, texto):
    possiveis_classes = re.compile("company|empresa|jsCompany", re.IGNORECASE)

    empresa_tag = soup.find(attrs={"class": possiveis_classes})

    if empresa_tag:
        empresa = empresa_tag.get_text(" ", strip=True)

        if empresa:
            return empresa[:100]

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    for linha in linhas:
        linha_normalizada = normalizar_texto(linha)

        if "empresa" in linha_normalizada and len(linha) < 120:
            return linha[:100]

    return "Não informada"


def extrair_links_da_busca(soup):
    links = {}

    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "")

        if not href:
            continue

        link = urljoin(BASE_URL, href)
        link_limpo = link.split("?")[0].rstrip("/")

        texto = tag.get_text(" ", strip=True)
        texto_normalizado = normalizar_texto(texto + " " + link)

        if "infojobs.com.br" not in link_limpo:
            continue

        itens_para_ignorar = [
            "/login",
            "/candidato",
            "/empresa",
            "/candidate",
            "/company",
            "/politica",
            "/termos",
            "#",
        ]

        if any(item in link_limpo.lower() for item in itens_para_ignorar):
            continue

        parece_vaga = (
            "vaga" in texto_normalizado
            or "vagas-de-emprego" in link_limpo.lower()
            or ".aspx" in link_limpo.lower()
        )

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

        tem_palavra_chave = any(
            re.search(r"\b" + re.escape(palavra) + r"\b", texto_normalizado)
            for palavra in palavras_chave
        )

        if parece_vaga and tem_palavra_chave:
            links.setdefault(link_limpo, None)

    return links


def extrair_dados_vaga(link):
    try:
        soup = buscar_soup(link)
    except Exception as erro:
        print(f"Erro ao abrir vaga InfoJobs: {link}")
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
        "empresa": extrair_empresa(soup, texto),
        "cidade": cidade_no_titulo(titulo) or extrair_campos(soup).get("cidade", "Não informada"),
        "salario": extrair_salario(texto),
        "descricao": extrair_campos(soup).get("descricao", texto[:1800]),
        "tipo_contrato": extrair_campos(soup).get("tipo_contrato", ""),
        "descricao_confiavel": extrair_campos(soup).get("descricao_confiavel", False),
        "modalidade": extrair_campos(soup).get("modalidade", ""),
        "link": link,
        "fonte": "InfoJobs"
    }

    return vaga


def buscar_vagas():
    print("Buscando vagas no InfoJobs...")

    cargos = [
        cargo.strip()
        for cargo in os.getenv(
            "CARGOS_BUSCA",
            "Suporte Técnico,Analista de Suporte,Help Desk,Infraestrutura,Assistente de TI,Suporte Sistemas"
        ).split(",")
        if cargo.strip()
    ]

    cidades = [
        cidade.strip()
        for cidade in os.getenv("CIDADES", "Campinas,Valinhos").split(",")
        if cidade.strip()
    ]

    links_encontrados = {}

    for cidade in cidades:
        for cargo in cargos:
            termo = quote_plus(cargo)
            cidade_url = quote_plus(f"{cidade}, sp")

            url = f"{BASE_URL}/vagas-de-emprego-{termo}-em-{cidade_url}.aspx"

            print(f"Consultando: {url}")

            try:
                soup = buscar_soup(url)
                links = extrair_links_da_busca(soup)
                links_encontrados.update({link: None for link in links})
            except Exception as erro:
                print(f"Erro na busca InfoJobs: {erro}")

            time.sleep(0.5)

    if os.getenv("BUSCAR_REMOTAS_BRASIL", "true").lower() == "true":
        # Busca nacional home office: não restringir a Campinas/Valinhos.
        # Ex.: https://www.infojobs.com.br/vagas-de-suporte-tecnico-trabalho-home-office.aspx
        from scrapers.trabalhabrasil import slugify
        termos_remotos = [x.strip() for x in os.getenv(
            "CARGOS_BUSCA_REMOTO", "Suporte Técnico,Analista de Suporte,Help Desk"
        ).split(",") if x.strip()]
        for cargo in termos_remotos:
            url = f"{BASE_URL}/vagas-de-{slugify(cargo)}-trabalho-home-office.aspx"
            try:
                soup = buscar_soup(url)
                for link in extrair_links_da_busca(soup):
                    links_encontrados.setdefault(link, "Remoto")
            except Exception as erro:
                print(f"Erro na busca remota InfoJobs: {erro}")
            time.sleep(0.5)

    print(f"InfoJobs: links encontrados: {len(links_encontrados)}")

    limite_links = int(os.getenv("MAX_LINKS_INFOJOBS", "20"))

    links_para_detalhar = distribuir_links(links_encontrados, limite_links)

    print(f"InfoJobs: detalhando apenas {len(links_para_detalhar)} vagas para teste...")

    vagas = []

    for link in links_para_detalhar:
        vaga = extrair_dados_vaga(link)

        if vaga:
            if links_encontrados.get(link) == "Remoto":
                vaga["modalidade"] = "Remoto"
            vagas.append(vaga)

        time.sleep(0.3)

    return vagas