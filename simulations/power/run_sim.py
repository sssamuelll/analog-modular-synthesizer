"""Simula el rectificador + filtro + pre-regulador de la fuente v3 y mide el
margen de dropout real de LM2941 (U1, VRAW+) y LM2991 (U2, VRAW-).

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" run_sim.py

Que pregunta responde: con la red al -10% y el transformador cargado, ¿el
valle instantaneo de VRAW se queda por encima de lo que el pre-regulador
necesita para seguir regulando su propia salida (13,1 V en U1, -12,9 V en U2
-- design-notes.md §16.8)? Es la unica cuenta del modulo que no se cierra a
mano, porque con filtro de entrada capacitiva la corriente por el devanado no
es senoidal: circula en picos estrechos de 2-3 veces la continua, asi que la
caida en la resistencia del secundario es bastante peor de lo que sale de
multiplicar corriente media por resistencia.

Hasta el issue #128 este fichero simulaba la v1 (7812, transformador de 2 A,
dropout de 2 V) -- diseño abandonado el 2026-08-17 -- y corria como puerta en
`main` contestando una pregunta que ya nadie hace. Modela ahora la v3:
transformador real (Nuvotem Talema 0120P1-2-012, 13,42 V en vacio / 12 V a
5 A -- design-notes.md §16.4) y el dropout GARANTIZADO (no tipico) de LM2941
y LM2991, leido de la hoja primaria el 2026-08-25:

    LM2941 (TI SNVS770I, rev. ene-2015, tabla 6.5/6.6 p.5-6):
        dropout MAX 1,0 V a IOUT = 1 A, sobre toda la temperatura
    LM2991 (TI SNVS099I, rev. oct-2016, tabla 6.5 p.5):
        dropout MAX 1,0 V a IOUT = 1 A, sobre toda la temperatura

Ninguna hoja garantiza el dropout justo a 650 mA (solo hay fila a 100 mA y a
1 A): se usa el de 1 A como cota conservadora, porque el dropout crece con la
corriente (curva tipica de la propia hoja) y 650 mA < 1 A. No es el numero
mas ajustado que existe -- es el mas ajustado que el datasheet GARANTIZA
(leccion §16.1: garantizado != tipico).

Ya no se barre la regulacion del transformador (`reg` en versiones previas de
este fichero): antes el BOM no la fijaba y por eso se barria; ahora la hoja
de Nuvotem la fija en un numero, no en un rango (design-notes.md §16.4,
corregido el 2026-08-19).

`U3` (7805) tambien cuelga de VRAW+ (sec.10.1 / design-notes.md §16.12), pero
su propio margen -- 5 V + ~2 V de dropout tipico de un 7805 -- nunca es el
limitante frente a los ~14-20 V de VRAW+: no se gatea aparte. Lo que si suma
es su CORRIENTE, que sale del mismo nodo VRAW+ que U1 y por eso hunde el
valle igual que ella.

No usa un binario de ngspice porque KiCad no lo trae: solo ngspice.dll, que es
la que usa su simulador interno. Se maneja por ctypes. El fichero
sam17-power.cir de al lado es el mismo circuito en formato estandar, para
poder repetirlo en LTspice o en un ngspice de consola sin depender de esto.
"""
from __future__ import annotations

import ctypes as C
import os
import sys

KICAD_BIN = os.environ.get("KICAD_BIN", r"C:\Program Files\KiCad\10.0\bin")

V_NOM = 230.0                    # red nominal europea
V_SEC = 12.0                     # por semidevanado, a PLENA carga (5 A) -- Nuvotem 0120P1-2-012
I_SEC_NOM = 5.0
REG = 1.42 / 12.0                # (13.42 - 12) / 12 -- hoja Nuvotem, design-notes.md §16.4
C_BULK = 9400e-6                 # 2x4700 uF/riel en paralelo -- design-notes.md §16.5

# Carga en VRAW+: LT3045 x2 (bus +-12 V) MAS U3/7805, que cuelga del mismo
# VRAW+ (sec.10.1 / design-notes.md §16.12). Carga en VRAW-: solo LT3094 x2 --
# no hay equivalente de U3 en el riel negativo.
I_12_CENSO = 0.174               # A/riel de censo real, con margen (#70)
I_5_CENSO = 0.030                # U3: modulo 2 + isla de telemetria (spec 2026-08-18 §3.1)
I_12_DISENO = 0.650              # A/riel, envolvente de diseno
I_5_DISENO = 0.300               # A, techo de U3 (design-notes.md §16.12)

