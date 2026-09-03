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

        # Contar con el mismo predicado que leer_ruteo no prueba nada: si el
        # downcast de pcbnew fallara, los dos lados darian cero y la igualdad
        # se cumpliria. Asi que ademas se comprueba la GEOMETRIA pieza a
        # pieza, reconstruida aqui desde el board, y un ancla concreta.
        esperados = {
            (t.GetNetname(), self.board.GetLayerName(t.GetLayer()),
             (t.GetStart().x / 1e6, t.GetStart().y / 1e6),
             (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6),
             t.GetWidth() / 1e6)
            for t in tracks_board
        }
        leidos = {(net, capa, tuple(pts[0]), tuple(pts[1]), ancho)
                  for net, capa, pts, ancho in tracks}
        self.assertEqual(leidos, esperados)

        # El ancla va sobre un carril de RED, que rutear_red traza a
        # coordenadas literales escritas en el guion. Lo que se mueve al
        # cambiar el arbol de masa o un fanout no sirve de ancla: ya paso.
        self.assertIn(('/L', 'F.Cu', [(38.0, 123.0), (126.0, 123.0)], 1.0),
                      tracks)

    def test_main_no_regenera_el_ruteo(self) -> None:
        '''Volver a llamar rutear(board) reintroduciria los 228,8 s.'''
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
        """Dos capas sobre la misma x,y NO estan unidas: un cruce no es un nodo.

        Sin este limite la regla inventaria conexiones donde solo hay cobre
        que pasa por encima de otro cobre, y cantaria bucles que no existen.
        """
        tracks = [
            ('GND', 'F.Cu', [(0.0, 0.0), (1.0, 0.0)], 0.2),
            ('GND', 'B.Cu', [(0.0, 0.0), (1.0, 0.0)], 0.2),
        ]
        with ruteo_temporal(tracks, []):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(fallos, [])

    def test_lazo_que_cierra_por_dos_vias_si_se_caza(self) -> None:
        """La espira de sec.7: ida por una cara, vuelta por la otra.

        Es LA forma en que un lazo aparece en una placa de dos capas con GND
        en las dos y 38 transiciones de capa. El comentario de la seccion del
        arbol dice que un lazo alrededor del puente es una espira de 100 Hz
        acoplada a todo; si la regla no ve esta, no ve ninguna de verdad.
        """
        tracks = [
            ('GND', 'F.Cu', [(0.0, 0.0), (10.0, 0.0)], 0.5),
            ('GND', 'B.Cu', [(0.0, 0.0), (10.0, 0.0)], 0.5),
        ]
        vias = [(0.0, 0.0, 'GND', 0.6, 0.3), (10.0, 0.0, 'GND', 0.6, 0.3)]
        with ruteo_temporal(tracks, vias):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(len(fallos), 1, fallos)
        self.assertIn('bucle de GND', fallos[0])
        self.assertIn('via', fallos[0])

    def test_lazo_de_cuatro_tramos_alternando_capa_si_se_caza(self) -> None:
        """El caso general: cuatro tramos, cuatro vias, una sola espira."""
        tracks = [
            ('GND', 'F.Cu', [(0.0, 0.0), (20.0, 0.0)], 0.5),
            ('GND', 'B.Cu', [(20.0, 0.0), (20.0, 20.0)], 0.5),
            ('GND', 'F.Cu', [(20.0, 20.0), (0.0, 20.0)], 0.5),
            ('GND', 'B.Cu', [(0.0, 20.0), (0.0, 0.0)], 0.5),
        ]
        vias = [(x, y, 'GND', 0.6, 0.3) for x, y in
                ((0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0))]
        with ruteo_temporal(tracks, vias):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(len(fallos), 1, fallos)

    def test_una_via_que_no_cierra_lazo_no_es_bucle(self) -> None:
        """Bajar de capa es lo normal: solo la SEGUNDA bajada cierra."""
        tracks = [
            ('GND', 'F.Cu', [(0.0, 0.0), (10.0, 0.0)], 0.5),
            ('GND', 'B.Cu', [(10.0, 0.0), (10.0, 10.0)], 0.5),
        ]
        vias = [(10.0, 0.0, 'GND', 0.6, 0.3)]
        with ruteo_temporal(tracks, vias):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(fallos, [])

    def test_extremos_a_media_micra_son_el_mismo_nodo(self) -> None:
        """El generador redondea los enganches y las vias con distinto paso.

        En la placa real la costilla acaba en 82.812 y la via esta en
        82.8125: 0.5 um. Con anchos de 1 mm esos dos cobres se solapan
        enteros, asi que son un nodo. Si la regla los separa, deja de ver el
        lazo que pasa por ahi.
        """
        tracks = [
            ('GND', 'B.Cu', [(0.0, 0.0), (10.0, 0.0)], 1.0),
            ('GND', 'B.Cu', [(10.0005, 0.0), (10.0, 6.0)], 1.0),
            ('GND', 'B.Cu', [(10.0, 6.0), (0.0, 0.0)], 1.0),
        ]
        with ruteo_temporal(tracks, []):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(len(fallos), 1, fallos)

    def test_la_placa_commiteada_no_tiene_ni_un_lazo_de_masa(self) -> None:
        """sec.14.5: «no hay ni un bucle». La puerta lo asevera, no lo supone."""
        tracks, vias = check_pcb.leer_ruteo(self.board)
        with ruteo_temporal(tracks, vias):
            fallos = check_pcb.bp.revisar_estrella()

        self.assertEqual(fallos, [], f"{len(fallos)} lazos de masa: {fallos}")

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


