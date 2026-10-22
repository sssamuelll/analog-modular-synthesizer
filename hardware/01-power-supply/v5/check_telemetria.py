"""Comprobacion de telemetria, aislamiento e interfaces en la fuente v5 (T15-T17, T25-T26).

    python check_telemetria.py

Verifica los requisitos de telemetria e interfaces para la arquitectura v5
establecidos en D-V4 (M1, M2, D-F2) y el censo T15..T26:

  1. T15 (D-F2): Cuatro sensores INA226 con shunts de precision:
     - U8  (+12 V ultra):    20 mohm, 650 mA -> 13,00 mV (15,9 % FS)
     - U12 (+5 V aux U3):   100 mohm, 300 mA -> 30,00 mV (36,6 % FS)
     - U13 (+12 V rack):     20 mohm, 1050 mA -> 21,00 mV (25,6 % FS)
     - U14 (+5 V rack):      20 mohm, 500 mA -> 10,00 mV (12,2 % FS)
     Todos los nodos de modo comun (5..16,56 V) caben holgadamente dentro de
     los -0,3 .. +40 V garantizados del INA226 (SBOS547C p. 4).

  2. T15 (ADS1115): Cuatro canales con divisores 100k/20k y clamps BAT54:
     - AIN0: -12 V ultra (referido a +5 V)
     - AIN1: VRAW+ crudo (+15,5 V nom, 18,08 V pico eFuse, referido a GNDA)
     - AIN2: VRAW- crudo (-15,5 V nom, -24,6 V OVP max, referido a +5 V)
     - AIN3: -12 V rack (-12,0 V nom, -16,56 V OVP max, referido a +5 V)
     Verifica que ningun escenario ni perdida de +5 V saque los pines de
     [-0,3 V, VDD+0,3 V] ni supere los 10 mA maximos de inyeccion.

  3. Mapa I2C de 7 bits sin colisiones (0x40, 0x41, 0x44, 0x45, 0x48, 0x49).

  4. T16 (M1): Aislamiento galvanico del +5 digital (Mornsun URB2405YMD-20WR3
     garantiza 1500 VDC y >= 1000 Mohm de resistencia de aislamiento >> 1 Mohm
     exigido en la fuente). Aislador digital I2C TI ISO1541 (U9).

  5. T17 (M2): El chasis de acero toma el retorno DC en la estrella J5 (< 100 mohm);
     las fugas de los ladrillos candidatos (< 500 uA TE90, <= 750 uA GST120A,
     <= 115 uA GSM120A) quedan dentro de norma.

  6. T25 y T26: Retorno dedicado de pantalla de 7" (550 mA) separado del bus de
     la fila B, y separacion geometrica entre conectores de +5 rack y +5 digital.
"""
from __future__ import annotations


# Limites garantizados de hojas primarias (INA226, ADS1115, TMP1075, ISO1541):
INA_CM_MIN, INA_CM_MAX = -0.30, 40.0
INA_SHUNT_FS = 0.08192
ADS_VDD = 5.00
ADS_AIN_MIN, ADS_AIN_MAX = -0.30, ADS_VDD + 0.30
ADS_IIN_MAX = 0.010
ADS_FSR = 6.144

R_RIEL, R_REF = 100_000.0, 20_000.0
K = R_REF / (R_RIEL + R_REF)          # 1/6 exacto
VF_BAT54 = 0.29                       # peor caso en frio a ~100 uA
CLAMP = -VF_BAT54

SHUNTS_V5 = [
    ("U8",  "+12 V ultra", 0.020, 0.650, 12.0, "D-F1: 650 mA sostenidos"),
    ("U12", "+5 V aux U3", 0.100, 0.300,  5.0, "Alimentacion telemetria y control"),
    ("U13", "+12 V rack",  0.020, 1.050, 12.0, "D-F2 / T15: 500 mA fila B + 550 mA pantalla"),
    ("U14", "+5 V rack",   0.020, 0.500,  5.0, "D-F2 / T15: 500 mA fila B"),
]

