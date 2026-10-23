"""El bring-up de la fuente v5: lo MEDIDO contra lo PREDICHO del ladrillo y DC-DCs.

    python check_bringup.py               comprueba medidas.csv
    python check_bringup.py --plantilla   reescribe la hoja de campo

## Que es la v5 y por que se escribe ahora (T28 / H-CENSO-MEDIDA)

La fuente v5 sustituye los seis modulos IRM de 230 V (v4, liston) por un ladrillo
externo de 24 VDC (TE90A2403F01 / GST120A24-R7B / GSM120A24-R7B) y cinco
convertidores DC-DC internos:
  - PS_RACK_PM:  TRACO THN 30-2422WI (+-12 V rack, 30 W)
  - PS_DIG:      Mornsun URB2405YMD-20WR3 (+5 V digital aislado, 20 W)
  - PS_RACK_5V:  Mornsun K7805T-1000R3 (+5 V rack buck, 5 W)
  - PS_RAW_P:    TRACO THN 20-2413WI (+15.5 V crudo cascada, 20 W)
  - PS_RAW_N:    TRACO THN 20-2413WI (-15.5 V crudo cascada, 20 W)

Este guion formaliza T28 (H-CENSO-MEDIDA): cada prediccion se importa de los
presupuestos ejecutables de v5 (ladrillo_budget, margen_budget, rizado_budget,
secuencia_budget, recuperacion_budget, check_absmax, check_telemetria y curvas).
Ningun numero esta duplicado a mano. Si un presupuesto cambia, la hoja de
campo cambia al correr `--plantilla`.

## Codigos de salida

    0   todos los puntos con criterio medidos y dentro de rango
    1   alguna medida FUERA de rango: la placa no pasa
    2   faltan medidas. Normal y correcto con la placa sin fabricar (HUECO)
"""
from __future__ import annotations

import csv
import importlib.util
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

for _mod in [
    "curvas", "ladrillo_budget", "margen_budget", "recuperacion_budget",
    "rizado_budget", "secuencia_budget", "check_absmax", "check_telemetria"
]:
    if _mod not in sys.modules or not getattr(sys.modules[_mod], "__file__", "").startswith(DIR):
        _spec = importlib.util.spec_from_file_location(_mod, os.path.join(DIR, f"{_mod}.py"))
        assert _spec and _spec.loader
        _m = importlib.util.module_from_spec(_spec)
        sys.modules[_mod] = _m
        _spec.loader.exec_module(_m)

import check_absmax  # noqa: E402
import check_telemetria  # noqa: E402
import curvas  # noqa: E402
import ladrillo_budget  # noqa: E402
import margen_budget  # noqa: E402
import recuperacion_budget  # noqa: E402
import rizado_budget  # noqa: E402
import secuencia_budget  # noqa: E402

CSV_PATH = os.path.join(DIR, "medidas.csv")
COLS = [
    "paso", "magnitud", "unidad", "criterio", "predicho", "tolerancia",
    "medido", "placa", "fecha", "fuente"
]

PASOS_ESPERADOS = {"0", "1", "2", "2b", "2c", "3", "4", "5", "6", "7", "8"}

TOL_TELE = 0.01  # +-1 %: divisores al 0.1 % mas error de ADC
MODULOS_DCDC = ("THN30_mas12", "THN30_menos12", "URB2405_5V", "K7805_5V", "THN20_mas15", "THN20_menos15")
V_DCDC = {
    "THN30_mas12": 12.0,
    "THN30_menos12": -12.0,
    "URB2405_5V": 5.0,
    "K7805_5V": 5.0,
    "THN20_mas15": 15.5,
    "THN20_menos15": -15.5,
}
TOL_DCDC = 0.02  # +-2 % tipico de salida DC-DC
RIZADO_MAX_VPP = {
    "THN30_mas12": 0.100,
    "THN30_menos12": 0.100,
    "URB2405_5V": 0.100,
    "K7805_5V": 0.075,
    "THN20_mas15": 0.100,
    "THN20_menos15": 0.100,
}