# Pre-reguladores de la cascada v2/v3 (design-notes.md §16.8): el pre no
# entrega 12,000 V -- entrega el escalon que necesita el post-regulador
# (LT3045 x2 / LT3094 x2) para tener margen.
VOUT_U1 = 13.1                   # V, salida de LM2941 (VRAW+)
VOUT_U2 = 12.9                   # V, |salida| de LM2991 (VRAW-)
DROPOUT_U1 = 1.0                 # V, MAX a 1 A / temperatura completa -- TI SNVS770I p.5-6
DROPOUT_U2 = 1.0                 # V, MAX a 1 A / temperatura completa -- TI SNVS099I p.5
MIN_VIN_U1 = VOUT_U1 + DROPOUT_U1  # 14.1 V
MIN_VIN_U2 = VOUT_U2 + DROPOUT_U2  # 13.9 V


class VecInfo(C.Structure):
    _fields_ = [("v_name", C.c_char_p), ("v_type", C.c_int),
                ("v_flags", C.c_short), ("v_realdata", C.POINTER(C.c_double)),
                ("v_compdata", C.c_void_p), ("v_length", C.c_int)]


class Ng:
    def __init__(self) -> None:
        os.add_dll_directory(KICAD_BIN)
        self.lib = C.CDLL(os.path.join(KICAD_BIN, "ngspice.dll"))
        self.log: list[str] = []
        SC = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)
        SS = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)
        CE = C.CFUNCTYPE(C.c_int, C.c_int, C.c_bool, C.c_bool, C.c_int, C.c_void_p)
        self._cbs = (SC(self._recoge), SS(lambda *a: 0), CE(lambda *a: 0))
        self.lib.ngGet_Vec_Info.restype = C.POINTER(VecInfo)
        if self.lib.ngSpice_Init(*self._cbs, None, None, None, None) != 0:
            raise RuntimeError("ngSpice_Init fallo")

    def _recoge(self, s, _i, _u):
        self.log.append(s.decode(errors="replace"))
        return 0

    def corre(self, netlist: str) -> None:
        self.log.clear()
        self.lib.ngSpice_Command(b"remcirc")
        buf = [linea.encode() for linea in netlist.strip().splitlines()] + [None]
        arr = (C.c_char_p * len(buf))(*buf)
        if self.lib.ngSpice_Circ(arr) != 0:
            raise RuntimeError("netlist rechazado:\n" + "\n".join(self.log[-8:]))
        self.lib.ngSpice_Command(b"run")

    def vec(self, nombre: str) -> list[float]:
        vi = self.lib.ngGet_Vec_Info(nombre.encode())
        if not vi:
            raise RuntimeError(f"no existe el vector {nombre}\n"
                               + "\n".join(self.log[-8:]))
        v = vi.contents
        return [v.v_realdata[i] for i in range(v.v_length)]


def netlist(v_red: float, reg: float, i_pos: float, i_neg: float,
            c_bulk: float = C_BULK) -> str:
    """Secundario partido + puente + bulk + cargas de corriente constante.

    Las cargas son fuentes de corriente y no resistencias a proposito: un
    regulador lineal EN REGULACION consume corriente casi constante pase lo que
    pase con el rizado de su entrada. Modelarlo como resistencia daria un
    rizado optimista.
    """
    v_vacio = V_SEC * (1.0 + reg)                 # el dato de 12 V es a plena carga
    r_dev = reg * V_SEC / I_SEC_NOM               # caida repartida en el devanado
    v_pico = v_vacio * 2 ** 0.5 * (v_red / V_NOM)
    return f"""sam17 modulo 1 - rectificacion y filtrado
V1 a 0 SIN(0 {v_pico:.4f} 50)
V2 0 b SIN(0 {v_pico:.4f} 50)
Rw1 a a1 {r_dev:.4f}
Rw2 b b1 {r_dev:.4f}
D1 a1 vp DMOD
D2 b1 vp DMOD
D3 vn a1 DMOD
D4 vn b1 DMOD
Vmc vp cp 0
C1 cp 0 {c_bulk}
C2 0 vn {c_bulk}
I1 vp 0 {i_pos}
I2 0 vn {i_neg}
.model DMOD D(IS=1e-8 N=1.9 RS=0.025 BV=1000)
.ic v(vp)=15 v(vn)=-15
.tran 20u 400m 340m 20u
.end
"""


def mide(ng: Ng, **kw) -> dict:
    ng.corre(netlist(**kw))
    vp, vn = ng.vec("v(vp)"), ng.vec("v(vn)")
    ic1 = ng.vec("i(vmc)")
    n = len(vp)
    rms = (sum(i * i for i in ic1) / n) ** 0.5
    return {"vp_min": min(vp), "vp_max": max(vp), "vp_pp": max(vp) - min(vp),
            "vn_max": max(vn), "vn_pp": max(vn) - min(vn),
            "ic1_rms": rms}


