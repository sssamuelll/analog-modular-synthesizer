"""La cadena termica de la fuente v4, de la sala al silicio, y lo que sale de
ella: la corriente SOSTENIDA de cada riel. Es la columna que la sec.1 del papel
tiene vacia, y el dueno de techo del #151.

    python calor_budget.py

## Por que existe

Una corriente sostenible no es propiedad de un modulo: lo es de la terna
(modulo, recinto, ambiente). El liston se firmo el 2026-09-03 en corriente DE
PLACA --3,8 / 2,5 / 4,0 A de rack-- y la v1 del papel lo llamo "superior a la
A-100PSU3" sin mirar donde iba a vivir. La PSU3 entrega sus 2 A en un case
ABIERTO, al aire de la sala; estos IRM entregan lo que su curva de derating
diga al aire que haya dentro de una caja de acero. Samuel firmo D-F3 = A el
2026-09-03 --ventilar recinto y cajon por conveccion natural, sin
ventilador-- y este guion es el que dice cuanto compro esa decision.

## El modelo, en tres tramos

  1. Aire del cajon sobre la sala: la MISMA ecuacion de tiro de chimenea de
     guarda_aire() en case/clearance_budget.py (P = k * dT**1.5), con sus
     constantes importadas y no copiadas. Dos diferencias declaradas: la T
     absoluta del termino de flotabilidad son 318 K (sala de 45 C, spec del
     chasis sec.3.1) y no los 293 K del case --un cambio del 8,5 % en T
     absoluta que baja k un 4 % y sube dT un 2,8 %--; y el area efectiva de
     hoy (3299 mm2) y su tiro (105 mm) son los
     del case SIN las aberturas de D-F3: `area_venteo_mm2` se le suma.
  2. Aire del recinto de acero sobre el del cajon: conduccion por la chapa
     (0,1453 m2 x 9 W/m2K) en paralelo con una chimenea propia de
     `area_venteo_mm2` y 83 mm de tiro. Se resuelve por biseccion.
  3. El modulo: la hoja da su derating contra el aire que lo rodea, y ese
     aire es el del recinto. No se anade salto propio: la curva ya lo trae.

SOSTENIDO es un PUNTO FIJO, no una evaluacion: la corriente que el rack puede
dar calienta el cajon, el calor sube el aire, el aire recorta la corriente.
Se itera desde PLACA_A hasta que el residuo baja de 1 mA en todos los rieles;
guarda_liston() y el escenario cerrado relajan a 1/4 porque la iteracion
directa oscila con poco venteo (un estado caliente y flojo alterna con uno
frio y fuerte); SOSTENIDO en P_BASE converge a paso entero.

## Lo que salio, y por que el rojo no se rebaja

La busqueda de area prueba primero la guarda con 200 000 mm2 y, si ahi ya
salta, publica infinito: no hay venteo que arregle un margen que no existe.
Y no existe: rack+5 tiene 4,0 A en PLACA_A y 4,0 A en PSU3_A --la IRM-20-5
son 20 W a 5 V, o sea la placa entera-- y la curva IRM-20/5V solo conserva el
100 % hasta 45 C, que es justo la sala de diseno. Con cualquier potencia
positiva el aire queda por encima de 45 y el sostenido por debajo de 4,0.
Es una decision de liston (talla de PS5, o liston del +5 V de rack), no un
aserto que se baje.

## Lo que este modelo NO cubre

  * El coeficiente de descarga (CD_TIRO) y h_conv (9 W/m2K) son supuestos,
    no medidas: el sostenido es una PREDICCION y el paso 7 del bring-up es lo
    que la vuelve cifra.
  * La conduccion por el encapsulado del IRM a la chapa (papel sec.12.7): se
    ignora, a favor de seguridad.
  * El transitorio: todo es regimen permanente.
  * La geometria del recinto de la spec del chasis (83 mm, 0,1453 m2) no es
    la del CAD de hoy (64 mm, 0,1257 m2): es un desfase conocido entre
    documentos, no una razon para cambiar el modelo en silencio.
"""
from __future__ import annotations

import math
import os
import sys
from typing import Mapping

DIR = os.path.dirname(os.path.abspath(__file__))
CASE_DIR = os.path.join(DIR, "..", "..", "..", "case")
if CASE_DIR not in sys.path:
    sys.path.insert(0, CASE_DIR)
from clearance_budget import CD_TIRO, CP_AIRE, G, RHO_AIRE  # noqa: E402

