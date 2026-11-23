"""Filtros de vagas de TI para o Job Hunter IA.

Padrões conservadores: não confundir salário desconhecido com salário baixo,
nem ausência de vínculo com uma confirmação de CLT.
"""
import re
import unicodedata
from areas_ti import identificar_areas


def normalizar_texto(texto):
    valor = unicodedata.normalize('NFD', str(texto or '').lower())
    return ''.join(ch for ch in valor if unicodedata.category(ch) != 'Mn').strip()


def contem(texto, expressao):
    return re.search(expressao, texto, re.IGNORECASE) is not None


# A ordem representa a prioridade; não confundir a experiência anterior com
# desenvolvimento de software avançado (não demonstrado no currículo).
CATEGORIAS = [
    ('Alta', 95, r'\b(?:analista|tecnico|assistente|auxiliar|especialista)?\s*(?:de\s+)?(?:suporte\s+(?:tecnico|ao\s+usuario|a\s+usuarios|de\s+ti|ti|n[12])|help\s*desk|service\s*desk|central\s+de\s+servicos|atendimento\s+ti)\b'),
    ('Alta', 90, r'\b(?:analista\s+de\s+suporte|suporte\s+(?:n[12]|ti|informatica)|helpdesk|servicedesk)\b'),
    ('Alta', 85, r'\b(?:assistente|auxiliar|tecnico)\s+(?:de|em)\s+(?:ti|informatica|tecnologia\s+da\s+informacao)\b'),
    ('Media', 77, r'\b(?:analista|assistente|tecnico)\s+(?:de\s+)?(?:infraestrutura|redes|sistemas|monitoramento|noc)\b'),
    ('Media', 75, r'\b(?:suporte\s+(?:a|de)\s+(?:sistemas|aplicacoes)|analista\s+de\s+implantacao\s+de\s+sistemas)\b'),
    ('Exploratoria', 55, r'\b(?:desenvolvedor|programador)\s+(?:junior|jr|trainee|i)\b'),
    ('Exploratoria', 50, r'\b(?:analista\s+de\s+dados|analista\s+de\s+bi)\s+(?:junior|jr|trainee)?\b'),
]

EXCLUSOES_CARGO = (
    r'\b(?:estagio|estagiario|estagiaria|aprendiz|jovem\s+aprendiz)\b',
    r'\b(?:senior|sr\.?|pleno|coordenador|gerente|diretor|lider\s+tecnico|especialista\s+senior)\b',
)
EXCLUSOES_VINCULO_TITULO = r'\b(?:pj|pessoa\s+juridica|freelanc(?:er|e)|autonomo|temporario|intermitente|contrato\s+de\s+estagio)\b'
CIDADES_CONHECIDAS = (
    'campinas', 'valinhos', 'indaiatuba', 'sumare', 'hortolandia',
    'monte mor', 'nova odessa', 'paulinia', 'vinhedo', 'americana',
    'cosmopolis', 'jaguariuna', 'itapira', 'sao paulo', 'sorocaba',
)


# Pontuações iniciais de compatibilidade com o currículo.
# Não representam percentual de aprovação nem avaliação por IA.
PRIORIDADES_TI = {
    "Automação e IA": ("Media", 84),
    "Análise de Dados": ("Media", 76),
    "BI": ("Media", 74),
    "Desenvolvimento": ("Exploratoria", 60),
}


def classificar_cargo(titulo):
    titulo_padronizado = normalizar_texto(titulo)
    if re.search(r"\berp\b", titulo_padronizado):
        return None

    # Mantém as exclusões atuais, que serão revisadas numa etapa própria.
    if any(contem(titulo_padronizado, padrao) for padrao in EXCLUSOES_CARGO):
        return None

    # Busca correspondências nas cinco áreas cadastradas em areas_ti.py.
    areas = identificar_areas(titulo)
    if areas:
        return max((PRIORIDADES_TI[area] for area in areas), key=lambda item: item[1])

    # Preserva reconhecimento anterior de Suporte, Help Desk e Infraestrutura.
    for prioridade, pontos, regex in CATEGORIAS:
        if contem(titulo_padronizado, regex):
            return prioridade, pontos
    return None