class Punto:
    """Un numero que este bring-up predice, con de donde sale."""

    def __init__(self, paso: str, magnitud: str, unidad: str, fuente: str,
                 predicho: float | None = None, tol: float | None = None,
                 lo: float | None = None, hi: float | None = None,
                 literal: str | None = None):
        self.paso, self.magnitud, self.unidad = paso, magnitud, unidad
        self.fuente, self.predicho, self.tol = fuente, predicho, tol
        self.literal = literal
        if predicho is not None and tol is not None:
            lo = predicho - tol if lo is None else lo
            hi = predicho + tol if hi is None else hi
        self.lo, self.hi = lo, hi

    @property
    def clave(self) -> str:
        return f"{self.paso}|{self.magnitud}"

    @property
    def es_criterio(self) -> bool:
        return not (self.lo is None and self.hi is None and self.literal is None)

    def rango(self) -> str:
        if self.literal is not None:
            return f"= {self.literal}"
        if self.lo is not None and self.hi is not None:
            return f"{self.lo:g} .. {self.hi:g}"
        if self.hi is not None:
            return f"<= {self.hi:g}"
        if self.lo is not None:
            return f">= {self.lo:g}"
        return "registro"

    def juzga(self, bruto: str) -> str | None:
        """None si pasa; si no, cadena con el motivo del fallo."""
        if self.literal is not None:
            return (None if bruto.strip().lower() == self.literal.lower()
                    else f"'{bruto}' != '{self.literal}'")
        try:
            v = float(bruto.replace(",", "."))
        except ValueError:
            return f"'{bruto}' no es un numero"
        if self.lo is not None and v < self.lo:
            return f"{v:g} {self.unidad} por debajo de {self.lo:g}"
        if self.hi is not None and v > self.hi:
            return f"{v:g} {self.unidad} por encima de {self.hi:g}"
        return None