from curvas import derating  # noqa: E402

# Spec fuente-chasis-telemetria sec.3.1: ambiente peor caso.
T_SALA = 45.0
# Spec fuente-chasis-telemetria sec.3.3: geometria; sec.3.1 usa esta area.
AREA_RECINTO_M2 = 0.1453
# Spec fuente-chasis-telemetria sec.3.1: valor de manual, no medido.
H_CONV_W_M2K = 9.0
# CONTRA: case/cad/params.scad:1707 fija interior z=61; la salida actual de
# case/clearance_budget.py:5903-5905 deriva exterior z=64 mm.
# DERIVADO: 2(.3386*.064)+2(.1766*.064)+.3386*.1766 ~= 0.1257 m2.
# docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md sec.6.
P_RECINTO_MAX = 28.9
P_CAJON_MAX = 120.3
# Papel sec.1, D-F1 firmada 2026-09-03: corriente DE PLACA por riel.
PLACA_A = {"rack+12": 3.8,       # PS3 = IRM-45-12
           "rack-12": 2.5,       # PS4 = IRM-45-12
           "rack+5": 4.0,        # PS5 = IRM-20-5: 20 W / 5 V, la placa ENTERA
           "digital+5": 8.0}     # PS6 = IRM-45-5
# doepfer.de/a100_man/a100t_e.htm, leido 2026-09-03 (papel sec.0).
PSU3_A = {"rack+12": 2.0,
          "rack-12": 1.2,
          "rack+5": 4.0}
# Que curva de derating lee cada riel (curvas.py). La IRM-45 dibuja UNA
# curva para toda la serie; la IRM-20 dibuja aparte la de "3.3V,5V".
CURVA = {"rack+12": "IRM-45",
         "rack-12": "IRM-45",
         "rack+5": "IRM-20/5V",
         "digital+5": "IRM-45"}

# Papel del liston sec.6: PS1+PS2, U1, U2, LT x4 y U3 tipicos.
_CONSTANTE_RECINTO_W = 1.91 + 0.65 + 0.69 + 0.35 + 0.30
# DERIVADO: resto del maximo de sec.6 que escala con corriente.
_DEPENDIENTE_RECINTO_W = P_RECINTO_MAX - _CONSTANTE_RECINTO_W
# Salida de `python case/clearance_budget.py` el 2026-09-03, sin D-F3.
A_EF_BASE_MM2 = 3299.0
H_TIRO_CAJON_M = 0.105
# Spec del chasis sec.3.3: exterior derivado 338.6 x 176.6 x 83 mm.
H_TIRO_RECINTO_M = 0.083
T_ABS_AIRE_K = 318.0         # K; mandato T3 para sala 45 C, no 293 K del case.

AREA_BUSQUEDA_MAX_MM2 = 200000.0  # mm2; mandato directo: buscar hasta aqui.
TOL_PUNTO_FIJO_A = 0.001          # A; mandato: menos de 1 mA en cada riel.
# DERIVADO en RED: paso directo y 1/2 oscilan a area baja; 1/4 converge.
RELAJACION_PUNTO_FIJO = 0.25
MAX_ITERACIONES_PUNTO_FIJO = 512  # COTA: >20 veces las 24 cerradas observadas.
PASOS_BISECCION_AREA = 48         # COTA: resolucion mucho menor que 1 mm2.
PASOS_BISECCION_DT = 80           # COTA: biseccion termica, precision sobrada.
PASO_AREA_DISENO_MM2 = 100.0      # mm2; plan T3, redondear arriba a centena.
FRACCION_SENSIBILIDAD = 0.10      # Convencion: perturbacion comparativa 10 %.

ESTIMADOS = (
    "H_CONV_W_M2K=9.0: manual, no medido (chassis spec sec.3.1)",
    "CD_TIRO=0.65: SUPUESTO de rejilla (clearance_budget.py)",
    "P_BASE area: hipotesis para #289; el papel del case fija la real",
)
HUECOS = ()


def _k(area_mm2: float, altura_m: float, cd: float = CD_TIRO) -> float:
    # Formula de guarda_aire() del case; 1e-6 convierte mm2 a m2.
    return (RHO_AIRE * CP_AIRE * cd * area_mm2 * 1e-6
            * math.sqrt(2.0 * G * altura_m / T_ABS_AIRE_K))


