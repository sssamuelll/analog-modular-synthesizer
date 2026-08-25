"""Estabilidad de la transimpedancia MIX OUT -> VOICE_OUT del modulo 3.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" iv_stage.py

QUE PREGUNTA RESPONDE, y por que esta es simulable y el chip no
-------------------------------------------------------------------------
El README de al lado explica por que el SSI2130 no se simula: no hay modelo
publico y escribirlo desde el datasheet seria validar el diseno contra el
invento. Esta etapa es OTRA COSA. Lo unico que hace falta del SSI2130 es lo
que su datasheet DECLARA de su pin 25: que MIX OUT es una salida de
CORRIENTE. Una fuente de corriente no es un invento del chip, es la interfaz
que el fabricante publica. Todo lo demas de este lazo -- R_IV, el TL074H, el
cable de patcheo -- tiene numeros publicados.

El circuito, tal cual sale de build_schematic.py (`dibujar_voz`):

     MIX OUT (pin 25)                R_IV = 10k
     ----o------ MIXO_n ----+---/\/\/\---+---- VOICE_OUT_n --> punta J_OUT
       (corriente)          |            |
                            |  |\        |
                            +--|-\       |
                               |  >------+------------------> cable de patcheo
                        GNDA --|+/
                               |/  U9 unidad n (TL074H)

Dos cosas de ese dibujo son las que se preguntan aqui, y **ninguna de las dos
la ve ningun gate del repo**: no hay condensador de realimentacion sobre
R_IV, y no hay resistencia serie entre la salida del opamp y la punta del
jack.

  1. TRANSIMPEDANCIA SIN COMPENSAR. La capacidad del nodo MIXO_n (salida del
     SSI2130 + pista + entrada del opamp) con R_IV forma un cero en la
     ganancia de ruido. Por encima de el la ganancia de ruido sube 20 dB por
     decada y corta la caida del lazo abierto con pendiente doble: el margen
     de fase se hunde. Es el fallo clasico del amplificador de
     transimpedancia y se arregla con UN condensador.

  2. CABLE DE PATCHEO COLGANDO DE LA SALIDA. El datasheet caracteriza el
     TL074H con **CL = 20 pF**. Un cable apantallado de instrumento son del
     orden de 100 pF por metro. La salida va del pin del opamp a la punta del
     jack sin nada en medio.

FUENTES PRIMARIAS (TL074H, datasheet TI SLOSE01, tablas 6.5-6.7)
-------------------------------------------------------------------------
  GBW ................ 5.25 MHz
  AOL ................ 125 dB tipico (118 dB minimo)
  Slew rate .......... 20 V/us  (VS = 40 V, G = +1, CL = 20 pF)
  Margen de fase ..... 56 grados (G = +1, RL = 10k, CL = 20 pF)
  Zo lazo abierto .... 125 ohm  (f = 1 MHz, IO = 0 A)
  Headroom de salida . 115 mV tip / 210 mV max contra el riel (RL = 10k)

LO QUE **NO** ESTA EN EL DATASHEET, y por eso se BARRE en vez de suponerse
-------------------------------------------------------------------------
La **capacidad de entrada** del TL074H no aparece en ninguna tabla (buscado:
"capacitance" sale una sola vez, y es un consejo de layout). Tampoco esta
publicada la capacidad de salida del pin 25 del SSI2130. Asi que la capacidad
total del nodo MIXO_n es desconocida y aqui se barre de 5 a 100 pF: lo que el
datasheet no fija se barre, no se supone. (`simulations/power/run_sim.py`
barria asi la regulacion del transformador hasta el issue #128, porque el BOM
tampoco la fijaba entonces -- ahora la fija la hoja de Nuvotem y ya no hace
falta barrerla.)

LO QUE ESTE CALCULO **NO** CUBRE
-------------------------------------------------------------------------
  * El SSI2130. Su mezclador entra aqui como fuente de corriente ideal.
    La impedancia REAL de ese pin (que amortigua o empeora el lazo) no esta
    publicada y no se modela.
  * Ruido y THD. El macromodelo es de dos polos: sirve para estabilidad,
    no para el suelo de ruido.
  * Diafonia entre las cuatro unidades del mismo encapsulado.
  * El layout. Este modelo tiene la capacidad como un parametro, no como una
    geometria.
  * El macromodelo NO es el modelo de TI. Es de dos polos, construido con
    los numeros publicados de arriba y CALIBRADO contra el margen de fase que
    el propio datasheet especifica. Un modelo del fabricante seria mejor;
    esa es la mejora, no un rehacer.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "power"))
from run_sim import Ng  # noqa: E402  (el envoltorio de ngspice.dll ya existe)

# --- constantes del TL074H, todas del datasheet -----------------------------
GBW = 5.25e6            # Hz
AOL_DB = 125.0          # dB tipico
SLEW = 20e6             # V/s
PM_HOJA = 56.0          # grados, en G=+1, RL=10k, CL=20pF
RO = 125.0              # ohm, Zo lazo abierto a 1 MHz
RL_HOJA, CL_HOJA = 10e3, 20e-12   # la carga con la que se midio ese PM

# --- el circuito real, de build_schematic.py y bom.csv ----------------------
R_IV = 10e3             # bom.csv: "R_IV1-4, 10k 1%"
I_MIX_MAX = 500e-6      # bom.csv: "Transimpedancia MIX OUT (500uA -> 5V)"
# Estos dos valores NACIERON aqui: este barrido encontro que sin ellos la
# transimpedancia timbra siempre y oscila con cualquier cable, y de aqui
# pasaron al esquematico y al BOM (C_IV1-4 y R_OUT1-4). Ahora el script
# cambia de papel: dejo de ser el que encuentra el fallo y paso a ser el que
# vigila que no vuelva. Si alguien quita el condensador, esta puerta se pone
# roja.
C_FB = 33e-12           # bom.csv: "C_IV1-4, 33p C0G"
R_SERIE = 220.0         # bom.csv: "R_OUT1-4, 220R 1%"

# --- lo desconocido, que se barre -------------------------------------------
C_NODO = [5e-12, 10e-12, 20e-12, 50e-12, 100e-12]     # nodo MIXO_n
C_CABLE = [0.0, 100e-12, 300e-12, 660e-12]            # 0 m, 1 m, 3 m, 6 m

# --- criterio de aceptacion (ELEGIDO, no del datasheet) ---------------------
# El datasheet caracteriza la pieza a 56 grados de margen de fase. 45 grados
# es el minimo clasico por debajo del cual el escalon timbra de forma visible
# (sobreimpulso ~23%). Se toma 45 como suelo y se dice que es una eleccion.
PM_MINIMO = 45.0
SOBREIMPULSO_MAX = 25.0   # %, el que corresponde a ~45 grados

PI = 3.141592653589793
AOL = 10 ** (AOL_DB / 20.0)
C1 = 1e-9                      # arbitrario: fija la escala de GM y R1


def opamp(fp2: float, gbw1: float) -> str:
    """Macromodelo de dos polos + Zo publicada.

    `gbw1` es el producto ganancia-ancho de la PRIMERA etapa sola; no es el
    GBW de la hoja. Al anadir el segundo polo el cruce por 0 dB BAJA, asi que
    los dos parametros hay que resolverlos juntos (ver `calibrar`) -- fijar
    gbw1 = GBW de la hoja y luego buscar el polo da un cruce 15% bajo. Lo
    caza autocomprobacion(), y de ahi salio esta firma.

    Etapa 1 fija AOL y la escala de frecuencia; etapa 2 es el polo que ajusta
    el margen de fase; el buffer lleva la Zo de 125 ohm publicada, que es la
    que convierte el cable de patcheo en un polo.
    """
    gm = 2 * PI * gbw1 * C1
    r1 = AOL / gm
    r2, c2 = 1e3, 1.0 / (2 * PI * 1e3 * fp2)
    return f""".subckt opamp np nm no
