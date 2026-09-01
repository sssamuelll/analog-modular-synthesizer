"""El enlace J2 punto a punto: UNA rama, y por que el modelo viejo no la sanciona.

    python enlace_budget.py

REESCRITO por el J2 punto a punto (docs/superpowers/specs/2026-08-25-j2-punto-
a-punto-design.md, S7): "Modelo por enlace. Muere la pelea de MISO. Gana: la
asercion de R-P3 (el modelo concentrado no sanciona enlaces punto a punto), la
cadena de S4.2 con maximos de hoja, la terminacion como parametro, y la ranura
de la Voz por longitud".

La version anterior (PR #198, issue #199) modelaba OCHO ramas colgando de UN
pin del cerebro: 5,9 m de cinta, 337 pF, un limite de 8,90 MHz contra 8,70
exigidos -- el +2,2 % que disparo el rediseno. Esa red ya no existe: cada
ranura es un enlace privado con su propio maestro (D1). Lo que ese guion
encontro sigue siendo verdad como HISTORIA (esta en git) y su heredero es la
palanca de longitud por enlace de S4.2.

--- Lo que sale de correr las cuentas ---------------------------------------

1. EL ENLACE PUNTO A PUNTO ES UNA LINEA DE TRANSMISION DESDE EL PRIMER
   MEGAHERCIO (R-P3). Con una rama sola (~42 pF), el maximo de flanco que la
   hoja da para el N657 en Speed 11 y 50 pF (4,4 ns) es mas
   rapido que la frontera de vuelo del cable (6 x 3,7 ns = 22 ns) A CUALQUIER
   RELOJ -- el criterio ni siquiera lleva el reloj dentro. El modelo RC solo
   valdria por debajo de unos 15 cm de rama. Consecuencia: NADIE sanciona un
   enlace con el modelo viejo. Se termina en la fuente y se MIDE (R-P4).

2. EL TECHO DEL PELDANO 1 LO PONE EL VIAJE, no el maestro (105 MHz) ni el
   esclavo (34,5): tv(SO)max + ida + vuelta + tsu(MI) tiene que caber en
   medio periodo. Al peor mazo (738 mm) son 22,9 MHz; a 200 mm, 30,3. El largo
   de la rama es una palanca POR ENLACE: la ranura de la Voz se elige por
   longitud.

3. D8 JUBILA ESA CADENA: con la respuesta al ciclo siguiente, el techo pasa a
   la fila electrica del esclavo, 34,5 MHz, y el largo deja de fijar el reloj
   del enlace de la Voz. Sigue fijandolo para quien hable el dialecto legado.

--- Lo que NO esta confirmado ------------------------------------------------

  * V_PROP (5 ns/m) y Z0_CINTA: catalogo generico de cinta IDC 1,27 mm. "Esa
    deuda no la salda el cambio de chip" (S4.2). Se leen de la hoja del cable
    que se compre.
  * CAP_PIN es el CIO tipico de la hoja; no publica maximo. Con una rama, la
    capacidad dominante es la del cable y el valor final se mide en bring-up.
  * Las cifras de salida son las del STM32N657 en Speed 11, la configuracion
    que condiciona la propia tabla SPI. VOL <= 0,4 V a la misma corriente; el
    modelo usa VOH y no consume VOL.
  * Los numeros del esclavo (Tabla 114 del N657) llevan la nota 1: "Evaluated
    by characterization. Not tested in production" (S8, riesgo 2). Se miden.
  * Nada de esto esta medido. Es aritmetica sobre hojas y geometria.
"""
from __future__ import annotations

# --- el esclavo: STM32N657, DS14791 Rev 10, Tabla 114 "SPI characteristics" --
# pp. 222-223. Las cifras de #210 S4.1 no cambian; la tabla si fue renumerada.
TV_SO_MAX_S = 10e-9         # "tv(SO) Data output valid time, Target mode",
                            # tip 8,5 / MAX 10 ns. Gobierna el MAX (S4.1)
TV_SO_TIP_S = 8.5e-9        # se anota para que nadie "recupere" ese margen
TSU_MI_S = 4.5e-9           # "tsu(MI) Data input setup time, Controller
                            # mode", 4,5 ns. El maestro de clase STM32 lo pide;
                            # la nota (2) de la tabla supone tsu(MI) = 0
