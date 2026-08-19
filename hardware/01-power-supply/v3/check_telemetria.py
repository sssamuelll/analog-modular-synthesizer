"""Puerta: el instrumento no se destruye midiendo, y no hay dos chips en la misma direccion.

    python hardware/01-power-supply/v3/check_telemetria.py

Por que existe. La isla de telemetria mide rieles que van de +20,54 V a -20,54 V
con chips cuyo maximo absoluto es de 6 o 7 V. Lo unico que hay entre esos dos
mundos son seis resistencias, y si una pareja se pone al reves el divisor deja de
atenuar. Esta puerta hace la aritmetica y la compara contra los limites
GARANTIZADOS de cada datasheet primario, no contra los tipicos.

Es la hermana de `check_absmax.py`: aquella pregunta si los modulos sobreviven a
un fallo de la fuente, esta pregunta si el medidor sobrevive a medir.

Bloques:

  1. Los tres divisores del ADS1115, canal por canal, contra su ventana de
     entrada.
  2. El fallo que de verdad importa: +5 V muerto y el riel negativo vivo, que es
     cuando el instrumento tiene que seguir diciendo la verdad.
  3. Los dos shunts contra el modo comun y el fondo de escala del INA226.
  4. El mapa I2C dentro del canal del mux que toma la fuente.
  5. Las alimentaciones de los cinco chips contra su abs max.

Sale en ROJO (exit 2) si algo se sale de un limite garantizado.

--- Los limites, con cita. Nada de aqui es un valor tipico. -------------------

ADS1115  TI SBAS444E rev. DEC-2024
  p.4 tabla 5.1  : AIN0-3 de GND-0,3 V a VDD+0,3 V; corriente continua por
                   cualquier pin +-10 mA.
  p.29 sec. 9.1.3: "can be permanently damaged by analog input voltages that
                   exceed approximately 300mV beyond the rails"; "The ADS111x
                   analog inputs can withstand continuous currents as large as
                   10mA" -- de ahi que la resistencia del riel valga de
                   limitadora, que es la proteccion que TI nombra.
  p.13 sec. 7.3.1: "Overdriving an input on the ADS1115 can affect conversions
                   taking place on other inputs." Ese es el argumento que mete
                   los BAT54: no es supervivencia, es que las OTRAS medidas se
                   corrompen justo durante el fallo que hay que diagnosticar.
  p.15 tabla 7-2 : FSR +-6,144 V -> 187,5 uV por LSB, y con VDD > 4 V ese rango
                   admite entradas hasta la propia alimentacion.

INA226   TI SBOS547C rev. AUG-2026
  p.4 tabla 5.1  : IN+/IN- modo comun de -0,3 a 40 V; VBUS de -0,3 a 40 V; VS
                   6 V; corriente por cualquier pin 5 mA. El -0,3 V de modo
                   comun es la razon citable de por que el riel de -12 V NO
                   puede llevar un INA226 sin un segundo dominio aislado entero.
  fondo de escala del shunt +-81,92 mV, 2,5 uV por LSB.

TMP1075  TI SBOS854F rev. JUN-2024
  p.4  : V+ de 1,7 a 5,5 V. La variante N seria 1,62 a 3,6 V: NO sirve a 5 V.
  p.5 tabla 6.1 : V+ abs max 6,5 V.
  p.14 tabla 7-2: A2=A1=A0=0 -> 1001000b = 0x48, los mismos straps que el
                   modulo 3, asi que el driver ya escrito vale tal cual.

ISO1541  TI SLLSEB6F rev. DEC-2022
  p.6 tabla 6.1 : VCC1/VCC2 de -0,5 a 6 V; SDA/SCL hasta VCCx+0,5 sin pasar de
                   6 V; corriente de salida lado 1 <= 20 mA, lado 2 <= 100 mA.
  p.1  : 3,0 a 5,5 V por lado, independientes. Lado 1 a 3,3 V (dominio del
                   RP2350) y lado 2 a 5,0 V (dominio analogico) es su caso de
                   uso publicado, no un apano.
"""
from __future__ import annotations

import sys

ADS_VDD = 5.00
ADS_AIN_MIN, ADS_AIN_MAX = -0.30, ADS_VDD + 0.30
ADS_IIN_MAX = 10e-3
ADS_FSR = 6.144
INA_CM_MIN, INA_CM_MAX = -0.30, 40.0
INA_SHUNT_FS = 81.92e-3