Gm 0 n1 np nm {gm:.6e}
R1 n1 0 {r1:.6e}
C1 n1 0 {C1:.6e}
E2 n2 0 n1 0 1
R2 n2 n3 {r2:.6e}
C2 n3 0 {c2:.6e}
E3 n4 0 n3 0 1
Ro n4 no {RO:.6e}
.ends
"""


def _ac(ng: Ng, net: str) -> tuple[list[float], list[float], list[float]]:
    """Corre un .ac y devuelve (f, modulo dB, fase grados) como reales."""
    ng.corre(net)
    for nombre, expr in (("ff", "real(frequency)"),
                         ("mm", "db(v(out))"),
                         ("pp", "ph(v(out))*180/pi")):
        ng.lib.ngSpice_Command(f"let {nombre} = {expr}".encode())
    return ng.vec("ff"), ng.vec("mm"), ng.vec("pp")


def _lazo(ng: Ng, fp2: float, gbw1: float, rl: float,
          cl: float) -> tuple[float, float]:
    """(frecuencia de cruce por 0 dB, margen de fase) en seguidor.

    En G=+1 el lazo ES el lazo abierto, asi que no hay que romper nada.
    """
    net = f"""tl074h lazo abierto
{opamp(fp2, gbw1)}
Vin np 0 AC 1
X1 np 0 out opamp
RL out 0 {rl:.6e}
CL out 0 {cl:.6e}
.ac dec 200 1 1e9
.end
"""
    f, mag, fase = _ac(ng, net)
    for i in range(1, len(mag)):
        if mag[i - 1] > 0.0 >= mag[i]:
            t = mag[i - 1] / (mag[i - 1] - mag[i])
            fc = f[i - 1] + t * (f[i] - f[i - 1])
            return fc, 180.0 + (fase[i - 1] + t * (fase[i] - fase[i - 1]))
    raise RuntimeError("el lazo abierto no cruza 0 dB")


def margen_fase(ng: Ng, fp2: float, gbw1: float, rl: float = RL_HOJA,
                cl: float = CL_HOJA) -> float:
    return _lazo(ng, fp2, gbw1, rl, cl)[1]


def calibrar(ng: Ng) -> tuple[float, float]:
    """Resuelve los DOS parametros libres contra las DOS anclas publicadas.

    Anclas: el cruce por 0 dB tiene que caer en los 5.25 MHz de GBW, y el
    margen de fase en los 56 grados, ambos en la condicion que fija la hoja
    (G=+1, RL=10k, CL=20pF). Dos ecuaciones, dos incognitas (gbw1 y fp2).

    Estan acopladas -- subir el polo mueve el cruce y mover el cruce cambia el
    margen -- asi que se alternan hasta que las dos cierran. Esto NO es
    ajustar hasta que salga bonito: los dos objetivos los publica el
    fabricante, y si no converge, el modelo no vale y el script lo dice.
    """
    gbw1 = GBW
    for _ in range(40):
        lo, hi = 1e6, 1e10                      # bisecar fp2 -> margen de fase
        for _ in range(50):
            mid = (lo * hi) ** 0.5
            if margen_fase(ng, mid, gbw1) < PM_HOJA:
                lo = mid                        # polo mas alto -> menos retraso
            else:
                hi = mid
        fp2 = (lo * hi) ** 0.5
        fc, pm = _lazo(ng, fp2, gbw1, RL_HOJA, CL_HOJA)
        if abs(fc - GBW) / GBW < 1e-3 and abs(pm - PM_HOJA) < 0.2:
            return fp2, gbw1
        gbw1 *= GBW / fc                        # reescalar y volver a bisecar
    raise AssertionError(
        f"la calibracion no converge: cruce {fc/1e6:.2f} MHz contra "
        f"{GBW/1e6:.2f}, margen {pm:.1f} contra {PM_HOJA}")


def autocomprobacion(ng: Ng, fp2: float, gbw1: float) -> None:
    """El modelo contra numeros publicados y contra su propia coherencia."""
    fc, pm = _lazo(ng, fp2, gbw1, RL_HOJA, CL_HOJA)
    assert abs(fc - GBW) / GBW < 0.02, \
        f"GBW del modelo {fc/1e6:.2f} MHz contra los {GBW/1e6:.2f} de la hoja"
    assert abs(pm - PM_HOJA) < 0.5, \
        f"margen del modelo {pm:.1f} contra los {PM_HOJA} de la hoja"

    # AOL en continua: no se uso para calibrar, tiene que salir sola.
    net = f"""aol
{opamp(fp2, gbw1)}
Vin np 0 AC 1
X1 np 0 out opamp
RL out 0 {RL_HOJA:.6e}
CL out 0 {CL_HOJA:.6e}
.ac dec 200 1 1e9
.end
"""
    _, mag, _ = _ac(ng, net)
    assert abs(mag[0] - AOL_DB) < 1.0, \
        f"AOL en continua {mag[0]:.1f} dB contra los {AOL_DB} de la hoja"

    # Control de signo: mas capacidad de carga NO puede mejorar el margen.
    assert margen_fase(ng, fp2, gbw1, cl=1e-9) < \
        margen_fase(ng, fp2, gbw1, cl=CL_HOJA), \
        "mas capacidad de carga mejoro el margen: el modelo tiene el signo al reves"


def transimpedancia(ng: Ng, fp2: float, gbw1: float, c_nodo: float,
                    c_cable: float, c_fb: float = C_FB,
                    r_serie: float = R_SERIE) -> dict:
    """El circuito REAL: corriente dentro, tension en la punta del jack.

    Mide dos cosas de la misma corrida: el pico de la respuesta (dB sobre la
    banda plana) y el sobreimpulso del escalon. El pico dice si el lazo esta
    justo; el sobreimpulso dice como suena.
    """
    rs = f"Rs out jack {r_serie:.6e}" if r_serie > 0 else "Rs out jack 1e-6"
    cf = f"Cf mixo out {c_fb:.6e}" if c_fb > 0 else ""
    base = f"""{opamp(fp2, gbw1)}