# Las mutaciones historicas, UNA POR UNA. Cada fila trae el mutador, el trozo
# de la linea de fallo que TIENE que aparecer por su causa, y CUANTAS lineas
# tiene que producir en total.
#
# El total va escrito fila a fila y no supuesto igual a uno: dos de estas
# mutaciones disparan dos reglas de verdad -- el cobre que se cruza con otra
# red y el que se sube a un pad ajeno se quedan ademas colgando por una punta,
# y eso es un munon de verdad, no ruido. Escribirlo es lo que hace que una
# regla nueva salga a la luz en la revision en vez de colarse en un total.
#
# Se aplican por separado a proposito. Juntas, el unico aserto posible era el
# total ("FALLO: 5") y ese numero no distingue "las cinco se cazan" de "una
# aporta cero y otra aporta dos": tapaba justo lo que el canario existe para
# ver. Por separado, si manana una deja de cazarse, su fila se pone roja con
# su nombre.
MUTACIONES = [
    (
        'pieza movida a mano',
        lambda b: b.FindFootprintByReference('TP1').SetPosition(
            pcbnew.VECTOR2I(mm(94.1), mm(38.0))),
        'TP1 esta en (94.10, 38.00)', 1,
    ),
    (
        # Sale de una via de GND que existe y se mete por encima del carril de
        # -12 V. Dos lineas: el cruce y la punta libre, que tambien es un
        # defecto de verdad -- una pista anadida a mano siempre deja una.
        'cruce entre redes',
        lambda b: anadir_pista(
            b, 'GND', 'F.Cu', (52.775, 89.7), (52.775, 83.4), 0.2),
        'cruce: GND~-12V en F.Cu', 2,
    ),
    (
        'bucle de masa en una capa',
        lambda b: anadir_pista(
            b, 'GND', 'B.Cu', (41.4, 99.0), (41.6, 101.0), 1.0),
        'masa: bucle de GND al cerrar por pista', 1,
    ),
    (
        # (16.525, 66.0) es uno de los tres sitios donde el arbol de masa ya
        # tiene cobre en las DOS caras sin via que las una. Cosiendolas ahi
        # se cierra la espira de sec.7: ida por arriba, vuelta por abajo.
        'bucle de masa que cruza de capa por una via',
        lambda b: anadir_via(b, 'GND', (16.525, 66.0)),
        'masa: bucle de GND al cerrar por via', 1,
    ),
    (
        'pista sobre pad ajeno',
        lambda b: anadir_pista(
            b, 'GND', 'F.Cu', (85.9, 88.0), (85.9, 87.5), 0.2),
        'pista sobre pad: GND en F.Cu', 2,
    ),
    (
        # Un rabito de masa que sale de la costilla y muere en el aire. Es lo
        # que dejaba la poda antes de recortar, y lo que el DRC manual llama
        # track_dangling: aqui lo caza la puerta que corre sola.
        'munon de masa colgando',
        lambda b: anadir_pista(
            b, 'GND', 'B.Cu', (17.175, 79.0), (14.0, 79.0), 1.0),
        'munon: cobre de GND sin servir', 1,
    ),
    (
        'via duplicada sobre otra',
        lambda b: anadir_via(b, 'GND', (82.2, 88.0)),
        'taladros a 0.00mm', 1,
    ),
]


