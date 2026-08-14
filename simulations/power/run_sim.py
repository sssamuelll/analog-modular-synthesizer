"""Simula el rectificador y el filtro del modulo 1 y mide el margen de dropout.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" run_sim.py

Que pregunta responde: con la red al -10% y el transformador cargado, la
tension MINIMA INSTANTANEA sobre C1, ¿se queda por encima de lo que el 7812
necesita para seguir regulando? Es la unica cuenta del modulo que no se puede
cerrar a mano, porque con filtro de entrada capacitiva la corriente por el
devanado no es senoidal: circula en picos estrechos de 2-3 veces la continua,
asi que la caida en la resistencia del secundario es bastante peor de lo que
sale de multiplicar corriente media por resistencia.

No usa un binario de ngspice porque KiCad no lo trae: solo ngspice.dll, que es
la que usa su simulador interno. Se maneja por ctypes. El fichero
sam17-power.cir de al lado es el mismo circuito en formato estandar, para poder
repetirlo en LTspice o en un ngspice de consola sin depender de esto.

Modelo del transformador: fuente ideal por semidevanado mas una resistencia
serie que representa la regulacion. Un transformador se especifica a PLENA
carga, asi que en vacio da mas tension; ese margen es justo lo que decide si el
diseno aguanta a 207 V, y como el BOM no lo fija, aqui se BARRE en vez de
suponerlo.
"""
from __future__ import annotations

import ctypes as C
import os
import sys

KICAD_BIN = os.environ.get("KICAD_BIN", r"C:\Program Files\KiCad\10.0\bin")

V_NOM = 230.0                   # red nominal europea
V_SEC = 12.0                    # por semidevanado, A PLENA CARGA (2 A)
I_SEC_NOM = 2.0
C_BULK = 4700e-6
I_POS = 0.450                   # 300 mA del 7812 + 150 mA del 7805 (sec.10.1)
I_NEG = 0.300                   # solo el 7912: los rieles NO van igual de cargados
DROPOUT = 2.0                   # 78xx/79xx, peor caso de datasheet
V_OUT = 12.0


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
        buf = [l.encode() for l in netlist.strip().splitlines()] + [None]
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


def main() -> int:
    ng = Ng()
    autocomprobacion(ng)
    minimo = V_OUT + DROPOUT

    print(f"\nMinimo que necesita el 7812 para seguir regulando: {minimo:.1f} V")
    print(f"Carga: +{I_POS*1000:.0f} mA en VRAW+ (7812 + 7805), "
          f"-{I_NEG*1000:.0f} mA en VRAW-\n")
    print(f"{'red':>6} {'reg':>5} | {'VRAW+ min':>10} {'rizado':>8} {'margen':>8} "
          f"| {'VRAW- min':>10} {'margen':>8} | {'Irms C1':>8} | ")
    print("-" * 88)

    fallos = []
    for reg in (0.08, 0.12, 0.20):
        for v_red in (253.0, 230.0, 207.0):
            m = mide(ng, v_red=v_red, reg=reg, i_pos=I_POS, i_neg=I_NEG)
            marg_p = m["vp_min"] - minimo
            marg_n = abs(m["vn_max"]) - minimo
            ok = "OK" if min(marg_p, marg_n) >= 0 else "NO REGULA"
            if min(marg_p, marg_n) < 0:
                fallos.append((v_red, reg, marg_p, marg_n))
            print(f"{v_red:6.0f} {reg*100:4.0f}% | {m['vp_min']:9.2f}V "
                  f"{m['vp_pp']:7.2f}V {marg_p:+7.2f}V | {abs(m['vn_max']):9.2f}V "
                  f"{marg_n:+7.2f}V | {m['ic1_rms']:7.2f}A | {ok}")
        print()

    print("Nota: 'reg' es la regulacion del transformador — cuanto sube su "
          "tension\nen vacio respecto al dato de placa, que es a plena carga. "
          "El BOM no la fija;\npor eso se barre.")
    if fallos:
        print(f"\nSALE DE REGULACION en {len(fallos)} de los 9 casos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
