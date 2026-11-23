import unittest
from pathlib import Path

from areas_ti import AREAS_TI
from services.avaliador_perfil import PESOS, COMPETENCIAS
from services.filtro import PRIORIDADES_TI, CATEGORIAS
from services.filtro_novas_oportunidades import (
    _PRIORIDADE_AREA,
    _RE_TI_ADICIONAL,
)


class ConfigSemERPTest(unittest.TestCase):

    def test_erp_nao_e_area(self):
        self.assertNotIn("ERP", AREAS_TI)
        self.assertNotIn("ERP", PRIORIDADES_TI)
        self.assertNotIn("ERP", _PRIORIDADE_AREA)

    def test_erp_nao_recebe_peso(self):
        self.assertNotIn("ERP", PESOS)
        self.assertNotIn("ERP", COMPETENCIAS)

    def test_erp_nao_e_termo_generico(self):
        self.assertNotIn(
            "erp", _RE_TI_ADICIONAL.pattern.lower()
        )

        for _, _, padrao in CATEGORIAS:
            self.assertNotIn("erp", padrao.lower())

    def test_erp_nao_e_palavra_chave_dos_coletores(self):
        pasta = (
            Path(__file__).resolve().parents[1]
            / "scrapers"
        )

        for nome in (
            "empregacampinas.py",
            "infojobs.py"
        ):
            with self.subTest(arquivo=nome):
                conteudo = (
                    pasta / nome
                ).read_text(encoding="utf-8")

                self.assertNotIn("'erp',", conteudo)
