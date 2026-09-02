"""Canarios de la puerta que vuelve a ejercitar el ruteador escrito a mano.

La puerta existe porque al quitar `bp.rutear()` de check_pcb.py (#139) las
aserciones del generador dejaron de correr en ninguna parte (#282). Estos
canarios exigen dos cosas distintas: que una asercion rota salga como FALLO
con su texto, y que un desfase entre el guion y la placa se vea.
"""
from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import pcbnew

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "kicad"))

import check_generador as cg                             # noqa: E402
import check_pcb                                         # noqa: E402


def corre() -> tuple[int, str]:
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        codigo = cg.main()
    return codigo, salida.getvalue()


def con_placa_mutada(mutador) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as directorio:
        board = pcbnew.LoadBoard(check_pcb.PCB)
        mutador(board)
        ruta = Path(directorio) / "mutada.kicad_pcb"
        pcbnew.SaveBoard(str(ruta), board)
        with mock.patch.object(check_pcb, "PCB", str(ruta)):
            return corre()


class GeneradorAlDiaTests(unittest.TestCase):
    def test_el_guion_y_la_placa_commiteada_coinciden(self) -> None:
        codigo, salida = corre()

        self.assertEqual(codigo, 0, salida)
        self.assertIn("esta en la placa commiteada", salida)

    def test_ejercita_de_verdad_las_cuatro_a_mano(self) -> None:
        """Si alguna dejara de llamarse, el cruce contra la placa se caeria.

        Es lo que separa esta puerta de un `import`: no basta con que el
        modulo cargue, tienen que correr y producir cobre.
        """
        _codigo, salida = corre()

        self.assertIn("el guion traza 330 tramos y 50 vias", salida)


class GeneradorRotoTests(unittest.TestCase):
    def test_una_asercion_del_generador_sale_como_FALLO_con_su_texto(
            self) -> None:
        """El caso que el #282 nombra: rutear() se rompe y nadie se entera."""
        with mock.patch.object(
                cg.bp, "rutear_gnd",
                side_effect=AssertionError(
                    "la via de GND de U9.5 no cabe: ni recta ni girando")):
            codigo, salida = corre()

        self.assertEqual(codigo, 1, salida)
        self.assertIn("el generador se planto", salida)
        self.assertIn("la via de GND de U9.5 no cabe", salida)

    def test_una_pista_del_arbol_borrada_de_la_placa_se_ve(self) -> None:
        def borrar(board) -> None:
            for cobre in list(board.GetTracks()):
                if isinstance(cobre, pcbnew.PCB_VIA):
                    continue
                if (cobre.GetNetname().lstrip("/") == "GND"
                        and board.GetLayerName(cobre.GetLayer()) == "B.Cu"):
                    board.Delete(cobre)
                    return
            raise AssertionError("no hay pistas de GND en B.Cu")

        codigo, salida = con_placa_mutada(borrar)

        self.assertEqual(codigo, 1, salida)
        self.assertIn("tramos que el guion traza y la placa", salida)

    def test_una_via_del_arbol_borrada_de_la_placa_se_ve(self) -> None:
        def borrar(board) -> None:
            for cobre in list(board.GetTracks()):
                if (isinstance(cobre, pcbnew.PCB_VIA)
                        and cobre.GetNetname().lstrip("/") == "GND"):
                    board.Delete(cobre)
                    return
            raise AssertionError("no hay vias de GND")

        codigo, salida = con_placa_mutada(borrar)

        self.assertEqual(codigo, 1, salida)
        self.assertIn("vias que el guion traza y la placa", salida)


if __name__ == "__main__":
    unittest.main()
