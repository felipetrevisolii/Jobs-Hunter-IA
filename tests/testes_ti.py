import unittest
from services.filtro import filtrar_vagas, extrair_salario_numero, identificar_cidade_titulo


def vaga(titulo, cidade='Campinas/SP', salario='R$ 2.800,00', descricao='', tipo_contrato='', modalidade=''):
    return dict(titulo=titulo,cidade=cidade,salario=salario,descricao=descricao,
                tipo_contrato=tipo_contrato,modalidade=modalidade,fonte='Teste', link='https://exemplo.com/'+titulo.replace(' ','-'))


def passar(v):
    return filtrar_vagas([v],[],['Campinas','Valinhos'],2500, salario_faixa_boa=3000, salario_meta=3500)


class FiltrosTITest(unittest.TestCase):
    def test_suporte_alta(self):
        v=passar(vaga('Analista de Suporte N2 - CLT'))
        self.assertEqual(v[0]['prioridade'],'Alta')

    def test_suporte_ao_usuario(self):
        self.assertTrue(passar(vaga("Técnico de Suporte ao Usuário N1")))

    def test_remoto_fora_cidade(self):
        v=passar(vaga('Suporte Técnico N1 - 100% remoto','Belo Horizonte/MG', 'A combinar',modalidade='Remoto'))
        self.assertEqual(v[0]['modalidade'],'Remoto')

    def test_titulo_prevalece_rodape(self):
        self.assertFalse(passar(vaga('ANALISTA DE SUPORTE / INDAIATUBA / 1 VAGA(S)','Campinas/SP')))

    def test_hibrido_outra_cidade(self):
        self.assertFalse(passar(vaga('Técnico de Suporte / SUMARÉ / 1 VAGA(S)','Campinas/SP', modalidade='Híbrido')))

    def test_pj(self):
        self.assertFalse(passar(vaga('Analista de Suporte N1 PJ')))

    def test_pj_vinculo(self):
        self.assertFalse(passar(vaga('Suporte Técnico',tipo_contrato='PJ')))

    def test_internship(self):
        self.assertFalse(passar(vaga('Estágio em Suporte Técnico')))

    def test_senior(self):
        self.assertFalse(passar(vaga('Analista de Infraestrutura Sênior')))

    def test_logistica(self):
        self.assertFalse(passar(vaga('Auxiliar de Logística')))

    def test_salario_sem_centavos(self):
        self.assertEqual(extrair_salario_numero('R$ 2500'),2500)
        self.assertEqual(extrair_salario_numero('R$ 3.500'),3500)
        self.assertEqual(extrair_salario_numero('R$ 2.500,00'),2500)

    def test_abaixo_minimo_rejeitado(self):
        self.assertFalse(passar(vaga('Analista de Suporte N1', salario='R$ 2.300,00')))
        self.assertFalse(passar(vaga('Analista de Suporte N1', salario='R$ 2.499,00')))

    def test_minimo_aceito(self):
        v=passar(vaga('Analista de Suporte N1', salario='R$ 2.500,00'))[0]
        self.assertIn('Aceitável', v['faixa_salarial'])
        self.assertEqual(v['salario_estimado_mensal'], 2500)

    def test_faixa_boa(self):
        v=passar(vaga('Analista de Suporte N1', salario='R$ 3.000,00'))[0]
        self.assertIn('Boa oportunidade', v['faixa_salarial'])
        self.assertEqual(v['salario_estimado_mensal'], 3000)

    def test_meta_atingida(self):
        v=passar(vaga('Analista de Suporte N1', salario='R$ 3.500,00'))[0]
        self.assertIn('Meta alcançada', v['faixa_salarial'])
        self.assertEqual(v['salario_estimado_mensal'], 3500)

    def test_prioriza_melhor_salario_mesma_funcao(self):
        vagas=[vaga('Analista de Suporte N1',salario='R$ 2.600,00'), vaga('Analista de Suporte N1',salario='R$ 3.600,00')]
        aprovadas=filtrar_vagas(vagas,[],['Campinas','Valinhos'],2500,salario_faixa_boa=3000,salario_meta=3500)
        self.assertEqual(aprovadas[0]['salario_estimado_mensal'],3600)

    def test_faixa_salario_piso(self):
        self.assertEqual(extrair_salario_numero('R$ 1.800 a R$ 3.500'),1800)
        self.assertFalse(passar(vaga('Técnico de Suporte',salario='R$ 1.800 a R$ 3.500')))

    def test_salario_desconhecido(self):
        v=passar(vaga('Analista de Suporte',salario='A combinar'))
        self.assertEqual(v[0]['vinculo'],'A confirmar')
        self.assertIsNone(v[0]['salario_estimado_mensal'])
        self.assertEqual(v[0]['faixa_salarial'], 'Não divulgado — confirmar')

    def test_presencial_campinas(self):
        self.assertTrue(passar(vaga('Suporte Técnico Presencial','Campinas/SP')))

    def test_sem_localizacao(self):
        self.assertFalse(passar(vaga('Suporte Técnico','Não informada')))

    def test_cidade_titulo(self):
        self.assertEqual(identificar_cidade_titulo('ANALISTA DE SUPORTE / VALINHOS / 1 VAGA'),'valinhos')

    def test_hibrido_campinas(self):
        self.assertTrue(passar(vaga('Assistente de TI - Híbrido','Campinas/SP')))


if __name__ == '__main__': unittest.main()