F_ESCLAVO_FD_NOMINAL_HZ = 50e6   # fila "Target mode transmitter/full duplex",
                                 # 50 MHz CON NOTA (2): solo con tsu(MI) = 0
F_ESCLAVO_RX_HZ = 100e6     # "Target receiver mode"
F_MAESTRO_N657_HZ = 105e6   # "Controller mode, 3.00 < VDD < 3.6 V" -- si el
                            # cerebro fuera un N657. No esta decidido (#209)

# La nota (2), literal: "Maximum frequency in target transmitter mode is
# determined by the sum of tv(SO) and tsu(MI) which has to fit into SCK low or
# high phase preceding the SCK sampling edge". Con un maestro real:
F_PELDANO_2_HZ = 1.0 / (2.0 * (TV_SO_MAX_S + TSU_MI_S))     # 34,5 MHz (D8)

# --- el driver del STM32N657, en el Speed 11 que usa la tabla SPI ------------
IOVDD = 3.3                 # V tip. DS14791 Rev 10, Tabla 24, p. 140
VOH_MIN = IOVDD - 0.4       # V min a 20 mA. DS14791 Rev 10, Tabla 65, p. 171
DRIVE_A = 20e-3             # A, Speed 11. DS14791 Rev 10, Tabla 65, pp. 170-171
C_FLANCO = 50e-12           # F. DS14791 Rev 10, Tabla 68, p. 173
T_FLANCO_MAX_S = 4.4e-9     # s max, Speed 11. DS14791 Rev 10, Tabla 68, p. 173


def r_driver(drive_a: float = DRIVE_A) -> float:
    """Equivalente estatico en el punto IIO/VOH publicado; no modela slew."""
    return (IOVDD - VOH_MIN) / drive_a


# --- la cinta (POR_CONFIRMAR, catalogo generico de IDC 1,27 mm) -------------
Z0_CINTA = 105.0            # ohm
V_PROP = 5.0e-9             # s/m. ~0,67c en PVC. "POR CONFIRMAR contra la
                            # cinta real -- esa deuda no la salda el cambio de
                            # chip" (S4.2)
CAP_PIN = 5.0e-12           # F, CIO tip. DS14791 Rev 10, Tabla 66, p. 171
CAP_CONECTOR = 2.0e-12      # F. DECLARADA, por contacto IDC
CAP_POR_METRO = V_PROP / Z0_CINTA      # 47,6 pF/m; deriva, no se declara

# --- la longitud de rama, DERIVADA del cajon (peor caso; #199 lo derivo) ----
LARGO_RIEL = 0.52832        # m. case/cad/params.scad: "largo_riel = 528.32"
PASO_HORIZONTAL = 0.060     # m. params.scad: "paso_horizontal = 60"
HOLGURA_SERVICIO = 0.150    # m. DECLARADA (evento C9: "recortarla es
                            # legitimo; consumirla en silencio no")
LARGO_RAMA = LARGO_RIEL + PASO_HORIZONTAL + HOLGURA_SERVICIO   # 0,738 m

# --- la terminacion, como parametro (S7) --------------------------------------
R_SERIE = 33.0              # ohm. Valor de PARTIDA: "terminacion serie en el
                            # extremo del cerebro" (bring-up.md :343). El
                            # valor final lo pone el ojo en bring-up (R-P4)
R_PULLDOWN_MISO = 10e3      # ohm. SOBREVIVE por su segunda funcion (D4):
                            # "para que un MISO sin nadie lea cero". Ya no
                            # forma divisor con nadie: no hay serie de pelea

# --- I2C: canal propio por ranura via mux, o sea UNA rama (cerebro S4) ------
R_PULLUP_I2C = 4.7e3
T_SUBIDA_I2C_FAST = 300e-9  # s, modo rapido (400 kHz)
FACTOR_I2C = 0.8473         # ln(9): 30 % -> 70 % de VDD