def cargo_corresponde(titulo, cargos=None):
    return bool(classificar_cargo(titulo))


def converter_valor_brasileiro(valor):
    texto = str(valor or '').upper().replace('R$', '').replace(' ', '').strip()
    texto = re.sub(r'[^\d,.]', '', texto)
    if not texto:
        return 0
    # Formatos usuais brasileiros: 2500, 2.500, 2500,00, 2.500,00.
    if ',' in texto:
        texto = texto.split(',', 1)[0].replace('.', '')
    elif '.' in texto:
        partes = texto.split('.')
        texto = ''.join(partes) if len(partes[-1]) == 3 else partes[0]
    return int(texto) if texto.isdigit() else 0


def extrair_valores_monetarios(texto):
    return [converter_valor_brasileiro(valor) for valor in re.findall(r'R\$\s*([\d.,]+)', str(texto or ''), re.I)]


def extrair_salario_numero(salario):
    texto = normalizar_texto(salario)
    if not texto or 'a combinar' in texto or 'nao informad' in texto or 'confidencial' in texto:
        return 0
    valores = [v for v in extrair_valores_monetarios(salario) if v]
    if not valores:
        return 0
    # Piso da faixa salarial: evita aprovar faixa 1800-3500 como piso 3500.
    valor = min(valores)
    if any(term in texto for term in ('por hora', '/hora', 'por dia', 'diaria', 'ao dia')):
        return 0   # Não inventar conversão para mensal em vínculos não comparáveis.
    return valor


def inferir_modalidade(vaga):
    campos = ('titulo', 'modalidade', 'descricao') if vaga.get('descricao_confiavel') else ('titulo','modalidade')
    texto = normalizar_texto(' '.join(str(vaga.get(k) or '') for k in campos))
    if contem(texto, r'\b(?:hibrid[oa]|h[íi]brid[oa])\b'):
        return 'Híbrido'
    if contem(texto, r'\b(?:100%\s*remoto|totalmente\s+remoto|trabalho\s+remoto|vaga\s+remota|home\s*office|teletrabalho|\bremoto\b|\bremota\b)'):
        return 'Remoto'
    if contem(texto, r'\b(?:presencial|onsite|on-site)\b'):
        return 'Presencial'
    return 'Não informada'


def inferir_vinculo(vaga):
    titulo = normalizar_texto(vaga.get('titulo'))
    if contem(titulo, EXCLUSOES_VINCULO_TITULO):
        return 'Não CLT'
    tipo = normalizar_texto(vaga.get('tipo_contrato'))
    descricao = normalizar_texto(vaga.get('descricao')) if vaga.get('descricao_confiavel') else ''
    if tipo:
        if contem(tipo, r'\b(?:pj|temporario|freelancer|autonomo|estagio|intermitente)\b') and not contem(tipo, r'\bclt\b'):
            return 'Não CLT'
        if contem(tipo, r'\bclt\b|tempo\s+indeterminado|efetiv[oa]'):
            return 'CLT informado'
    if contem(descricao, r'(?:regime|contratacao|contrato|vinculo)\s*(?:de|:)?\s*(?:trabalho\s*)?\b(?:pj|temporario|freelancer|autonomo|intermitente)\b'):
        return 'Não CLT'
    if contem(descricao, r'\b(?:contratacao|regime|contrato|vinculo)\s*(?:de|:)?\s*(?:trabalho\s*)?\bclt\b'):
        return 'CLT informado'
    return 'A confirmar'


def identificar_cidade_titulo(titulo):
    t = normalizar_texto(titulo)
    # No Emprega Campinas, cargos têm o padrão: CARGO / CIDADE / N VAGAS.
    partes = [p.strip(' -') for p in t.split('/')]
    for parte in partes[1:]:
        for cidade in CIDADES_CONHECIDAS:
            if re.search(r'\b'+re.escape(cidade)+r'\b', parte):
                return cidade
    # Se a URL ou o h1 indicam especificamente a cidade, prevalece sobre
    # textos de navegação de páginas que citam Campinas indiscriminadamente.
    return None


