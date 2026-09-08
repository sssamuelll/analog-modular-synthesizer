"""Prueba del disipador de C: NO DA el criterio literal, dentro del modelo.

    python hardware/01-power-supply/v4/disipador_budget.py

Fuentes (rutas relativas a la raiz; paginas PDF contadas desde la portada):
  * docs/superpowers/specs/2026-09-04-recinto-partido-design.md:192: objetivo
    Tj <= 61 C con 12,80 W. La orden de descarte esta en :242 (sec.7, no 8).
  * docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md:879: carga
    SOSTENIDA firmada; :1040 deja todos los IRM en R, :1041 pone la cascada
    en C; :1248 y :1249 fijan LT1963A y LT3015. MIC29152 es candidato (:228),
    no el tercer regulador: ese es LM7805 (../v3/bom.csv:6).
  * calor_budget.py:133, :138, :140, :142, :329: modelo del aire, sin copiar
    ni cambiar T_SALA, AREA_RECINTO_M2, H_CONV_W_M2K ni CD_TIRO.
    :204 y :256 ya retiran del digital una carga que el papel aun conserva.
  * docs/reference/datasheets/lt1963a-rev-g-2021-02.pdf p.19, fila
    "T Package, 5-Lead TO-220": theta_JC = 4 C/W, sin maximo declarado.
  * docs/reference/datasheets/lt3015-rev-b.pdf p.19, misma fila:
    theta_JC = 3 C/W, sin maximo declarado.
  * docs/reference/datasheets/mic29152-ds20005685b-2019.pdf p.8, fila
    "Thermal Resistance TO-220": 2 C/W TIPICO, columna Max vacia;
    p.24, "Thermal Design", ecuaciones 4-1 y 4-2: cadena y despeje.

El contrato mezcla generaciones y potencias. Los 61 C vienen de la cuenta
del LM2991 antiguo (spec 2026-08-18-fuente-chasis-telemetria.md:188-204), cuya
autoridad termica fue revocada (:50-66). Los 12,80 W incluyen perdidas de IRM
que NO salen de R. Se conserva el objetivo para contestarlo; no se convierte
esa cuenta antigua en una prestacion demostrada de la fuente vigente.

Escenario: carga sostenida firmada y abertura P_BASE vigente. No se exige
PLACA_A entera ni se inventa otro punto fijo: basta un punto de carga que el
instrumento promete. Se comprueba que los modulos lo sostienen al aire de R.
Mover C conserva TODO el calor del cajon. aire_recinto_c(0, P_total, ...)
anula solamente el salto recinto->cajon y devuelve el aire que rodea C. No
significa que R deje de disipar. No se redimensiona R: su geometria propuesta
no esta firmada; el aire de C en este modelo depende del total, no del reparto.

La cadena fisica queda detenida donde falta un dato. Las potencias de la
tabla firmada son contabilidad nominal, NO disipaciones actuales garantizadas:
P_i = (abs(Vin_i)-abs(Vout_i))*Iout_i + abs(Vin_i)*Ignd_i (LT1963A p.19 y
LT3015 p.19, "Calculating Junction Temperature"). Faltan sus condiciones
completas, el consumo aguas abajo y la hoja del LM7805. No se reutilizan los
60 mA de margen_budget.py:258: su fuente (:257) es el LM2941 retirado.

La cota que decide no necesita rellenar esos huecos: con potencia positiva
y resistencias pasivas no negativas, Tj >= Tc >= Ts >= Taire. Si hasta Taire
supera el objetivo, ninguna theta_SA pasiva sirve. Los ceros de esta prueba
son un LIMITE IDEAL algebraico, no valores supuestos de piezas. El resultado
es condicional al modelo heredado, cuyos ESTIMADOS y HUECOS se imprimen.
"""
from __future__ import annotations

import math
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)
import calor_budget as calor  # noqa: E402

