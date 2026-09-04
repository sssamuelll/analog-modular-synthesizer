"""El bring-up de la fuente v4: lo MEDIDO contra lo PREDICHO, escrito antes.

    python check_bringup.py               comprueba medidas.csv
    python check_bringup.py --plantilla   reescribe la hoja de campo

## Por que se escribe ahora, con la placa sin dibujar

Un bring-up escrito DESPUES de medir es un acta, no una prediccion. Este se
escribe con la placa R todavia en el papel, igual que el de la v3, y hereda su
forma: cada paso predice un numero, `medidas.csv` lo guarda, y este guion lo
juzga.

## Lo que cambia respecto del de la v3, y lo que NO

**No pierde ninguno de sus pasos.** Los 6 (telemetria contra multimetro), 7
(termica) y 8 de la v3 siguen; la v1 del papel de la v4 los habia dejado caer.
Lo que muere es el paso 4 --el valle-- porque sin rectificador no hay valle: su
sustituto es el paso 2.

**Y las predicciones se IMPORTAN de los presupuestos, no se copian.** Es la
diferencia grande con el de la v3, donde cada numero estaba escrito a mano con
su cita. Aqui el minimo de +15 V con carga sale de `margen_budget.py`, la
temperatura del aire de `calor_budget.py`, el rizado del riel de
`rizado_budget.py`, la corriente de red de `fusible_budget.py`, el desfase en
cents de `ground_budget.py` y el disparo del crowbar de `check_absmax.py`. Si
un presupuesto cambia, la hoja de campo cambia con el y nadie tiene que
acordarse. Un bring-up cuya prediccion se queda vieja mide la placa contra un
diseno que ya no existe.

## Los codigos de salida, y por que 2 con la placa sin fabricar

    0   todos los puntos con criterio medidos y dentro de rango
    1   alguna medida FUERA de rango: la placa no pasa
    2   faltan medidas. Ni bien ni mal: no se sabe todavia

Con la placa aun sin fabricar lo correcto es 2. Un fichero de medidas vacio que
saliera en verde seria la version de banco de la hoja de 711 bytes que paso el
ERC con cero errores (constitucion, Principio III).

## Dos clases de punto

  * **criterio**: hay un rango y suspender significa algo.
  * **registro**: no hay rango porque el numero AUN no existe --la temperatura
    de la carcasa de un IRM, que su hoja no publica--. Se anota porque solo
    significa algo comparado con la placa siguiente. Un registro nunca pone
    nada en rojo, pero se cuenta y se lista.

## El paso 0.1 sigue siendo el que autoriza a enchufar

El aislamiento de los tres tabs es lo unico de esta lista que decide si la
placa se enchufa. Dos de los tres estan a +-15 V crudos y la pared contra la
que atornillan es acero a PE. Va primero y su umbral es de megaohmios.
"""
from __future__ import annotations

