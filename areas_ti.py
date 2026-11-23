
"""Configuração das áreas de TI do Jobs Hunter IA."""

import re
import unicodedata

# 1. Áreas profissionais que queremos pesquisar

AREAS_TI = {
    "Automação e IA": [
        "analista de automação",
        "assistente de automação",
        "estágio em automação",
        "automação de processos",
        "estágio em inteligência artificial",
        "analista de inteligência artificial",

    ],

    "Análise de Dados": [
        "analista de dados",
        "assistente de dados",
        "estágio em dados",
        "estágio em análise de dados",
        "data analyst",
        "analista de indicadores",
    ],

    "BI": [
        "analista de bi",
        "analista de power bi",
        "assistente de bi",
        "assistente de power bi",
        "estágio em bi",
        "estagio em power bi"
        "business intelligence",
        "analista de power bi",
    ],

    "Desenvolvimento": [
        "desenvolvedor junior",
        "desenvolvedor jr",
        "estágio em desenvolvimento",
        "estagiário em desenvolvimento",
        "desenvolvedor web",
        "desenvolvedor front end",
        "desenvolvedor back end",
        "desenvolvedor full stack",
        "programador junior",
        "programador jr",
        "desenvolvedor de software",
    ],
}

# 2. Cargos complementares

CARGOS_COMPLEMENTARES = [
    "suporte técnico",
    "analista de suporte",
    "help desk",
    "service desk",
    "técnico de ti",
    "assistente de ti",
]


# 3. Padronização dos textos

def normalizar(texto):
    texto = unicodedata.normalize(
        "NFKD", texto.lower()
    )

    texto = "".join(
        letra for letra in texto
        if not unicodedata.combining(letra)
    )

    texto = re.sub(r"[^a-z0-9]+", " ", texto)

    return re.sub(r"\s+", " ", texto).strip()


# 4. Identificação da área de uma vaga

def identificar_areas(titulo):
    titulo_normalizado = f" {normalizar(titulo)} "
    resultado = []

    for area, termos in AREAS_TI.items():
        for termo in termos:
            termo_normalizado = f" {normalizar(termo)} "

            if termo_normalizado in titulo_normalizado:
                resultado.append(area)
                break

    return resultado


# 5. Testes locais das cinco áreas

if __name__ == "__main__":

    exemplos = {
        "Estágio em Automação de Processos": "Automação e IA",
        "Analista de Dados Júnior": "Análise de Dados",
        "Analista de BI Jr": "BI",
        "Desenvolvedor Front-end Jr": "Desenvolvimento",
    }

    for titulo, area_esperada in exemplos.items():
        areas = identificar_areas(titulo)

        assert area_esperada in areas, (
            f"Falha para: {titulo}"
        )

        print(f"OK: {titulo} -> {', '.join(areas)}")

    assert identificar_areas(
        "Conferente de Mercadorias"
    ) == []

    print("SUCESSO: Configuração das cinco áreas validada!")