FIRMADO = "docs/superpowers/specs/2026-09-03-fuente-v4-liston-design.md"
PROPUESTA = "docs/superpowers/specs/2026-09-04-recinto-partido-design.md"
CHASIS = "docs/superpowers/specs/2026-08-18-fuente-chasis-telemetria.md"
HOJAS = "docs/reference/datasheets/"
MIC = HOJAS + "mic29152-ds20005685b-2019.pdf"
FUENTE_AIRE = "calor_budget.py:329 (reparto y evaluacion: escenario_c_fuera)"
FUENTE_CADENA = MIC + ' p.24, "Thermal Design", ecuaciones 4-1 y 4-2'

TJ_OBJETIVO_C = 61.0  # 2026-09-04-recinto-partido-design.md:192.
P_LITERAL_W = 12.80  # 2026-09-04-recinto-partido-design.md:93 y :192; CONTRA.
AREA_FIRMADA_MM2 = 22200.0  # 2026-09-03-fuente-v4-liston-design.md:879; nuevos.
CARGA_A = {
    "rack+12": 2.0,  # 2026-09-03-fuente-v4-liston-design.md:879, sostenido.
    "rack-12": 2.0,  # Misma fuente:879, NO el liston de la PSU3 de calor:160.
    "rack+5": 4.0,  # Misma fuente:879, sostenido declarado.
    "digital+5": calor.CAJON_DIGITAL_A,  # calor_budget.py:204; carga, no techo.
}
PIEZAS = {"U1": "LT1963A", "U2": "LT3015", "U3": "LM7805"}
# Identidades: firmado:1248, :1249; hardware/01-power-supply/v3/bom.csv:6.
P_TABLA_W = {
    "U1": 1.24,  # Firmado:851 y calor_budget.py:257; solo termino de paso.
    "U2": 1.37,  # Firmado:851 y calor_budget.py:257; solo termino de paso.
    "U3": 0.30,  # Firmado:852 y calor_budget.py:258; carga nominal de :1053.
}
P_ISLA_LT_W = 1.30  # Firmado:852; calor_budget.py:257. Disipa en PCB, no tabs.
P_C_TABLA_W = sum(P_TABLA_W.values()) + P_ISLA_LT_W  # DERIVADO de esas filas.
THETA_JC_PUBLICADA = {
    "U1": 4.0,  # lt1963a-rev-g-2021-02.pdf p.19, "T Package, 5-Lead TO-220".
    "U2": 3.0,  # lt3015-rev-b.pdf p.19, "T Package, 5-Lead TO-220".
    "U3": None,  # HUECO: v3/bom.csv:6 no nombra fabricante ni hoja de U3.
}
FUENTE_JC = {
    "U1": HOJAS + 'lt1963a-rev-g-2021-02.pdf p.19, "T Package, 5-Lead TO-220"',
    "U2": HOJAS + 'lt3015-rev-b.pdf p.19, "T Package, 5-Lead TO-220"',
    "U3": "hardware/01-power-supply/v3/bom.csv:6; HUECO de hoja",
}
THETA_JC_MIC_TIP = 2.0  # MIC p.8, "Thermal Resistance TO-220", columna Typ.
# None significa RAMA DETENIDA, nunca resistencia o potencia nula.
P_REAL_W = dict.fromkeys(PIEZAS)  # HUECO: LT1963A/LT3015 p.19, formula de P.
THETA_JC_MAX = dict.fromkeys(PIEZAS)  # HUECO: fuentes FUENTE_JC, sin maximos.
THETA_CS_MAX = dict.fromkeys(PIEZAS)  # HUECO: v3/bom.csv:19, interfaz pendiente.
THETA_SA_REAL = None  # HUECO: propuesta:192-196, sin disipador seleccionado.
CERO = 0.0  # Limite ideal sin salto/perdida: MIC p.24 ecuacion 4-2; no pieza.

