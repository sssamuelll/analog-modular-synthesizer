"""Comprobacion de telemetria, aislamiento e interfaces en la fuente v5 (T15-T17, T25-T26).

    python check_telemetria.py     # 0 verde, 1 infraccion, 2 hueco (algo sin poder comprobar)

Lee sam17-power-v5.net y bom.csv, y calcula lo que el circuito va a hacer. A
mano solo quedan los limites de las hojas de datos (con su pagina), las
etiquetas de texto y los escenarios de fallo que vienen de otros modelos.

  1. T15 INA226: el shunt de cada INA226 es la resistencia que la netlist pone
     entre IN+ e IN-, con su valor de bom.csv. La tension a plena corriente
     tiene que caber en el rango de entrada de shunt (+-81,92 mV, ina226.pdf
     SBOS547C p. 5) y el modo comun del riel en 0..36 V (p. 5). La corriente
     sale de ladrillo_budget (cascada, fila B, pantalla).
  2. T15 ADS1115: cada divisor se lee de la netlist (resistencia al riel y
     resistencia a la referencia, con su valor de bom.csv) y se barren los
     escenarios del riel contra [GND-0,3 V, VDD+0,3 V] (ads1115.pdf SBAS444E
     p. 4), tambien con la perdida del +5 V y el limite de 10 mA por pin.
  3. Mapa I2C: la direccion de cada INA226, del ADS1115 y del TMP1075 sale de
     las redes en sus patillas de direccion, por la tabla de su hoja (ina226.pdf
     Table 6-2 p. 18, ads1115.pdf Table 7-2 p. 20, tmp1075.pdf Table 7-2 p. 14),
     y se busca colision en cada bus (par SDA/SCL).
  4. Tension de alimentacion de cada chip contra su maximo absoluto.
  5. T16/T17/T25/T26: lo que la netlist demuestra (GNDD solo toca GNDA/GND24
     por el URB y el ISO1541, el I2C solo cruza por el ISO1541, J5 en GNDA, +5 V
     de rack y +5 V digital en conectores distintos) se comprueba; lo que es una
     medida fisica (continuidad, aislamiento, fugas) se busca en medidas.csv y,
     si no esta medido, sale como HUECO con el motivo. Nada de eso se imprime en
     verde sin evidencia.

Una infraccion sale con codigo 1. Sin infracciones pero con cosas sin verificar,
con codigo 2 (gates.py lo cuenta como HUECO).
"""
from __future__ import annotations