class UmbralDelFiltroTests(unittest.TestCase):
    """El limite que se le pasa a _aabb_descarta, no el predicado.

    El predicado ya tiene su prueba. Lo que no la tenia es el ARGUMENTO en
    cada sitio donde se llama: quitarle el ancho de pista al limite dejaba
    los 19 canarios en verde, porque todos los testigos estaban o solapados
    (distancia entre cajas = 0, ciega al limite) o a 100-1400 mm (idem).
    Estos tres viven en la banda [minimo, minimo + ancho/2), que es la unica
    donde el termino del ancho decide.
    """

    @staticmethod
    def _pad_falso(x0, y0, x1, y1, red, capas=(pcbnew.F_Cu,)):
        caja = mock.Mock()
        caja.GetLeft.return_value = mm(x0)
        caja.GetRight.return_value = mm(x1)
        caja.GetTop.return_value = mm(y0)
        caja.GetBottom.return_value = mm(y1)
        caja.GetWidth.return_value = mm(x1 - x0)
        caja.GetHeight.return_value = mm(y1 - y0)
        juego = mock.Mock()
        juego.Contains.side_effect = lambda c: c in capas
        pad = mock.Mock()
        pad.GetBoundingBox.return_value = caja
        pad.GetNetname.return_value = red
        pad.GetNumber.return_value = '1'
        pad.GetLayerSet.return_value = juego
        huella = mock.Mock()
        huella.GetReference.return_value = 'X1'
        huella.Pads.return_value = [pad]
        board = mock.Mock()
        board.GetFootprints.return_value = [huella]
        return board

    def test_pista_a_030mm_de_un_pad_ajeno_se_caza(self) -> None:
        """0.30 mm entre cajas, ancho 1.0: el limite real es 0.627.

        Sin el termino del ancho el limite seria 0.127, la caja quedaria
        descartada y la infraccion no se miraria nunca.
        """
        board = self._pad_falso(10.0, 9.5, 11.0, 10.5, 'OTRA')
        tracks = [('GND', 'F.Cu', [(5.0, 10.0), (9.7, 10.0)], 1.0)]

        with ruteo_temporal(tracks, []):
            fallos = check_pcb.bp.revisar_pista_pad(board)

        self.assertEqual(len(fallos), 1, fallos)
        self.assertIn('GND en F.Cu', fallos[0])

    def test_dos_pistas_a_030mm_se_cazan(self) -> None:
        """Mismo hueco, entre pistas: limite real 0.127 + (1.0+1.0)/2."""
        tracks = [
            ('GND', 'F.Cu', [(0.0, 10.0), (5.0, 10.0)], 1.0),
            ('+5V', 'F.Cu', [(5.3, 10.0), (9.0, 10.0)], 1.0),
        ]
        with ruteo_temporal(tracks, []):
            fallos = check_pcb.bp.revisar_pistas()

        self.assertEqual(len(fallos), 1, fallos)

    def test_via_a_040mm_de_un_pad_ajeno_se_caza(self) -> None:
        """La via aporta su radio al limite: 0.127 + 0.3 = 0.427."""
        board = self._pad_falso(10.0, 9.5, 11.0, 10.5, 'OTRA')
        vias = [(9.6, 10.0, 'GND', 0.6, 0.3)]

        with ruteo_temporal([], vias):
            fallos = check_pcb.bp.revisar_vias(board)

        self.assertEqual(len(fallos), 1, fallos)