# --- El divisor: dos valores, tres canales ----------------------------------
# Invariante de montaje: el 100 k mira SIEMPRE al riel medido y el 20 k mira
# SIEMPRE a la referencia (GNDA en el canal positivo, +5 V en los negativos).
# Cambiarlos de sitio es el error de ensamblaje que esta puerta no puede ver,
# asi que va escrito en el bom.csv y tiene que ir en la seda de la placa.
R_RIEL, R_REF = 100_000.0, 20_000.0
K = R_REF / (R_RIEL + R_REF)          # 1/6 exacto con estos dos valores
VF_BAT54 = 0.29                       # peor caso en frio (~0 C) a ~100 uA
CLAMP = -VF_BAT54


def tap(v_riel: float, v_ref: float, clamp: bool) -> tuple[float, float]:
    """Tension del punto medio del divisor y corriente que entra al pin."""
    ideal = v_ref - (v_ref - v_riel) * K
    if clamp and ideal < CLAMP:
        # El diodo sujeta el nodo; la corriente la limita la resistencia del
        # riel, que es la "current-limiting resistor" de la seccion 9.1.3.
        return CLAMP, abs((CLAMP - v_riel) / R_RIEL)
    return ideal, 0.0


# (canal, nombre, referencia, [(escenario, tension del riel)], lleva clamp)
CANALES = [
    ("AIN1", "VRAW+", 0.0, [
        ("en vacio, red +10 %", 20.54),
        ("al punto de diseno de 650 mA", 15.70),
        ("limite fisico del bulk de 25 V", 25.00),
        ("apagada", 0.0),
    ], False),
    ("AIN0", "-12 V", ADS_VDD, [
        ("nominal", -12.00),
        ("post-regulador en corto", -12.90),
        ("las dos etapas en corto", -20.54),
        ("apagada", 0.0),
    ], True),
    ("AIN2", "VRAW-", ADS_VDD, [
        ("en vacio, red +10 %", -20.54),
        ("al punto de diseno", -15.70),
        ("limite fisico del bulk de 25 V", -25.00),
        ("apagada", 0.0),
    ], True),
]

# El fallo que justifica los clamps: U3 abierto deja la isla sin VDD mientras
# el riel negativo sigue vivo. Sin diodo el pin se va a -2,15 V.
FALLO_U3 = [("AIN0", "-12 V", -12.90), ("AIN2", "VRAW-", -20.54)]

# (ref, riel, shunt en ohm, corriente maxima esperada, de donde sale el tope)
SHUNTS = [
    ("R19", "+12 V", 0.020, 0.650, "techo del censo de corriente (spec v2)"),
    ("R20", "+5 V de U3", 0.100, 0.300, "techo de diseno de design-notes 16.12"),
]

# (ref, chip, direccion, como se fija)
I2C = [
    ("U8", "INA226", 0x40, "A1 y A0 a GND"),
    ("U9", "INA226", 0x41, "A0 a VDD"),
    ("U10", "ADS1115", 0x49, "ADDR a VDD"),
    ("U11", "TMP1075", 0x48, "A2/A1/A0 a GND -- identicos al modulo 3"),
]
# Fuera de la isla, pero en el mismo canal si algun dia se fusionan ramas:
RESERVADAS = {0x50: "EEPROM de identidad (todas las placas)"}

# (ref, chip, riel, abs max del riel)
ALIMENTACION = [
    ("U8", "INA226", 5.00, 6.0),
    ("U9", "INA226", 5.00, 6.0),
    ("U10", "ADS1115", 5.00, 7.0),
    ("U11", "TMP1075", 5.00, 6.5),
    ("U12", "ISO1541 lado 2", 5.00, 6.0),
    ("U12", "ISO1541 lado 1", 3.30, 6.0),
]