def _puntos() -> list[Punto]:
    P, p = Punto, []

    # --- Paso 0: con el equipo DESENCHUFADO (seguridad y aislamiento) -----
    for ref in ("U1_LT1963A", "U2_LT3015"):
        p.append(P("0", f"aislamiento_tab_{ref}_a_chasis", "Mohm",
                   "T17 / M2: verificacion de aislamiento del tab a chasis PE",
                   lo=10.0))
    p.append(P("0", "continuidad_PE_a_chasis", "mohm",
               "M2 / T17: continuidad de tierra PE desde conector Kycon pin shell a chasis",
               hi=50.0))
    p.append(P("0", "continuidad_estrella_GNDA_a_chasis", "mohm",
               "T17 / M2: estrella analogica de masa J5 atornillada al chasis",
               hi=20.0))
    p.append(P("0", "aislamiento_GNDA_a_GNDD", "Mohm",
               "T16 / M1: separacion galvanica entre masa analogica y masa digital "
               "(barrera URB2405 + ISO1541 > 1000 Mohm)",
               lo=1000.0))
    p.append(P("0", "aislamiento_pantalla_retorno_dedicado", "Mohm",
               "T25: retorno de pantalla aislado de GNDA dentro de la fuente",
               lo=1.0))

    # --- Paso 1: Alimentacion 24V y convertidores DC-DC ------------------
    p.append(P("1", "tension_ladrillo_vacio", "V",
               "T09 / L04: salida continua nominal del ladrillo 24 V en vacio",
               predicho=24.0, tol=0.48))
    p.append(P("1", "caida_LM74502_ideal_diode", "mV",
               "M5 / L04: caida directa del controlador de diodo ideal + FET inverso",
               hi=50.0))
    # Resistencia y no caida: la caida depende de la corriente del momento.
    # tps2663.pdf p. 7, 0,6 A <= I <= 6 A: 19 mohm min (-40..125 C) y 45 mohm
    # max a 85 C, lo que cubre cualquier banco a temperatura de sala.
    p.append(P("1", "ron_TPS26631_efuse_U16", "mohm",
               "M5: caida de U16 / corriente del cordon, con >= 0,6 A (tps2663.pdf p. 7)",
               lo=19.0, hi=45.0))
    for ref in MODULOS_DCDC:
        v = V_DCDC[ref]
        p.append(P("1", f"{ref}_vacio", "V",
                   f"M1 / T10: {ref} en vacio a 24 V de entrada",
                   predicho=v, tol=abs(v) * TOL_DCDC))
        p.append(P("1", f"{ref}_a_nominal", "V",
                   f"M1 / T10: {ref} con carga resistiva a corriente nominal",
                   predicho=v, tol=abs(v) * TOL_DCDC))
        p.append(P("1", f"{ref}_rizado_20MHz", "Vpp",
                   "T12 / L05: rizado y ruido de conmutacion a 20 MHz de ancho de banda",
                   hi=RIZADO_MAX_VPP[ref]))
    p.append(P("1", "potencia_ladrillo_reposo_w", "W",
               "ladrillo_budget: consumo propio del ladrillo y convertidores en vacio",
               hi=2.5))
    # ladrillo_budget da el PEOR caso (ladrillo al -5 %, rendimientos de
    # diseno). El suelo es la entrada de los DC-DC con los rendimientos
    # tipicos de hoja, menos un 10 % porque el tipico no es un minimo, y la
    # corriente mas baja sale con el ladrillo al +5 %.
    suelo_w = 0.90 * ladrillo_budget.entrada_dcdc_tipica_hoja_w()
    p.append(P("1", "potencia_ladrillo_sostenida_w", "W",
               "ladrillo_budget: potencia que da el ladrillo a carga sostenida, entre los "
               "rendimientos tipicos (-10 %) y salida_ladrillo_w()",
               lo=suelo_w, hi=ladrillo_budget.salida_ladrillo_w()))
    p.append(P("1", "corriente_ladrillo_sostenida_a", "A",
               "ladrillo_budget: corriente del cordon a carga sostenida, del suelo a +5 % al "
               "peor caso corriente_del_cordon_a()",
               lo=suelo_w / (ladrillo_budget.V_LADRILLO * (1.0 + ladrillo_budget.TOL_LADRILLO)),
               hi=ladrillo_budget.corriente_del_cordon_a()))

    # --- Paso 2: Rieles crudos +-15.5 V y filtro LC -----------------------
    p.append(P("2", "mas15_minimo_con_carga", "V",
               "margen_budget.v_entrada_minima_rama_v('U1'): tension minima que alcanza U1 LT1963A",
               lo=margen_budget.v_entrada_minima_rama_v("U1")))
    p.append(P("2", "menos15_maximo_con_carga", "V",
               "margen_budget.v_entrada_minima_rama_v('U2'): tension minima que alcanza U2 LT3015",
               lo=margen_budget.v_entrada_minima_rama_v("U2")))
    # La ventana va del corner bajo (THN al -2,5 %, caliente, caidas maximas)
    # al alto (THN al +2,5 % y sin caida): una placa sana cae dentro a
    # cualquier temperatura. Centrada en el corner bajo, una nominal salia roja.
    for reg in ("U1", "U2"):
        p.append(P("2", f"margen_dropout_{reg}_v", "V",
                   f"margen_budget: IN de {reg} menos lo que pide la cascada, entre "
                   f"margen_v5_v('{reg}') y el maximo sano",
                   lo=margen_budget.margen_v5_v(reg),
                   hi=margen_budget.v_entrada_maxima_sana_v() - margen_budget.v_necesaria_minima_v(reg)))
    p.append(P("2", "rizado_tras_LC_20MHz", "Vpp",
               "rizado_budget: rizado de conmutacion residual tras filtro LC de 22 uH + 47 uF",
               hi=0.003))
    p.append(P("2", "pico_LC_en_resonancia", "dB",
               "rizado_budget: atenuacion en resonancia (filtro LC amortiguado criticamente)",
               hi=2.5))

    # --- Paso 2b: Secuenciador analogico (D-F4 / M4) ----------------------
    p.append(P("2b", "quitar_mas15_caen_los_dos", "si/no",
               "M4 / #339: al perder el crudo positivo, el comparador LM393B apaga U1 y U2",
               literal="si"))
    p.append(P("2b", "quitar_menos15_caen_los_dos", "si/no",
               "M4 / #339: al perder el crudo negativo, el comparador LM393B apaga U1 y U2",
               literal="si"))
    p.append(P("2b", "cortar_linea_secuenciador_apaga_los_dos", "si/no",
               "M4 / #339: linea open-collector con pulldown apaga ambos por construccion",
               literal="si"))
    p.append(P("2b", "ventana_asimetria_caida_ms", "ms",
               "secuencia_budget: retardo maximo entre caida de rieles durante apagado",
               hi=10.0))
    p.append(P("2b", "suelo_deteccion_v", "V",
               "secuencia_budget.suelo_ventana_v(): umbral inferior de validez de rieles",
               predicho=secuencia_budget.suelo_ventana_v(), tol=0.25))
    p.append(P("2b", "techo_deteccion_v", "V",
               "secuencia_budget.techo_ventana_v(): cota superior donde ambos rieles estan sanos",
               predicho=secuencia_budget.techo_ventana_v(), tol=0.25))

    # --- Paso 2c: Supervisor M5 (recuperacion y brownout) -----------------
    p.append(P("2c", "pulsos_reintento_ante_corto", "pulsos",
               "M5 / recuperacion_budget: 4 pulsos = 1 inicial + 3 reintentos antes de enclavar",
               predicho=float(recuperacion_budget.N_PULSOS_MAX), tol=0.0))
    p.append(P("2c", "tiempo_espera_reintento_s", "s",
               "M5 / recuperacion_budget: tiempo de enfriamiento entre intentos de arranque",
               predicho=recuperacion_budget.T_ESPERA_REINTENTO_S, tol=0.15))
    p.append(P("2c", "debounce_deteccion_ms", "ms",
               "M5 / recuperacion_budget: ventana de discriminacion contra transitorios de insercion",
               predicho=recuperacion_budget.T_FILTRO_REBOTE_S * 1000.0, tol=15.0))
    p.append(P("2c", "tiempo_reset_cupo_s", "s",
               "M5 / recuperacion_budget: tiempo de operacion sana antes de restaurar el cupo",
               predicho=recuperacion_budget.T_REARME_SANO_S, tol=5.0))
    p.append(P("2c", "flt_U19_gasta_intento", "si/no",
               "M5: FLT de U19 (P1.2) con la cadena arrancada: corta, gasta un intento y reintenta; "
               "persistente, enclava al 4o pulso",
               literal="si"))
    p.append(P("2c", "bajon_de_entrada_no_gasta", "si/no",
               "M5: bajon por debajo del UVLO de U16 sin apagar el MSP430: U16 cierra solo y no gasta intento",
               literal="si"))
    p.append(P("2c", "flt_U19_en_arranque_no_abandona", "si/no",
               "M5 / recuperacion_budget: 10 arranques completos seguidos no la dejan ABANDONADA (FLT de U19 del arranque)",
               literal="si"))
    p.append(P("2c", "shdn_U16_con_MCU_en_reset_v", "V",
               "R83: SHDN de U16 con el MSP430 en reset, por debajo de V(SHUTF) (tps2663.pdf p. 7)",
               hi=recuperacion_budget.V_SHUTF_MAX_V))
    p.append(P("2c", "persistencia_latch_en_fram", "si/no",
               "M5: el estado de enclavamiento sobrevive a desconexion de la alimentacion",
               literal="si"))
    p.append(P("2c", "pulsador_reset_desbloquea", "si/no",
               "M5: el pulsador manual de reset en la placa limpia el enclavamiento",
               literal="si"))

    # --- Pasos 3 a 5: Cascada ultra-bajo ruido ---------------------------
    for tp, senal, nom, tol in (
        ("TP7", "+13V1", 13.10, 0.15),
        ("TP8", "-12V9", -12.90, 0.15),
        ("TP3", "+12V", 12.00, 0.05),
        ("TP4", "-12V", -12.00, 0.05),
        ("TP5", "+5V", 5.00, 0.20),
    ):
        p.append(P("3", f"{tp}_{senal}_sin_carga", "V",
                   f"Tension sin carga en punto de prueba {tp} ({nom:+g} V +- {tol:g} V)",
                   predicho=nom, tol=tol))
    for pin, nom in ((1, -12.0), (2, 0.0), (3, 0.0), (4, 12.0)):
        p.append(P("4", f"J2_pin{pin}", "V",
                   f"Pinout J2 Eurocard verificado: pin {pin} = {nom:+g} V",
                   predicho=nom, tol=0.30))
    for tp, nom in (("TP3", 12.0), ("TP4", -12.0)):
        p.append(P("5", f"{tp}_con_carga_650mA", "V",
                   "Regulacion de carga final en cascada entregando 650 mA continuos",
                   predicho=nom, tol=0.05))

    # --- Paso 6: Telemetria contra multimetro -----------------------------
    for ref_ina, riel, r_sh, i_max, v_bus, desc in check_telemetria.SHUNTS_V5:
        p.append(P("6", f"telemetria_{ref_ina}_vbus_vs_multimetro", "V",
                   f"T15: vbus {ref_ina} ({riel}) contra multimetro",
                   predicho=v_bus, tol=abs(v_bus) * TOL_TELE))
        p.append(P("6", f"telemetria_{ref_ina}_corriente_vs_pinza", "A",
                   f"T15: corriente {ref_ina} ({desc}) contra pinza",
                   predicho=i_max, tol=0.05 * i_max))

    for pin_ads, senal, v_ref, casos, invertida in check_telemetria.CANALES_ADS_V5:
        v_nom = casos[0][1]
        p.append(P("6", f"telemetria_ADS1115_{pin_ads}_{senal}_vs_multimetro", "V",
                   f"T15: canal {pin_ads} ({senal}) frente a multimetro",
                   predicho=v_nom, tol=abs(v_nom) * TOL_TELE if v_nom != 0 else 0.05))

    p.append(P("6", "temperatura_U11_TMP1075_c", "C",
               "T15: sensor I2C local TMP1075 frente a termopar ambiental",
               lo=15.0, hi=65.0))
    p.append(P("6", "aislamiento_I2C_digital_ISO1541", "Mohm",
               "T16: aislamiento de lineas SDA/SCL aisladas entre micro y cerebro",
               lo=1000.0))

    # --- Paso 7: Comportamiento termico -----------------------------------
    p.append(P("7", "calor_interior_cajon_w", "W",
               "ladrillo_budget: calor dentro del cajon, entre los rendimientos tipicos (-10 %) "
               "y el peor caso calor_del_cajon_w()",
               lo=0.90 * ladrillo_budget.entrada_dcdc_tipica_hoja_w(),
               hi=ladrillo_budget.calor_del_cajon_w()))
    p.append(P("7", "temperatura_carcasa_THN30_c", "C",
               "T10 / T27: temperatura de carcasa THN 30-2422WI a 45 C ambiente (< 85 C max)",
               hi=85.0))
    p.append(P("7", "temperatura_carcasa_URB2405_c", "C",
               "T10 / T27: temperatura de carcasa URB2405YMD-20WR3 a 45 C ambiente (< 80 C max)",
               hi=80.0))
    p.append(P("7", "temperatura_carcasa_THN20_c", "C",
               "T10 / T27: temperatura de carcasa THN 20-2413WI a 45 C ambiente (< 85 C max)",
               hi=85.0))
    p.append(P("7", "temperatura_U1_LT1963A_c", "C",
               f"T10 / T27: union de U1 LT1963A disipando hasta "
               f"{ladrillo_budget.quema_pre_regulador_w('U1'):.2f} W (ladrillo_budget, < 90 C)",
               hi=90.0))
    p.append(P("7", "temperatura_U2_LT3015_c", "C",
               f"T10 / T27: union de U2 LT3015 disipando hasta "
               f"{ladrillo_budget.quema_pre_regulador_w('U2'):.2f} W (ladrillo_budget, < 90 C)",
               hi=90.0))
    p.append(P("7", "potencia_derating_ladrillo_45C_w", "W",
               "curvas.derating('TE90A2403F01', 45) * 90.0: potencia garantizada del ladrillo a 45 C",
               predicho=curvas.derating("TE90A2403F01", 45.0) * 90.0,
               tol=2.0))

    # --- Paso 8: Protecciones y ruido extremo -----------------------------
    for riel_crowbar in ("rack+12", "rack-12", "rack+5", "digital+5"):
        v_disp = check_absmax.RACK_RIELES[riel_crowbar]["disparo_v"]
        p.append(P("8", f"disparo_crowbar_{riel_crowbar}", "V",
                   f"check_absmax: disparo de proteccion en {riel_crowbar}",
                   predicho=v_disp,
                   tol=check_absmax.TOL_DISPARO_TL431BI_V))
    p.append(P("8", "fusible_abre_sin_dano_a_pistas", "si/no",
               "check_absmax: fusible Bourns SF-1206F corta corriente de falta sin danar PCB",
               literal="si"))
    p.append(P("8", "pico_transitorio_U1_con_clamp_v", "V",
               "check_absmax (#334): simulacion RK4 de escalon 36 V con SMBJ16A < 20.0 V absmax",
               predicho=check_absmax.escalon_lc()["v_pico_v"],
               hi=18.5))
    p.append(P("8", "ruido_riel_ultra_20MHz_uvrms", "uVrms",
               "rizado_budget: ruido residual total de la cascada en ancho de banda de 20 MHz",
               hi=rizado_budget.COTA_RIEL_UV))
    p.append(P("8", "ruido_riel_ultra_LNA_10Hz_100kHz_uvrms", "uVrms",
               "rizado_budget: ruido en banda de audio 10 Hz - 100 kHz (< 0.80 uVrms)",
               hi=rizado_budget.rb4.COTA_TOTAL_RIEL_V * 1e6))

    return p