def autocomprobacion(ng: Ng) -> None:
    """Valida el modelo contra dos casos de respuesta conocida.

    Un integrador propio te da numeros con toda la confianza del mundo aunque
    este mal; esto es SPICE, pero el netlist es mio y puede estarlo igual.
    """
    # 1) Sin carga la salida tiene que subir al pico menos un diodo.
    sin_carga = mide(ng, v_red=V_NOM, reg=0.0, i_pos=1e-6, i_neg=1e-6)
    pico_ideal = V_SEC * 2 ** 0.5
    err = pico_ideal - sin_carga["vp_max"]
    assert 0.3 < err < 1.2, f"caida de un diodo fuera de rango: {err:.2f} V"
    assert sin_carga["vp_pp"] < 0.02, f"en vacio no puede haber rizado: {sin_carga['vp_pp']:.3f}"

    # 2) El rizado tiene que escalar ~1/C: al doblar C, se parte por la mitad.
    a = mide(ng, v_red=V_NOM, reg=0.12, i_pos=0.45, i_neg=0.3, c_bulk=4700e-6)
    b = mide(ng, v_red=V_NOM, reg=0.12, i_pos=0.45, i_neg=0.3, c_bulk=9400e-6)
    ratio = a["vp_pp"] / b["vp_pp"]
    assert 1.7 < ratio < 2.3, f"el rizado no escala con 1/C: ratio {ratio:.2f}"

    # 3) Contra la aproximacion analitica I/(f*C), que debe quedar por encima.
    analitico = 0.45 / (100 * 4700e-6)
    assert a["vp_pp"] < analitico * 1.1, (
        f"rizado {a['vp_pp']:.3f} por encima de la cota analitica {analitico:.3f}")
    print(f"autocomprobacion OK  (diodo {err:.2f} V, escala 1/C {ratio:.2f}x, "
          f"rizado {a['vp_pp']:.3f} < cota {analitico:.3f} V)")


ESCENARIOS_CARGA = [
    ("censo real, con margen (#70)", I_12_CENSO, I_5_CENSO),
    ("envolvente de diseno", I_12_DISENO, I_5_DISENO),
]


def main() -> int:
    ng = Ng()
    autocomprobacion(ng)

    print(f"\nTransformador Nuvotem 0120P1-2-012: {V_SEC:.0f}-0-{V_SEC:.0f} V a "
          f"{I_SEC_NOM:.0f} A, regulacion {REG * 100:.2f}% "
          f"(13.42 V en vacio -- hoja del fabricante, design-notes.md §16.4)")
    print(f"Bulk: {C_BULK * 1e6:.0f} uF/riel (design-notes.md §16.5)")
    print(f"U1 LM2941 (VRAW+): sale a {VOUT_U1} V, dropout MAX {DROPOUT_U1:.1f} V a 1 A "
          f"(TI SNVS770I) -> VIN minimo {MIN_VIN_U1:.1f} V")
    print(f"U2 LM2991 (VRAW-): sale a -{VOUT_U2} V, dropout MAX {DROPOUT_U2:.1f} V a 1 A "
          f"(TI SNVS099I) -> VIN minimo {MIN_VIN_U2:.1f} V\n")

    print(f"{'carga':32} {'red':>5} | {'VRAW+ min':>10} {'margen U1':>10} | "
          f"{'VRAW- min':>10} {'margen U2':>10} | {'Irms C1':>8} |")
    print("-" * 100)

    fallos = []
    for nombre, i_12, i_5 in ESCENARIOS_CARGA:
        i_pos, i_neg = i_12 + i_5, i_12
        for v_red in (253.0, 230.0, 207.0):
            m = mide(ng, v_red=v_red, reg=REG, i_pos=i_pos, i_neg=i_neg, c_bulk=C_BULK)
            marg_pos = m["vp_min"] - MIN_VIN_U1
            marg_neg = abs(m["vn_max"]) - MIN_VIN_U2
            ok = min(marg_pos, marg_neg) >= 0
            if not ok:
                fallos.append((nombre, v_red, marg_pos, marg_neg))
            print(f"{nombre:32} {v_red:5.0f} | {m['vp_min']:9.2f}V {marg_pos:+9.2f}V | "
                  f"{abs(m['vn_max']):9.2f}V {marg_neg:+9.2f}V | {m['ic1_rms']:7.2f}A | "
                  f"{'OK' if ok else 'NO REGULA'}")
        print()

    if not fallos:
        print("OK: los dos pre-reguladores regulan en todos los escenarios, contra el "
              "dropout GARANTIZADO (no tipico) de su propia hoja.")
        return 0

    print(f"NO REGULA en {len(fallos)} caso(s):")
    for nombre, v_red, mp, mn in fallos:
        print(f"  {nombre}, red {v_red:.0f} V: margen U1 {mp:+.2f} V, margen U2 {mn:+.2f} V")
    print("\nEsto usa el dropout MAXIMO garantizado a 1 A (TI), no el tipico a 650 mA: "
          "es una cota conservadora, no una medida real. Issue #128.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
