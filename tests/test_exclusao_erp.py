import os
import unittest

from services.filtro import (
    classificar_cargo,
    filtrar_vagas as filtrar_clt,
)

from services.filtro_novas_oportunidades import (
    filtrar_vagas as filtrar_geral,
)


def vaga(
    titulo,
    contrato="CLT",
    cidade="Campinas/SP",
    modalidade="Presencial",
):
    return {
        "titulo": titulo,
        "tipo_contrato": contrato,
        "cidade": cidade,
        "modalidade": modalidade,
        "salario": "R$ 3.000",
        "descricao": "",
        "link": (
            "https://exemplo.invalid/" +
            titulo.replace(" ", "-")
        ),
    }


class ExclusaoERPTest(unittest.TestCase):

    def test_cargos_erp_rejeitados(self):
        cargos = (
            "Analista de Suporte ERP Jr",
            "Analista ERP",
            "Desenvolvedor ERP",
        )

        for titulo in cargos:
            with self.subTest(titulo=titulo):
                self.assertIsNone(
                    classificar_cargo(titulo)
                )

    def test_clt_erp_rejeitado(self):
        resultado = filtrar_clt(
            [vaga("Analista de Suporte ERP Jr")],
            [],
            ["Campinas"],
            2500,
        )
        self.assertFalse(resultado)

    def test_estagio_erp_rejeitado(self):
        anterior = os.environ.get(
            "ACEITAR_ESTAGIO"
        )

        os.environ["ACEITAR_ESTAGIO"] = "true"

        try:
            resultado = filtrar_geral(
                [
                    vaga(
                        "Estagio em Suporte ERP",
                        contrato="Estagio",
                    )
                ],
                [],
                ["Campinas"],
                2500,
            )

            self.assertFalse(resultado)

        finally:
            if anterior is None:
                os.environ.pop(
                    "ACEITAR_ESTAGIO", None
                )
            else:
                os.environ["ACEITAR_ESTAGIO"] = anterior

    def test_erp_remoto_rejeitado(self):
        resultado = filtrar_geral(
            [
                vaga(
                    "Analista ERP",
                    cidade="Recife/PE",
                    modalidade="Remoto",
                )
            ],
            [],
            ["Campinas"],
            2500,
        )

        self.assertFalse(resultado)

    def test_suporte_sem_erp_preservado(self):
        resultado = filtrar_clt(
            [vaga("Analista de Suporte N1")],
            [],
            ["Campinas"],
            2500,
        )

        self.assertTrue(resultado)
