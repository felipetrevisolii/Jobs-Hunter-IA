"""Avalia a compatibilidade das vagas com o perfil profissional."""

import re
import unicodedata
from areas_ti import identificar_areas

# Pontuacao inicial por area, baseada no curriculo
PESOS = {
    "Suporte/Infraestrutura": 86,
    "Automação e IA": 75,
    "Análise de Dados": 68,
    "BI": 66,
    "Desenvolvimento": 58,
}

# Conhecimentos anteriores e projetos atuais
COMPETENCIAS = {
    "SAP": r"\bsap\b",
    "Linux": r"\blinux\b|\bcentos\b|\bredhat\b",
    "SQL": r"\bsql\b",
    "Power BI": r"\bpower\s*bi\b",
    "Google Sheets": r"\bgoogle\s*sheets\b",
    "ITIL": r"\bitil\b",
    "n8n": r"\bn8n\b",
    "suporte N1/N2": r"\bsuporte\b|\bhelp\s*desk\b|\bservice\s*desk\b",
    "backup": r"\bbackup\b",
}

# Tecnologias que exigem verificacao adicional
APRENDIZADO = {
    "Java": r"\bjava\b",
    "React": r"\breact\b",
    "AWS": r"\baws\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b",
    "Machine Learning": r"\bmachine\s*learning\b",
}


def normalizar(texto):
    texto = unicodedata.normalize(
        "NFKD", str(texto or "").lower()
    )
    return "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )


def avaliar_vaga(vaga):
    """Avalia e acrescenta informacoes ao anuncio."""

    titulo = normalizar(vaga.get("titulo"))
    descricao_original = str(vaga.get("descricao") or "")
    descricao = normalizar(descricao_original)
    texto = titulo + " " + descricao

    areas = identificar_areas(vaga.get("titulo", ""))

    if not areas:
        anteriores = str(vaga.get("area_ti") or "")
        areas = [a for a in PESOS if a in anteriores]

    if not areas and re.search(
        r"\bsuporte\b|\bhelp\s*desk\b|\bservice\s*desk\b|\binfraestrutura\b",
        titulo
    ):
        areas = ["Suporte/Infraestrutura"]

    area = (
        max(areas, key=lambda a: PESOS.get(a, 50))
        if areas else "TI (conferir)"
    )

    pontos = PESOS.get(area, 50)
    motivos = [f"Area relacionada: {area}"]
    alertas = []

    # Adequacao ao nivel profissional
    if (
        re.search(r"\bestagio\b|\bestagiari[oa]\b", titulo)
        or vaga.get("tipo_oportunidade") == "Estágio"
    ):
        pontos += 8
        motivos.append("Estagio compativel com graduacao em andamento")

    elif re.search(r"\bjunior\b|\bjr\b|\btrainee\b", titulo):
        pontos += 5
        motivos.append("Nivel de entrada indicado no titulo")

    elif re.search(r"\bpleno\b|\bsenior\b|\bsr\b", titulo):
        pontos -= 30
        alertas.append("Senioridade acima do perfil atual")

    # Identifica conhecimentos relacionados ao curriculo
    encontradas = [
        nome for nome, padrao in COMPETENCIAS.items()
        if re.search(padrao, texto)
    ]

    if encontradas:
        pontos += min(len(encontradas) * 2, 8)
        motivos.append(
            "Conhecimentos relacionados: " +
            ", ".join(encontradas[:4])
        )

    # Identifica tecnologias a verificar
    novas = [
        nome for nome, padrao in APRENDIZADO.items()
        if re.search(padrao, descricao)
    ]

    if novas:
        alertas.append(
            "Verificar dominio exigido: " +
            ", ".join(novas[:3])
        )

    # Experiencia minima anunciada
    anos = re.search(
        r"(?:experiencia\s+(?:minima\s+)?de|pelo\s+menos|ao\s+menos)\s*(\d+)\s*anos",
        descricao
    )

    if anos and int(anos.group(1)) >= 3:
        pontos -= 10
        alertas.append(
            "Experiencia exigida: confirmar tempo especifico na area"
        )

    if len(descricao_original.strip()) < 80:
        alertas.append(
            "Descricao curta ou ausente: confirmar requisitos no anuncio"
        )

    pontos = max(0, min(100, pontos))

    nivel = (
        "Alta" if pontos >= 85
        else "Boa" if pontos >= 70
        else "Exploratoria"
    )

    vaga["area_ti"] = ", ".join(areas) if areas else "TI (conferir)"
    vaga["pontuacao_perfil"] = pontos
    vaga["compatibilidade_perfil"] = nivel
    vaga["motivos_perfil"] = "; ".join(motivos)
    vaga["alertas_perfil"] = (
        "; ".join(alertas)
        if alertas else "Confirmar requisitos completos no anuncio"
    )

    return vaga
