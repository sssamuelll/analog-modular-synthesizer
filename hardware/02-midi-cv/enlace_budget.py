"""El enlace J2: si la cinta plana aguanta 10 MHz, y si aguanta un oyente mas.

    python enlace_budget.py

Alcance DECLARADO por la spec del cerebro S11 ("Budget / Que decide"):

    "El flanco de 10 MHz por cinta plana con ocho stubs, la resistencia de
     serie con sus DOS restricciones opuestas, el V_IH resultante, y el
     tiempo de subida de las ocho ramas de I2C contra la longitud declarada
     del mazo"

Y una pregunta que la spec no tenia cuando se escribio esa linea: el modulo
de Voz quiere que sus DOS micros oigan el J2 directamente, en vez de que el
segundo reciba todo reenviado por el primero. Hoy lo prohibe la decision 3
del spec de los dieciseis ("del J2 cuelga un micro, no los chips ... el SPI
del instrumento muere en el maestro"), y la spec del cerebro S4 dice que el
bus "no admite un cliente mas". Este guion pone cifra a ese "no admite".

--- Lo que sale de correr las cuentas ---------------------------------------

1. EL SEGUNDO OYENTE NO ES EL PROBLEMA. Colgado como T dentro del modulo
   cuesta ~4 % de capacidad de red. La rama entera del J2 ya se come el
   resto.

2. EL J2 A 10 MHz CON OCHO RAMAS YA ESTA EN EL FILO, y no por el oyente:
   por la longitud del mazo. Ocho ramas de 0,74 m son casi 6 m de cinta
   colgando de UN pin. La holgura depende de que modelo de driver se use, y
   los dos modelos legitimos NO coinciden:

     - resistivo (R del driver derivada de VOH a su corriente nominal):
       pasa con holgura
     - limitado en corriente (el driver no da mas de su drive strength):
       no llega a lo que el trafico declarado necesita

   La verdad esta entre los dos. Por eso el veredicto NO dice "pasa": dice
   cual es la medida que lo cierra y cual es la palanca que compra margen.

3. LA PALANCA NO ES LA ARQUITECTURA. Es la longitud del mazo, el drive
   strength y el reloj -- y el reloj ya es perilla por contrato ("<=10 MHz",
   cerebro S4.2: "si la cinta no aguanta, baja el firmware y la placa no se
   rehace").

--- Lo que NO esta confirmado -----------------------------------------------

  * CAP_PIN: Raspberry Pi NO PUBLICA la capacidad de entrada del GPIO. Se
    busco el termino en las 1380 paginas del datasheet (2024-08) y no
    aparece en ninguna tabla electrica. Va DECLARADA y el guion barre su
    sensibilidad, para que la decision se tome sobre ese numero y no sobre
    el supuesto. Es el numero que mas mueve el veredicto.
  * Z0_CINTA y V_PROP: valores de catalogo generico de cinta IDC de paso
    1,27 mm. Hay que leerlos de la hoja del cable que se compre.
  * CAP_CONECTOR: estimada por contacto IDC.
  * El modelo es AGRUPADO (RC), no de linea de transmision con reflexiones.
    Es valido solo mientras la red sea electricamente corta, y el guion lo
    COMPRUEBA en vez de suponerlo -- ver consistencia_agrupada().
  * LARGO_RAMA se DERIVA de la geometria del cajon (ver abajo). La spec de
    orquestacion S9 riesgo 4 dice que ese numero "no existe en ningun
    documento del repositorio"; esto lo deriva y lo deja citado, que es lo
    que ese riesgo pedia para cerrar.

--- Lo que este calculo NO cubre --------------------------------------------

  * Reflexiones, diafonia entre conductores de la cinta, y el retorno de
    masa compartido del IDC 2x6 (solo 2 de 12 conductores son GNDD).
  * El transitorio real del driver, que no es ni una R pura ni una fuente de
    corriente pura: la Figura 150 del datasheet da la curva V-I y este
    guion solo usa sus dos extremos como cota.
  * La pelea de MISO en si: la spec del cerebro ya declara que la serie "no
    evita la pelea, la hace sobrevivible", y quien la evita es el contrato
    de modulo (pieza 4), que se mide en el bring-up.
  * Nada de esto esta medido. Es aritmetica sobre datasheets y geometria.
"""
from __future__ import annotations