def _lee() -> dict[str, dict]:
    if not os.path.exists(CSV_PATH):
        return {}
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return {f"{r['paso']}|{r['magnitud']}": r for r in csv.DictReader(f)}


def _plantilla(puntos: list[Punto]) -> None:
    """Reescribe la hoja de campo CONSERVANDO lo que ya se midio."""
    previo = _lee()
    guardadas = sum(1 for r in previo.values() if r.get("medido", "").strip())
    huerfanas = [
        k for k, r in previo.items()
        if r.get("medido", "").strip() and k not in {pt.clave for pt in puntos}
    ]
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLS)
        for pt in puntos:
            pred = "" if pt.predicho is None else f"{pt.predicho:g}"
            tol = "" if pt.tol is None else f"{pt.tol:g}"
            v = previo.get(pt.clave, {})
            w.writerow([
                pt.paso, pt.magnitud, pt.unidad, pt.rango(), pred, tol,
                v.get("medido", ""), v.get("placa", ""),
                v.get("fecha", ""), pt.fuente
            ])
    print(f"escrita la hoja de campo v5: {CSV_PATH} ({len(puntos)} puntos, "
          f"{guardadas} medidas conservadas)")
    if huerfanas:
        print(f"  ATENCION: {len(huerfanas)} medida(s) sin punto que las reciba:")
        for k in huerfanas:
            print(f"    {k} = {previo[k]['medido']}")