HUECOS = (
    "Potencias reales garantizadas: las filas de calor son nominales y no "
    "incluyen Ignd. LT1963A/LT3015 p.5, 'GND Pin Current', no tabulan la carga "
    "real de la cascada; p.19 exige incluirla. margen_budget.py:257 conserva "
    "el consumo del regulador retirado. No se completa esta rama.",
    "U3: falta fabricante/hoja del LM7805 (v3/bom.csv:6); no se conocen aqui "
    "Ignd ni theta_JC garantizados. MIC29152 no lo sustituye (firmado:228).",
    "theta_JC de U1/U2: valor publicado sin maximo declarado (hojas p.19). "
    "MIC solo tipico (p.8). No se usan como garantias.",
    "theta_CS maxima del aislante y montaje: pendiente (v3/bom.csv:19). "
    "U2 lleva el tab a IN (lt3015-rev-b.pdf p.2, 'T PACKAGE'); el limite "
    "ideal sin interfaz no autoriza a montar los tabs sin aislamiento.",
    "Disipador de C, orientacion y curva: sin hoja (propuesta:192). El arbol "
    "nombra Fischer SK129/38,1 (v2/bom.csv:23), pero sus cifras son tipicas "
    "(notes/design-notes.md:1251). No se certifica esa pieza ni su montaje.",
    "Aire fisico: P_BASE y coeficientes son hipotesis heredadas, no medidas "
    "(calor_budget.py:286); las perdidas parciales y cargas pendientes "
    "siguen abiertas (:292). La rama fisica garantizada queda detenida; "
    "NO DA es el resultado del modelo solicitado.",
)


def escenario_c_fuera(area_mm2: float | None = None) -> dict[str, float]:
    """Misma carga, C pasa al cajon y todos los IRM permanecen en R."""
    area = calor.P_BASE["area_venteo_mm2"] if area_mm2 is None else area_mm2
    # calor_budget.py:380/:372 y firmado:1040/:1041; se conserva la suma.
    p_r = calor.p_recinto_w(CARGA_A) - P_C_TABLA_W
    p_cajon = calor.p_cajon_w(CARGA_A) + P_C_TABLA_W
    t_r = calor.aire_recinto_c(p_r, p_cajon, area_venteo_mm2=area,
                              t_sala_c=calor.T_SALA)  # calor_budget.py:138.
    # calor_budget.py:333-350: con salto interior nulo queda SOLO cajon->sala.
    t_c = calor.aire_recinto_c(CERO, p_r + p_cajon, area_venteo_mm2=area,
                              t_sala_c=calor.T_SALA)  # calor_budget.py:138.
    return dict(area_mm2=area, p_r_w=p_r, p_cajon_w=p_cajon,
                p_total_w=p_r + p_cajon, t_r_c=t_r, t_c_c=t_c)


def cadena_termica(t_aire: float, potencias: dict, theta_jc: dict,
                   theta_cs: dict, theta_sa: float | None) -> dict:
    """Ts=Ta+sum(P)*SA; Tc_i=Ts+P_i*CS_i; Tj_i=Tc_i+P_i*JC_i.

    Fuente: MIC p.24 ecuacion 4-2, sumando potencias en el disipador comun;
    spec del chasis:189-192 distingue potencia comun y potencia propia.
    No calcula temperaturas de piezas reales con datos ausentes.
    """
    entradas = [t_aire, theta_sa, *potencias.values(),
                *theta_jc.values(), *theta_cs.values()]
    if any(v is None for v in entradas):
        raise ValueError("HUECO: cadena real sin potencia o resistencia garantizada")
    assert all(math.isfinite(v) for v in entradas), "entrada termica no finita"
    assert theta_sa >= CERO and all(
        v >= CERO for d in (potencias, theta_jc, theta_cs) for v in d.values()
    ), "una cadena pasiva no admite potencias ni resistencias negativas"
    ts = t_aire + sum(potencias.values()) * theta_sa
    resultado = {}
    for ref, p in potencias.items():
        tc = ts + p * theta_cs[ref]
        tj = tc + p * theta_jc[ref]
        resultado[ref] = dict(tj=tj, tc=tc, ts=ts, taire=t_aire)
    return resultado


