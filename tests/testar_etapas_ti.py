"""Testes offline das novas regras (não envia notificações)."""
import os
from pathlib import Path
from dotenv import load_dotenv
from services.filtro_novas_oportunidades import filtrar_vagas

load_dotenv(Path(__file__).resolve().parent / '.env', override=True)
os.environ['ACEITAR_ESTAGIO'] = 'true'


def vaga(titulo, cidade='Campinas/SP', salario='Não informado',
         contrato='', modalidade='', sufixo='1'):
    return dict(titulo=titulo, cidade=cidade, salario=salario,
                tipo_contrato=contrato, modalidade=modalidade,
                descricao='', link='https://exemplo.invalid/' + sufixo,
                fonte='Teste local')


amostras = [
    vaga('Estágio em Análise de Dados', salario='R$ 1.200', contrato='Estágio', sufixo='1'),
    vaga('Freelancer Automação de Processos n8n', cidade='São Paulo/SP',
         contrato='Freelancer', modalidade='Remoto', sufixo='2'),
    vaga('Analista de Suporte ERP Jr', salario='R$ 3.200', contrato='CLT', sufixo='3'),
    vaga('Gerente de Logística', salario='R$ 5.000', sufixo='4'),
    vaga('Estágio em Desenvolvimento', cidade='Sorocaba/SP', sufixo='5'),
    vaga('Analista de Dados Sênior Freelancer', contrato='Freelancer', sufixo='6'),
    vaga('Analista de Suporte ERP PJ', contrato='PJ', salario='R$ 5.000', sufixo='7'),
]

resultado, diagnostico = filtrar_vagas(
    amostras, [], ['Campinas', 'Valinhos', 'Sumaré', 'Hortolândia'], 2500,
    retornar_diagnostico=True,
)
titulos = {v['titulo'] for v in resultado}
assert 'Estágio em Análise de Dados' in titulos
assert 'Freelancer Automação de Processos n8n' not in titulos
assert 'Analista de Suporte ERP Jr' not in titulos
assert 'Gerente de Logística' not in titulos
assert 'Estágio em Desenvolvimento' not in titulos
assert 'Analista de Dados Sênior Freelancer' not in titulos
assert 'Analista de Suporte ERP PJ' not in titulos
assert diagnostico['estagios_adicionados'] == 1
assert diagnostico['freelances_adicionados'] == 0
print('OK: estágio reconhecido mesmo com bolsa inferior ao piso CLT.')
print('OK: vagas freelance rejeitadas.')
print('OK: vagas de ERP rejeitadas.')
print('OK: logística, senioridade, outras cidades e PJ integral não foram aceitos.')
print('SUCESSO: testes offline das novas oportunidades passaram!')
