'Canarios de mutacion para la puerta del cobre commiteado de la fuente v3.'
from __future__ import annotations

import contextlib
import inspect
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import pcbnew

import check_pcb


@contextlib.contextmanager
def ruteo_temporal(tracks, vias):
    anteriores = check_pcb.bp.TRACKS, check_pcb.bp.VIAS
    check_pcb.bp.TRACKS, check_pcb.bp.VIAS = tracks, vias
    try:
        yield
    finally:
        check_pcb.bp.TRACKS, check_pcb.bp.VIAS = anteriores


def mm(valor: float) -> int:
    return pcbnew.FromMM(valor)


def anadir_pista(board, red, capa, inicio, fin, ancho) -> None:
    pista = pcbnew.PCB_TRACK(board)
    pista.SetStart(pcbnew.VECTOR2I(mm(inicio[0]), mm(inicio[1])))
    pista.SetEnd(pcbnew.VECTOR2I(mm(fin[0]), mm(fin[1])))
    pista.SetWidth(mm(ancho))
    pista.SetLayer({'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu}[capa])
    pista.SetNet(board.FindNet(red))
    board.Add(pista)


def anadir_via(board, red, posicion, diametro=0.6, taladro=0.3) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(mm(posicion[0]), mm(posicion[1])))
    via.SetWidth(mm(diametro))
    via.SetDrill(mm(taladro))
    via.SetNet(board.FindNet(red))
    board.Add(via)


def eliminar_via(board, red, posicion) -> None:
    objetivo = (mm(posicion[0]), mm(posicion[1]))
    for cobre in list(board.GetTracks()):
        if not isinstance(cobre, pcbnew.PCB_VIA):
            continue
        p = cobre.GetPosition()
        if cobre.GetNetname() == red and (p.x, p.y) == objetivo:
            board.Delete(cobre)
            return
    raise AssertionError(f'no existe la via {red} en {posicion}')


def ejecutar_mutacion(mutador) -> tuple[int, str]:
    anteriores = check_pcb.bp.TRACKS, check_pcb.bp.VIAS
    try:
        with tempfile.TemporaryDirectory() as directorio:
            board = pcbnew.LoadBoard(check_pcb.PCB)
            mutador(board)
            mutada = Path(directorio) / 'mutada.kicad_pcb'
            pcbnew.SaveBoard(str(mutada), board)
            salida = io.StringIO()
            with mock.patch.object(check_pcb, 'PCB', str(mutada)):
                with contextlib.redirect_stdout(salida):
                    resultado = check_pcb.main()
            return resultado, salida.getvalue()
    finally:
        check_pcb.bp.TRACKS, check_pcb.bp.VIAS = anteriores


class LeerRuteoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.board = pcbnew.LoadBoard(check_pcb.PCB)

    def test_lee_cada_segmento_y_via_commiteados(self) -> None:
        '''No puede omitir cobre real y sustituirlo por intencion generada.'''
        self.assertTrue(
            hasattr(check_pcb, 'leer_ruteo'),
            'falta leer_ruteo(board): la puerta todavia no lee el cobre',
        )

        tracks, vias = check_pcb.leer_ruteo(self.board)
        tracks_board = [
            t for t in self.board.GetTracks()
            if not isinstance(t, pcbnew.PCB_VIA)
        ]
        vias_board = [
            t for t in self.board.GetTracks()
            if isinstance(t, pcbnew.PCB_VIA)
        ]

        self.assertEqual(len(tracks), len(tracks_board))
        self.assertEqual(len(vias), len(vias_board))
        self.assertIn(
            ('/SEC_A', 'B.Cu', [(188.9, 97.5), (188.9, 100.3)], 1.0),
            tracks,
        )
        self.assertIn((80.1125, 110.375, 'GND', 0.6, 0.3), vias)

    def test_main_no_regenera_el_ruteo(self) -> None:
        '''Volver a llamar rutear(board) reintroduciria los 154 segundos.'''
        self.assertNotIn('bp.rutear', inspect.getsource(check_pcb.main))
        self.assertNotIn('bp.rutear', inspect.getsource(check_pcb.revisar_ruteo))
        with mock.patch.object(
            check_pcb.bp,
            'rutear',
            side_effect=AssertionError('main intento regenerar el ruteo'),
        ):
            with mock.patch.object(check_pcb, 'revisar_ruteo', return_value=[]):
                with contextlib.redirect_stdout(io.StringIO()):
                    try:
                        resultado = check_pcb.main()
                    except AssertionError as exc:
                        self.fail(str(exc))
        self.assertEqual(resultado, 0)

    def test_rechaza_una_via_no_pasante(self) -> None:
        board = pcbnew.LoadBoard(check_pcb.PCB)
        via = pcbnew.PCB_VIA(board)
        via.SetViaType(pcbnew.VIATYPE_MICROVIA)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetPosition(pcbnew.VECTOR2I(mm(50.0), mm(50.0)))
        via.SetWidth(mm(0.2))
        via.SetDrill(mm(0.1))
        board.Add(via)

        with self.assertRaisesRegex(AssertionError, 'via no pasante'):
            check_pcb.leer_ruteo(board)

    def test_rechaza_una_via_con_diametro_distinto_por_cara(self) -> None:
        board = pcbnew.LoadBoard(check_pcb.PCB)
        via = pcbnew.PCB_VIA(board)
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetPosition(pcbnew.VECTOR2I(mm(50.0), mm(50.0)))
        via.SetDrill(mm(0.3))
        padstack = via.Padstack()
        padstack.SetMode(pcbnew.PADSTACK.MODE_CUSTOM)
        padstack.SetSize(
            pcbnew.VECTOR2I(mm(0.6), mm(0.6)), pcbnew.F_Cu
        )
        padstack.SetSize(
            pcbnew.VECTOR2I(mm(0.8), mm(0.8)), pcbnew.B_Cu
        )
        board.Add(via)

        with self.assertRaisesRegex(AssertionError, 'diametro distinto'):
            check_pcb.leer_ruteo(board)

    def test_rechaza_una_zona_gnd_no_representada(self) -> None:
        zona = mock.Mock()
        zona.GetIsRuleArea.return_value = False
        zona.GetNetname.return_value = 'GND'
        board = mock.Mock()
        board.GetCopperLayerCount.return_value = 2
        board.Zones.return_value = [zona]
        board.GetDrawings.return_value = []
        board.GetTracks.return_value = []

        with self.assertRaisesRegex(AssertionError, 'zona GND'):
            check_pcb.leer_ruteo(board)

    def test_rechaza_un_shape_grafico_en_cobre(self) -> None:
        shape = mock.Mock()
        shape.GetLayer.return_value = pcbnew.F_Cu
        board = mock.Mock()
        board.GetCopperLayerCount.return_value = 2
        board.Zones.return_value = []
        board.GetDrawings.return_value = [shape]
        board.GetTracks.return_value = []

        with self.assertRaisesRegex(AssertionError, 'shape grafico'):
            check_pcb.leer_ruteo(board)

class FiltroAabbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.board = pcbnew.LoadBoard(check_pcb.PCB)

    def test_descarta_solo_si_las_cajas_ya_cumplen_el_umbral(self) -> None:
        self.assertTrue(
            hasattr(check_pcb.bp, '_aabb_descarta'),
            'falta la cota inferior AABB',
        )
        descarta = check_pcb.bp._aabb_descarta

        self.assertTrue(descarta((0, 0, 1, 1), (3, 0, 4, 1), 2.0))
        self.assertFalse(descarta((0, 0, 1, 1), (2.999, 0, 4, 1), 2.0))
        self.assertTrue(descarta((0, 0, 0, 0), (0.8, 0.8, 0.8, 0.8), 1.0))
        self.assertFalse(descarta((0, 0, 0, 0), (0.7, 0.7, 0.7, 0.7), 1.0))
        self.assertFalse(descarta((0, 0, 1, 1), (0.5, 0.5, 0.5, 0.5), 1.0))

    def test_segmento_largo_que_atraviesa_pad_tiene_distancia_cero(self) -> None:
        '''El cruce puede caer entre las muestras de la aproximacion vieja.'''
        distancia = check_pcb.bp.dist_seg_rect(
            (0.0, 0.0), (100.0, 0.0),
            52.5, 0.0, 0.2, 0.2,
        )

        self.assertEqual(distancia, 0.0)

    def test_pista_larga_que_atraviesa_pad_si_se_detecta(self) -> None:
        caja = mock.Mock()
        caja.GetLeft.return_value = mm(52.3)
        caja.GetRight.return_value = mm(52.7)
        caja.GetTop.return_value = mm(-0.2)
        caja.GetBottom.return_value = mm(0.2)
        caja.GetWidth.return_value = mm(0.4)
        caja.GetHeight.return_value = mm(0.4)
        capas = mock.Mock()
        capas.Contains.side_effect = lambda capa: capa == pcbnew.F_Cu
        pad = mock.Mock()
        pad.GetBoundingBox.return_value = caja
        pad.GetNetname.return_value = 'PAD_NET'
        pad.GetNumber.return_value = '1'
        pad.GetLayerSet.return_value = capas
        huella = mock.Mock()
        huella.GetReference.return_value = 'X1'
        huella.Pads.return_value = [pad]
        board = mock.Mock()
        board.GetFootprints.return_value = [huella]
        tracks = [
            ('TRACK_NET', 'F.Cu', [(0.0, 0.0), (100.0, 0.0)], 0.2),
        ]

        with ruteo_temporal(tracks, []):
            fallos = check_pcb.bp.revisar_pista_pad(board)

        self.assertEqual(len(fallos), 1)
        self.assertIn('TRACK_NET en F.Cu', fallos[0])
        self.assertIn('pad X1.1[PAD_NET]', fallos[0])

    def test_pistas_lejanas_no_calculan_distancia_exacta(self) -> None:
        tracks = [
            ('GND', 'F.Cu', [(0.0, 0.0), (1.0, 0.0)], 0.2),
            ('+5V', 'F.Cu', [(100.0, 100.0), (101.0, 100.0)], 0.2),
        ]
        with ruteo_temporal(tracks, []):
            with mock.patch.object(
                check_pcb.bp,
                'dist_seg',
                side_effect=AssertionError('calculo exacto innecesario'),
            ):
                try:
                    fallos = check_pcb.bp.revisar_pistas()
                except AssertionError as exc:
                    self.fail(str(exc))
        self.assertEqual(fallos, [])

    def test_pista_lejana_no_se_compara_con_cada_pad(self) -> None:
        tracks = [('GND', 'F.Cu', [(-1000.0, -1000.0), (-999.0, -1000.0)], 0.2)]
        with ruteo_temporal(tracks, []):
            with mock.patch.object(
                check_pcb.bp,
                'dist_seg_rect',
                side_effect=AssertionError('calculo pista-pad innecesario'),
            ):
                try:
                    fallos = check_pcb.bp.revisar_pista_pad(self.board)
                except AssertionError as exc:
                    self.fail(str(exc))
        self.assertEqual(fallos, [])

    def test_via_lejana_no_se_compara_con_cada_pad(self) -> None:
        vias = [(-1000.0, -1000.0, 'GND', 0.6, 0.3)]
        with ruteo_temporal([], vias):
            with mock.patch.object(
                check_pcb.bp,
                'dist_seg_rect',
                side_effect=AssertionError('calculo via-pad innecesario'),
            ):
                try:
                    fallos = check_pcb.bp.revisar_vias(self.board)
                except AssertionError as exc:
                    self.fail(str(exc))
        self.assertEqual(fallos, [])

    def test_via_cercana_a_pad_ajeno_si_se_detecta(self) -> None:
        vias = [(33.8, 66.0, 'GND', 0.6, 0.3)]
        with ruteo_temporal([], vias):
            fallos = check_pcb.bp.revisar_vias(self.board)

        self.assertEqual(len(fallos), 1)
        self.assertIn('via GND en (33.8,66.0)', fallos[0])
        self.assertIn('del pad C26.1', fallos[0])

    def test_via_cercana_a_pista_ajena_si_se_detecta(self) -> None:
        tracks = [
            ('/-12V9', 'F.Cu', [(77.0, 46.0), (79.0, 46.0)], 0.3),
        ]
        vias = [(78.0, 46.0, 'GND', 0.6, 0.3)]
        with ruteo_temporal(tracks, vias):
            fallos = check_pcb.bp.revisar_vias(self.board)

        self.assertEqual(len(fallos), 1)
        self.assertIn('via GND en (78.0,46.0)', fallos[0])
        self.assertIn('de pista /-12V9', fallos[0])

    def test_taladros_desiguales_usan_sus_diametros_reales(self) -> None:
        board = mock.Mock()
        board.GetFootprints.return_value = []
        vias = [
            (0.0, 0.0, 'GND', 1.2, 1.0),
            (0.8, 0.0, 'GND', 0.6, 0.3),
        ]
        with ruteo_temporal([], vias):
            fallos = check_pcb.bp.revisar_vias(board)

        self.assertEqual(len(fallos), 1)
        self.assertIn('taladros a 0.80mm', fallos[0])
        self.assertIn('hacen falta 0.9', fallos[0])

    def test_gnd_no_fusiona_capas_sin_una_via(self) -> None:
        tracks = [
            ('GND', 'F.Cu', [(0.0, 0.0), (1.0, 0.0)], 0.2),
            ('GND', 'B.Cu', [(0.0, 0.0), (1.0, 0.0)], 0.2),
        ]
        with ruteo_temporal(tracks, []):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(fallos, [])

    def test_bucle_gnd_con_enganche_interior_si_se_detecta(self) -> None:
        tracks = [
            ('GND', 'B.Cu', [(94.0, 66.0), (187.0, 66.0)], 1.0),
            ('GND', 'B.Cu', [(100.0, 66.0), (100.0, 67.0)], 0.2),
            ('GND', 'B.Cu', [(100.0, 67.0), (94.0, 66.0)], 0.2),
        ]
        with ruteo_temporal(tracks, []):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(len(fallos), 1)
        self.assertIn('bucle de GND', fallos[0])


class MutacionesDeLaPuertaTests(unittest.TestCase):
    def test_cinco_mutaciones_historicas_ponen_roja_la_puerta(self) -> None:
        def mutar(board) -> None:
            board.FindFootprintByReference('TP1').SetPosition(
                pcbnew.VECTOR2I(mm(94.1), mm(38.0))
            )
            anadir_pista(
                board, 'GND', 'B.Cu',
                (187.0, 74.0), (187.0, 76.1), 0.2,
            )
            anadir_pista(
                board, 'GND', 'B.Cu',
                (41.4, 99.0), (41.6, 101.0), 1.0,
            )
            anadir_pista(
                board, 'GND', 'F.Cu',
                (85.9, 88.0), (85.9, 87.5), 0.2,
            )
            anadir_via(board, 'GND', (80.1125, 110.375))

        resultado, salida = ejecutar_mutacion(mutar)

        self.assertEqual(resultado, 1)
        self.assertIn('FALLO: 5 en la placa', salida)
        firmas = {
            'pieza movida': ('TP1 esta en (94.10, 38.00)',),
            'cruce entre redes': ('cruce: /SEC_A~GND', 'en B.Cu'),
            'bucle GND': ('masa: bucle de GND',),
            'pista sobre pad': (
                'pista sobre pad: GND en F.Cu', 'pad U10.2',
            ),
            'via duplicada': (
                'via: via GND(80.1125,110.375)',
                'taladros a 0.00mm',
            ),
        }
        for mutacion, marcadores in firmas.items():
            with self.subTest(mutacion=mutacion):
                for marcador in marcadores:
                    self.assertIn(marcador, salida)

    def test_via_gnd_eliminada_deja_una_conexion_abierta(self) -> None:
        board = pcbnew.LoadBoard(check_pcb.PCB)
        eliminar_via(board, 'GND', (82.2, 88.0))
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / 'sin-via.kicad_pcb'
            pcbnew.SaveBoard(str(ruta), board)
            recargada = pcbnew.LoadBoard(str(ruta))

            self.assertEqual(check_pcb.conexiones_sin_rutear(recargada), 1)


if __name__ == '__main__':
    unittest.main()