import csv
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
for _ruta in (DIR, os.path.join(DIR, "..", "..", "tools"),
              os.path.join(DIR, "..", "..", "bus-board")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import check_absmax  # noqa: E402
import fuga_budget  # noqa: E402
import fusible_budget  # noqa: E402
import ground_budget  # noqa: E402
import margen_budget  # noqa: E402
import rizado_budget  # noqa: E402
from calor_budget import (P_BASE, PLACA_A, SOSTENIDO,  # noqa: E402
                          aire_recinto_c, p_cajon_w, p_recinto_w)

CSV_PATH = os.path.join(DIR, "medidas.csv")
COLS = ["paso", "magnitud", "unidad", "criterio", "predicho", "tolerancia",
        "medido", "placa", "fecha", "fuente"]

# Los pasos que el papel sec.9.1 enumera. Si falta uno en el CSV, el bring-up
# no falla: PASA, y por eso los pasos 6, 7 y 8 de la v3 se habian perdido en
# la v1 de este papel. Se asevera la cobertura, no solo los valores.
PASOS_ESPERADOS = {"0", "1", "2", "2b", "3", "4", "5", "6", "7", "8"}

TOL_TELE = 0.01          # +-1 %: divisores al 0,1 % mas el error del ADS1115
MODULOS = ("PS1", "PS2", "PS3", "PS4", "PS5", "PS6")
V_MODULO = {"PS1": 15.0, "PS2": -15.0, "PS3": 12.0, "PS4": -12.0,
            "PS5": 5.0, "PS6": 5.0}
TOL_MODULO = 0.025       # hoja p. 2, VOLTAGE TOLERANCE
RIZADO_MAX_VPP = {"PS1": 0.200, "PS2": 0.200, "PS3": 0.150, "PS4": 0.150,
                  "PS5": 0.080, "PS6": 0.080}


class Punto:
    """Un numero que este bring-up predice, con de donde sale."""

    def __init__(self, paso, magnitud, unidad, fuente, predicho=None,
                 tol=None, lo=None, hi=None, literal=None):
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
        return not (self.lo is None and self.hi is None
                    and self.literal is None)

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
        """None si pasa; si no, por que falla."""
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


def t_aire_diseno_c() -> float:
    return aire_recinto_c(p_recinto_w(SOSTENIDO), p_cajon_w(SOSTENIDO),
                          area_venteo_mm2=P_BASE["area_venteo_mm2"])


def _puntos() -> list[Punto]:
    P, p = Punto, []

    # --- Paso 0: con el equipo DESENCHUFADO -------------------------------
    for ref in ("U1", "U2", "U3"):
        p.append(P("0", f"aislamiento_tab_{ref}_a_chasis", "Mohm",
                   "papel sec.9.1 paso 0: el tab esta a un riel crudo y la "
                   "pared es acero a PE. ESTA medida autoriza a enchufar",
                   lo=10.0))
    p.append(P("0", "continuidad_PE_a_chasis", "mohm",
               "papel sec.9.1 paso 0: continuidad de tierra", hi=100.0))
    # NUEVO en la v4: la estrella son seis bornes que llegan a un nodo, y hay
    # que medir las dos cosas -- que cada uno LLEGA, y que entre ellos no hay
    # camino cuando el nodo se desconecta.
    for ref in MODULOS[:5]:
        p.append(P("0", f"continuidad_borne_estrella_{ref}", "mohm",
                   "papel sec.9.1 paso 0 (nuevo): cada borne de estrella con "
                   "el nodo. En PS2 y PS4, apiladas, el borne que toca la "
                   "estrella es el POSITIVO", hi=20.0))
    p.append(P("0", "aislamiento_entre_bornes_estrella_sin_nodo", "Mohm",
               "papel sec.9.1 paso 0 (nuevo): con la estrella DESCONECTADA, "
               "entre el borne de un modulo y el de otro. No 'abierto': "
               "> 1 Mohm", lo=1.0))
    p.append(P("0", "aislamiento_GNDA_a_GNDD", "Mohm",
               "papel sec.4.1: PS6 sale flotante y GNDD se une donde el papel "
               "del cerebro decida. La v3 ya lo aseveraba (paso 6.2)", lo=1.0))

    # --- Paso 1: R sola, cada IRM por separado ----------------------------
    for ref in MODULOS:
        v = V_MODULO[ref]
        p.append(P("1", f"{ref}_vacio", "V",
                   "papel sec.9.1 paso 1: cada IRM uno por uno, en vacio",
                   predicho=v, tol=abs(v) * TOL_MODULO))
        p.append(P("1", f"{ref}_a_nominal", "V",
                   "papel sec.9.1 paso 1: con carga ficticia a su nominal",
                   predicho=v, tol=abs(v) * TOL_MODULO))
        p.append(P("1", f"{ref}_rizado_20MHz", "Vpp",
                   "hoja p. 2, RIPPLE & NOISE (max.), con el metodo de su "
                   "Note.2: par trenzado de 12 pulgadas terminado con "
                   "0,1 uF || 47 uF, y 20 MHz de ancho de banda",
                   hi=RIZADO_MAX_VPP[ref]))
    p.append(P("1", "corriente_red_rms_a_liston", "A",
               "fusible_budget.i_red_rms_a('liston'), con pinza",
               predicho=fusible_budget.i_red_rms_a("liston"),
               tol=0.30 * fusible_budget.i_red_rms_a("liston")))
    p.append(P("1", "inrush_pico_arranque_frio", "A",
               "fusible_budget: Vpico sobre la NTC fria mas la red",
               hi=1.5 * fusible_budget.i_pico_a(
                   fusible_budget.r_arranque_frio_ohm())))
    p.append(P("1", "inrush_pico_rearranque_100ms", "A",
               "fusible_budget: el caso que dimensiona el fusible. Cortar y "
               "volver a los 100 ms",
               hi=1.5 * fusible_budget.i_pico_a(
                   fusible_budget.r_rearranque_caliente_ohm())))
    p.append(P("1", "fuga_a_PE_seis_encendidos", "mA",
               "fuga_budget.fuga_total_ma(), con los seis en marcha. Es "
               "tambien la medida que arbitra D-F5",
               hi=fuga_budget.LIMITE_NORMA_MA))

    # --- Paso 2: los +-15 V con carga, despues del LC ---------------------
    p.append(P("2", "mas15_minimo_con_carga", "V",
               "margen_budget.v_entrada_minima_v(): lo que le tiene que "
               "llegar a U1 en el peor caso",
               lo=margen_budget.v_entrada_minima_v()))
    p.append(P("2", "mas15_necesario_para_regular", "V",
               "margen_budget.v_necesaria_v('U1'): REGISTRO del criterio, "
               "para que la hoja de campo lleve el numero contra el que se "
               "compara. Hoy el margen es NEGATIVO (HUECO de margen_budget)"))
    p.append(P("2", "rizado_tras_LC_20MHz", "Vpp",
               "rizado_budget: los 200 mVp-p del IRM por la transferencia del "
               "LC amortiguado a 65 kHz",
               hi=3.0 * rizado_budget.RIZADO_IRM_VPP
               * rizado_budget.h_lc(rizado_budget.F_CONMUTACION_HZ)))
    p.append(P("2", "pico_del_LC_en_resonancia", "dB",
               "rizado_budget.pico_lc_db(): el LC amortiguado no puede "
               "amplificar dentro de la banda de 10 Hz-100 kHz",
               hi=rizado_budget.PICO_MAX_DB))

    # --- Paso 2b: EL SECUENCIADOR, que valida D-F4 ------------------------
    p.append(P("2b", "quitar_red_a_PS1_caen_los_dos", "si/no",
               "papel sec.9.1 paso 2b: con PS2 viva, los dos rieles de la "
               "cascada caen juntos. Sin este paso, D-F4 es una promesa",
               literal="si"))
    p.append(P("2b", "quitar_red_a_PS2_caen_los_dos", "si/no",
               "papel sec.9.1 paso 2b, el otro sentido", literal="si"))
    p.append(P("2b", "quitar_red_a_PS3_cae_el_rack_entero", "si/no",
               "papel sec.4.3: el mismo detector, replicado en el rack",
               literal="si"))
    p.append(P("2b", "ventana_riel_solo_medida", "ms",
               "secuencia_budget: el transitorio en el que la cascada sigue "
               "habilitada con un riel solo", hi=10.0))

    # --- Pasos 3 a 5: la cascada, como en la v3 ---------------------------
    for tp, senal, nom, tol in (("TP7", "+13V1", 13.1, 0.3),
                                ("TP8", "-12V9", -12.9, 0.3),
                                ("TP3", "+12V", 12.00, 0.05),
                                ("TP4", "-12V", -12.00, 0.05),
                                ("TP5", "+5V", 5.00, 0.25)):
        p.append(P("3", f"{tp}_{senal}_sin_carga", "V",
                   f"como la v3: {nom:+g} +-{tol}. La ventana de TP7/TP8 la "
                   f"vigila margen_budget, que hoy dice que no cabe",
                   predicho=nom, tol=tol))
    for pin, nom in ((1, -12.0), (2, 0.0), (3, 0.0), (4, 12.0)):
        p.append(P("4", f"J2_pin{pin}", "V",
                   f"como la v3 (#121): {nom:+g} V MEDIDO, no leido del "
                   f"rotulo", predicho=nom, tol=0.5))
    for tp, nom in (("TP3", 12.0), ("TP4", -12.0)):
        p.append(P("5", f"{tp}_con_carga_650mA", "V",
                   "como la v3: la cascada entregando su riel",
                   predicho=nom, tol=0.05))

    # --- Paso 6: telemetria contra multimetro -----------------------------
    for canal, nom in (("U8_mas12", 12.0), ("U9_mas5", 5.0),
                       ("U10_menos12", -12.0), ("U10_mas15", 15.0),
                       ("U10_menos15", -15.0),
                       ("U10_menos12_rack", -12.0)):
        p.append(P("6", f"telemetria_{canal}_vs_multimetro", "V",
                   "papel sec.7: la telemetria contra un multimetro. Los "
                   "+-15 V con carga son nuevos de la v4, y el cuarto canal "
                   "del ADS1115 va al -12 de rack",
                   predicho=nom, tol=abs(nom) * TOL_TELE))
    for ina, riel in (("U13", "rack+12"), ("U14", "rack+5")):
        p.append(P("6", f"{ina}_corriente_{riel}_vs_pinza", "A",
                   f"D-F2: los dos INA226 de rack, poblados. Con la carga "
                   f"ficticia del liston ({PLACA_A[riel]:.1f} A)",
                   predicho=PLACA_A[riel], tol=0.05 * PLACA_A[riel]))

    # --- Paso 7: la termica, que valida calor_budget.py -------------------
    p.append(P("7", "aire_recinto_a_carga_sostenida", "C",
               "calor_budget.py, punto fijo con D-F3 = A y el venteo minimo. "
               "ES LA MEDIDA QUE DECIDE si la columna 'sostenido' de sec.1 es "
               "cierta",
               predicho=t_aire_diseno_c(), tol=8.0))
    p.append(P("7", "area_venteo_construida", "mm2",
               "el venteo que el papel del case acabe dibujando (#289). Por "
               "debajo del que calor_budget pide, el sostenido no vale",
               lo=P_BASE["area_venteo_mm2"]))
    for ref in ("PS3", "PS6"):
        p.append(P("7", f"carcasa_{ref}_termopar", "C",
                   "REGISTRO: la hoja publica la temperatura del AIRE (-30 a "
                   "+85 C) y no la de la carcasa. Solo significa algo "
                   "comparado con la placa siguiente"))
    p.append(P("7", "NTC_carcasa", "C",
               "REGISTRO: fusible_budget la estima disipando "
               f"{fusible_budget.calor_ntc_w():.2f} W dentro del recinto, y "
               f"la tabla de calor del papel sec.6 no la lleva"))
    for riel in ("rack+12", "rack-12", "rack+5"):
        p.append(P("7", f"sostenido_{riel}_medido", "A",
                   f"calor_budget.SOSTENIDO['{riel}']: la carga que el riel "
                   f"aguanta sin salirse de su curva a la T de arriba",
                   lo=SOSTENIDO[riel] * 0.9))

    # --- Paso 8: lo nuevo de la v4 ----------------------------------------
    # DOS puntos, y no uno, porque son DOS medidas distintas y la primera
    # version de este guion las confundio: predecia el desfase del NETO de los
    # tres rieles (4,00 A) con una instruccion que manda cargar SOLO el +12
    # con 2 A, que produce la mitad. Y con +-50 % la cota inferior caia
    # EXACTAMENTE encima del valor del procedimiento escrito: cualquier
    # lectura redondeada a dos decimales salia roja.
    i_un_riel = 2.0
    mv1 = ground_budget.desfase_mv(i_un_riel, 10)
    p.append(P("8", "desfase_masa_rack_a_GNDREF_con_2A_en_mas12", "mV",
               f"ground_budget.desfase_mv({i_un_riel:.0f}) : cargando SOLO el "
               f"+12 de rack con {i_un_riel:.0f} A de carga ficticia, que es "
               f"lo que dice el papel sec.9.1. Por masa vuelven esos mismos "
               f"{i_un_riel:.0f} A",
               predicho=mv1, tol=0.6 * mv1))
    mv2 = ground_budget.desfase_mv(ground_budget.I_RACK_SOSTENIDO_A, 10)
    p.append(P("8", "desfase_masa_rack_a_GNDREF_a_carga_sostenida", "mV",
               f"ground_budget.desfase_mv() con el rack ENTERO a su carga "
               f"sostenida: por masa vuelve el NETO, "
               f"{ground_budget.I_RACK_SOSTENIDO_A:.2f} A (+12 y +5 menos el "
               f"-12). El numero es GRANDE a proposito: lo que se verifica no "
               f"es que sea pequeno",
               predicho=mv2, tol=0.6 * mv2))
    p.append(P("8", "desafinacion_1Voct_por_la_bahia", "cents",
               "LA MEDIDA QUE DE VERDAD IMPORTA: un CV de 1 V entrando por la "
               "bahia desde un jack cargado. Si la bahia recibe en "
               "diferencial, el desfase se resta y esto tiene que salir "
               "PEQUENO aunque el de arriba salga grande",
               hi=ground_budget.OBJETIVO_CENTS))
    p.append(P("8", "disparo_crowbar_rack_mas12", "V",
               "check_absmax.V_DISPARO_V: forzar el disparo con PS3 cargada",
               predicho=check_absmax.V_DISPARO_V["rack+12"],
               tol=check_absmax.TOL_DISPARO_V))
    p.append(P("8", "disparo_crowbar_rack_mas5", "V",
               "check_absmax: el del +5, que es el que tiene la ventana "
               "estrecha (0,27 V con la dispersion supuesta)",
               predicho=check_absmax.V_DISPARO_V["rack+5"],
               tol=check_absmax.TOL_DISPARO_V))
    p.append(P("8", "tras_disparo_PS3_en_hiccup_PS4_apagada", "si/no",
               "D-F6: el lazo cierra porque el IRM entra en hiccup, y el "
               "secuenciador apaga el otro riel. Nada humea", literal="si"))
    peor_f, peor_v = rizado_budget.peor_de_la_banda()
    p.append(P("8", "ruido_riel_ultra_20MHz_ancho_de_banda", "uV",
               f"rizado_budget: el peor punto de la banda cae en "
               f"{peor_f / 1e6:.3g} MHz. El LNA del #58 mira 10 Hz-100 kHz y "
               f"puede dar verde con RF entrando por otro lado",
               hi=rizado_budget.COTA_RUIDO_V * 1e6))
    p.append(P("8", "ruido_riel_ultra_LNA_10Hz_100kHz", "uV",
               "#58: la puerta de siempre del riel ultra, que sigue estando y "
               "ya no basta sola",
               hi=rizado_budget.COTA_TOTAL_RIEL_V * 1e6))

    return p


def _lee() -> dict[str, dict]:
    if not os.path.exists(CSV_PATH):
        return {}
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return {f"{r['paso']}|{r['magnitud']}": r for r in csv.DictReader(f)}


def _plantilla(puntos: list[Punto]) -> None:
    """Reescribe la hoja de campo CONSERVANDO lo que ya se midio.

    La primera version la reescribia en blanco, y eso era una trampa: el
    aserto de "predicciones viejas" de _contrato() manda correr --plantilla
    por su nombre, asi que el dia que un presupuesto se moviera con medidas ya
    tomadas, el unico remedio que el propio mensaje prescribe habria borrado
    los datos de banco. Lo medido no lo genera nadie otra vez."""
    previo = _lee()
    guardadas = sum(1 for r in previo.values() if r.get("medido", "").strip())
    huerfanas = [k for k, r in previo.items()
                 if r.get("medido", "").strip()
                 and k not in {pt.clave for pt in puntos}]
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for pt in puntos:
            pred = "" if pt.predicho is None else f"{pt.predicho:g}"
            tol = "" if pt.tol is None else f"{pt.tol:g}"
            v = previo.get(pt.clave, {})
            # La columna `criterio` lleva el rango ESCRITO, no solo el par
            # predicho/tolerancia: 33 de los 71 criterios tienen cota unica
            # (>= o <=) y salian con las dos columnas vacias, o sea que quien
            # esta en el banco no tenia contra que juzgar.
            w.writerow([pt.paso, pt.magnitud, pt.unidad, pt.rango(), pred, tol,
                        v.get("medido", ""), v.get("placa", ""),
                        v.get("fecha", ""), pt.fuente])
    print(f"escrita la hoja de campo: {CSV_PATH} ({len(puntos)} puntos, "
          f"{guardadas} medidas conservadas)")
    # Y SI ALGUNA MEDIDA SE QUEDA SIN SITIO, SE DICE. Renombrar una magnitud
    # deja su fila huerfana; sin este aviso la medida desaparece y el punto
    # nuevo se cuenta como "sin medir", que no es lo mismo.
    if huerfanas:
        print(f"  ATENCION: {len(huerfanas)} medida(s) sin punto que las "
              f"reciba, y NO estan en la hoja nueva:")
        for k in huerfanas:
            print(f"    {k} = {previo[k]['medido']}")
        print("  Alguien renombro una magnitud. Recuperalas del git antes de "
              "commitear.")


def _contrato(puntos: list[Punto], filas: dict[str, dict]) -> None:
    """Lo que este guion se asevera a si mismo, antes de juzgar nada."""
    pasos = {pt.paso for pt in puntos}
    assert PASOS_ESPERADOS <= pasos, (
        f"faltan pasos en la lista: {sorted(PASOS_ESPERADOS - pasos)}. Un "
        f"bring-up al que se le cae un paso no falla: PASA, y por eso los "
        f"pasos 6, 7 y 8 de la v3 se habian perdido en la v1 de este papel")
    sin_criterio = [pt.clave for pt in puntos
                    if not pt.es_criterio and "REGISTRO" not in pt.fuente]
    assert not sin_criterio, (
        f"puntos sin numero predicho y sin declararse REGISTRO: "
        f"{sin_criterio}. Un paso sin numero predicho no es un bring-up, es "
        f"una lista de tareas")
    # Y QUE LA HOJA DE CAMPO NO SE HAYA QUEDADO VIEJA. Las predicciones viven
    # en el codigo y se importan de los presupuestos; el CSV las lleva escritas
    # para quien mide. Si un presupuesto cambia y nadie regenera la plantilla,
    # el que este en el banco compara contra un diseno que ya no existe.
    viejas = []
    for pt in puntos:
        fila = filas.get(pt.clave)
        if fila is None or pt.predicho is None or not fila.get("predicho", ""):
            continue
        # 1e-5 relativo y no 1e-9: la hoja se escribe con %g, que redondea a
        # seis cifras significativas para que quien mida la pueda leer. La
        # tolerancia tiene que estar por encima de ese redondeo y muy por
        # debajo de cualquier deriva real.
        if abs(float(fila["predicho"]) - pt.predicho) > 1e-5 * max(
                1.0, abs(pt.predicho)):
            viejas.append(f"{pt.clave}: hoja {fila['predicho']} != codigo "
                          f"{pt.predicho:g}")
    assert not viejas, (
        f"la hoja de campo tiene predicciones viejas: {viejas}. Los "
        f"presupuestos cambiaron y nadie corrio --plantilla; quien mida "
        f"comparara contra un diseno que ya no existe")
    faltan = [pt.clave for pt in puntos if pt.clave not in filas]
    assert not faltan or not filas, (
        f"la hoja de campo existe pero le faltan filas: {faltan[:5]}"
        f"{'...' if len(faltan) > 5 else ''}. Corre --plantilla")


def main(argv: list[str]) -> int:
    puntos = _puntos()
    if "--plantilla" in argv:
        _plantilla(puntos)
        return 0

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

    print("check_bringup v4: lo medido contra lo predicho\n")
    print(f"  {len(puntos)} puntos en {len(PASOS_ESPERADOS)} pasos: "
          f"{len(criterios)} con criterio, {len(registros)} de registro")
    print("  predicciones importadas de: calor_budget, margen_budget, "
          "rizado_budget,")
    print("  fusible_budget, fuga_budget, ground_budget y check_absmax.")
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