def cidade_corresponde(cidade_vaga, cidades):
    local = normalizar_texto(cidade_vaga)
    for cidade in cidades:
        nome = normalizar_texto(cidade)
        if re.search(r'\b'+re.escape(nome)+r'\b', local):
            return True
    return False


def criar_amostra(vaga, motivo):
    return {'motivo':motivo, 'titulo':vaga.get('titulo',''), 'cidade':vaga.get('cidade',''),
            'salario':vaga.get('salario',''), 'fonte':vaga.get('fonte',''), 'link':vaga.get('link','')}


def filtrar_vagas(vagas, cargos, cidades, salario_minimo, retornar_diagnostico=False,
                  aceitar_salario_nao_informado=True, aceitar_vinculo_nao_informado=True,
                  salario_faixa_boa=3000, salario_meta=3500):
    aprovadas = []
    diagnostico = {'total_analisadas':0, 'reprovadas_cargo':0, 'reprovadas_cidade':0,
                   'reprovadas_salario':0, 'reprovadas_vinculo':0,
                   'salario_nao_informado':0, 'salario_igual_ou_abaixo':0,
                   'aprovadas':0, 'amostras':[]}
    for original in vagas:
        vaga = dict(original)
        diagnostico['total_analisadas'] += 1
        titulo = vaga.get('titulo','')
        cargo = classificar_cargo(titulo)
        if not cargo:
            motivo = 'cargo'
        else:
            modalidade = inferir_modalidade(vaga)
            cidade_titulo = identificar_cidade_titulo(titulo)
            cidade = cidade_titulo or vaga.get('cidade','')
            if modalidade != 'Remoto' and not cidade_corresponde(cidade, cidades):
                motivo = 'cidade'
            else:
                motivo = None
            vinculo = inferir_vinculo(vaga)
            if not motivo and (vinculo == 'Não CLT' or (vinculo == 'A confirmar' and not aceitar_vinculo_nao_informado)):
                motivo = 'vinculo'
            salario = extrair_salario_numero(vaga.get('salario',''))
            if not motivo and ((salario == 0 and not aceitar_salario_nao_informado) or (0 < salario < salario_minimo)):
                motivo = 'salario'
        if motivo:
            diagnostico['reprovadas_'+motivo] += 1
            if motivo == 'salario':
                if salario == 0: diagnostico['salario_nao_informado'] += 1
                else: diagnostico['salario_igual_ou_abaixo'] += 1
            if len(diagnostico['amostras']) < 10:
                diagnostico['amostras'].append(criar_amostra(vaga,motivo))
            continue
        if salario == 0:
            faixa_salarial = 'Não divulgado — confirmar'
            bonus_salario = 0
        elif salario >= salario_meta:
            faixa_salarial = f'Meta alcançada (a partir de R$ {salario_meta:,.0f})'.replace(',', '.')
            bonus_salario = 15
        elif salario >= salario_faixa_boa:
            faixa_salarial = f'Boa oportunidade (R$ {salario_faixa_boa:,.0f}–{salario_meta-1:,.0f})'.replace(',', '.')
            bonus_salario = 8
        else:
            faixa_salarial = f'Aceitável (R$ {salario_minimo:,.0f}–{salario_faixa_boa-1:,.0f})'.replace(',', '.')
            bonus_salario = 2
        vaga.update({
            'area_ti': ', '.join(identificar_areas(titulo)) or 'Suporte/Infraestrutura',
            'faixa_salarial': faixa_salarial,
            'prioridade':cargo[0], 'pontuacao':cargo[1], 'modalidade':modalidade,
            'vinculo':vinculo, 'salario_estimado_mensal':salario or None,
            'cidade':cidade_titulo.title()+'/SP' if cidade_titulo else vaga.get('cidade','Não informada'),
        })
        if vinculo == 'CLT informado': vaga['pontuacao'] += 5
        vaga['pontuacao'] += bonus_salario
        if modalidade == 'Remoto': vaga['pontuacao'] += 1
        aprovadas.append(vaga)
        diagnostico['aprovadas'] += 1
    aprovadas.sort(key=lambda v:v.get('pontuacao',0), reverse=True)
    return (aprovadas,diagnostico) if retornar_diagnostico else aprovadas