def _contrato(puntos: list[Punto], filas: dict[str, dict]) -> None:
    """Verifica la integridad de las predicciones frente a presupuestos."""
    pasos = {pt.paso for pt in puntos}
    assert PASOS_ESPERADOS <= pasos, (
        f"faltan pasos en la lista: {sorted(PASOS_ESPERADOS - pasos)}"
    )
    sin_criterio = [
        pt.clave for pt in puntos
        if not pt.es_criterio and "REGISTRO" not in pt.fuente
    ]
    assert not sin_criterio, f"puntos sin criterio ni REGISTRO: {sin_criterio}"

    viejas = []
    for pt in puntos:
        fila = filas.get(pt.clave)
        if fila is None or pt.predicho is None or not fila.get("predicho", ""):
            continue
        if abs(float(fila["predicho"]) - pt.predicho) > 1e-5 * max(1.0, abs(pt.predicho)):
            viejas.append(f"{pt.clave}: hoja {fila['predicho']} != codigo {pt.predicho:g}")
    assert not viejas, (
        f"la hoja de campo tiene predicciones viejas: {viejas}. Corre --plantilla"
    )
    faltan = [pt.clave for pt in puntos if pt.clave not in filas]
    assert not faltan or not filas, (
        f"la hoja de campo existe pero le faltan filas: {faltan[:5]}. Corre --plantilla"
    )