class LeerRuteoRechazaTests(unittest.TestCase):
    """Los guardias de «no se representar esto». Media docena no tenia canario.

    El argumento entero para leer el cobre commiteado en vez de regenerarlo es
    que la puerta mide el artefacto. Eso solo vale si la puerta se planta
    cuando el artefacto trae algo que no sabe traducir, en vez de traducirlo
    mal en silencio. La via no circular es la peor: sin el guardia se lee su
    diametro por un solo eje y la separacion sale medida de menos.
    """

    def test_rechaza_un_arco_de_cobre(self) -> None:
        board = pcbnew.LoadBoard(check_pcb.PCB)
        arco = pcbnew.PCB_ARC(board)
        arco.SetStart(pcbnew.VECTOR2I(mm(50.0), mm(50.0)))
        arco.SetMid(pcbnew.VECTOR2I(mm(51.0), mm(51.0)))
        arco.SetEnd(pcbnew.VECTOR2I(mm(52.0), mm(50.0)))
        arco.SetWidth(mm(0.3))
        arco.SetLayer(pcbnew.F_Cu)
        arco.SetNet(board.FindNet('GND'))
        board.Add(arco)

        with self.assertRaisesRegex(AssertionError, 'arco'):
            check_pcb.leer_ruteo(board)

    def test_rechaza_una_via_no_circular(self) -> None:
        board = pcbnew.LoadBoard(check_pcb.PCB)
        via = pcbnew.PCB_VIA(board)
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetPosition(pcbnew.VECTOR2I(mm(50.0), mm(50.0)))
        via.SetDrill(mm(0.3))
        padstack = via.Padstack()
        padstack.SetMode(pcbnew.PADSTACK.MODE_CUSTOM)
        for capa in (pcbnew.F_Cu, pcbnew.B_Cu):
            padstack.SetSize(pcbnew.VECTOR2I(mm(0.8), mm(0.6)), capa)
        board.Add(via)

        with self.assertRaisesRegex(AssertionError, 'no circular'):
            check_pcb.leer_ruteo(board)

    def test_un_cobre_que_no_sabe_leer_sale_como_HUECO_no_como_traceback(
            self) -> None:
        """Codigo 2 con el motivo escrito: la convencion de gates.py.

        Un traceback no lo clasifica el resumen, y un HUECO silencioso es
        peor que un fallo. Aqui tiene que salir el hueco Y su causa.
        """
        def mutar(board) -> None:
            arco = pcbnew.PCB_ARC(board)
            arco.SetStart(pcbnew.VECTOR2I(mm(50.0), mm(50.0)))
            arco.SetMid(pcbnew.VECTOR2I(mm(51.0), mm(51.0)))
            arco.SetEnd(pcbnew.VECTOR2I(mm(52.0), mm(50.0)))
            arco.SetWidth(mm(0.3))
            arco.SetLayer(pcbnew.F_Cu)
            arco.SetNet(board.FindNet('GND'))
            board.Add(arco)

        resultado, salida = ejecutar_mutacion(mutar)

        self.assertEqual(resultado, 2, salida)
        self.assertIn('HUECO:', salida)
        self.assertIn('arco', salida)


class MutacionesDeLaPuertaTests(unittest.TestCase):
    def test_la_placa_commiteada_pasa_la_puerta_entera(self) -> None:
        """El cero de partida, aparte. Sin el, cada canario de mutacion
        estaria aseverando dos cosas a la vez y no podrias saber cual fallo.
        """
        resultado, salida = ejecutar_mutacion(lambda board: None)

        self.assertEqual(resultado, 0, salida)
        self.assertIn('OK: colocacion, ruteo guardado', salida)

    def test_cada_mutacion_historica_pone_roja_la_puerta(self) -> None:
        """Una linea de fallo, la suya, y ninguna mas.

        Las dos mitades van juntas a proposito: "se caza" sin "y solo esa"
        deja pasar que una mutacion aporte dos lineas y la vecina cero, que
        es lo que el aserto de "FALLO: 5" daba por hecho sin comprobarlo.
        """
        for nombre, mutador, marcador, esperadas in MUTACIONES:
            with self.subTest(mutacion=nombre):
                resultado, salida = ejecutar_mutacion(mutador)

                self.assertEqual(resultado, 1, salida)
                lineas = [x for x in salida.splitlines()
                          if x.startswith('  - ')]
                casan = [x for x in lineas if marcador in x]
                self.assertEqual(
                    len(casan), 1,
                    f"{nombre}: {len(casan)} lineas con {marcador!r} "
                    f"entre {lineas}")
                self.assertEqual(
                    len(lineas), esperadas,
                    f"{nombre} produjo {len(lineas)} fallos y su fila "
                    f"declara {esperadas}: {lineas}")

    def test_via_gnd_eliminada_deja_una_conexion_abierta(self) -> None:
        """Y la puerta ENTERA se pone roja por ello, no solo el contador."""
        resultado, salida = ejecutar_mutacion(
            lambda b: eliminar_via(b, 'GND', (82.2, 88.0)))

        self.assertEqual(resultado, 1, salida)
        self.assertIn('ruteo: quedan 1 conexiones sin rutear', salida)


if __name__ == '__main__':
    unittest.main()