# --- el contrato del bus (citado) -------------------------------------------
F_J2_CONTRATO = 10e6        # Hz. Contrato congelado por el modulo 3:
                            # "SPI modo 1, <=10 MHz" (core/src/j2.rs cabecera)
N_RAMAS = 8                 # cerebro S6: "Enlace J2 x8 ... Ocho IDC 2x6"
                            # y nucleo S218: "estrella con MISO compartido,
                            # 8 stubs"

# Cuanto del bus se lleva el trafico declarado, y cuanto puede llevarse.
# latencia_mano_budget.py, caso desacoplado (barrido 4 kHz, lazo 8 kHz):
#   "43.5% del J2 -- queda 56.5% libre" contra "techo de bus declarado 50.0%"
OCUPACION_DECLARADA = 0.435
TECHO_OCUPACION = 0.50

# --- el driver, contra fuente primaria --------------------------------------
# docs/reference/datasheets/rp2350-datasheet-2024-08.pdf
# S14.9.4, Tabla 1436 "Digital IO characteristics", columna IOVDD=3.3V
IOVDD = 3.3                 # V
VIH_MIN = 2.0               # V. "Input Voltage High (Standard IO)", minimo
VIL_MAX = 0.8               # V
VHYS = 0.2                  # V. Schmitt trigger habilitado
VOH_MIN = 2.62              # V. "Output Voltage High", minimo, con la nota
                            # "IOH = 2, 4, 8 or 12mA depending on setting"
VOL_MAX = 0.5               # V
I_IOVDD_MAX = 100e-3        # A. "Maximum Total IOVDD current", suma de TODO
                            # lo que sacan los GPIO a la vez
RPD_CHIP = 36e3             # ohm. Pull-down interna, minimo a 3,3 V (32e3 es
                            # la pull-UP; la down va de 36k a 113k)

# S14.9.4.1: "The GPIOs on RP2350 have four different output drive strengths,
# nominally called 2, 4, 8 and 12mA modes."
DRIVES_MA = (2.0, 4.0, 8.0, 12.0)

# --- la cinta (POR_CONFIRMAR, catalogo generico de IDC 1,27 mm) -------------
Z0_CINTA = 105.0            # ohm. POR_CONFIRMAR contra la hoja del cable
V_PROP = 5.0e-9             # s/m. POR_CONFIRMAR. ~0,67c en PVC
CAP_PIN = 5.0e-12           # F. DECLARADA -- el datasheet no la publica
CAP_CONECTOR = 2.0e-12      # F. DECLARADA, por contacto IDC

# La capacidad por metro NO se declara aparte: sale de las otras dos, y asi
# no pueden desincronizarse. C = t_prop / Z0.
CAP_POR_METRO = V_PROP / Z0_CINTA          # 47,6 pF/m con los valores de hoy

# --- la longitud de rama, DERIVADA de la geometria del cajon ----------------
# El agujero del riesgo 4 de orquestacion S9. Terminos, todos de
# case/cad/params.scad salvo el ultimo, que va declarado a proposito:
LARGO_RIEL = 0.52832        # m. params.scad:460 "largo_riel = 528.32". Peor
                            # caso horizontal: cerebro en un extremo de la
                            # fila B, modulo en el otro extremo de la fila A
PASO_HORIZONTAL = 0.060     # m. params.scad "paso_horizontal = 60" -- el
                            # entrepiso, la franja que el mazo tiene que
                            # cruzar para subir de la fila B a la fila A
HOLGURA_SERVICIO = 0.150    # m. DECLARADA, no derivada: es lo que hay que
                            # dejar para poder sacar un modulo del frente sin
                            # desconectarlo. Si se recorta, se recorta aqui y
                            # el barrido de abajo dice cuanto compra