# --- el modelo por enlace ------------------------------------------------------
def cap_rama(largo_m: float, cap_pin: float = CAP_PIN) -> float:
    """Lo que un pin del cerebro ve en UN enlace: la cinta y el pin de enfrente."""
    return largo_m * CAP_POR_METRO + cap_pin + CAP_CONECTOR


def t_vuelo(largo_m: float) -> float:
    return largo_m * V_PROP


def t_flanco_modelo_viejo(largo_m: float) -> float:
    """Maximo Tr/Tf publicado para Speed 11 con 50 pF, sin interpolar.

    Se usa solo para demostrar que el modelo agrupado esta fuera de regimen
    (R-P3). La rama tiene que caber en la carga de la fila publicada.
    """
    c = cap_rama(largo_m)
    assert c <= C_FLANCO, (
        f"la rama carga {c*1e12:.1f} pF y la ultima fila publicada de "
        f"Tr/Tf cubre {C_FLANCO*1e12:.0f} pF")
    return T_FLANCO_MAX_S


def es_electricamente_corta(largo_m: float) -> bool:
    """S4.3: "flanco > 6 x vuelo" es el criterio de linea corta. Se aplica al
    FLANCO, no al reloj: el reloj no entra."""
    return t_flanco_modelo_viejo(largo_m) > 6.0 * t_vuelo(largo_m)


def largo_frontera_m() -> float:
    """Por debajo de que largo el modelo agrupado volveria a valer."""
    lo, hi = 0.0, LARGO_RAMA
    assert es_electricamente_corta(lo) and not es_electricamente_corta(hi)
    while hi - lo > 1e-4:
        m = (lo + hi) / 2
        lo, hi = (m, hi) if es_electricamente_corta(m) else (lo, m)
    return (lo + hi) / 2


def f_peldano_1(largo_m: float, tv_so: float = TV_SO_MAX_S) -> float:
    """S4.2: full duplex, respuesta en el MISMO ciclo. Medio periodo >=
    tv(SO) + vuelo de SCLK + vuelo de MISO + tsu(MI)."""
    return 1.0 / (2.0 * (tv_so + 2.0 * t_vuelo(largo_m) + TSU_MI_S))


def f_modelo_viejo(largo_m: float) -> float:
    """Lo que el modelo agrupado DIRIA de una rama. No sanciona nada (R-P3);
    se imprime para que se vea que numero seria y por que no vale."""
    return 1.0 / (2.0 * t_flanco_modelo_viejo(largo_m))


def i_dinamica(largo_m: float, f_hz: float) -> float:
    """I = C V f por pin, en UN enlace."""
    return cap_rama(largo_m) * IOVDD * f_hz


def t_subida_i2c(largo_m: float, r_pullup: float = R_PULLUP_I2C) -> float:
    return FACTOR_I2C * r_pullup * cap_rama(largo_m, cap_pin=2 * CAP_PIN)


def autocomprobacion() -> None:
    """Los numeros del papel, reproducidos, y un caso a mano."""
    # S4.1: el peldano 2 sale de la nota (2) con tsu(MI) real.
    assert abs(F_PELDANO_2_HZ - 34.48e6) < 0.05e6, F_PELDANO_2_HZ
    # S4.2, tabla recalculada contra el N657: 738/400/200 mm.
    for mm, esperado in ((738, 22.9e6), (400, 27.0e6), (200, 30.3e6)):
        f = f_peldano_1(mm / 1e3)
        assert abs(f - esperado) < 0.06e6, (mm, f)
    # Y con el TIPICO saldrian 24,5/29,4/33,3 -- se anota, no se usa.
    assert abs(f_peldano_1(0.738, TV_SO_TIP_S) - 24.5e6) < 0.06e6
    # S4.3: 738 mm -> vuelo 3,69 ns; ~42 pF; flanco max 4,4 ns < 22 ns.
    assert abs(t_vuelo(LARGO_RAMA) - 3.69e-9) < 0.01e-9
    assert abs(cap_rama(LARGO_RAMA) - 42.1e-12) < 0.2e-12
    assert cap_rama(LARGO_RAMA) < C_FLANCO
    assert t_flanco_modelo_viejo(LARGO_RAMA) == T_FLANCO_MAX_S
    # La frontera existe y esta por debajo de la rama: si no, R-P3 miente.
    assert not es_electricamente_corta(LARGO_RAMA)
    assert es_electricamente_corta(0.010)