def main() -> int:
    rojo = False
    lsb_riel = ADS_FSR / 32768 / K * 1e3
    print(f"Divisor: {R_RIEL/1000:.0f}k al riel / {R_REF/1000:.0f}k a la "
          f"referencia -> atenuacion 1/{1/K:.0f}. FSR +-{ADS_FSR} V, "
          f"{ADS_FSR/32768*1e6:.1f} uV/LSB = {lsb_riel:.2f} mV por LSB "
          f"medidos en el riel.\n")

    print("=== 1. Los divisores contra la ventana del ADS1115 ===\n")
    for canal, nombre, v_ref, escenarios, clamp in CANALES:
        ref_txt = "GNDA" if v_ref == 0 else f"+{v_ref:.2f} V"
        extra = "   con clamp BAT54" if clamp else ""
        print(f"  {canal}  {nombre:6s} referencia {ref_txt}{extra}")
        for etiqueta, v in escenarios:
            v_tap, _ = tap(v, v_ref, clamp)
            ok = ADS_AIN_MIN < v_tap < ADS_AIN_MAX
            fs = "" if abs(v_tap) <= ADS_FSR else "   OJO: fuera del fondo"
            marca = "verde" if ok else "ROJO "
            print(f"     [{marca}] {etiqueta:32s} riel {v:+7.2f} V "
                  f"-> pin {v_tap:+6.3f} V{fs}")
            rojo |= not ok
        print()

    print("=== 2. El fallo que mete los diodos: U3 abierto, riel vivo ===\n")
    for canal, nombre, v in FALLO_U3:
        sin_d, _ = tap(v, 0.0, False)
        con_d, i = tap(v, 0.0, True)
        ok = ADS_AIN_MIN < con_d < ADS_AIN_MAX and i < ADS_IIN_MAX
        marca = "verde" if ok else "ROJO "
        print(f"  [{marca}] {canal} {nombre:6s} sin diodo {sin_d:+6.2f} V "
              f"(fuera)  ->  con BAT54 {con_d:+.2f} V, {i*1e6:.0f} uA "
              f"por el pin, {ADS_IIN_MAX/i:.0f}x bajo el limite "
              f"de {ADS_IIN_MAX*1e3:.0f} mA")
        rojo |= not ok
    print()

    print("=== 3. Los shunts contra el INA226 ===\n")
    for ref, riel, ohm, imax, origen in SHUNTS:
        vsh = ohm * imax
        cm = 12.0 if "+12" in riel else 5.0
        ok = vsh <= INA_SHUNT_FS and INA_CM_MIN < cm < INA_CM_MAX
        marca = "verde" if ok else "ROJO "
        print(f"  [{marca}] {ref} {riel:12s} {ohm*1000:5.0f} mOhm a "
              f"{imax*1000:.0f} mA -> {vsh*1e3:5.2f} mV "
              f"({vsh/INA_SHUNT_FS*100:4.1f} % del fondo), "
              f"{2.5e-6/ohm*1e6:.0f} uA/LSB, {vsh*imax*1e3:.0f} mW, "
              f"modo comun {cm:.0f} V")
        print(f"            el tope de {imax*1000:.0f} mA sale de: {origen}")
        rojo |= not ok
    print()

    print("=== 4. Las direcciones, dentro del canal del mux de la fuente ===\n")
    vistas: dict[int, str] = {}
    for ref, chip, addr, como in I2C:
        choca = vistas.get(addr) or RESERVADAS.get(addr)
        marca = "ROJO " if choca else "verde"
        print(f"  [{marca}] 0x{addr:02X}  {ref:4s} {chip:8s} {como}")
        if choca:
            print(f"            CHOCA con {choca}")
            rojo = True
        vistas[addr] = f"{ref} ({chip})"
    print()

    print("=== 5. Las alimentaciones contra su abs max ===\n")
    for ref, chip, v, lim in ALIMENTACION:
        ok = v < lim
        marca = "verde" if ok else "ROJO "
        print(f"  [{marca}] {ref:4s} {chip:16s} {v:.2f} V  vs  {lim:.1f} V"
              f"   margen {lim-v:+.2f} V")
        rojo |= not ok

    print("""
  NOTA, y no es menor: los cinco cuelgan del +5 V de U3, un 7805. Un 7805 en
  corto pone los 20,54 V de VRAW+ en ese nodo y se lleva la isla entera Y el
  modulo 2 por J6. No es un riesgo que traiga la telemetria -- ya existia para
  el modulo 2 -- pero ahora tiene mas detras. Queda como cuestion abierta del
  spec y no como fila del BOM: un clamp sin nada que abra el circuito es el
  error del crowbar otra vez (issue #118).
""")

    if rojo:
        print("ROJO: algo se sale de un limite garantizado.")
        return 2
    print("verde: los tres divisores, los dos shunts, las cuatro direcciones y")
    print("       las seis alimentaciones caben dentro de los limites")
    print("       garantizados de sus datasheets primarios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