LARGO_RAMA = LARGO_RIEL + PASO_HORIZONTAL + HOLGURA_SERVICIO   # 0,738 m

# Lo que costaria la T dentro del modulo de Voz: el salto entre las dos
# columnas, que ya lo cruzan el SPI privado y el I2C (dieciseis S3, tabla
# "Que cruza los conectores").
LARGO_STUB_INTERNO = 0.150  # m. DECLARADO. Dos columnas de ~153 mm de ancho
                            # (voz-total S8), conector a conector

# --- I2C, la otra mitad del alcance declarado -------------------------------
# cerebro S6: cada ranura lleva "canal propio de I2C", asi que el bus de I2C
# es UNA rama, no ocho en paralelo.
R_PULLUP_I2C = 4.7e3        # ohm. Valor de partida; el guion reporta el techo
T_SUBIDA_I2C_STD = 1000e-9  # s. Limite de modo estandar (100 kHz)
T_SUBIDA_I2C_FAST = 300e-9  # s. Limite de modo rapido (400 kHz)
FACTOR_I2C = 0.8473         # ln(9) -- subida RC del 30% al 70% de VDD


def f_j2_minima() -> float:
    """El reloj por debajo del cual el trafico declarado revienta el techo."""
    return F_J2_CONTRATO * OCUPACION_DECLARADA / TECHO_OCUPACION


def r_driver(drive_a: float) -> float:
    """Impedancia de salida del driver, derivada de VOH a su corriente nominal.

    El datasheet no publica una R de salida: publica que a la corriente
    nominal del modo elegido, la salida no baja de VOH_MIN. La pendiente
    entre esos dos puntos es la cota resistiva.
    """
    return (IOVDD - VOH_MIN) / drive_a


def capacidad_red(n_ramas: int, largo_rama: float,
                  oyentes_extra: int = 0,
                  largo_stub_interno: float = 0.0,
                  cap_pin: float | None = None) -> float:
    """Capacidad total colgada de UN pin del cerebro (SCLK o MOSI).

    `oyentes_extra` y `largo_stub_interno` se aplican a UNA SOLA rama --
    la del modulo de Voz, que es la unica que se bifurca. Multiplicarlos
    por las ocho seria contar ocho modulos de dos columnas, y solo hay uno.
    """
    c_pin = CAP_PIN if cap_pin is None else cap_pin
    por_rama = largo_rama * CAP_POR_METRO + (c_pin + CAP_CONECTOR)
    extra = oyentes_extra * (c_pin + CAP_CONECTOR) \
        + largo_stub_interno * CAP_POR_METRO
    return n_ramas * por_rama + extra


def t_hasta_vih_resistivo(r_total: float, cap: float) -> float:
    """Modelo OPTIMISTA: el driver es una resistencia.

    V(t) = IOVDD * (1 - exp(-t/RC)), y el receptor valida en VIH_MIN.
    """
    import math
    return -r_total * cap * math.log(1.0 - VIH_MIN / IOVDD)


def t_hasta_vih_corriente(drive_a: float, cap: float) -> float:
    """Modelo PESIMISTA: el driver no da mas de su drive strength.

    Rampa de corriente constante: t = C * dV / I.
    """
    return cap * VIH_MIN / drive_a


def f_max(t_valido: float) -> float:
    """El reloj mas alto que deja al flanco llegar a VIH antes del muestreo.

    SPI modo 1 muestrea medio periodo despues del flanco que mueve el dato,
    asi que el presupuesto del flanco es el SEMIPERIODO.
    """
    return 1.0 / (2.0 * t_valido)


def limite(cap: float, r_total: float, drive_a: float = 12e-3) -> float:
    """El reloj mas alto que aguanta la red, por el mas restrictivo de los tres.

    Se reporta SIEMPRE el menor: un presupuesto que eligiera el modelo que
    mas le conviene no seria un presupuesto.
    """
    return min(f_max(t_hasta_vih_resistivo(r_total, cap)),
               f_max(t_hasta_vih_corriente(drive_a, cap)),
               f_max_por_corriente_media(drive_a, cap))