def _biseccion_potencia(potencia: float, funcion) -> float:
    if potencia <= 0.0:
        return 0.0
    lo, hi = 0.0, 1.0
    while funcion(hi) < potencia:
        hi *= 2.0
    # Natural-stack guard equation: P = k * dT**1.5 (case guarda_aire).
    # Conversion mm2 -> m2 is 1e-6; exponent 2/3 inverts that equation.
    for _ in range(PASOS_BISECCION_DT):
        mid = (lo + hi) / 2.0
        if funcion(mid) < potencia:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def aire_recinto_c(p_recinto_w: float, p_cajon_w: float, *,
                   area_venteo_mm2: float, t_sala_c: float = T_SALA) -> float:
    """Return enclosure air temperature, with the cabinet stage in series.

    The enclosure loses only ``p_recinto_w`` through sheet convection and its
    new opening. The cabinet's ``p_cajon_w + p_recinto_w`` ends in the cabinet
    stack, as all enclosure heat ultimately enters that air path. The 83 mm
    enclosure height is DERIVED from the chassis document, not estimated.
    """
    if area_venteo_mm2 < 0.0 or p_recinto_w < 0.0 or p_cajon_w < 0.0:
        raise ValueError("area y potencia no pueden ser negativas")
    # Cajon->sala evacua p_cajon+p_recinto; el area nueva se suma a la actual.
    k_cajon = _k(A_EF_BASE_MM2 + area_venteo_mm2, H_TIRO_CAJON_M)
    dt_cajon = ((p_cajon_w + p_recinto_w) / k_cajon) ** (2.0 / 3.0)
    # Recinto->cajon: la chimenea propia usa solo el area nueva.
    k_recinto = (_k(area_venteo_mm2, H_TIRO_RECINTO_M)
                 if area_venteo_mm2 > 0 else 0.0)
    h_area = AREA_RECINTO_M2 * H_CONV_W_M2K
    dt_recinto = _biseccion_potencia(
        p_recinto_w,
        lambda dt: h_area * dt + k_recinto * dt ** 1.5)
    return t_sala_c + dt_recinto + dt_cajon


def _temperaturas(p_recinto_w: float, p_cajon_w: float, area_venteo_mm2: float,
                  t_sala_c: float = T_SALA, *, area_recinto_m2: float = AREA_RECINTO_M2,
                  h_conv: float = H_CONV_W_M2K, cd: float = CD_TIRO) -> tuple[float, float, float]:
    """Private parametrizable form: (air C, cabinet dT K, enclosure dT K)."""
    if area_venteo_mm2 < 0 or p_recinto_w < 0 or p_cajon_w < 0:
        raise ValueError("area y potencia no pueden ser negativas")
    kc = _k(A_EF_BASE_MM2 + area_venteo_mm2, H_TIRO_CAJON_M, cd)
    dc = ((p_cajon_w + p_recinto_w) / kc) ** (2.0 / 3.0)
    kr = _k(area_venteo_mm2, H_TIRO_RECINTO_M, cd) if area_venteo_mm2 else 0.0
    dr = _biseccion_potencia(p_recinto_w,
                             lambda x: area_recinto_m2 * h_conv * x + kr * x ** 1.5)
    return t_sala_c + dc + dr, dc, dr


def _ratio(corrientes: dict[str, float]) -> float:
    if any(v < 0.0 for v in corrientes.values()):
        raise ValueError("corriente no puede ser negativa")
    return sum(corrientes.get(r, 0.0) for r in PLACA_A) / sum(PLACA_A.values())


def p_cajon_w(corrientes: dict[str, float]) -> float:
    """Calor del cajon: 120.3 W en PLACA_A, proporcional a corriente."""
    return P_CAJON_MAX * _ratio(corrientes)


def p_recinto_w(corrientes: dict[str, float]) -> float:
    """Calor del recinto: cascada 3.90 W fija mas carga proporcional."""
    return _CONSTANTE_RECINTO_W + _DEPENDIENTE_RECINTO_W * _ratio(corrientes)


def sostenido_a(riel: str, t_aire_c: float) -> float:
    if riel not in PLACA_A:
        raise KeyError(riel)
    return PLACA_A[riel] * derating(t_aire_c, CURVA[riel])


