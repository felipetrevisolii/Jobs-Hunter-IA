"""Camada adicional somente para estágios em TI.

Mantém o filtro de vagas CLT original e acrescenta oportunidades
compatíveis com ADS sem tratar bolsa de estágio como salário CLT.
Nenhuma candidatura ou acesso à internet ocorre neste módulo.
"""
import os
import re

from areas_ti import identificar_areas
from services.filtro import (
    filtrar_vagas as filtrar_vagas_clt,
    normalizar_texto,
    inferir_modalidade,
    identificar_cidade_titulo,
    cidade_corresponde,
    extrair_salario_numero,
)

_PRIORIDADE_AREA = {
    'Automação e IA': ('Media', 85),
    'Análise de Dados': ('Media', 79),
    'BI': ('Media', 77),
    'Desenvolvimento': ('Exploratoria', 65),
}

_RE_ESTAGIO = re.compile(r'\b(?:estagio|estagiari[oa])\b')
_RE_FREELANCE = re.compile(
    r'\b(?:freelanc(?:er|e)|autonom[oa]|por projeto|projeto avulso)\b'
)
_RE_SENIOR = re.compile(
    r'\b(?:senior|sr\.?|pleno|coordenador|gerente|diretor|lider tecnico|especialista senior)\b'
)
_RE_APRENDIZ = re.compile(r'\b(?:aprendiz|jovem aprendiz)\b')
_RE_TI_ADICIONAL = re.compile(
    r'\b(?:suporte tecnico|help desk|service desk|informatica|tecnologia da informacao|'
    r'power bi|inteligencia artificial|automacao|integracoes|integracao|dados|analytics|'
    r'sap|n8n|python|javascript|desenvolvimento|desenvolvedor|programador|'
    r'software|sql|business intelligence|bi)\b'
)


def _ativado(chave, padrao='false'):
    return os.getenv(chave, padrao).strip().lower() == 'true'


def _tipo_oportunidade(vaga):
    """Reconhece estágios, nunca vagas marcadas como freelance."""
    texto = normalizar_texto(
        f"{vaga.get('titulo', '')} {vaga.get('tipo_contrato', '')} {vaga.get('vinculo', '')}"
    )
    if _RE_FREELANCE.search(texto):
        return None
    if _RE_ESTAGIO.search(texto):
        return 'Estágio'
    return None


def _categorias(titulo):
    areas = identificar_areas(titulo)
    if areas:
        return areas
    if _RE_TI_ADICIONAL.search(normalizar_texto(titulo)):
        return ['Suporte/Infraestrutura']
    return []


def _oportunidade_extra(vaga_original, cidades, tipo):
    vaga = dict(vaga_original)
    titulo = str(vaga.get('titulo') or '')
    titulo_normalizado = normalizar_texto(titulo)
    if re.search(r"\berp\b", titulo_normalizado):
        return None

    if _RE_SENIOR.search(titulo_normalizado) or _RE_APRENDIZ.search(titulo_normalizado):
        return None

    areas = _categorias(titulo)
    if not areas:
        return None

    modalidade = inferir_modalidade(vaga)
    cidade_titulo = identificar_cidade_titulo(titulo)
    cidade = cidade_titulo or vaga.get('cidade', '')
    if modalidade != 'Remoto' and not cidade_corresponde(cidade, cidades):
        return None

    if tipo != 'Estágio':
        return None
    valor = extrair_salario_numero(vaga.get('salario', ''))
    faixa = ('Bolsa de estágio informada — conferir carga horária'
             if valor else 'Bolsa de estágio não divulgada — conferir')
    salario_mensal = valor or None  # Somente valor anunciado: confirmar periodicidade.
    vinculo = 'Estágio'
    bonus = 0

    prioridade, pontos = max(
        (_PRIORIDADE_AREA.get(area, ('Media', 72)) for area in areas),
        key=lambda item: item[1],
    )
    vaga.update({
        'area_ti': ', '.join(areas),
        'tipo_oportunidade': tipo,
        'vinculo': vinculo,
        'modalidade': modalidade,
        'cidade': (cidade_titulo.title() + '/SP') if cidade_titulo else vaga.get('cidade', 'Não informada'),
        'prioridade': prioridade,
        'pontuacao': pontos + bonus + (1 if modalidade == 'Remoto' else 0),
        'faixa_salarial': faixa,
        'salario_estimado_mensal': salario_mensal,
    })
    return vaga


def filtrar_vagas(vagas, cargos, cidades, salario_minimo, retornar_diagnostico=False,
                  aceitar_salario_nao_informado=True, aceitar_vinculo_nao_informado=True,
                  salario_faixa_boa=3000, salario_meta=3500):
    """Mantém assinatura do filtro original para compatibilidade com main.py."""
    # Bloqueia freelance ANTES do filtro CLT e do filtro de estágios.
    vagas_validas = [
        vaga for vaga in vagas
        if not _RE_FREELANCE.search(normalizar_texto(
            ' '.join(str(vaga.get(campo) or '')
                     for campo in ('titulo', 'tipo_contrato', 'vinculo'))
        ))
    ]
    aprovadas, diagnostico = filtrar_vagas_clt(
        vagas_validas, cargos, cidades, salario_minimo,
        retornar_diagnostico=True,
        aceitar_salario_nao_informado=aceitar_salario_nao_informado,
        aceitar_vinculo_nao_informado=aceitar_vinculo_nao_informado,
        salario_faixa_boa=salario_faixa_boa,
        salario_meta=salario_meta,
    )
    links_aprovados = {v.get('link') for v in aprovadas if v.get('link')}
    adicionados = {'Estágio': 0}

    for vaga in vagas_validas:
        tipo = _tipo_oportunidade(vaga)
        if tipo == 'Estágio' and not _ativado('ACEITAR_ESTAGIO'):
            continue
        if tipo is None:
            continue
        # Não duplicar um anúncio já aceito pelo filtro original.
        link = vaga.get('link')
        if link and link in links_aprovados:
            continue
        nova = _oportunidade_extra(vaga, cidades, tipo)
        if nova is None:
            continue
        aprovadas.append(nova)
        if link:
            links_aprovados.add(link)
        adicionados[tipo] += 1

    aprovadas.sort(key=lambda v: v.get('pontuacao', 0), reverse=True)
    diagnostico['estagios_adicionados'] = adicionados['Estágio']
    diagnostico['freelances_adicionados'] = 0
    diagnostico['aprovadas'] = len(aprovadas)
    diagnostico['nota_diagnostico'] = (
        'Contadores reprovadas_* refletem o filtro CLT original; '
        'somente estágios são acrescentados em uma segunda passagem.'
    )
    return (aprovadas, diagnostico) if retornar_diagnostico else aprovadas
