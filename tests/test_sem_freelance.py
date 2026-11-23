import unittest
from unittest.mock import patch
from services.filtro_novas_oportunidades import filtrar_vagas, _oportunidade_extra


def vaga(titulo, contrato='', salario='R$ 900', vinculo='', cidade='Campinas/SP'):
    return dict(titulo=titulo, tipo_contrato=contrato, salario=salario,
                vinculo=vinculo, cidade=cidade, modalidade='Presencial',
                descricao='', link='https://exemplo.invalid/' + titulo.replace(' ', '-'))


class SemFreelanceTest(unittest.TestCase):
    def test_estagio_preservado_e_freelance_rejeitado(self):
        with patch.dict('os.environ', {'ACEITAR_ESTAGIO': 'true', 'ACEITAR_FREELANCE': 'true'}):
            aprovadas, diag = filtrar_vagas([
                vaga('Estágio em Análise de Dados', 'Estágio'),
                vaga('Freelancer Automação n8n', 'Freelancer'),
                vaga('Estágio em Dados Freelancer', 'Estágio'),
            ], [], ['Campinas'], 2500, retornar_diagnostico=True)
        self.assertEqual([v['titulo'] for v in aprovadas], ['Estágio em Análise de Dados'])
        self.assertEqual(diag['estagios_adicionados'], 1)
        self.assertEqual(diag['freelances_adicionados'], 0)

    def test_impede_freelance_que_poderia_passar_como_clt(self):
        with patch.dict('os.environ', {'ACEITAR_FREELANCE': 'true'}):
            aprovadas = filtrar_vagas([
                vaga('Analista de Suporte N1', '', 'R$ 3000', vinculo='Freelancer'),
                vaga('Analista de Suporte N1 CLT', 'CLT', 'R$ 3000'),
            ], [], ['Campinas'], 2500)
        self.assertEqual([v['titulo'] for v in aprovadas], ['Analista de Suporte N1 CLT'])

    def test_chamada_direta_nunca_aprova_freelance(self):
        self.assertIsNone(_oportunidade_extra(vaga('Automação n8n', 'Freelancer'), ['Campinas'], 'Freelance'))