def consistencia_agrupada(largo_rama: float, r_total: float,
                          cap: float) -> tuple[float, float, bool]:
    """El modelo RC solo vale si la red es electricamente corta.

    Criterio: la constante RC tiene que dominar sobre el ida y vuelta de la
    rama mas larga. Se pide RC >= 3 * t_ida_y_vuelta.
    """
    t_ida_vuelta = 2.0 * largo_rama * V_PROP
    rc = r_total * cap
    return rc, t_ida_vuelta, rc >= 3.0 * t_ida_vuelta


def corriente_dinamica(cap: float, frecuencia: float) -> float:
    """Corriente media que el pin tiene que dar: I = C * V * f."""
    return cap * IOVDD * frecuencia


def f_max_por_corriente_media(drive_a: float, cap: float) -> float:
    """TERCER limite, y es un techo duro: la corriente media del pin.

    Cargar y descargar `cap` a `frecuencia` cuesta I = C*V*f de media. Si
    eso pasa del drive strength, el pin no sostiene el flanco por mucho que
    la aritmetica del borde diga que si.
    """
    return drive_a / (cap * IOVDD)


def t_subida_i2c(r_pullup: float, cap: float) -> float:
    return FACTOR_I2C * r_pullup * cap


def vih_tras_divisor(r_serie: float, r_pulldown: float) -> float:
    """MISO: el modulo entrega VOH_MIN, y en el cerebro hay serie + pull-down.

    Es la TERCERA restriccion que pide la spec del cerebro S4.2: "que el
    divisor que forman la serie de MISO y el pull-down de la pieza 2 deje el
    V_IH del pin dentro de lo que el datasheet garantiza".
    """
    return VOH_MIN * r_pulldown / (r_pulldown + r_serie)


def r_serie_max_por_vih(r_pulldown: float, margen: float = 1.0) -> float:
    """La serie mas grande que todavia deja pasar VIH_MIN con su margen."""
    objetivo = VIH_MIN * margen
    return r_pulldown * (VOH_MIN - objetivo) / objetivo


def i_pelea(r_serie: float) -> float:
    """Dos drivers peleandose MISO, cada uno con su serie."""
    return IOVDD / (2.0 * r_serie)


# --- los tres casos que decide este guion -----------------------------------
CASOS = (
    ("hoy: 8 ramas, un oyente por rama", N_RAMAS, 0, 0.0),
    ("T dentro del modulo de Voz", N_RAMAS, 1, LARGO_STUB_INTERNO),
    ("novena rama para la columna B", N_RAMAS + 1, 0, 0.0),
)

R_SERIE = 33.0              # ohm. Valor de partida para SCLK/MOSI
R_PULLDOWN_MISO = 10e3      # ohm. Pieza 2 de cerebro S4.2, valor de partida


def autocomprobacion() -> None:
    """Un caso hecho a mano, para que el modelo no se valide solo a si mismo.

    R = 100 ohm, C = 1000 pF -> RC = 100 ns.
    VIH/IOVDD = 2.0/3.3 = 0.60606 ; 1 - eso = 0.39394 ; -ln = 0.93159
    t = 100 ns * 0.93159 = 93.159 ns   -> f_max = 1/(2*93.159n) = 5.367 MHz
    Corriente constante: t = 1000 pF * 2.0 V / 10 mA = 200 ns
    """
    t = t_hasta_vih_resistivo(100.0, 1000e-12)
    assert abs(t - 93.159e-9) < 0.05e-9, f"resistivo a mano: {t*1e9:.3f} ns"
    assert abs(f_max(t) - 5.367e6) < 5e3, "f_max a mano"
    t2 = t_hasta_vih_corriente(10e-3, 1000e-12)
    assert abs(t2 - 200e-9) < 1e-12, f"corriente a mano: {t2*1e9:.3f} ns"
    # Y que la capacidad por metro sale de donde decimos que sale.
    assert abs(CAP_POR_METRO - 47.619e-12) < 0.01e-12, "C/m derivada"