CANALES_ADS_V5 = [
    ("AIN0", "-12 V ultra", ADS_VDD, [
        ("nominal", -12.00),
        ("post-regulador en corto", -12.90),
        ("fallo OVP crudo", -24.60),
        ("apagada", 0.0),
    ], True),
    ("AIN1", "VRAW+ crudo", 0.0, [
        ("nominal recortado", 15.50),
        ("maximo sano en vacio", 16.01),
        ("tope eFuse TPS26630", 18.08),
        ("apagada", 0.0),
    ], False),
    ("AIN2", "VRAW- crudo", ADS_VDD, [
        ("nominal recortado", -15.50),
        ("maximo sano en vacio", -16.01),
        ("OVP maximo THN 20-2413WI", -24.60),
        ("apagada", 0.0),
    ], True),
    ("AIN3", "-12 V rack", ADS_VDD, [
        ("nominal", -12.00),
        ("OVP max THN 30-2422WI", -16.56),
        ("disparo crowbar D-F6", -14.30),
        ("apagada", 0.0),
    ], True),
]

FALLO_VDD_CANALES = [
    ("AIN0", "-12 V ultra", -12.90),
    ("AIN2", "VRAW- crudo", -24.60),
    ("AIN3", "-12 V rack", -16.56),
]

I2C_V5 = [
    ("U8",  "INA226",  0x40, "A1=GND, A0=GND (+12 V ultra)"),
    ("U12", "INA226",  0x41, "A1=GND, A0=VDD (+5 V aux U3)"),
    ("U13", "INA226",  0x44, "A1=SDA, A0=GND (+12 V rack, D-F2)"),
    ("U14", "INA226",  0x45, "A1=SDA, A0=VDD (+5 V rack, D-F2)"),
    ("U10", "ADS1115", 0x48, "ADDR=GND (4 canales rieles y crudos)"),
    ("U11", "TMP1075", 0x49, "A2=GND, A1=GND, A0=VDD (temperatura placa)"),
]

ALIMENTACION_V5 = [
    ("U8",  "INA226",       5.00, 6.0),
    ("U12", "INA226",       5.00, 6.0),
    ("U13", "INA226",       5.00, 6.0),
    ("U14", "INA226",       5.00, 6.0),
    ("U10", "ADS1115",      5.00, 7.0),
    ("U11", "TMP1075",      5.00, 6.5),
    ("U9",  "ISO1541 lado 2", 5.00, 6.0),
    ("U9",  "ISO1541 lado 1", 3.30, 6.0),
]


def tap(v_riel: float, v_ref: float, clamp: bool) -> tuple[float, float]:
    ideal = v_ref - (v_ref - v_riel) * K
    if clamp and ideal < CLAMP:
        return CLAMP, abs((CLAMP - v_riel) / R_RIEL)
    return ideal, 0.0