def theta_sa_necesaria(t_aire: float, potencias: dict, theta_jc: dict,
                       theta_cs: dict) -> float:
    """min_i[(Tobjetivo-Ta-P_i*(JC_i+CS_i))/sum(P)], MIC p.24 ec.4-1/4-2.

    Un resultado negativo demuestra imposibilidad pasiva, no una pieza.
    """
    base = cadena_termica(t_aire, potencias, theta_jc, theta_cs, CERO)
    total = sum(potencias.values())
    assert total > CERO, "despeje sin potencia en el disipador"
    return min((TJ_OBJETIVO_C - t["tj"]) / total for t in base.values())


def theta_sa_literal_ideal(t_aire: float) -> float:
    # DERIVADO: MIC p.24 ec.4-1/4-2, suprimiendo TODOS los saltos JC y CS.
    # Es el mejor caso algebraico de P_LITERAL_W, no reparte esa cifra falsa.
    return (TJ_OBJETIVO_C - t_aire) / P_LITERAL_W


def _autocomprobacion() -> None:
    e = escenario_c_fuera()
    assert P_LITERAL_W > CERO and P_C_TABLA_W > CERO
    assert e["p_r_w"] >= CERO and e["p_cajon_w"] >= CERO
    assert e["area_mm2"] > CERO, "se perdio el venteo de D-F3"
    total_antes = calor.p_recinto_w(CARGA_A) + calor.p_cajon_w(CARGA_A)
    assert math.isclose(e["p_total_w"], total_antes), "sacar C ha borrado calor"
    assert math.isclose(e["p_r_w"] + P_C_TABLA_W,
                        calor.p_recinto_w(CARGA_A)), "se movieron los IRM a C"
    for ref, carga in CARGA_A.items():
        assert calor.sostenido_a(ref, e["t_r_c"]) >= carga, (
            f"{ref}: el escenario exige mas corriente de la sostenible en R")
    assert e["t_r_c"] > e["t_c_c"] > calor.T_SALA, "nodos de aire confundidos"

    # ESTE aserto protege la conclusion. Cambiar ambiente, carga, venteo o
    # criterio hasta invertirla debe producir ROJO, no conservar el titular.
    for caso in (e, escenario_c_fuera(AREA_FIRMADA_MM2)):
        assert caso["t_c_c"] > TJ_OBJETIVO_C, (
            f"la cota de aire ya NO descarta: {caso['t_c_c']:.4f} C contra "
            f"{TJ_OBJETIVO_C:.4f}. Rehacer el veredicto, no aflojar el aserto")
        assert theta_sa_literal_ideal(caso["t_c_c"]) < CERO, (
            "el despeje ideal ya no exige resistencia negativa")

    # Identidad del limite ideal: ni calor nominal ni parametros de prueba
    # se hacen pasar por un montaje. Fuente del cero: CERO, MIC p.24 ec.4-2.
    nulas = dict.fromkeys(PIEZAS, CERO)
    ideal = cadena_termica(e["t_c_c"], P_TABLA_W, nulas, nulas, CERO)
    assert all(t["tj"] == t["tc"] == t["ts"] == t["taire"]
               for t in ideal.values()), "el disipador ideal no es isotermo"
    assert theta_sa_necesaria(e["t_c_c"], P_TABLA_W, nulas, nulas) < CERO
    try:
        cadena_termica(e["t_c_c"], P_REAL_W, THETA_JC_MAX,
                       THETA_CS_MAX, THETA_SA_REAL)
    except ValueError as exc:
        assert "HUECO" in str(exc)
    else:
        raise AssertionError("se publicaria una cadena real con huecos pendientes")