def _fixed_point(p: Mapping[str, float], *, damping: float = 1.0,
                 area_recinto_m2: float = AREA_RECINTO_M2,
                 h_conv: float = H_CONV_W_M2K, cd: float = CD_TIRO) -> dict[str, float]:
    """Iterate I->heat->air->derating from PLACA_A to a <1 mA residual.

    Relaxation 1/4 is necessary: the direct map oscillates at low vent area
    between a hot low-current state and a cool high-current state. It does not
    change the fixed point and converges at both ends of the search interval.
    """
    corrientes = dict(PLACA_A)  # Mandato: comenzar exactamente en PLACA_A.
    for _ in range(MAX_ITERACIONES_PUNTO_FIJO):
        fraccion = _ratio(corrientes)
        # Sec.6/direct order: 3.90 W stays fixed; remaining heat scales with I.
        calor_recinto = (_CONSTANTE_RECINTO_W
                          + (p["p_recinto_w"] - _CONSTANTE_RECINTO_W) * fraccion)
        calor_cajon = p["p_cajon_w"] * fraccion
        temp = _temperaturas(
            calor_recinto, calor_cajon,
            p["area_venteo_mm2"], p["t_sala_c"],
            area_recinto_m2=area_recinto_m2, h_conv=h_conv, cd=cd)[0]
        objetivo = {r: sostenido_a(r, temp) for r in PLACA_A}
        residuo = {r: objetivo[r] - corrientes[r] for r in PLACA_A}
        if all(abs(residuo[r]) < TOL_PUNTO_FIJO_A for r in PLACA_A):
            return objetivo
        corrientes = {
            r: corrientes[r] + damping * residuo[r]
            for r in PLACA_A
        }
    mayor = max(abs(residuo[r]) for r in PLACA_A)
    raise RuntimeError(
        f"punto fijo no converge en {MAX_ITERACIONES_PUNTO_FIJO}; "
        f"residuo {mayor:.6f} A")


def guarda_liston(p: dict[str, float]) -> None:
    """Puerta rack contra PSU3; su texto estable alimenta el canario."""
    valores = _fixed_point(p, damping=RELAJACION_PUNTO_FIJO)
    for riel in PSU3_A:
        assert valores[riel] >= PSU3_A[riel], (
            f"SIGUE sin existir: {riel} sostenido {valores[riel]:.3f} A < "
            f"PSU3 {PSU3_A[riel]:.3f} A")


def _falla_por_liston(p: dict[str, float]) -> tuple[bool, str]:
    try:
        guarda_liston(p)
    except AssertionError as exc:
        if "SIGUE sin existir" not in str(exc):
            raise
        return True, str(exc)
    return False, ""


def _busca_area_minima() -> tuple[float, float, str]:
    """Bisect the first green area, or publish infinity after testing 200000."""
    base = {
        "area_venteo_mm2": 0.0,  # mm2; physical lower boundary.
        "p_recinto_w": P_RECINTO_MAX,
        "p_cajon_w": P_CAJON_MAX,
        "t_sala_c": T_SALA,
    }
    alto = dict(base)
    alto["area_venteo_mm2"] = AREA_BUSQUEDA_MAX_MM2
    falla_alto, mensaje = _falla_por_liston(alto)
    if falla_alto:
        return float("inf"), AREA_BUSQUEDA_MAX_MM2, mensaje

    falla_bajo, _ = _falla_por_liston(base)
    if not falla_bajo:
        return 0.0, 0.0, ""

    lo, hi = 0.0, AREA_BUSQUEDA_MAX_MM2
    for _ in range(PASOS_BISECCION_AREA):
        medio = (lo + hi) / 2.0
        candidato = dict(base)
        candidato["area_venteo_mm2"] = medio
        falla, _ = _falla_por_liston(candidato)
        if falla:
            lo = medio
        else:
            hi = medio
    area_base = math.ceil(hi / PASO_AREA_DISENO_MM2) * PASO_AREA_DISENO_MM2
    return hi, area_base, ""


AREA_VENTEO_MIN_MM2, _AREA_BASE_MM2, _FALLO_AREA_MAX = _busca_area_minima()
P_BASE = {
    # ESTIMADO - hipotesis para #289, el papel del case fija la real.
    # Como no existe area finita, queda el extremo explorado por mandato.
    "area_venteo_mm2": _AREA_BASE_MM2,
    "p_recinto_w": P_RECINTO_MAX,  # W; papel sec.6.
    "p_cajon_w": P_CAJON_MAX,      # W; papel sec.6.
    "t_sala_c": T_SALA,            # C; chassis spec sec.3.1.
}
SOSTENIDO = _fixed_point(P_BASE, damping=1.0)