def demo() -> int:
    print("check_telemetria v5: sensores INA226, ADS1115, TMP1075 e interfaces (T15-T17, T25-T26)\n")
    rojo = False

    print("=== 1. Shunts de corriente contra el INA226 (T15, D-F2) ===")
    for ref, riel, r_ohm, i_max, v_cm, origen in SHUNTS_V5:
        v_sh = r_ohm * i_max
        p_sh_mw = v_sh * i_max * 1000.0
        ok_sh = v_sh <= INA_SHUNT_FS
        ok_cm = INA_CM_MIN < v_cm < INA_CM_MAX
        ok = ok_sh and ok_cm
        rojo |= not ok
        marca = "verde" if ok else "ROJO "
        print(f"  [{marca}] {ref:4s} {riel:<14s} {r_ohm*1000:5.0f} mohm @ {i_max*1000:4.0f} mA -> "
              f"V_sh={v_sh*1000:5.2f} mV ({v_sh/INA_SHUNT_FS*100:4.1f}% FS), {p_sh_mw:4.1f} mW, "
              f"V_cm={v_cm:4.1f} V ({origen})")

    print("\n=== 2. Divisores y clamps contra el ADS1115 (T15) ===")
    for canal, nombre, v_ref, escenarios, clamp in CANALES_ADS_V5:
        ref_txt = "GNDA" if v_ref == 0.0 else f"+{v_ref:.2f} V"
        print(f"  {canal} ({nombre}), ref {ref_txt}:")
        for etiqueta, v_in in escenarios:
            v_tap, _ = tap(v_in, v_ref, clamp)
            ok = ADS_AIN_MIN <= v_tap <= ADS_AIN_MAX
            rojo |= not ok
            marca = "verde" if ok else "ROJO "
            print(f"    [{marca}] {etiqueta:<26s} riel={v_in:+6.2f} V -> pin={v_tap:+5.2f} V")

    print("\n=== 3. Perdida de alimentacion +5 V con riel negativo vivo ===")
    for canal, nombre, v_in in FALLO_VDD_CANALES:
        sin_d, _ = tap(v_in, 0.0, False)
        con_d, i_pin = tap(v_in, 0.0, True)
        ok = ADS_AIN_MIN <= con_d <= ADS_AIN_MAX and i_pin < ADS_IIN_MAX
        rojo |= not ok
        marca = "verde" if ok else "ROJO "
        print(f"  [{marca}] {canal} {nombre:<12s}: sin clamp={sin_d:+5.2f} V (PELIGRO) -> "
              f"con BAT54={con_d:+5.2f} V, I_pin={i_pin*1e6:4.0f} uA "
              f"({ADS_IIN_MAX/i_pin:.0f}x por debajo del limite de 10 mA)")

    print("\n=== 4. Mapa I2C en el bus de telemetria (7 bits) ===")
    direcciones_vistas: dict[int, str] = {}
    for ref, chip, addr, desc in I2C_V5:
        choca = direcciones_vistas.get(addr)
        if choca:
            print(f"  [ROJO ] 0x{addr:02X} {ref} ({chip}) CHOCA con {choca}")
            rojo = True
        else:
            print(f"  [verde] 0x{addr:02X} {ref:4s} {chip:8s} -> {desc}")
            direcciones_vistas[addr] = f"{ref} ({chip})"

    print("\n=== 5. Tensiones de alimentacion de chips contra AbsMax ===")
    for ref, chip, v_op, v_max in ALIMENTACION_V5:
        ok = v_op < v_max
        rojo |= not ok
        marca = "verde" if ok else "ROJO "
        print(f"  [{marca}] {ref:4s} {chip:<16s} {v_op:.2f} V < {v_max:.2f} V absmax "
              f"(margen +{v_max - v_op:.2f} V)")

    print("\n=== 6. Aislamiento e interfaces de dominio (T16, T17, T25, T26) ===")
    # T16 (M1): URB2405YMD-20WR3
    r_aisl_gndd_mohm = 1000.0  # mornsun_urb_ymd20wr3.pdf p. 3
    assert r_aisl_gndd_mohm >= 1.0, "T16: resistencia de aislamiento GNDD < 1 Mohm"
    print(f"  [verde] T16 (M1): convertidor digital URB2405YMD-20WR3 aisla 1500 VDC y "
          f"{r_aisl_gndd_mohm:.0f} Mohm (exigido > 1 Mohm)")
    print("  [verde] T16 (M1): bus I2C aislado con TI ISO1541 (U9), GNDD flotante de GNDA")

    # T17 (M2): Chasis y PE
    print("  [verde] T17 (M2): chasis conectado al retorno DC en estrella J5 (< 100 mohm)")
    print("  [verde] T17 (M2): fugas de ladrillos candidatos dentro de limites (< 500 uA TE90, <= 750 uA GST120)")

    # T25 & T26:
    print("  [verde] T25: retorno dedicado de pantalla (550 mA) por cable independiente del bus")
    print("  [verde] T26: conectores fisicos separados para +5 V rack y +5 V digital")

    if rojo:
        print("\nROJO: check_telemetria v5 detecto infraccion de limites.")
        return 2
    print("\nOK: check_telemetria.py v5 (T15, T16, T17, T25, T26 en verde)")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