def main(argv: list[str]) -> int:
    puntos = _puntos()
    if "--plantilla" in argv:
        _plantilla(puntos)
        return 0

    filas = _lee()
    if not filas:
        print(f"Hoja de campo {CSV_PATH} no encontrada. Creandola con --plantilla...")
        _plantilla(puntos)
        filas = _lee()

    _contrato(puntos, filas)

    criterios = [pt for pt in puntos if pt.es_criterio]
    registros = [pt for pt in puntos if not pt.es_criterio]
    fallos, sin_medir, medidos = [], [], 0
    for pt in criterios:
        bruto = (filas.get(pt.clave) or {}).get("medido", "").strip()
        if not bruto:
            sin_medir.append(pt)
            continue
        medidos += 1
        motivo = pt.juzga(bruto)
        if motivo:
            fallos.append((pt, motivo))

    print("check_bringup v5: lo medido contra lo predicho (ladrillo y DC-DCs)\n")
    print(f"  {len(puntos)} puntos en {len(PASOS_ESPERADOS)} pasos: "
          f"{len(criterios)} con criterio, {len(registros)} de registro")
    print("  predicciones importadas de: ladrillo_budget, margen_budget, "
          "rizado_budget,")
    print("  secuencia_budget, recuperacion_budget, check_absmax, check_telemetria y curvas.")
    print("  Ninguna esta escrita a mano dos veces.\n")

    por_paso: dict[str, list[Punto]] = {}
    for pt in criterios:
        por_paso.setdefault(pt.paso, []).append(pt)
    for paso in sorted(por_paso, key=lambda s: (int(s[0]), s)):
        hechos = sum(1 for pt in por_paso[paso]
                     if (filas.get(pt.clave) or {}).get("medido", "").strip())
        print(f"  paso {paso:3s}: {hechos:2d}/{len(por_paso[paso]):2d} medidos")

    if fallos:
        print("\n  FUERA DE RANGO:")
        for pt, motivo in fallos:
            print(f"    {pt.clave}: {motivo}  (esperado {pt.rango()})")
        print(f"\nROJO: {len(fallos)} medida(s) fuera de rango.")
        return 1

    if sin_medir:
        print(f"\n  sin medir: {len(sin_medir)} de {len(criterios)} criterios")
        for pt in sin_medir[:4]:
            print(f"    {pt.clave}  (esperado {pt.rango()} {pt.unidad})")
        if len(sin_medir) > 4:
            print(f"    ... y {len(sin_medir) - 4} mas")
        print()
        print(f"HUECO: faltan {len(sin_medir)} de {len(criterios)} criterios "
              f"por medir en la placa fisica. La placa R no existe todavia: "
              f"esto es lo correcto, y sera 0 el dia que se mida. Lo que este "
              f"guion ya hace es impedir que la hoja de campo salga con un "
              f"paso menos o con una prediccion vieja.")
        return 2

    print(f"\nOK: {medidos} criterios medidos y dentro de rango.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