def demo() -> None:
    autocomprobacion()
    r_drv = r_driver()

    print("ENLACE J2 PUNTO A PUNTO -- una rama, un maestro, un esclavo\n")
    print("el esclavo, Tabla 114 del N657 (DS14791 Rev 10, pp. 222-223):")
    print(f"  tv(SO)                    tip {TV_SO_TIP_S*1e9:4.1f} / MAX {TV_SO_MAX_S*1e9:4.1f} ns"
          "   manda el MAX")
    print(f"  tsu(MI) del maestro           {TSU_MI_S*1e9:4.1f} ns"
          "   la nota (2) supone 0; un STM32 pide esto")
    print(f"  full duplex, portada          {F_ESCLAVO_FD_NOMINAL_HZ/1e6:5.1f} MHz   con nota (2)")
    print(f"  full duplex, REAL (peldano 2) {F_PELDANO_2_HZ/1e6:5.1f} MHz"
          f"   1 / (2 x ({TV_SO_MAX_S*1e9:.0f} + {TSU_MI_S*1e9:.1f}) ns)  <- D8\n")

    print("la rama, derivada del cajon (peor caso: extremos opuestos del riel):")
    print(f"  riel {LARGO_RIEL*1e3:.2f} + entrepiso {PASO_HORIZONTAL*1e3:.0f} + holgura "
          f"{HOLGURA_SERVICIO*1e3:.0f} (DECLARADA) = {LARGO_RAMA*1e3:.1f} mm")
    print(f"  capacidad de UN enlace        {cap_rama(LARGO_RAMA)*1e12:5.1f} pF"
          f"   (eran 337 pF con ocho ramas en un pin)")
    print(f"  vuelo una via                 {t_vuelo(LARGO_RAMA)*1e9:5.2f} ns\n")

    print("R-P3 -- el modelo agrupado esta fuera de regimen, a cualquier reloj:")
    t_fl = t_flanco_modelo_viejo(LARGO_RAMA)
    print(f"  flanco maximo publicado              {t_fl*1e9:5.2f} ns  "
          f"(max de Tabla 68 a {C_FLANCO*1e12:.0f} pF, Speed 11)")
    print(f"  frontera de linea corta, 6 x vuelo   {6*t_vuelo(LARGO_RAMA)*1e9:5.2f} ns")
    print(f"  flanco / frontera                    {t_fl/(6*t_vuelo(LARGO_RAMA)):5.2f}x  (linea corta pide > 1)")
    frontera = largo_frontera_m()
    print(f"  el modelo agrupado solo valdria por debajo de {frontera*1e3:.0f} mm de rama.")
    print(f"  Lo que ese modelo DIRIA de esta rama, {f_modelo_viejo(LARGO_RAMA)/1e6:.0f} MHz, no")
    print("  sanciona nada: la cinta es una linea de transmision. Se termina en")
    print("  la fuente y se mide (R-P4).")
    assert not es_electricamente_corta(LARGO_RAMA), (
        "la rama salio electricamente corta: el modelo agrupado volveria a "
        "valer y R-P3 habria que reescribirla. Revisar V_PROP y el driver")
    assert frontera < 0.5 * LARGO_RAMA, (
        f"la frontera ({frontera*1e3:.0f} mm) esta a menos de la mitad de la "
        "rama: R-P3 se sostiene por poco y hay que decirlo en el papel")

    print("\nla terminacion en la fuente, como parametro:")
    r_ideal = Z0_CINTA - r_drv
    print(f"  driver del N657               {r_drv:5.1f} ohm   (IOVDD - VOH) / {DRIVE_A*1e3:.0f} mA")
    print(f"  Z0 de la cinta                {Z0_CINTA:5.1f} ohm   POR_CONFIRMAR")
    print(f"  serie ideal = Z0 - driver     {r_ideal:5.1f} ohm")
    print(f"  serie de partida              {R_SERIE:5.1f} ohm   bring-up.md :343; el ojo la ajusta")
    assert r_drv < Z0_CINTA, (
        "el driver ya es mas 'duro' que la cinta: no hay terminacion en la "
        "fuente posible con serie, y hay que cambiar de driver o de cinta")

    print("\nS4.2 -- el techo del peldano 1 lo pone el viaje, por longitud de rama:\n")
    print(f"  {'rama':>7}  {'vuelo i/v':>10}  {'medio periodo':>14}  "
          f"{'peldano 1':>10}  {'con tip.':>9}   {'modelo viejo':>12}")
    for mm in (200, 300, 400, 500, 600, 738, 900):
        L = mm / 1e3
        medio = TV_SO_MAX_S + 2 * t_vuelo(L) + TSU_MI_S
        marca = "  <- derivado hoy" if mm == 738 else ""
        print(f"  {mm:4d} mm  {2*t_vuelo(L)*1e9:7.2f} ns  {medio*1e9:11.2f} ns  "
              f"{f_peldano_1(L)/1e6:7.1f} MHz  {f_peldano_1(L, TV_SO_TIP_S)/1e6:6.1f} MHz"
              f"   {f_modelo_viejo(L)/1e6:8.0f} MHz{marca}")
    print(f"\n  peldano 2 (D8), sin viaje:  {F_PELDANO_2_HZ/1e6:.1f} MHz a cualquier largo.")
    print("  'con tip.' usa tv(SO) tipico y NO gobierna: se imprime para que")
    print("  nadie recupere ese margen sin saber que compra. 'modelo viejo' es")
    print("  lo que el RC diria, y no vale (R-P3).")
    print("  La ranura de la Voz se elige por longitud: cada 100 mm menos")
    print(f"  compran ~{(f_peldano_1(0.638)-f_peldano_1(0.738))/1e6:.1f} MHz de peldano 1. Con D8 el largo deja de")
    print("  fijar el reloj de la Voz; sigue fijandolo para el dialecto legado.")

    print("\nla corriente del pin, por enlace (STM32N657, Speed 11):")
    for nombre, f in (("piso legado 10 MHz", 10e6), ("peldano 2", F_PELDANO_2_HZ)):
        i = i_dinamica(LARGO_RAMA, f)
        print(f"  SCLK a {nombre:20} {i*1e3:5.2f} mA de {DRIVE_A*1e3:.0f}"
              f"   {'OK' if i < DRIVE_A else '<< POR ENCIMA'}")
    assert i_dinamica(LARGO_RAMA, F_PELDANO_2_HZ) < DRIVE_A, (
        "un solo enlace al peldano 2 pide mas corriente media que el drive")
    print("  Ocho enlaces son ocho pines: la suma va contra los limites")
    print("  acumulados de la hoja del STM32N657; 20 mA es por pin.")

    print("\nI2C -- canal propio por ranura (una rama, cerebro S4):")
    t = t_subida_i2c(LARGO_RAMA)
    print(f"  {cap_rama(LARGO_RAMA, 2*CAP_PIN)*1e12:.1f} pF con pull-up de {R_PULLUP_I2C/1e3:.1f}k"
          f"  ->  subida de {t*1e9:.0f} ns  "
          f"(modo rapido pide <= {T_SUBIDA_I2C_FAST*1e9:.0f})"
          f"  {'OK' if t <= T_SUBIDA_I2C_FAST else 'NO'}")
    assert t <= T_SUBIDA_I2C_FAST, "el I2C no llega a modo rapido con este mazo"

    print("\nlo que MURIO con D4 y ya no se calcula aqui: la pelea de drivers en")
    print("MISO, el divisor serie/pull-down contra VIH, las ocho ramas en un")
    print(f"pin, y el barrido de CAP_PIN. El pull-down de {R_PULLDOWN_MISO/1e3:.0f}k se queda: un")
    print("MISO sin nadie lee cero.")
    print("\nOK: presupuesto cerrado. Esto NO es una prueba: es una puerta.")
    print("La medida que sanciona cada enlace es el ojo en el extremo del")
    print("modulo, en el bring-up del cerebro (R-P4, #210 S8 riesgo 1).")


if __name__ == "__main__":
    demo()