def demo() -> int:
    _autocomprobacion()
    e = escenario_c_fuera()
    print(f"NO DA (modelo): Tj >= Taire_C = {e['t_c_c']:.4f} C > "
          f"{TJ_OBJETIVO_C:.2f} C [{FUENTE_AIRE}; {PROPUESTA}:192]")
    print(f"  theta_SA <= {theta_sa_literal_ideal(e['t_c_c']):.4f} C/W aun "
          f"con JC=CS=0 ideal y los {P_LITERAL_W:.2f} W literales "
          f"[{FUENTE_CADENA}; {PROPUESTA}:192]")
    print("  Ningun disipador pasivo de catalogo tiene esa resistencia negativa.")
    print("  La cadena fisica garantizada: HUECO; no hay Tj real calculada.\n")
    print(f"  Carga sostenida: {CARGA_A} A [{FIRMADO}:879; calor_budget.py:204]")
    print(f"  Venteo nuevo vigente: {e['area_mm2']:.0f} mm2 "
          "[calor_budget.py:526, :530; se suma al area base :271]")
    print(f"  Sala: {calor.T_SALA:.2f} C [calor_budget.py:138]")
    print(f"  R: {e['p_r_w']:.4f} W; cajon fuera de R: {e['p_cajon_w']:.4f} W; "
          f"total: {e['p_total_w']:.4f} W "
          f"[calor_budget.py:372, :380; {FIRMADO}:851, :852, :1040, :1041]")
    print(f"  Aire_R: {e['t_r_c']:.4f} C; aire_C: {e['t_c_c']:.4f} C "
          f"[{FUENTE_AIRE}]")
    anterior = escenario_c_fuera(AREA_FIRMADA_MM2)
    print(f"  Con {AREA_FIRMADA_MM2:.0f} mm2 del firmado: "
          f"aire_C = {anterior['t_c_c']:.4f} C; theta_SA ideal <= "
          f"{theta_sa_literal_ideal(anterior['t_c_c']):.4f} C/W "
          f"[{FIRMADO}:879; {FUENTE_AIRE}; {FUENTE_CADENA}]")
    print("\n  Cadena completa: Tj_i = Tc_i + P_i*JC_i; "
          "Tc_i = Ts + P_i*CS_i; Ts = Taire_C + sum(P_i)*SA")
    print(f"  Fuente: {FUENTE_CADENA}; {CHASIS}:189")
    print("  pieza | P tabla W (NO real garantizada) | JC publicada C/W | "
          "P real / JC max / CS max / SA / Ts / Tc / Tj")
    for ref, nombre in PIEZAS.items():
        jc = THETA_JC_PUBLICADA[ref]
        valor = "HUECO" if jc is None else f"{jc:.2f}, sin maximo"
        print(f"  {ref} {nombre} | {P_TABLA_W[ref]:.2f} [{FIRMADO}:851-852] | "
              f"{valor} [{FUENTE_JC[ref]}] | HUECO (rama detenida)")
    print(f"  C contabilizada = {P_C_TABLA_W:.2f} W, de los cuales "
          f"{P_ISLA_LT_W:.2f} W van a la isla LT "
          f"[{FIRMADO}:851-852; calor_budget.py:257-258].")
    print(f"  Los {P_LITERAL_W:.2f} W del papel incluyen IRM que viven en R "
          f"[{PROPUESTA}:89-94; {FIRMADO}:846-852, :1040].")
    print(f"  MIC29152: candidato a U1; JC={THETA_JC_MIC_TIP:.2f} C/W TIPICO "
          f"[{FIRMADO}:228; {MIC} p.8, 'Thermal Resistance TO-220', Typ].")
    print("\n  HUECOS:")
    for hueco in HUECOS:
        print(f"    - {hueco}")
    print("  ESTIMADOS heredados (sin convertirlos en garantias):")
    for estimado in calor.ESTIMADOS:
        print(f"    - {estimado} [calor_budget.py:286]")
    for hueco in calor.HUECOS:
        print(f"    - {hueco} [calor_budget.py:292]")
    print(f"\n  Segun su propia puerta, la propuesta cae aqui [{PROPUESTA}:242].")
    print("OK: disipador_budget.py; autocomprobacion pasada, criterio termico NO DA.")
    return 0  # Contrato del encargo: diagnostico reproducible con salida limpia.


if __name__ == "__main__":
    raise SystemExit(demo())