import csv
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
for _d in (DIR, os.path.join(DIR, "kicad")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from bom_valores import filas, valor  # noqa: E402
from check_netlist import (NET, direccion_ina226, leer, red_de,  # noqa: E402
                           resistencias_entre)

# check_absmax ANTES que ladrillo_budget: este arrastra los modulos de la v4 al
# sys.path, y la v4 tiene su propio check_absmax.py que taparia al de la v5.
import check_absmax  # noqa: E402
import ladrillo_budget  # noqa: E402

MEDIDAS_CSV = os.path.join(DIR, "medidas.csv")

# --- Hojas de datos (TI, descargadas de ti.com; pagina = la impresa en el PDF) ---
# INA226 SBOS547C. Patillas (Table 4-1, p. 3): A1 1, A0 2, SDA 4, SCL 5, VS 6,
# GND 7, VBUS 8, IN- 9, IN+ 10.
INA_VS_ABSMAX_V = 6.0               # p. 4, 5.1: VVS
INA_CM_MIN_V, INA_CM_MAX_V = 0.0, 36.0   # p. 5, 5.5: Bus voltage input range
INA_SHUNT_FS_V = 0.08192            # p. 5, 5.5: Shunt voltage input range, 81,92 mV
# ADS1115 SBAS444E. Patillas DGS (Table 4-1, p. 3): ADDR 1, GND 3, AIN0..AIN3 4..7,
# VDD 8, SDA 9, SCL 10.
ADS_VDD_ABSMAX_V = 7.0              # p. 4, 5.1
ADS_AIN_MARGEN_V = 0.30             # p. 4, 5.1: AINx entre GND-0,3 V y VDD+0,3 V
ADS_IIN_MAX_A = 0.010               # p. 4, 5.1: 10 mA continuos por pin
ADS_DIR = {"GND": 0x48, "VDD": 0x49, "SDA": 0x4A, "SCL": 0x4B}   # p. 20, Table 7-2
# TMP1075 SBOS854F. Patillas DGK (Table 5-1, p. 4): SDA 1, SCL 2, GND 4, A2 5,
# A1 6, A0 7, V+ 8.
TMP_VMAS_ABSMAX_V = 6.5             # p. 5, 6.1: V+
# Table 7-2 (p. 14): "A2 A1 A0 direccion". 0 = GND, 1 = V+.
TMP_DIR = {tuple(f.split()[:3]): int(f.split()[3], 16) for f in """
0 0 SDA 0x40
0 0 SCL 0x41
0 1 SDA 0x42
0 1 SCL 0x43
1 0 SDA 0x44
1 0 SCL 0x45
1 1 SDA 0x46
1 1 SCL 0x47
0 0 0 0x48
0 0 1 0x49
0 1 0 0x4A
0 1 1 0x4B
1 0 0 0x4C
1 0 1 0x4D
1 1 0 0x4E
1 1 1 0x4F
0 SDA SDA 0x50
0 SDA SCL 0x51
0 SCL SDA 0x52
0 SCL SCL 0x53
1 SDA SDA 0x54
1 SDA SCL 0x55
1 SCL SDA 0x56
1 SCL SCL 0x57
0 SDA 0 0x58
0 SDA 1 0x59
0 SCL 0 0x5A
0 SCL 1 0x5B
1 SDA 0 0x5C
1 SDA 1 0x5D
1 SCL 0 0x5E
1 SCL 1 0x5F
""".strip().splitlines()}
# ISO1541 SLLSEB6F. Patillas (Table 5-1, p. 4): VCC1 1, SDA1 2, SCL1 3, GND1 4,
# GND2 5, SCL2 6, SDA2 7, VCC2 8.
ISO_VCC_ABSMAX_V = 6.0              # p. 6, 6.1: VCC1, VCC2

# BAT54S (onsemi BAT54SLT1G, D14..D17): no hay hoja en docs/reference/datasheets.
VF_BAT54_V = 0.29                   # peor caso en frio a ~100 uA; SIN HOJA, ver _HUECOS
CLAMP_V = -VF_BAT54_V

# Solo texto: medidas.csv y check_bringup lo copian tal cual.
_RIEL_Y_DESC = {
    "U8":  ("+12 V ultra", "D-F1: 650 mA sostenidos"),
    "U12": ("+5 V aux U3", "Alimentacion telemetria y control"),
    "U13": ("+12 V rack",  "D-F2 / T15: 500 mA fila B + 550 mA pantalla"),
    "U14": ("+5 V rack",   "D-F2 / T15: 500 mA fila B"),
}
_AIN_SENAL = {"AIN0": "-12 V ultra", "AIN1": "VRAW+ crudo",
              "AIN2": "VRAW- crudo", "AIN3": "-12 V rack"}

# Corriente de plena escala de cada shunt, del presupuesto del ladrillo. La de
# U12 (+5 V auxiliar) es el techo de diseno del riel, un ESTIMADO alli: nada
# en el riel la limita, y se avisa.
I_AUX_A = ladrillo_budget.AUX_A


def _corrientes() -> dict[str, float]:
    return {
        "U8": ladrillo_budget.CASCADA_A,
        "U12": I_AUX_A,
        "U13": ladrillo_budget.FILA_B_A + ladrillo_budget.PANTALLA_A,
        "U14": ladrillo_budget.FILA_B_A,
    }


def _pico_tope_u1() -> float:
    """El pico en VRAW+ lo da el modelo RK4 de check_absmax.py con las piezas
    de la BOM, no un 18,08 copiado (#474)."""
    return check_absmax.escalon_lc(v_fallo_v=36.0)["v_pico_v"]


def _disparo_alto_rack12() -> float:
    return check_absmax.RACK_RIELES["rack-12"]["disparo_v"] + check_absmax.TOL_DISPARO_TL431BI_V


# Escenarios del riel tras el nominal, de otros modelos (check_absmax, hojas de
# TRACO): no se derivan de la netlist.
_NOMINAL_ETIQUETA = {"AIN0": "nominal", "AIN1": "nominal recortado",
                     "AIN2": "nominal recortado", "AIN3": "nominal"}
_U2_V = ladrillo_budget.SETPOINT_V["U2"]                 # -12V9 con U6/U7 en corto
_OVP_THN20_V = check_absmax.V_OVP_MAX_THN20_V            # traco_thn20wi.pdf p. 2
_SANO_CRUDO_V = check_absmax.v_sano_max_u1_v()           # margen_budget
_OVP_THN30_V = check_absmax.RACK_RIELES["rack-12"]["ovp_max_v"]
_ESCENARIOS = {
    "AIN0": [("post-regulador en corto", -_U2_V), ("fallo OVP crudo", -_OVP_THN20_V), ("apagada", 0.0)],
    "AIN1": [("maximo sano en vacio", _SANO_CRUDO_V),
             ("tope eFuse TPS26631 (modelo RK4)", _pico_tope_u1()), ("apagada", 0.0)],
    "AIN2": [("maximo sano en vacio", -_SANO_CRUDO_V),
             ("OVP maximo THN 20-2413WI", -_OVP_THN20_V), ("apagada", 0.0)],
    "AIN3": [("OVP max THN 30-2422WI", -_OVP_THN30_V),
             ("disparo crowbar D-F6 (borde alto)", -_disparo_alto_rack12()), ("apagada", 0.0)],
}
# Riel negativo vivo con el +5 V caido (peor caso por canal).
_FALLO_VDD = {"AIN0": -_U2_V, "AIN2": -_OVP_THN20_V, "AIN3": -_OVP_THN30_V}

# Lo que no se pudo derivar al construir las tablas de abajo; demo() lo imprime.
_FALLOS: list[str] = []
_HUECOS: list[str] = []


def _tension_de(red: str | None) -> float | None:
    """Tension nominal que dice el NOMBRE de la red: +12V_ULTRA 12, -15V5_LC -15,5,
    +3V3_DIG 3,3, GNDA 0. None si el nombre no la dice."""
    if red is None:
        return None
    if red.startswith("GND"):
        return 0.0
    m = re.match(r"([+-])(\d+)V(\d?)(?:_|$)", red)
    if not m:
        return None
    v = float(f"{m.group(2)}.{m.group(3) or '0'}")
    return -v if m.group(1) == "-" else v


def _num(ref: str) -> int:
    return int(re.sub(r"\D", "", ref))


def _refs(prefijo: str) -> list[str]:
    """Designadores de bom.csv cuyo valor empieza por `prefijo`, en orden numerico."""
    return sorted((r for r, f in BOM.items() if f["value"].startswith(prefijo)), key=_num)


def _otra_pata(nets: dict[str, set[str]], nodo: str) -> str | None:
    ref, pin = nodo.split(".")
    return red_de(nets, f"{ref}.{'2' if pin == '1' else '1'}")


def _shunts(nets: dict[str, set[str]]) -> tuple[list[tuple], dict[str, str]]:
    """(SHUNTS_V5, {INA226: resistencia}). Cada tupla es (ref_ina, riel, r_sh,
    i_max, v_bus, desc): el shunt y el riel salen de la netlist y de bom.csv."""
    tuplas: list[tuple] = []
    resistencias: dict[str, str] = {}
    corrientes = _corrientes()
    for ref in _refs("INA226"):
        mas, menos, bus = (red_de(nets, f"{ref}.{p}") for p in (10, 9, 8))
        rs = resistencias_entre(nets, mas, menos) if mas and menos else []
        if len(rs) != 1:
            _FALLOS.append(f"{ref}: entre IN+ ({mas}) e IN- ({menos}) hay {len(rs)} "
                           f"resistencias {rs}; tiene que haber una (el shunt)")
            continue
        v_bus = _tension_de(bus)
        if v_bus is None or ref not in corrientes:
            _HUECOS.append(f"{ref}: sin tension de riel ({bus}) o sin corriente de plena "
                           "escala en el presupuesto; no se puede dimensionar el shunt")
            continue
        riel, desc = _RIEL_Y_DESC.get(ref, (bus, "sin etiqueta"))
        resistencias[ref] = rs[0]
        tuplas.append((ref, riel, valor(rs[0]), corrientes[ref], v_bus, desc))
    return tuplas, resistencias


def _canales(nets: dict[str, set[str]]) -> tuple[list[tuple], dict[str, tuple]]:
    """(CANALES_ADS_V5, {AINx: (R al riel, R a la referencia, red del riel, red de la
    referencia)}). Cada tupla es (pin, senal, v_ref, casos, clamp). El primer caso es
    el nominal, que sale del nombre de la red del riel."""
    tuplas: list[tuple] = []
    divisores: dict[str, tuple] = {}
    ads = _refs("ADS1115")
    if len(ads) != 1:
        _FALLOS.append(f"hay {len(ads)} ADS1115 en bom.csv ({ads}); la comprobacion espera uno")
        return tuplas, divisores
    u = ads[0]
    gnd, vdd = red_de(nets, f"{u}.3"), red_de(nets, f"{u}.8")
    for k in range(4):
        pin, red = f"AIN{k}", red_de(nets, f"{u}.{4 + k}")
        arriba, abajo, diodos = [], [], []
        for nodo in sorted(nets.get(red, ())):
            ref = nodo.split(".")[0]
            otra = _otra_pata(nets, nodo)
            if re.fullmatch(r"R\d+", ref):
                (abajo if otra in (vdd, gnd) else arriba).append((ref, otra))
            elif re.fullmatch(r"D\d+", ref):
                diodos.append(ref)
        if len(arriba) != 1 or len(abajo) != 1:
            _FALLOS.append(f"{u}.{pin} ({red}): el divisor no tiene una resistencia al riel y "
                           f"una a la referencia (arriba {arriba}, abajo {abajo})")
            continue
        (r_arriba, riel), (r_abajo, ref_red) = arriba[0], abajo[0]
        v_nom, v_ref = _tension_de(riel), _tension_de(ref_red)
        if v_nom is None or v_ref is None:
            _HUECOS.append(f"{pin}: el nombre de la red {riel} / {ref_red} no dice su tension")
            continue
        clamp = any(red_de(nets, f"{d}.{p}") == gnd for d in diodos for p in ("1", "2"))
        casos = [(_NOMINAL_ETIQUETA[pin], v_nom)] + _ESCENARIOS[pin]
        divisores[pin] = (valor(r_arriba), valor(r_abajo), riel, ref_red, r_arriba, r_abajo)
        tuplas.append((pin, _AIN_SENAL[pin], v_ref, casos, clamp))
    return tuplas, divisores


BOM = filas()
NETS = leer() if os.path.exists(NET) else None
SHUNTS_V5, _SHUNT_R = _shunts(NETS) if NETS else ([], {})
CANALES_ADS_V5, _DIVISOR = _canales(NETS) if NETS else ([], {})


def tap(v_riel: float, v_ref: float, clamp: bool, r_riel: float, r_ref: float) -> tuple[float, float]:
    """Tension en el pin del ADS1115 y corriente por el clamp (A)."""
    ideal = v_ref - (v_ref - v_riel) * r_ref / (r_riel + r_ref)
    if clamp and ideal < CLAMP_V:
        return CLAMP_V, abs((CLAMP_V - v_riel) / r_riel)
    return ideal, 0.0


def _dir_ads1115(nets: dict[str, set[str]], ref: str) -> int:
    gnd, vdd, sda, scl = (red_de(nets, f"{ref}.{p}") for p in (3, 8, 9, 10))
    nivel = {gnd: "GND", vdd: "VDD", sda: "SDA", scl: "SCL"}.get(red_de(nets, f"{ref}.1"))
    return ADS_DIR[nivel]


def _dir_tmp1075(nets: dict[str, set[str]], ref: str) -> int:
    sda, scl, gnd, vmas = (red_de(nets, f"{ref}.{p}") for p in (1, 2, 4, 8))
    nivel = {gnd: "0", vmas: "1", sda: "SDA", scl: "SCL"}
    return TMP_DIR[tuple(nivel.get(red_de(nets, f"{ref}.{p}")) for p in (5, 6, 7))]


def _bus(nets: dict[str, set[str]], ref: str, sda: int, scl: int) -> tuple[str | None, str | None]:
    return red_de(nets, f"{ref}.{sda}"), red_de(nets, f"{ref}.{scl}")


def _medidas() -> dict[str, dict[str, str]]:
    with open(MEDIDAS_CSV, encoding="utf-8", newline="") as fh:
        return {f["magnitud"]: f for f in csv.DictReader(fh)}


def _juzga(criterio: str, medido: float) -> bool | None:
    m = re.fullmatch(r"\s*(>=|<=)\s*([0-9.]+)\s*", criterio)
    if not m:
        return None
    lim = float(m.group(2))
    return medido >= lim if m.group(1) == ">=" else medido <= lim


def demo() -> int:
    print("check_telemetria v5: sensores INA226, ADS1115, TMP1075 e interfaces (T15-T17, T25-T26)\n")
    if NETS is None:
        print(f"HUECO: falta {os.path.basename(NET)} -- corre kicad/build_schematic.py")
        return 2
    nets = NETS
    violaciones: list[str] = list(_FALLOS)
    huecos: list[str] = list(_HUECOS)

    def linea(ok: bool, texto: str, sangria: int = 2) -> None:
        print(f"{' ' * sangria}[{'verde' if ok else 'ROJO '}] {texto}")
        if not ok:
            violaciones.append(texto)

    def hueco(texto: str, motivo: str) -> None:
        print(f"  [hueco] {texto}")
        huecos.append(f"{texto}: {motivo}")

    for f in _FALLOS:
        print(f"  [ROJO ] {f}")
    for h in _HUECOS:
        print(f"  [hueco] {h}")

    print("=== 1. Shunts de corriente contra el INA226 (T15, D-F2) ===")
    for ref, riel, r_ohm, i_max, v_cm, origen in SHUNTS_V5:
        v_sh = r_ohm * i_max
        ok = v_sh <= INA_SHUNT_FS_V and INA_CM_MIN_V <= v_cm <= INA_CM_MAX_V
        linea(ok, f"{ref:4s} {riel:<12s} {_SHUNT_R[ref]} {r_ohm*1000:5.0f} mohm @ {i_max*1000:4.0f} mA -> "
                  f"V_sh={v_sh*1000:5.2f} mV ({v_sh/INA_SHUNT_FS_V*100:4.1f}% de {INA_SHUNT_FS_V*1000:.2f} mV), "
                  f"{v_sh*i_max*1000:4.1f} mW, V_cm={v_cm:4.1f} V (rango {INA_CM_MIN_V:.0f}..{INA_CM_MAX_V:.0f} V)")
    if "U12" in _SHUNT_R:
        hueco(f"U12: corriente de +5V_AUX ({I_AUX_A*1000:.0f} mA)",
              "techo de diseno (ESTIMADO en ladrillo_budget.AUX_A), no una corriente medida ni limitada")

    vdd_ads = _tension_de(red_de(nets, f"{_refs('ADS1115')[0]}.8")) if _refs("ADS1115") else None
    print("\n=== 2. Divisores y clamps contra el ADS1115 (T15) ===")
    if vdd_ads is None:
        hueco("ADS1115", "no se sabe el VDD (nombre de la red de la patilla 8)")
    else:
        for canal, nombre, v_ref, escenarios, clamp in CANALES_ADS_V5:
            r_riel, r_ref, riel, ref_red, ra, rb = _DIVISOR[canal]
            print(f"  {canal} ({nombre}): {riel} -{ra} {r_riel/1e3:.0f}k- pin -{rb} {r_ref/1e3:.0f}k- "
                  f"{ref_red} ({v_ref:+.2f} V), clamp {'si' if clamp else 'NO'}")
            for etiqueta, v_in in escenarios:
                v_tap, _ = tap(v_in, v_ref, clamp, r_riel, r_ref)
                linea(-ADS_AIN_MARGEN_V <= v_tap <= vdd_ads + ADS_AIN_MARGEN_V,
                      f"{etiqueta:<34s} riel={v_in:+6.2f} V -> pin={v_tap:+5.2f} V", 4)

        print("\n=== 3. Perdida de alimentacion +5 V con riel negativo vivo ===")
        for canal, nombre, v_ref, escenarios, clamp in CANALES_ADS_V5:
            if canal not in _FALLO_VDD:
                continue
            r_riel, r_ref = _DIVISOR[canal][:2]
            v_in = _FALLO_VDD[canal]
            sin_d, _ = tap(v_in, 0.0, False, r_riel, r_ref)
            con_d, i_pin = tap(v_in, 0.0, clamp, r_riel, r_ref)
            ok = -ADS_AIN_MARGEN_V <= con_d <= vdd_ads + ADS_AIN_MARGEN_V and i_pin < ADS_IIN_MAX_A
            linea(ok, f"{canal} {nombre:<12s}: sin clamp={sin_d:+5.2f} V -> con BAT54={con_d:+5.2f} V, "
                      f"I_pin={i_pin*1e6:4.0f} uA (limite {ADS_IIN_MAX_A*1e3:.0f} mA)")
        hueco("clamps BAT54S", f"VF={VF_BAT54_V} V sin hoja en docs/reference/datasheets (D14..D17 son onsemi BAT54SLT1G)")

    print("\n=== 4. Mapa I2C en los buses de telemetria (7 bits, derivado de la netlist) ===")
    por_bus: dict[tuple, dict[int, str]] = {}
    chips: list[tuple[str, str, int, tuple]] = []        # (ref, chip, direccion, bus)
    for chip, refs, sda, scl in (("INA226", _refs("INA226"), 4, 5),
                                 ("ADS1115", _refs("ADS1115"), 9, 10),
                                 ("TMP1075", _refs("TMP1075"), 1, 2)):
        for ref in refs:
            try:
                if chip == "INA226":
                    a1, a0 = red_de(nets, f"{ref}.1"), red_de(nets, f"{ref}.2")
                    addr = direccion_ina226(a1, a0)
                    pines = f"A1={a1}, A0={a0}"
                elif chip == "ADS1115":
                    addr, pines = _dir_ads1115(nets, ref), f"ADDR={red_de(nets, f'{ref}.1')}"
                else:
                    addr = _dir_tmp1075(nets, ref)
                    pines = "A2/A1/A0=" + "/".join(str(red_de(nets, f"{ref}.{p}")) for p in (5, 6, 7))
            except KeyError as e:
                linea(False, f"{ref} ({chip}): las patillas de direccion estan en una red que la hoja "
                             f"no admite ({e})")
                continue
            bus = _bus(nets, ref, sda, scl)
            choca = por_bus.setdefault(bus, {}).get(addr)
            if choca:
                linea(False, f"0x{addr:02X} {ref} ({chip}) CHOCA con {choca} en el bus {bus[0]}/{bus[1]}")
            else:
                linea(True, f"0x{addr:02X} {ref:4s} {chip:8s} {pines}  bus {bus[0]}/{bus[1]}")
                por_bus[bus][addr] = f"{ref} ({chip})"
            chips.append((ref, chip, addr, bus))
    if not chips:
        linea(False, "no hay ningun INA226/ADS1115/TMP1075 en bom.csv")

    print("\n=== 5. Tensiones de alimentacion de chips contra AbsMax ===")
    alimentacion = [(ref, "INA226", 6, INA_VS_ABSMAX_V, "ina226.pdf p. 4") for ref in _refs("INA226")]
    alimentacion += [(ref, "ADS1115", 8, ADS_VDD_ABSMAX_V, "ads1115.pdf p. 4") for ref in _refs("ADS1115")]
    alimentacion += [(ref, "TMP1075", 8, TMP_VMAS_ABSMAX_V, "tmp1075.pdf p. 5") for ref in _refs("TMP1075")]
    for ref in _refs("ISO1541"):
        alimentacion += [(ref, "ISO1541 VCC1", 1, ISO_VCC_ABSMAX_V, "iso1541.pdf p. 6"),
                         (ref, "ISO1541 VCC2", 8, ISO_VCC_ABSMAX_V, "iso1541.pdf p. 6")]
    for ref, chip, pin, v_max, fuente in alimentacion:
        red = red_de(nets, f"{ref}.{pin}")
        v_op = _tension_de(red)
        if v_op is None:
            hueco(f"{ref} {chip}", f"la red {red} no dice su tension")
            continue
        linea(v_op < v_max, f"{ref:4s} {chip:<13s} {red} {v_op:.2f} V < {v_max:.2f} V absmax ({fuente})")

    print("\n=== 6. Aislamiento e interfaces de dominio (T16, T17, T25, T26) ===")

    def refs_en(red: str) -> set[str]:
        return {n.split(".")[0] for n in nets.get(red, ())}

    medidas = _medidas()

    def fisica(texto: str, magnitud: str) -> None:
        fila = medidas.get(magnitud)
        if fila is None:
            hueco(texto, f"no hay fila '{magnitud}' en medidas.csv")
        elif not fila["medido"].strip():
            hueco(texto, f"sin medir en la placa ({magnitud} {fila['criterio']} {fila['unidad']})")
        else:
            try:
                ok = _juzga(fila["criterio"], float(fila["medido"]))
            except ValueError:
                ok = None
            if ok is None:
                hueco(texto, f"medido '{fila['medido']}' o criterio '{fila['criterio']}' ilegibles")
            else:
                linea(ok, f"{texto}: medido {fila['medido']} {fila['unidad']} ({fila['criterio']})")

    # T16 (M1): la barrera es el URB y el ISO1541, nada mas.
    aislantes = {r for r, f in BOM.items() if f["value"].startswith(("URB2405", "ISO1541"))}
    puentes = (refs_en("GNDD") & (refs_en("GNDA") | refs_en("GND24"))) - aislantes
    linea(not puentes and bool(refs_en("GNDD") & aislantes),
          f"T16: GNDD solo comparte componente con GNDA/GND24 en {sorted(aislantes & refs_en('GNDD'))}"
          + (f"; ademas en {sorted(puentes)}" if puentes else ""))
    for ref in _refs("ISO1541"):
        for lado, (a, b) in (("SDA", (2, 7)), ("SCL", (3, 6))):
            red_a, red_b = red_de(nets, f"{ref}.{a}"), red_de(nets, f"{ref}.{b}")
            comunes = (refs_en(red_a) & refs_en(red_b)) if red_a and red_b else set()
            linea(comunes == {ref} and red_a != red_b,
                  f"T16: {lado} cruza de {red_a} a {red_b} solo por {ref} (comparten {sorted(comunes)})")
    fisica("T16: aislamiento GNDA-GNDD (barrera URB2405 + ISO1541)", "aislamiento_GNDA_a_GNDD")

    # T17 (M2): la estrella analogica es J5, un pin en GNDA.
    linea(red_de(nets, "J5.1") == "GNDA" and len(refs_en("GNDA") & {"J5"}) == 1,
          f"T17: J5 (puente unico GNDA-chasis) cuelga de {red_de(nets, 'J5.1')}")
    fisica("T17: continuidad estrella GNDA-chasis", "continuidad_estrella_GNDA_a_chasis")
    hueco("T17: fuga a PE de los ladrillos candidatos", "ni medidas.csv ni ningun presupuesto de la v5 "
          "la tiene (fuga_budget.py es de la v4, con la red dentro del chasis)")

    # T25: el reparto del retorno de la pantalla vive en el cableado.
    hueco("T25: retorno dedicado de la pantalla (550 mA)",
          "la netlist no tiene conector ni red de retorno de pantalla (J3 lleva un solo pin GNDA); "
          "lo demostraria la medida aislamiento_pantalla_retorno_dedicado, sin medir")

    # T26: +5 V de rack y +5 V digital, conectores distintos.
    con_rack = {r for r in refs_en("+5V_RACK") if r.startswith("J")}
    con_dig = {r for r in refs_en("+5V_DIG") if r.startswith("J")}
    linea(bool(con_rack) and bool(con_dig) and not (con_rack & con_dig),
          f"T26: +5V_RACK sale por {sorted(con_rack)} y +5V_DIG por {sorted(con_dig)}")

    if violaciones:
        print(f"\nROJO: {len(violaciones)} infracciones en check_telemetria v5:")
        for v in violaciones:
            print(f"  - {v}")
        return 1
    if huecos:
        print(f"\nSin infracciones, pero {len(huecos)} afirmaciones sin poder comprobar:")
        for h in huecos:
            print(f"  - {h}")
        print(f"\nHUECO: {len(huecos)} afirmaciones de telemetria sin verificar (ver arriba)")
        return 2
    print("\nOK: check_telemetria.py v5 (T15, T16, T17, T25, T26 verificados)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