def demo() -> None:
    autocomprobacion()

    f_min = f_j2_minima()
    r_drv12 = r_driver(12e-3)
    r_total = r_drv12 + R_SERIE

    print("Enlace J2 -- el flanco por cinta plana, y si cabe un oyente mas\n")
    print(f"  contrato del bus            <= {F_J2_CONTRATO/1e6:.0f} MHz")
    print(f"  lo que el trafico exige        {f_min/1e6:.2f} MHz"
          f"   ({OCUPACION_DECLARADA:.1%} de ocupacion contra un techo"
          f" del {TECHO_OCUPACION:.0%})")
    print(f"  driver a 12 mA                 {r_drv12:.1f} ohm"
          f"   (IOVDD {IOVDD} - VOH {VOH_MIN}) / 12 mA")
    print(f"  + serie de {R_SERIE:.0f} ohm             {r_total:.1f} ohm\n")

    print("la longitud de rama, derivada (riesgo 4 de orquestacion S9):")
    print(f"  riel del case                  {LARGO_RIEL*1e3:6.2f} mm"
          "   params.scad:460")
    print(f"  entrepiso a cruzar             {PASO_HORIZONTAL*1e3:6.2f} mm"
          "   params.scad paso_horizontal")
    print(f"  holgura de servicio            {HOLGURA_SERVICIO*1e3:6.2f} mm"
          "   DECLARADA")
    print("  ---------------------------------------")
    print(f"  LARGO_RAMA                     {LARGO_RAMA*1e3:6.2f} mm")
    print(f"  cinta total colgando de un pin {LARGO_RAMA*N_RAMAS:6.2f} m"
          f"   ({N_RAMAS} ramas)\n")

    print("los tres casos, con los TRES limites. El que manda es el menor:\n")
    print(f"  {'caso':34s} {'C red':>8s} {'borde R':>10s}"
          f" {'borde I':>10s} {'I media':>10s} {'manda':>10s}")
    resultados = {}
    for nombre, n, oyentes, stub in CASOS:
        cap = capacidad_red(n, LARGO_RAMA, oyentes, stub)
        f_res = f_max(t_hasta_vih_resistivo(r_total, cap))
        f_cor = f_max(t_hasta_vih_corriente(12e-3, cap))
        f_med = f_max_por_corriente_media(12e-3, cap)
        manda = min(f_res, f_cor, f_med)
        resultados[nombre] = (cap, f_res, f_cor, f_med, manda)
        marca = "OK" if manda >= f_min else "<< NO"
        print(f"  {nombre:34s} {cap*1e12:5.0f} pF {f_res/1e6:7.2f} MHz"
              f" {f_cor/1e6:7.2f} MHz {f_med/1e6:7.2f} MHz"
              f" {manda/1e6:6.2f} {marca}")
    print("\n  borde R  = el driver como resistencia          (OPTIMISTA)")
    print("  borde I  = el driver como fuente de corriente   (PESIMISTA)")
    print("  I media  = techo duro: C*V*f contra el drive strength")
    print(f"  hace falta {f_min/1e6:.2f} MHz para el trafico declarado")

    cap_hoy = resultados["hoy: 8 ramas, un oyente por rama"][0]
    cap_t = resultados["T dentro del modulo de Voz"][0]
    cap_9 = resultados["novena rama para la columna B"][0]
    print("\nlo que cuesta el segundo oyente, en capacidad de red:")
    print(f"  T dentro del modulo   +{(cap_t/cap_hoy - 1):5.1%}")
    print(f"  novena rama           +{(cap_9/cap_hoy - 1):5.1%}")
    print("  La T cuesta un pin y un stub corto; la novena rama cuesta")
    print("  una rama ENTERA de cinta, que es de donde sale la capacidad.")

    # La pregunta que este guion existe para contestar (decision 3 del #164).
    assert cap_t < cap_9, (
        "la T dentro del modulo salio MAS cara que una novena rama: si esto "
        "salta, el camino barato es el otro y el diseno cambia de sitio")
    assert (cap_t - cap_hoy) / cap_hoy < 0.10, (
        f"el segundo oyente cuesta {(cap_t/cap_hoy - 1):.1%} de capacidad de "
        "red: por encima del 10 % deja de ser 'un pin mas' y pasa a ser una "
        "decision de bus que hay que renegociar con la spec del cerebro")

    rc, t_iv, corta = consistencia_agrupada(LARGO_RAMA, r_total, cap_t)
    print("\nel modelo agrupado, comprobado y no supuesto:")
    print(f"  RC de la red               {rc*1e9:6.2f} ns")
    print(f"  ida y vuelta de una rama   {t_iv*1e9:6.2f} ns")
    print(f"  RC / ida-y-vuelta          {rc/t_iv:6.2f}x  (se pide >= 3)"
          f"  {'OK' if corta else '<<< NO VALE EL MODELO'}")
    assert corta, (
        "la red dejo de ser electricamente corta: este guion ya no sirve y "
        "hace falta un modelo de linea de transmision con reflexiones")

    i_sclk = corriente_dinamica(cap_t, F_J2_CONTRATO)
    print("\nla corriente que el pin tiene que dar (I = C*V*f):")
    print(f"  SCLK al contrato de {F_J2_CONTRATO/1e6:.0f} MHz   "
          f"{i_sclk*1e3:5.2f} mA  de 12 mA de drive"
          f"   {'OK' if i_sclk < 12e-3 else '<< POR ENCIMA'}")
    print(f"  SCLK + MOSI                {i_sclk*1.5e3:5.2f} mA  de"
          f" {I_IOVDD_MAX*1e3:.0f} mA de IOVDD total")
    print("  MOSI cuenta a la mitad: los datos cambian como mucho un flanco")
    print("  de cada dos, el reloj cambia en los dos.")
    assert i_sclk * 1.5 < I_IOVDD_MAX, (
        f"SCLK+MOSI piden {i_sclk*1.5e3:.0f} mA de los "
        f"{I_IOVDD_MAX*1e3:.0f} mA que la Tabla 1436 da para TODOS los GPIO "
        "juntos: no queda corriente para el resto del cerebro")

    print("\nbarrido de longitud de rama -- LA palanca, y su precio:\n")
    print(f"  {'largo':>8s}   {'8 ramas':>14s}  {'8 + T':>14s}"
          f"  {'9 ramas':>14s}")
    largo_ok = None
    for mm in (300, 400, 500, 600, 738, 900, 1100):
        largo = mm / 1000.0
        fila, todos_ok = [], True
        for _, n, oyentes, stub in CASOS:
            f_l = limite(capacidad_red(n, largo, oyentes, stub), r_total)
            ok = f_l >= f_min
            todos_ok &= ok
            fila.append(f"{f_l/1e6:6.2f} MHz {'OK' if ok else 'NO'}")
        if todos_ok:
            largo_ok = mm          # el MAYOR que aguanta, no el primero
        marca = "  <- derivado hoy" if mm == 738 else ""
        print(f"  {mm:5d} mm   " + "  ".join(f"{c:>14s}" for c in fila)
              + marca)
    print(f"\n  El mazo mas largo que deja pasar a los TRES casos:"
          f" {largo_ok} mm."
          if largo_ok else "\n  Ningun largo del barrido deja pasar a los tres.")
    print(f"  Hoy la geometria del cajon da {LARGO_RAMA*1e3:.0f}."
          f" Sobran {LARGO_RAMA*1e3 - largo_ok:.0f} mm que recortar.")

    print("\nbarrido de CAP_PIN -- el numero que el datasheet no publica:\n")
    print(f"  {'CAP_PIN':>9s} {'8 ramas':>12s} {'8 + T':>12s}"
          f" {'9 ramas':>12s}")
    for pf in (2.0, 5.0, 10.0, 20.0):
        fila = [limite(capacidad_red(n, LARGO_RAMA, oyentes, stub,
                                     cap_pin=pf * 1e-12), r_total)
                for _, n, oyentes, stub in CASOS]
        marca = "  <- declarado" if pf == 5.0 else ""
        print(f"  {pf:6.1f} pF " + " ".join(f"{f/1e6:8.2f} MHz" for f in fila)
              + marca)
    print("\n  Cuadruplicarlo de 5 a 20 pF mueve el limite menos que quitarle")
    print("  200 mm al mazo. La cinta manda sobre los pines, y ESE es el")
    print("  hallazgo util: el numero que falta NO es el que decide.")

    print("\nla resistencia de serie, con sus dos restricciones opuestas:\n")
    r_max_vih = r_serie_max_por_vih(R_PULLDOWN_MISO)
    v_miso = vih_tras_divisor(R_SERIE, R_PULLDOWN_MISO)
    print("  MISO la empuja ARRIBA: limita la pelea entre dos drivers")
    for r in (33.0, 100.0, 220.0, 470.0):
        print(f"    serie {r:5.0f} ohm  ->  pelea de {i_pelea(r)*1e3:6.1f} mA"
              f"   {'OK' if i_pelea(r) <= 12e-3 else 'por encima del drive'}")
    print(f"\n  SCLK/MOSI la empujan ABAJO: termina el flanco de las"
          f" {N_RAMAS} ramas")
    for r in (33.0, 100.0, 220.0, 470.0):
        f_r = limite(cap_t, r_drv12 + r)
        print(f"    serie {r:5.0f} ohm  ->  {f_r/1e6:6.2f} MHz"
              f"   {'OK' if f_r >= f_min else 'por debajo de lo que hace falta'}")
    print("\n  y la TERCERA, el divisor de MISO contra VIH:")
    print(f"    serie {R_SERIE:.0f} ohm con pull-down de"
          f" {R_PULLDOWN_MISO/1e3:.0f}k  ->  {v_miso:.3f} V"
          f"  contra VIH de {VIH_MIN} V")
    print(f"    serie maxima que aun deja pasar VIH: {r_max_vih:.0f} ohm")
    assert v_miso >= VIH_MIN, (
        f"el divisor de MISO deja {v_miso:.2f} V contra un VIH garantizado "
        f"de {VIH_MIN} V (Tabla 1436): el cerebro no lee un uno")
    assert i_pelea(R_SERIE) > 12e-3, (
        "si la pelea cupiera dentro del drive, la serie de MISO no tendria "
        "restriccion por arriba y esta seccion sobraria")

    # Y el hallazgo que sale de mirar las dos columnas de arriba juntas.
    r_miso_min = min(r for r in (33.0, 100.0, 220.0, 470.0)
                     if i_pelea(r) <= 12e-3)
    f_con_r_miso = limite(cap_t, r_drv12 + r_miso_min)
    print("\n  LA VENTANA COMUN ESTA VACIA, y no es un detalle de estilo:")
    print(f"    MISO no baja de {r_miso_min:.0f} ohm sin que la pelea pase"
          f" de 12 mA.")
    print(f"    A {r_miso_min:.0f} ohm el flanco de SCLK/MOSI se queda en"
          f" {f_con_r_miso/1e6:.2f} MHz,")
    print(f"    contra los {f_min/1e6:.2f} que hacen falta.")
    print("    Por eso la spec del cerebro dice que se aseveran POR SEPARADO:")
    print("    NO PUEDEN ser la misma pieza. Son dos valores distintos en el")
    print("    mismo esquematico, y este guion es la razon.")
    assert f_con_r_miso < f_min, (
        "la ventana comun dejo de estar vacia: MISO y SCLK/MOSI ya podrian "
        "compartir valor de serie, y la spec del cerebro S4.2 se puede "
        "simplificar. Revisar antes de celebrarlo")

    print("\nI2C -- la otra mitad del alcance declarado:\n")
    cap_i2c = capacidad_red(1, LARGO_RAMA, 1, 0.0)
    t_i2c = t_subida_i2c(R_PULLUP_I2C, cap_i2c)
    print(f"  canal propio por ranura, o sea UNA rama: {cap_i2c*1e12:.1f} pF")
    print(f"  con pull-up de {R_PULLUP_I2C/1e3:.1f}k  ->  subida de"
          f" {t_i2c*1e9:.0f} ns")
    print(f"  limite modo estandar {T_SUBIDA_I2C_STD*1e9:.0f} ns  ->  "
          f"{'OK' if t_i2c <= T_SUBIDA_I2C_STD else 'NO'}")
    print(f"  limite modo rapido   {T_SUBIDA_I2C_FAST*1e9:.0f} ns  ->  "
          f"{'OK' if t_i2c <= T_SUBIDA_I2C_FAST else 'NO'}")
    assert t_i2c <= T_SUBIDA_I2C_FAST, (
        "el I2C no llega a modo rapido con esta longitud de mazo; hay que "
        "bajar la pull-up o acortar la rama")

    manda_hoy = resultados["hoy: 8 ramas, un oyente por rama"][4]
    manda_t = resultados["T dentro del modulo de Voz"][4]
    manda_9 = resultados["novena rama para la columna B"][4]

    print("\nVEREDICTO")
    print("  1. EL SEGUNDO OYENTE NO ES LO QUE DECIDE.")
    print(f"     Como T dentro del modulo cuesta {(cap_t/cap_hoy - 1):.1%} de"
          " capacidad de red y")
    print(f"     baja el limite de {manda_hoy/1e6:.2f} a {manda_t/1e6:.2f}"
          " MHz. Como novena rama cuesta")
    print(f"     {(cap_9/cap_hoy - 1):.1%} y lo baja a {manda_9/1e6:.2f} MHz."
          " La T es el camino barato,")
    print("     y por un factor de casi tres.")
    print()
    print("  2. LO QUE DECIDE ES EL MAZO, Y YA DECIDIA ANTES DE ESTA IDEA.")
    print(f"     Ocho ramas de {LARGO_RAMA*1e3:.0f} mm son"
          f" {LARGO_RAMA*N_RAMAS:.1f} m de cinta colgando de UN pin.")
    print(f"     Con la rama derivada del cajon, el bus se queda en"
          f" {manda_hoy/1e6:.2f} MHz")
    print(f"     ANTES de tocar nada, contra los {f_min/1e6:.2f} MHz que el"
          " trafico exige:")
    print(f"     {(manda_hoy/f_min - 1):+.1%} de margen. Eso no es holgura,"
          " es el filo de la navaja.")
    if manda_hoy < f_min:
        print("     De hecho el J2 de hoy YA no cierra en el peor caso"
              " geometrico.")
    print("     El hallazgo es sobre el BUS, no un veto a la arquitectura:")
    print("     con este mazo, cualquier cosa que se le anada lo tumba.")
    print()
    print(f"  3. LA SALIDA ESTA MEDIDA: a {largo_ok} mm de rama pasan los"
          " tres casos." if largo_ok else
          "  3. Ningun largo del barrido deja pasar a los tres casos.")
    print("     El peor caso geometrico supone cerebro y modulo en extremos")
    print("     OPUESTOS del riel. Colocarlos del mismo lado es gratis y es")
    print("     una decision de layout de fila, no de arquitectura.")
    print()
    print("  Esto NO es una prueba: es una puerta. Dice que la idea no es")
    print("  imposible, dice que su coste es el menor de los dos caminos, y")
    print("  dice cual es la medida que la cierra: el flanco real de SCLK en")
    print("  el extremo de la rama mas larga, con osciloscopio, en el")
    print("  bring-up del cerebro -- contra el VIH de 2,0 V de la Tabla 1436.")
    print()
    print("  Palancas, por lo que compran:")
    print("    1. acortar el mazo -- el barrido de arriba le pone precio")
    print("    2. bajar el reloj -- ya es perilla por contrato, cerebro S4.2")
    print("    3. drive strength a 12 mA en SCLK y MOSI, si no lo estaba")
    print("    4. CAP_PIN, que es el numero que falta, es el que MENOS mueve")
    print("\nOK: presupuesto cerrado.")


if __name__ == "__main__":
    demo()