X1 0 mixo out opamp
Riv mixo out {R_IV:.6e}
Cn mixo 0 {c_nodo:.6e}
{cf}
{rs}
Cl jack 0 {max(c_cable, 1e-15):.6e}
Rj jack 0 100e3
"""
    f, mag, _ = _ac(ng, f"iv ac\n{base}Iin 0 mixo AC 1\n.ac dec 200 10 1e8\n.end\n")
    plano = mag[0]
    pico = max(mag) - plano

    net_t = (f"iv escalon\n{base}"
             f"Iin 0 mixo PULSE(0 {I_MIX_MAX:.6e} 1u 20n 20n 40u 80u)\n"
             f".tran 20n 25u\n.end\n")
    ng.corre(net_t)
    v = ng.vec("v(jack)")
    t = ng.vec("time")
    cola = [v[i] for i in range(len(v)) if t[i] > 15e-6]
    final = sum(cola) / max(1, len(cola))
    pico_t = max(abs(x) for x in v)
    sobre = 100.0 * (pico_t - abs(final)) / max(abs(final), 1e-12)
    # Si la cola sigue moviendose, el lazo no esta timbrando: esta OSCILANDO,
    # y entonces "sobreimpulso" no significa nada (no hay valor final contra
    # el que medirlo). Se distingue, porque un 46957% invita a pensar que el
    # numero esta mal cuando lo que esta mal es el circuito.
    rizado = (max(cola) - min(cola)) if cola else 0.0
    oscila = rizado > 0.10 * abs(I_MIX_MAX * R_IV)
    return {"pico_db": pico, "plano_db": plano, "sobreimpulso": sobre,
            "v_final": final, "oscila": oscila, "rizado_cola": rizado}


def main() -> int:
    ng = Ng()
    fp2, gbw1 = calibrar(ng)
    autocomprobacion(ng, fp2, gbw1)
    print(f"macromodelo calibrado: segundo polo en {fp2/1e6:.2f} MHz "
          f"-> {margen_fase(ng, fp2, gbw1):.1f} grados en la condicion del datasheet "
          f"({PM_HOJA} publicados)\n")

    comp = (f"C_fb = {C_FB*1e12:.0f} pF, R_serie = {R_SERIE:.0f} ohm"
            if C_FB or R_SERIE else
            "SIN condensador de realimentacion y SIN resistencia serie")
    print(f"Transimpedancia R_IV = {R_IV/1e3:.0f}k, {comp}.")
    if C_FB:
        print(f"Polo del I/V en {1.0/(2*PI*R_IV*C_FB)/1e3:.0f} kHz.")
    print(f"Escalon de {I_MIX_MAX*1e6:.0f} uA -> {I_MIX_MAX*R_IV:.1f} V\n")
    print(f"{'C nodo':>8} {'C cable':>9} | {'pico':>8} {'sobreimpulso':>13} | ")
    print("-" * 58)

    malos = []
    for c_cable in C_CABLE:
        for c_nodo in C_NODO:
            r = transimpedancia(ng, fp2, gbw1, c_nodo, c_cable)
            ok = not r["oscila"] and r["sobreimpulso"] <= SOBREIMPULSO_MAX
            if not ok:
                malos.append((c_nodo, c_cable, r))
            veredicto = "OK" if ok else ("OSCILA" if r["oscila"] else "TIMBRA")
            sobre = "     --" if r["oscila"] else f"{r['sobreimpulso']:7.1f}%"
            print(f"{c_nodo*1e12:7.0f}p {c_cable*1e12:8.0f}p | "
                  f"{r['pico_db']:+7.2f}dB {sobre:>13} | {veredicto}")
        print()

    if not malos:
        print("El lazo aguanta todo el barrido.")
        return 0

    n_osc = sum(1 for m in malos if m[2]["oscila"])
    total = len(C_NODO) * len(C_CABLE)
    print(f"FALLO: {len(malos)} de {total} combinaciones fuera de criterio "
          f"(sobreimpulso <= {SOBREIMPULSO_MAX:.0f}%), y {n_osc} de ellas "
          f"OSCILAN (la cola del escalon no se asienta).")
    print(f"  Ninguna combinacion del barrido pasa, ni siquiera sin cable: "
          f"con 5 pF de nodo y la salida al aire ya hay "
          f"{malos[0][2]['sobreimpulso']:.0f}% de sobreimpulso.")

    print("\nEl arreglo son dos componentes por voz y no cambian el diseno:")
    print(f"{'C_fb':>6} {'R_serie':>8} | {'peor sobreimpulso':>18} "
          f"{'oscilan':>8} | {'polo del I/V':>13}")
    print("-" * 62)
    for c_fb, r_s in _CANDIDATOS:
        rs = [transimpedancia(ng, fp2, gbw1, cn, cc, c_fb=c_fb, r_serie=r_s)
              for cn in C_NODO for cc in C_CABLE]
        peor = max(r["sobreimpulso"] for r in rs if not r["oscila"])
        print(f"{c_fb*1e12:5.0f}p {r_s:7.0f}R | {peor:17.1f}% "
              f"{sum(1 for r in rs if r['oscila']):8d} | "
              f"{1.0/(2*PI*R_IV*c_fb)/1e3:10.0f} kHz")
    print("\nEl polo del I/V queda MUY por encima de la banda de audio: no "
          "cuesta nada musicalmente.")
    return 1


_CANDIDATOS = [(c, r) for c in (10e-12, 22e-12, 33e-12)
               for r in (0.0, 100.0, 220.0)]


def _mutar() -> int:
    """Prueba que este gate DISTINGUE (constitucion, Principio VIII).

    Un barrido que sale rojo no demuestra nada por si solo: podria salir rojo
    siempre. La mutacion es el circuito CORREGIDO -- si con el condensador de
    realimentacion y la resistencia serie sigue saliendo rojo, el gate no
    mide el lazo, mide otra cosa.
    """
    ng = Ng()
    fp2, gbw1 = calibrar(ng)
    autocomprobacion(ng, fp2, gbw1)

    # Las dos configuraciones van EXPLICITAS, no por defecto: el dia que
    # cambien C_FB/R_SERIE arriba, la mutacion tiene que seguir comparando lo
    # mismo -- circuito sin compensar contra circuito compensado.
    sin = [transimpedancia(ng, fp2, gbw1, cn, cc, c_fb=0.0, r_serie=0.0)
           for cn in C_NODO for cc in C_CABLE]
    con = [transimpedancia(ng, fp2, gbw1, cn, cc, c_fb=C_FB, r_serie=R_SERIE)
           for cn in C_NODO for cc in C_CABLE]
    malo = lambda rs: sum(1 for r in rs                       # noqa: E731
                          if r["oscila"] or r["sobreimpulso"] > SOBREIMPULSO_MAX)
    m_sin, m_con = malo(sin), malo(con)
    print(f"  sin compensar : {m_sin:2d} de {len(sin)} fuera de criterio")
    print(f"  compensado    : {m_con:2d} de {len(con)} fuera de criterio")
    if m_sin == len(sin) and m_con == 0:
        print("OK: el gate distingue el circuito roto del arreglado")
        return 0
    print("FALLO: el gate NO distingue. No vigila lo que dice vigilar.")
    return 1


if __name__ == "__main__":
    sys.exit(_mutar() if "--mutar" in sys.argv else main())
