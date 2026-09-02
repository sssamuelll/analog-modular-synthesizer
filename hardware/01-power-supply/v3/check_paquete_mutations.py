"""Canarios de la puerta que cruza la placa con su paquete de fabricacion.

La puerta existe porque en el #139 se podaron dos vias y el paquete viejo paso
en verde. Estos canarios reproducen esa situacion exacta -- tocar la placa y
NO regenerar -- y exigen que ahora se ponga roja.

Van aparte de check_pcb_mutations.py a proposito: alli cada mutacion se aplica
a una copia de la placa y se mide contra la placa. Aqui la mutacion es
precisamente que la placa deje de casar con un paquete que no se toca.
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

import check_paquete                                     # noqa: E402
import check_pcb                                         # noqa: E402


def mm(valor: float) -> int:
    return pcbnew.FromMM(valor)


def con_placa_mutada(mutador) -> tuple[int, str]:
    """Guarda una placa mutada, y corre la puerta contra el paquete de SIEMPRE."""
    with tempfile.TemporaryDirectory() as directorio:
        board = pcbnew.LoadBoard(check_pcb.PCB)
        mutador(board)
        ruta = Path(directorio) / "mutada.kicad_pcb"
        pcbnew.SaveBoard(str(ruta), board)
        salida = io.StringIO()
        with mock.patch.object(check_pcb, "PCB", str(ruta)):
            with contextlib.redirect_stdout(salida):
                codigo = check_paquete.main()
        return codigo, salida.getvalue()


def anadir_pista(board, red, capa, inicio, fin, ancho) -> None:
    pista = pcbnew.PCB_TRACK(board)
    pista.SetStart(pcbnew.VECTOR2I(mm(inicio[0]), mm(inicio[1])))
    pista.SetEnd(pcbnew.VECTOR2I(mm(fin[0]), mm(fin[1])))
    pista.SetWidth(mm(ancho))
    pista.SetLayer({"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}[capa])
    pista.SetNet(board.FindNet(red))
    board.Add(pista)


def anadir_via(board, red, posicion, diametro=0.6, taladro=0.3) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(mm(posicion[0]), mm(posicion[1])))
    via.SetWidth(mm(diametro))
    via.SetDrill(mm(taladro))
    via.SetNet(board.FindNet(red))
    board.Add(via)


def quitar_una_via(board, red) -> None:
    for cobre in list(board.GetTracks()):
        if isinstance(cobre, pcbnew.PCB_VIA) and cobre.GetNetname() == red:
            board.Delete(cobre)
            return
    raise AssertionError(f"no hay ninguna via de {red} que quitar")


class PaqueteAlDiaTests(unittest.TestCase):
    def test_la_placa_y_el_paquete_commiteados_casan(self) -> None:
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = check_paquete.main()

        self.assertEqual(codigo, 0, salida.getvalue())
        self.assertIn("son los de esta placa", salida.getvalue())


class PaqueteViejoTests(unittest.TestCase):
    """Cada una es «se toco la placa y no se regenero el paquete»."""

    def test_una_pista_nueva_deja_el_gerber_atras(self) -> None:
        codigo, salida = con_placa_mutada(
            lambda b: anadir_pista(b, "GND", "B.Cu",
                                   (17.175, 79.0), (14.0, 79.0), 1.0))

        self.assertEqual(codigo, 1, salida)
        self.assertIn("B_Cu: el gerber no es de esta placa", salida)
        self.assertIn("1 pistas sin exportar", salida)

    def test_una_via_nueva_deja_el_drill_atras(self) -> None:
        codigo, salida = con_placa_mutada(
            lambda b: anadir_via(b, "GND", (16.525, 66.0)))

        self.assertEqual(codigo, 1, salida)
        self.assertIn("el .drl no es de esta placa", salida)
        self.assertIn("1 taladros sin exportar", salida)

    def test_una_via_podada_deja_el_drill_con_uno_de_mas(self) -> None:
        """La situacion literal del #139: se poda una via y no se regenera."""
        codigo, salida = con_placa_mutada(lambda b: quitar_una_via(b, "GND"))

        self.assertEqual(codigo, 1, salida)
        self.assertIn("el .drl no es de esta placa", salida)
        self.assertIn("1 de mas", salida)

    def test_una_pista_movida_a_mano_se_ve_por_los_dos_lados(self) -> None:
        """No basta con contar: una pista movida no cambia el numero."""
        def mover(board) -> None:
            for cobre in board.GetTracks():
                if isinstance(cobre, pcbnew.PCB_VIA):
                    continue
                if cobre.GetNetname().lstrip("/") != "GND":
                    continue
                p = cobre.GetEnd()
                cobre.SetEnd(pcbnew.VECTOR2I(p.x + mm(0.3), p.y))
                return
            raise AssertionError("no hay pistas de GND que mover")

        codigo, salida = con_placa_mutada(mover)

        self.assertEqual(codigo, 1, salida)
        self.assertIn("pistas sin exportar", salida)
        self.assertIn("que el gerber trae de mas", salida)


if __name__ == "__main__":
    unittest.main()
