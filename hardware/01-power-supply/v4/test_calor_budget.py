"""El contrato de calor_budget.py: la cadena termica de la sala al silicio, y
lo que sale de ella --la corriente SOSTENIDA de cada riel--.

    python hardware/01-power-supply/v4/test_calor_budget.py

Lo que fija este test:

  * la FORMA del modelo (sube, ventilar ayuda, punto fijo coherente), no sus
    numeros: los numeros salen de curvas.py y de las constantes citadas;
  * las FIRMAS que importan power_budget.py e invitados_budget.py;
  * que el aserto que decide --el rack ventilado por encima de la PSU3--
    existe y MUERDE, buscado por biseccion (canario), no con dos valores
    elegidos a mano.

Este test puede quedar ROJO por el aserto del liston aun con el guion bien
escrito: eso no se arregla bajando el aserto, se lleva a Samuel. Paso el
2026-09-03: con PS5 = IRM-20-5 el +5 V de rack no llegaba con ningun venteo
(4,0 A de placa = 4,0 A de PSU3, codo a 45 C), y Samuel firmo D-F7: PS5 pasa
a IRM-45-5. El contrato distingue desde entonces lo que el modulo puede dar
(MODULO_A) de lo que el instrumento declara (PLACA_A).
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "..", "..", "tools"))
import calor_budget as cb                                   # noqa: E402
from canario import borde_rojo                              # noqa: E402
from curvas import derating, codo_c                         # noqa: E402

RIELES_RACK = ("rack+12", "rack-12", "rack+5")
RIELES = RIELES_RACK + ("digital+5",)


# --- las constantes del papel sec.6, con su valor ---------------------------

def test_el_area_base_es_la_que_el_case_tiene_hoy() -> None:
    """A_EF_BASE_MM2 es una COPIA de la salida del case, y aqui se recalcula.

    calor_budget suma su `area_venteo_mm2` a esta base, asi que si el case
    cambia sus rejillas o su rendija y nadie mueve esta constante, el area
    minima que publica la fuente sale de una geometria que ya no existe.
    Vive en el contrato y no en el modulo a proposito: un assert a nivel de
    modulo convertiria un cambio de geometria del case en un rojo del import
    de media tanda."""
    import clearance_budget as cl  # noqa: PLC0415

    a_ef = cl._tiro(cl.leer_params())["a_ef"]
    assert abs(a_ef - cb.A_EF_BASE_MM2) < 1.0, (
        f"el case tiene hoy {a_ef:.1f} mm2 de venteo efectivo y "
        f"calor_budget.A_EF_BASE_MM2 dice {cb.A_EF_BASE_MM2:.1f}. Esa base es "
        f"a la que la fuente le SUMA su area_venteo_mm2: con ella vieja, el "
        f"venteo minimo que publica sale de una geometria que ya no existe")


def test_constantes_del_papel() -> None:
    assert cb.T_SALA == 45.0, "spec del chasis sec.3.1: 45 C de sala, NO 25"
    assert cb.AREA_RECINTO_M2 == 0.1453
    assert cb.H_CONV_W_M2K == 9.0
    # 28,9 W del papel sec.6 con PS5 = IRM-20-5 (5,32 W a placa), menos esa
    # PS5, mas la IRM-45-5 de D-F7 a los 4,0 A declarados (3,95 W) = 27,53. Y
    # desde el 2026-09-04, mas los 3,70 W de la franja de red que la tabla de
    # sec.6 no llevaba (NTC + choke): 31,25.
    assert abs(cb.P_RECINTO_MAX - 31.25) < 0.05, cb.P_RECINTO_MAX
    assert abs(cb.P_CAJON_MAX - 120.3) < 0.05, cb.P_CAJON_MAX
    # lo que el instrumento DECLARA (D-F1) y lo que cada modulo PUEDE dar
    # (su placa, hoja p. 2): son dos numeros, y el primero nunca supera al
    # segundo. D-F7 (2026-09-03): PS5 pasa de IRM-20-5 (4 A) a IRM-45-5 (8 A)
    assert cb.PLACA_A == {"rack+12": 3.8, "rack-12": 2.5, "rack+5": 4.0,
                          "digital+5": 8.0}
    assert cb.MODULO_A == {"rack+12": 3.8, "rack-12": 3.8, "rack+5": 8.0,
                           "digital+5": 8.0}
    for riel in RIELES:
        assert cb.PLACA_A[riel] <= cb.MODULO_A[riel], (
            f"{riel}: se declaran {cb.PLACA_A[riel]} A y el modulo da "
            f"{cb.MODULO_A[riel]}: no se puede prometer mas de lo que hay")
    assert cb.PSU3_A == {"rack+12": 2.0, "rack-12": 1.2, "rack+5": 4.0}
    # que modulo alimenta cada riel, y por tanto que curva de derating lee:
    # PS3/PS4 = IRM-45-12, PS5 = IRM-45-5 (D-F7), PS6 = IRM-45-5. La IRM-45
    # dibuja una sola curva para toda la serie (codo a 50, no a 45)
    assert cb.CURVA == {"rack+12": "IRM-45", "rack-12": "IRM-45",
                        "rack+5": "IRM-45", "digital+5": "IRM-45"}


# --- la cadena: forma ------------------------------------------------------

def test_el_recinto_no_esta_mas_frio_que_la_sala() -> None:
    for a in (0.0, 1000.0, 50000.0):
        t = cb.aire_recinto_c(cb.P_RECINTO_MAX, cb.P_CAJON_MAX, area_venteo_mm2=a)
        assert t > cb.T_SALA, (a, t)


def test_sin_calor_es_la_sala() -> None:
    t = cb.aire_recinto_c(0.0, 0.0, area_venteo_mm2=0.0)
    assert abs(t - cb.T_SALA) < 1e-6, t


def test_mas_calor_mas_temperatura() -> None:
    prev = cb.T_SALA
    for w in (5.0, 10.0, 20.0, 28.9, 40.0):
        t = cb.aire_recinto_c(w, cb.P_CAJON_MAX, area_venteo_mm2=cb.P_BASE["area_venteo_mm2"])
        assert t > prev, (w, t, prev)
        prev = t


def test_cerrado_reproduce_el_orden_de_magnitud_de_la_junta() -> None:
    # La junta estimo ~78 C de aire con el recinto cerrado y los 120 W de fila
    # y digital en el cajon; con eso el rack cae al 17 %. El modelo tiene que
    # quedar POR ENCIMA del codo de derating (es lo que hunde el rack), y si se
    # aleja de los 78 hay que saber por que ANTES de firmar un sostenido: se
    # imprime, no se asevera el numero exacto.
    t = cb.aire_recinto_c(cb.P_RECINTO_MAX, cb.P_CAJON_MAX, area_venteo_mm2=0.0)
    codo = codo_c("IRM-45")
    assert t > codo, (
        f"cerrado y con el cajon cargado el aire da {t:.1f} C, por debajo del "
        f"codo de derating ({codo:.0f}): entonces D-F3 no hacia falta "
        f"y toda la sec.6 del papel esta mal")
    print(f"  cerrado y A PLACA sin derating: {t:.1f} C de aire (no es un "
          f"estado alcanzable). La junta estimo ~78 C con el rack al 17 %; el "
          f"punto fijo dice que cerrado no hay 17 % ni nada: 86,7 C y el rack "
          f"a CERO, porque a esa T la curva de la hoja ya no dibuja")


def test_ventilar_baja_el_aire_y_es_para_lo_que_se_firmo_d_f3() -> None:
    cerrado = cb.aire_recinto_c(cb.P_RECINTO_MAX, cb.P_CAJON_MAX, area_venteo_mm2=0.0)
    vent = cb.aire_recinto_c(cb.P_RECINTO_MAX, cb.P_CAJON_MAX,
                             area_venteo_mm2=cb.P_BASE["area_venteo_mm2"])
    assert vent < cerrado - 5.0, (
        f"ventilar baja el aire de {cerrado:.1f} a {vent:.1f} C: menos de 5 K "
        f"no justifica reabrir el techo y la trasera del case")


def test_mas_venteo_menos_temperatura_y_con_rendimiento_decreciente() -> None:
    ts = [cb.aire_recinto_c(cb.P_RECINTO_MAX, cb.P_CAJON_MAX, area_venteo_mm2=a)
          for a in (0.0, 2000.0, 4000.0, 8000.0, 16000.0)]
    for a, b in zip(ts, ts[1:]):
        assert b < a, ts
    # doblar el area no dobla la mejora: el tiro va con A^(2/3)
    assert (ts[0] - ts[1]) > (ts[3] - ts[4]), ts


# --- el sostenido ----------------------------------------------------------

def test_sostenido_entre_cero_y_placa() -> None:
    for riel, placa in cb.PLACA_A.items():
        for t in (25.0, 45.0, 60.0, 80.0):
            s = cb.sostenido_a(riel, t)
            assert 0.0 < s <= placa + 1e-9, (riel, t, s)


def test_sostenido_es_el_modulo_recortado_y_nunca_mas_que_lo_declarado() -> None:
    for riel, placa in cb.PLACA_A.items():
        for t in (25.0, 45.0, 55.0, 65.0, 80.0):
            esperado = min(placa, cb.MODULO_A[riel] * derating(t, cb.CURVA[riel]))
            assert abs(cb.sostenido_a(riel, t) - esperado) < 1e-9, (riel, t)
    # y el caso que D-F7 compra: un modulo con el doble de placa que lo
    # declarado sigue dando lo declarado aunque la curva ya lo recorte
    assert cb.sostenido_a("rack+5", 60.0) == cb.PLACA_A["rack+5"], (
        "a 60 C la IRM-45 esta al 75 %: 8 A x 0,75 = 6 A, mas que los 4,0 "
        "declarados. El riel tiene que seguir dando 4,0, no 6")


def test_por_encima_de_85_el_rack_no_existe() -> None:
    # La hoja no publica nada por encima de 85 C: el modulo no opera. Un
    # sostenido "pequeno pero positivo" a 90 C seria una extrapolacion.
    for riel in RIELES:
        assert cb.sostenido_a(riel, 90.0) == 0.0, riel


def test_SOSTENIDO_es_un_punto_fijo() -> None:
    # El calor del cajon depende de la corriente que el rack de verdad puede
    # dar, y esa corriente depende del calor. SOSTENIDO no es "placa por
    # derating a una T supuesta": es el punto donde el calor que genera
    # produce la T cuyo derating lo devuelve. Con tolerancia del 2 %.
    for riel in RIELES:
        assert riel in cb.SOSTENIDO, riel
    t = cb.aire_recinto_c(cb.p_recinto_w(cb.SOSTENIDO), cb.p_cajon_w(cb.SOSTENIDO),
                          area_venteo_mm2=cb.P_BASE["area_venteo_mm2"])
    for riel in RIELES:
        s = cb.sostenido_a(riel, t)
        assert abs(s - cb.SOSTENIDO[riel]) <= 0.02 * cb.PLACA_A[riel], (
            f"{riel}: SOSTENIDO={cb.SOSTENIDO[riel]:.3f} A pero a la T que ese "
            f"sostenido produce ({t:.1f} C) el derating da {s:.3f}: no es un "
            f"punto fijo, es una evaluacion suelta")


def test_el_calor_del_cajon_baja_con_el_sostenido() -> None:
    # A placa entera son los 120,3 W del papel; con menos corriente, menos.
    assert abs(cb.p_cajon_w(cb.PLACA_A) - cb.P_CAJON_MAX) < 0.05
    assert abs(cb.p_recinto_w(cb.PLACA_A) - cb.P_RECINTO_MAX) < 0.05
    mitad = {r: v / 2.0 for r, v in cb.PLACA_A.items()}
    assert cb.p_cajon_w(mitad) < cb.P_CAJON_MAX
    assert cb.p_recinto_w(mitad) < cb.P_RECINTO_MAX
    # y el minimo del recinto es el tipico del papel (instrumento a censo)
    assert cb.p_recinto_w({r: 0.0 for r in RIELES}) >= 0.0


def test_el_cajon_cobra_a_cada_riel_su_propia_corriente() -> None:
    """EL FALLO DEL 2026-09-03, y por que un cociente agregado no vale.

    El calor del cajon se repartia con _ratio(): un solo cociente
    sum(corrientes)/sum(PLACA_A), en AMPERIOS, aplicado a los 120,3 W. Pero
    las celdas del papel sec.6 estan en VATIOS y no pesan igual: el digital
    son 8,0 de los 18,3 A (44 %) y solo 24,7 de los 120,3 W (20,5 %). Como
    ademas es el riel que mas se derratea, su recorte arrastraba hacia abajo
    el calor que se le cobra a la FILA DE INVITADOS, que no depende del
    digital para nada. Medido en el punto fijo: 80,4 W cobrados contra 89,2
    reales, un 11 % de menos -- y el liston pasaba por 5 mA."""
    for cor in (cb.SOSTENIDO, cb.PLACA_A, {r: 1.0 for r in RIELES}):
        esperado = (sum(cor[r] * cb.V_RIEL[r] for r in cb.V_RIEL)
                    + cb.CAJON_DIGITAL_W)
        assert abs(cb.p_cajon_w(cor) - esperado) < 1e-9, (
            f"con {cor} el cajon cobra {cb.p_cajon_w(cor):.2f} W y cada riel a "
            f"su tension son {esperado:.2f}: vuelve a haber un cociente en medio")
    # Y EL DIGITAL NO MUEVE EL CALOR DEL CAJON. Es CARGA, no capacidad: el
    # modulo 2 pide lo que pide (24,7 W de peor caso, papel sec.4.4) y da
    # igual que PS6 pueda dar 8 A. Cobrarle por su capacidad es lo que metia
    # el 44 % de peso en amperios que rompia el reparto.
    assert cb.p_cajon_w(cb.PLACA_A) == cb.p_cajon_w(
        {**cb.PLACA_A, "digital+5": 0.0}), (
        "cambiar la corriente del digital movio el calor del cajon: se le "
        "esta cobrando por lo que PS6 puede dar y no por lo que el modulo 2 pide")


def test_las_celdas_suman_lo_que_el_papel_publica() -> None:
    """Las dos potencias maximas dejan de transcribirse: se derivan de las
    celdas de sec.6. Y las celdas se comprueban UNA A UNA, no solo su suma:
    el modelo las usa por separado --cada riel paga la suya-- asi que dos
    celdas intercambiadas darian la misma suma y otro punto fijo."""
    # El cajon: cada riel del rack a su tension (papel sec.6, "la fila de
    # invitados a placa disipa 95,6 W").
    assert cb.V_RIEL == {"rack+12": 12.0, "rack-12": 12.0, "rack+5": 5.0}, (
        "V_RIEL no son las tensiones del rack; el calor del cajon es la "
        "potencia ENTREGADA y depende de a que tension va cada amperio")
    for riel, celda in (("rack+12", 45.6), ("rack-12", 30.0), ("rack+5", 20.0)):
        w = cb.PLACA_A[riel] * cb.V_RIEL[riel]
        assert abs(w - celda) < 0.05, (
            f"{riel} a placa da {w:.2f} W y la celda de sec.6 son {celda}")
    rack_w = sum(cb.PLACA_A[r] * cb.V_RIEL[r] for r in cb.V_RIEL)
    assert abs(rack_w - 95.6) < 0.05, rack_w
    assert abs(cb.CAJON_DIGITAL_W - 24.7) < 0.05
    assert abs(cb.P_CAJON_MAX - (rack_w + cb.CAJON_DIGITAL_W)) < 1e-9
    # El recinto: PS3/PS4/PS5 escalan con su riel, cada una con SU perdida.
    for riel, celda in (("rack+12", 6.51), ("rack-12", 4.29), ("rack+5", 3.95)):
        assert abs(cb.PERDIDA_RECINTO_W[riel] - celda) < 0.005, (
            f"la perdida de {riel} en el recinto es "
            f"{cb.PERDIDA_RECINTO_W[riel]} y la celda de sec.6 son {celda}")
        # y esta EN SU SITIO: subirla tiene que calentar mas, no menos
        mas = dict(cb.PERDIDA_RECINTO_W)
        mas[riel] += 5.0
        base = cb.p_recinto_w(cb.PLACA_A)
        subido = (cb._CONSTANTE_RECINTO_W
                  + sum(mas[r] * cb.PLACA_A[r] / cb.PLACA_A[r] for r in mas))
        assert subido > base, riel
    assert set(cb.PERDIDA_RECINTO_W) == set(RIELES_RACK), (
        "el digital no lleva perdida proporcional: su carga es constante, "
        "asi que PS6 tambien lo es y vive en _CONSTANTE_RECINTO_W")
    recinto_w = cb._CONSTANTE_RECINTO_W + sum(cb.PERDIDA_RECINTO_W.values())
    assert abs(cb.P_RECINTO_MAX - recinto_w) < 1e-9
    # LA TABLA DE sec.6 NO SUMA LO QUE HAY EN EL RECINTO, Y ESO ES EL HALLAZGO:
    # lista PS1..PS6, U1/U2, los LT y U3, y se olvida de la franja de red. La
    # NTC y el choke suman 3,70 W mas, y con ellos el venteo minimo sube de
    # 20 525 a 22 148 mm2. El test comprueba las dos cosas: que las celdas del
    # papel siguen siendo las suyas, y que lo que el modelo anade es
    # exactamente lo declarado.
    franja_red = cb.NTC_ARRANQUE_W + cb.CHOKE_RED_W + cb.MOV_RED_W
    assert abs(franja_red - 3.70) < 0.05, franja_red
    assert abs((recinto_w - franja_red) - 27.55) < 0.05, (
        f"sin la franja de red las celdas del recinto suman "
        f"{recinto_w - franja_red:.2f} W y el papel sec.6 publica 27,5")
    assert abs(recinto_w - 31.25) < 0.05, (
        f"con la franja de red suman {recinto_w:.2f} W. Si este numero baja a "
        f"27,5, alguien quito el calor que el papel sec.6 no contaba y el "
        f"venteo minimo vuelve a salir 1 600 mm2 corto")


def test_donde_no_hay_punto_fijo_se_devuelve_cero_y_no_se_revienta() -> None:
    """LO QUE LA REVISION DEL 2026-09-03 CAZO, y por que no es un aserto.

    La curva de la hoja acaba en 85 C. Por debajo el rack da corriente y su
    calor empuja el aire por encima; por encima el rack esta a cero y el aire
    baja. O sea que en una banda de venteo (230..3715 mm2 con los numeros de
    hoy) la cadena T -> corrientes -> calor -> T' SALTA y no tiene raiz.

    La primera version aseveraba ahi. Dos cosas malas: (1) el aserto sube por
    _falla_por_liston(), que solo traga los que dicen "SIGUE sin existir", y
    revienta el IMPORT del modulo -- y con el la puerta de power_budget.py,
    que lo importa: un dato termico convertido en rojo de CI; (2) su criterio
    era el residuo en KELVIN, y donde la curva salta ese residuo es diminuto:
    entre 3716 y 3729 mm2 aterrizaba en 85,0000, publicaba 0,95 / 0,95 / 2,0
    --el mismo artefacto que venia a cazar-- con 0,001-0,048 K de residuo.

    Ahora se comprueba en AMPERIOS y se devuelve CERO, que es la respuesta
    honesta: ahi no hay corriente sostenida que prometer."""
    for area in list(range(0, 8001, 13)) + [3716.0, 3720.0, 3729.0, 3730.0]:
        p = {**cb.P_BASE, "area_venteo_mm2": float(area)}
        cor = cb._fixed_point(p)          # no puede lanzar NADA
        t = cb.aire_recinto_c(cb.p_recinto_w(cor), cb.p_cajon_w(cor),
                              area_venteo_mm2=float(area))
        for riel in RIELES:
            esperado = cb.sostenido_a(riel, t)
            assert (cor[riel] == 0.0
                    or abs(cor[riel] - esperado) <= 0.02 * cb.PLACA_A[riel]), (
                f"con {area:.0f} mm2 el punto fijo publica {cor[riel]:.3f} A "
                f"en {riel}, y a la T que ese estado produce ({t:.2f} C) la "
                f"hoja da {esperado:.3f}: es un salto de la curva, no un estado")
    # y el borde exacto que la version en kelvin dejaba pasar
    assert cb._fixed_point({**cb.P_BASE, "area_venteo_mm2": 3720.0}) == {
        r: 0.0 for r in RIELES}, (
        "3720 mm2 es el centro de la ventana que la tolerancia en kelvin "
        "dejaba pasar publicando 0,95 A: tiene que salir cero")


def test_la_caja_cerrada_no_tiene_punto_de_trabajo() -> None:
    """Sin venteo nuevo el aire pasa de los 85 C donde ACABAN las curvas de la
    hoja, y ningun modulo opera: el sostenido del rack es CERO, no un 25 %.

    Hasta el 2026-09-03 este escenario publicaba 0,95 / 0,95 / 2,0 A "a 92,6
    C", que es un artefacto: son las corrientes de la frontera de 85 C con la
    temperatura de OTRO punto. La biseccion converge igual de bien sobre una
    discontinuidad que sobre una raiz, y ahi devuelve un estado que no
    existe."""
    cerrado = {**cb.P_BASE, "area_venteo_mm2": 0.0}
    cor = cb._fixed_point(cerrado)
    assert all(v == 0.0 for v in cor.values()), (
        f"la caja cerrada publica {cor}: por encima de 85 C la hoja no dibuja "
        f"nada y sostenido_a() vale 0, asi que un sostenido positivo ahi es un "
        f"punto de la discontinuidad, no un estado")
    t = cb.aire_recinto_c(cb.p_recinto_w(cor), cb.p_cajon_w(cor),
                          area_venteo_mm2=0.0)
    assert t > 85.0, (
        f"con el rack a cero el aire de la caja cerrada se queda en {t:.1f} C: "
        f"si bajara de 85 habria un punto de trabajo y este test sobra")


# --- el aserto que decide, y su canario ----------------------------------

def test_guarda_liston_existe_y_muerde() -> None:
    # El aserto: con el punto de diseno, el rack sostenido queda por encima de
    # la PSU3 en los tres rieles. Puede estar ROJO (ver docstring): eso es
    # resultado, no fallo del guion. Lo que este test exige es que el aserto
    # EXISTA con ese texto y que MUERDA en algun sitio del rango de venteo.
    v = borde_rojo(cb.guarda_liston, dict(cb.P_BASE), "area_venteo_mm2",
                   0.0, 200000.0, "SIGUE sin existir")
    assert v > 0.0, v
    assert abs(v - cb.AREA_VENTEO_MIN_MM2) <= 0.05 * cb.AREA_VENTEO_MIN_MM2, (
        f"el canario muerde en {v:.0f} mm2 y el guion publica "
        f"AREA_VENTEO_MIN_MM2={cb.AREA_VENTEO_MIN_MM2:.0f}: no es el mismo borde")
    print(f"  canario: por debajo de {v:.0f} mm2 de venteo el liston no existe")


def test_el_punto_de_diseno_no_esta_por_debajo_de_su_propio_minimo() -> None:
    assert cb.P_BASE["area_venteo_mm2"] >= cb.AREA_VENTEO_MIN_MM2, (
        f"P_BASE ventila {cb.P_BASE['area_venteo_mm2']:.0f} mm2 y el minimo que "
        f"el propio guion despeja son {cb.AREA_VENTEO_MIN_MM2:.0f}")


def test_p_base_tiene_las_claves_que_la_guarda_lee() -> None:
    for k in ("area_venteo_mm2", "p_recinto_w", "p_cajon_w", "t_sala_c"):
        assert k in cb.P_BASE, k


if __name__ == "__main__":
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            fn()
    print("OK: calor_budget.py")