def demo() -> None:
    print("calor_budget: cadena termica (fuentes inline en constantes)")
    escenarios = ((0.0, "cerrado"), (P_BASE["area_venteo_mm2"], "P_BASE"))
    print("  tabla: escenario | dT cajon | dT recinto | T | riel / placa / PSU3")
    for area, etiqueta in escenarios:
        p = {**P_BASE, "area_venteo_mm2": area}
        valores = _fixed_point(p, damping=RELAJACION_PUNTO_FIJO)
        # Scenario rows are fixed points: recompute heat from those currents,
        # rather than displaying the full-load P_BASE heat beside them.
        p_rec = p_recinto_w(valores)
        p_caj = p_cajon_w(valores)
        t, dc, dr = _temperaturas(p_rec, p_caj, area)
        print(f"  {etiqueta}: {dc:.2f} K | {dr:.2f} K | {t:.2f} C")
        for riel in PLACA_A:
            psu = PSU3_A.get(riel)
            comparacion = "---" if psu is None else f"{psu:.3f}"
            estado = ("N/A" if psu is None else
                      ("PASA" if valores[riel] >= psu else "NO PASA"))
            print(f"    {riel}: {valores[riel]:.3f} / {PLACA_A[riel]:.3f} / "
                  f"{comparacion} ({100 * valores[riel] / PLACA_A[riel]:.1f}%, {estado})")
    tf, dcf, drf = _temperaturas(P_RECINTO_MAX, P_CAJON_MAX, 0.0)
    tp, dcp, drp = _temperaturas(P_RECINTO_MAX, P_CAJON_MAX,
                                 P_BASE["area_venteo_mm2"])
    print(f"  cadena full-load: cerrado dT cajon {dcf:.2f} K + dT recinto "
          f"{drf:.2f} K = {tf:.2f} C; P_BASE dT cajon {dcp:.2f} K + "
          f"dT recinto {drp:.2f} K = {tp:.2f} C")
    print(f"  AREA_VENTEO_MIN_MM2={AREA_VENTEO_MIN_MM2}")
    if math.isinf(AREA_VENTEO_MIN_MM2):
        print("!" * 72)
        print(f"FALLO: NINGUNA AREA FINITA HASTA "
              f"{AREA_BUSQUEDA_MAX_MM2:.0f} MM2 CUMPLE EL LISTON")
        print(f"DETALLE: {_FALLO_AREA_MAX.upper()}")
        print("!" * 72)
    base = SOSTENIDO
    cambios = {}
    factor = 1.0 + FRACCION_SENSIBILIDAD
    for nombre, kw in (("CD_TIRO", {"cd": CD_TIRO * factor}),
                       ("H_CONV_W_M2K", {"h_conv": H_CONV_W_M2K * factor}),
                       ("AREA_RECINTO_M2", {"area_recinto_m2": AREA_RECINTO_M2 * factor})):
        v = _fixed_point(P_BASE, **kw)
        cambios[nombre] = max(abs(v[r] - base[r]) for r in PLACA_A)
    dominante = max(cambios, key=cambios.get)
    print(f"  sensibilidad +10%: {cambios}; dominante={dominante}")
    print(f"  ESTIMADO: {len(ESTIMADOS)} (incluye P_BASE); HUECO: {len(HUECOS)}")


def _corre_contrato() -> None:
    """Corre todos los test_* y reune los rojos contractuales al final.

    Corre tambien el contrato de curvas.py: gates.py recoge por glob
    `*_budget.py` y `check_*.py`, asi que ni curvas.py ni test_curvas.py
    entran solos. Este presupuesto es su consumidor y el que responde de que
    sus puntos sigan siendo los de la hoja."""
    import importlib.util
    fallos: list[tuple[str, str]] = []
    for fichero in ("test_curvas.py", "test_calor_budget.py"):
        test_path = os.path.join(DIR, fichero)
        spec = importlib.util.spec_from_file_location(fichero[:-3], test_path)
        tests = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(tests)
        for nombre, fn in sorted(vars(tests).items()):
            if nombre.startswith("test_") and callable(fn):
                try:
                    fn()
                except AssertionError as exc:
                    fallos.append((nombre, str(exc)))
                    print(f"ROJO {nombre}: {exc}")
    if fallos:
        resumen = "; ".join(f"{nombre}: {mensaje}" for nombre, mensaje in fallos)
        raise AssertionError(f"contrato calor: {len(fallos)} rojo(s): {resumen}")
    print("OK: calor_budget.py")


def main() -> None:
    demo()
    _corre_contrato()


if __name__ == "__main__":
    main()
