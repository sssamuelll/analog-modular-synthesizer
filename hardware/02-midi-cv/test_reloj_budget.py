"""El contrato del arbol de relojes DEL HUB, escrito antes que el guion.

    python hardware/02-midi-cv/test_reloj_budget.py

De donde sale este archivo: el #150. Se abrio el 2026-08-21 contra el RP2350
--`clk_sys` con dos duenos que no se conocian-- y sus hechos se murieron con
ese chip. La tesis no: el 2026-09-08, en el pase a embassy-stm32 (#250, PR
#349), la misma forma de problema reaparecio con otro reloj. Hoy vive como un
comentario en `software/nucleo/fw/src/usb.rs:41-53` y no hay guion que lo
vigile.

Un grep de `PLL` en todo el repo devuelve UN solo sitio, y es ese comentario.
Este repo tiene presupuestos ejecutables para el ancho del panel, la corriente
por riel, la afinacion, las masas y el caudal de la PSRAM. Para el reloj del
cerebro, nada.

Lo que este contrato fija, y por que cada cosa:

  * QUE NINGUN CONSUMIDOR PIDA UNA FUENTE QUE EL CHIP NO LE DA. El RM da,
    peritferico a periferico, la lista cerrada de su MUX de reloj de kernel
    (RM0486 Rev 4, Tabla 72, p. 445-453). El LTDC solo ve ic16; el PHY de USB
    solo ve ic15; el I2C1 ve ic10 o ic15. Un arbol que le enchufe al LTDC un
    ic15 es un arbol que no existe en el silicio, y es el error facil de
    cometer leyendo la "asignacion tipica" de PLL de la p. 435 como si fuera
    vinculante. NO LO ES: cada ICx lleva su propio MUX de cuatro vias que
    elige cualquier PLL (RCC_ICxCFGR, ICxSEL[1:0], p. 507).

  * QUE LA ARITMETICA VIVA EN UN SOLO SITIO. Es la leccion de
    `sram_budget.py`, que sumaba cuatro costos en una funcion y dos a mano en
    el print de al lado, y publicaba techos inflados en 600 000 B. Aqui la
    cadena FREF -> DIVM -> DIVN -> PDIV1/2 -> ICINT se calcula UNA vez, y el
    contrato lo comprueba como identidad: la frecuencia que el guion resuelve
    para un consumidor, recorrida hacia atras con su propia aritmetica, tiene
    que dar exactamente la que se le pidio.

  * QUE LOS LIMITES SALGAN DE LA HOJA Y NO DEL DIBUJO. El bloque de la p. 436
    del RM rotula la entrada "5 to 1200 MHz". La hoja del producto (DS14791
    Rev 10, Tabla 58, p. 166) dice otra cosa y es la que manda:
    fPLL_IN 5..64 MHz, fPFD 5..50 MHz, fVCO 800..3200 MHz,
    fFOUTPOSTDIV 16,32..3200 MHz. `usb.rs:47` cita el rotulo del dibujo
    (5..1200) al lado de un numero que es el PFD. Las dos cifras pasan, pero
    la restriccion que se nombra no es la que se comprueba, y el HSI de
    64 MHz esta JUSTO en el techo de fPLL_IN: no hay ni un MHz de aire.

  * QUE LO QUE NO ES ENTERO SE PAGUE. La misma tabla da el precio del modo
    fraccionario: jitter integrado (10 kHz-20 MHz) de +-6,6 ps RMS max en
    entero contra +-11,9 ps en fracN. El papel de la interfaz de audio tiene
    una seccion titulada "El reloj, que ningun censo de pines ve" y ese
    numero no aparece en ella. Aqui el guion tiene que CALCULAR si una
    frecuencia de audio exacta sale en entero, no suponerlo.

  * QUE LO QUE NO ESTA ELEGIDO NO SE INVENTE. No hay panel elegido (el reloj
    de pixel es "clase ~33 MHz -- ESTIMADO hasta pieza", pantalla-motor
    sec.5), no hay codec elegido, y no hay cristal HSE decidido en ningun
    papel. Tres huecos reales: el censo sale en 2, no en 0.

  * QUE LOS OTROS TRES CHIPS NO SE DEN POR RESUELTOS. La firma del 2026-09-09
    puso cuatro N657. De los cuatro, solo el hub y la Voz tienen su lista de
    perifericos enumerada, y las dos viven en `micro_budget.py` (la del hub
    desde la l. 1115). El mago y el cuarto no tienen censo de pines todavia,
    asi que sus arboles no se pueden calcular; y sacarle el audio al hub sin
    decir donde cae es como se pierden los hercios entre papeles.

  * QUE LA MESA SEA LA DEL HUB. `micro_budget.py` lleva DOS censos de pines
    en el mismo archivo: el de la Voz arriba y el del hub desde la l. 1115.
    La primera version de este contrato se escribio contra el de la Voz --
    con las capturas del afinado y los tres DAC de CV dentro-- y cerro con
    numeros que no eran de este chip. El aserto de la mesa esta para que eso
    no vuelva a pasar en silencio.

Este test puede quedar rojo por el aserto del cuarto chip o por el del panel
aun con el guion bien escrito: eso no se arregla poniendo un numero, se lleva
a Samuel.
"""
from __future__ import annotations

import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "..", "tools"))
import reloj_budget as rb                                   # noqa: E402
from canario import borde_rojo                              # noqa: E402


# --- los limites: de la hoja, no del dibujo ---------------------------------

def test_los_limites_de_la_PLL_salen_de_la_hoja_del_producto() -> None:
    """DS14791 Rev 10, Tabla 58, p. 166. NO el rotulo del bloque del RM.

    El bloque de la p. 436 del RM dice "5 to 1200 MHz" en la entrada. La
    hoja dice fPLL_IN 5..64. Si alguien vuelve a poner 1200 aqui, esta
    citando un dibujo por encima de una tabla de caracterizacion."""
    assert rb.PLL_IN_HZ == (5e6, 64e6), (
        "fPLL_IN son 5..64 MHz (DS14791 Rev 10, Tabla 58, p. 166); los "
        "1200 MHz del bloque de la p. 436 del RM son otra cosa")
    assert rb.PFD_HZ == (5e6, 50e6)
    assert rb.VCO_HZ == (800e6, 3200e6)
    assert rb.FOUT_HZ == (16.32e6, 3200e6)


def test_los_rangos_de_los_divisores_son_los_de_los_registros() -> None:
    """DIVM[5:0], DIVN[11:0], PDIV1/2[2:0] y ICxINT[7:0].

    ICxINT divide por el valor+1: 0x00 es /1 y 0xFF es /256 (RM0486 Rev 4,
    RCC_IC1CFGR, p. 507-508). Escribir (0, 255) aqui seria copiar el campo
    en vez del divisor."""
    assert rb.DIVM == (1, 63)
    assert rb.DIVN_ENTERO == (16, 640)
    assert rb.DIVN_FRAC == (20, 320)
    assert rb.PDIV == (1, 7)
    assert rb.ICINT == (1, 256)
    assert rb.N_PLL == 4, "el N657 trae cuatro PLL (RM sec.14.6.5, p. 435)"


def test_el_HSI_esta_justo_en_el_techo_de_entrada_de_la_PLL() -> None:
    """64 MHz de HSI contra 64 MHz de fPLL_IN max: cero aire.

    No es una curiosidad. El firmware que hoy corre alimenta la PLL4 del PHY
    desde el HSI, y ese es el unico sitio del diseno donde una fuente se
    sienta EXACTAMENTE en su limite. El guion tiene que declararlo."""
    assert rb.HSI_HZ == rb.PLL_IN_HZ[1], (
        "si el HSI deja de estar en el techo de fPLL_IN, o cambio la hoja o "
        "cambio la fuente; en los dos casos hay que releer usb.rs")
    assert rb.HSI_AL_BORDE is True


# --- el MUX: nadie pide una fuente que el silicio no le da -------------------

def test_cada_consumidor_declara_el_MUX_que_el_RM_le_da() -> None:
    """Tabla 72. Las que mas duelen si se copian mal, comprobadas."""
    assert rb.CONSUMIDORES["OTGPHY1"].mux == ("ic15",), (
        "el PHY solo ve ic15 entre las salidas de PLL (RM Tabla 72, p. 449); "
        "hse_div2_ck y per_ck no son ICs")
    assert rb.CONSUMIDORES["LTDC"].mux == ("ic16",), (
        "el LTDC solo ve ic16 (RM Tabla 72, p. 448)")
    assert set(rb.CONSUMIDORES["SPI1"].mux) == {"ic8", "ic9"}
    assert set(rb.CONSUMIDORES["SPI4"].mux) == {"ic9", "ic14"}
    assert set(rb.CONSUMIDORES["SPI6"].mux) == {"ic8", "ic9"}
    assert set(rb.CONSUMIDORES["XSPI1"].mux) == {"ic3", "ic4"}
    assert set(rb.CONSUMIDORES["I2C1"].mux) == {"ic10", "ic15"}


# --- la mesa: los residentes del HUB, no los del vecino ----------------------

def test_la_mesa_sale_del_censo_de_pines_DEL_HUB() -> None:
    """`micro_budget.py` lleva DOS censos y el primero no es el del hub.

    El de arriba reparte la Voz (capturas de afinado, tres DAC de CV en
    SPI1-3, el crosspoint). El del hub empieza en `micro_budget.py:1115` y
    su base es otra: "6 ranuras J2 en SPI1-6, pantalla al LTDC en 24 bits,
    PSRAM del framebuffer, tronco I2C del descubrimiento, pedal".

    Un arbol de relojes construido sobre la lista del vecino cierra con
    numeros que no son de este chip. Que este aserto exista es la cicatriz
    de haberlo hecho asi la primera vez."""
    assert rb.MESA_RECONCILIADA is True, (
        "la mesa tiene que salir del censo del hub (micro_budget.py:1115 y "
        "siguientes), no del censo de la Voz que vive en el mismo archivo")
    assert rb.CENSO_FUENTE == "micro_budget.py:1115"


def test_las_seis_ranuras_del_J2_son_seis_maestros_SPI() -> None:
    """J2 punto a punto D3: "6 maestros SPI de hardware -- 4 activas + 2 de
    repuesto rapido" (citado en micro_budget.py:1122-1124).

    En el hub los seis SPI son del J2. Los tres DAC de CV que el censo de la
    Voz sienta en SPI1-3 NO estan aqui: el hub habla con los modulos, no
    mueve tensiones."""
    j2 = [n for n, c in rb.CONSUMIDORES.items() if c.trabajo == "J2"]
    assert sorted(j2) == ["SPI1", "SPI2", "SPI3", "SPI4", "SPI5", "SPI6"]


def test_las_capturas_de_afinado_no_son_del_hub() -> None:
    """Los 16 cronometros de TIM son del afinado, y el afinado vive en la
    Voz (`autotune_budget.py`, y micro_budget "SITIO 1 -- EL MODULO DE
    VOZ"). Cobrarselos al hub es contar dos veces el mismo trabajo."""
    for tim in ("TIM1", "TIM2", "TIM3", "TIM4", "TIM5"):
        assert tim not in rb.CONSUMIDORES, (
            f"{tim} entra por las capturas del afinado, que son de la Voz")


def test_el_SAI_dejo_de_ser_del_hub_cuando_se_firmo_A10() -> None:
    """El censo de pines todavia ofrece un "escenario + audio (A-6 en el
    hub)". Ese escenario murio el 2026-09-09: el acta A-10 le dio a la
    interfaz de audio su propio N657.

    El hub puede acabar teniendo un codec de cabecera, pero eso hoy no esta
    escrito en ningun papel: no se cobra por si acaso."""
    assert rb.AUDIO_EN_EL_HUB is False
    assert "SAI1" not in rb.CONSUMIDORES


def test_los_interruptores_mueven_de_verdad_el_reparto() -> None:
    """Un interruptor que no cambia el resultado es prosa, no un parametro.

    RGMII sigue condicionado a D9, que esta en cuarentena, asi que el censo
    lo cobra por defecto (conservador). Apagarlo tiene que soltar su IC."""
    con = rb.resuelve(rgmii=True).asignaciones
    sin = rb.resuelve(rgmii=False).asignaciones
    assert "ETH1" in con and "ETH1" not in sin, (
        "el interruptor de RGMII no mueve la mesa: o no se usa, o el "
        "reparto lo ignora")


def test_un_IC_compartido_hereda_el_techo_mas_bajo() -> None:
    """La consecuencia que se escapa al mirar la Tabla 72 fila a fila.

    SPI1/2/3/6 tienen techo de kernel 200 MHz y SPI4/5 lo tienen en 133
    (RM Tabla 72, p. 451). Los seis son maestros del J2 y los seis pueden
    sentarse en ic9. El dia que se sienten juntos, el techo del grupo es
    133, no 200 -- y nada en la tabla lo dice: sale del reparto."""
    sol = rb.resuelve()
    por_ic: dict[str, list[str]] = {}
    for nombre, asig in sol.asignaciones.items():
        por_ic.setdefault(asig.ic, []).append(nombre)
    for ic, quienes in por_ic.items():
        techo = min(rb.CONSUMIDORES[q].techo_hz for q in quienes)
        f = sol.asignaciones[quienes[0]].f_hz
        assert f <= techo, (
            f"{ic} corre a {f} Hz y lo comparten {sorted(quienes)}, cuyo "
            f"techo comun es {techo} Hz (el mas bajo manda)")


def test_la_solucion_no_le_da_a_nadie_un_IC_fuera_de_su_MUX() -> None:
    """El error facil: leer la 'asignacion tipica' de PLL de la p. 435 como
    si mandara, y repartir por PLL en vez de por IC."""
    sol = rb.resuelve()
    for nombre, asig in sol.asignaciones.items():
        assert asig.ic in rb.CONSUMIDORES[nombre].mux, (
            f"a {nombre} se le asigno {asig.ic}, que no esta en su MUX "
            f"{rb.CONSUMIDORES[nombre].mux} (RM Tabla 72)")


def test_un_IC_solo_puede_tener_una_frecuencia() -> None:
    """Es la restriccion que hace de esto un problema y no una lista.

    Los seis maestros del J2 caben todos en ic9 (SPI1,2,3,6 lo ven por
    ic8/ic9; SPI4,5 por ic9/ic14), y el ADC12 comparte ic7/ic8 con ellos.
    Dos consumidores en el mismo IC reciben el MISMO hercio."""
    sol = rb.resuelve()
    por_ic: dict[str, set[float]] = {}
    for nombre, asig in sol.asignaciones.items():
        por_ic.setdefault(asig.ic, set()).add(asig.f_hz)
    for ic, frecuencias in por_ic.items():
        assert len(frecuencias) == 1, (
            f"{ic} sale con {len(frecuencias)} frecuencias distintas "
            f"({sorted(frecuencias)}): un ICx es un solo divisor, no uno "
            f"por cliente (RM0486 Rev 4, RCC_ICxCFGR, p. 507)")


def test_no_se_usan_mas_de_cuatro_PLL() -> None:
    """El chip trae cuatro. Un arbol que necesite cinco no es un arbol."""
    sol = rb.resuelve()
    assert len(sol.plls) <= rb.N_PLL, (
        f"la solucion pide {len(sol.plls)} PLL y el N657 tiene {rb.N_PLL}")


# --- la aritmetica: una sola cuenta -----------------------------------------

def test_la_frecuencia_resuelta_se_reproduce_con_la_aritmetica_del_guion() -> None:
    """La identidad, no la cifra. Es la leccion de `sram_budget.py`.

    Si alguien escribe en cualquier sitio una division a mano en vez de
    llamar a la cadena del guion, esta identidad se rompe sola."""
    sol = rb.resuelve()
    for nombre, asig in sol.asignaciones.items():
        cfg = sol.plls[asig.pll]
        fout = rb.pll_out_hz(cfg)
        assert rb.ic_hz(fout, asig.icint) == asig.f_hz, (
            f"{nombre}: el guion dice {asig.f_hz} Hz pero su propia cadena "
            f"da {rb.ic_hz(fout, asig.icint)} Hz. Hay dos cuentas de lo mismo")


def test_ninguna_PLL_que_el_guion_emite_es_ilegal() -> None:
    """El solucionador no puede parir lo que la guarda rechazaria."""
    sol = rb.resuelve()
    for i, cfg in enumerate(sol.plls):
        razones = rb.pll_ilegal(cfg)
        assert razones == [], (
            f"PLL{i} de la solucion es ilegal por {razones}: el buscador y "
            f"el juez no estan usando la misma funcion")


def test_la_legalidad_se_juzga_en_un_solo_sitio() -> None:
    """Cada limite de la Tabla 58 tiene que poder poner roja una config.

    Si un limite esta declarado y nadie lo mira, es adorno."""
    base = rb.CFG_PHY_DEL_FIRMWARE
    assert rb.pll_ilegal(base) == []
    # PFD por encima de 50 MHz: DIVM 1 deja el PFD en 64.
    assert any("PFD" in r for r in rb.pll_ilegal(base._replace(divm=1)))
    # VCO por debajo de 800: DIVN 16 sobre un FREF de 16 MHz da 256 MHz.
    assert any("VCO" in r for r in rb.pll_ilegal(base._replace(divn=16)))
    # DIVN fuera del rango del registro.
    assert any("DIVN" in r for r in rb.pll_ilegal(base._replace(divn=641)))


def test_el_arbol_reproduce_el_que_el_firmware_ya_corre() -> None:
    """El ancla. `software/nucleo/fw/src/usb.rs:46-50`:

        hsi_ck  = 64 MHz
        FREF    = 64 / DIVM 4  = 16 MHz
        FVCO    = 16 * DIVN 60 = 960 MHz
        pll4_ck = 960 / 2 / 1  = 480 MHz
        ic15_ck = 480 / 20     = 24 MHz

    Un modelo del arbol que no reproduzca el arbol que ya enlaza y arranca
    no es un modelo del arbol: es una hoja de calculo bonita."""
    cfg = rb.CFG_PHY_DEL_FIRMWARE
    assert cfg.f_in_hz == rb.HSI_HZ
    assert (cfg.divm, cfg.divn, cfg.pdiv1, cfg.pdiv2) == (4, 60, 2, 1)
    assert rb.pfd_hz(cfg) == 16e6
    assert rb.vco_hz(cfg) == 960e6
    assert rb.pll_out_hz(cfg) == 480e6
    assert rb.ic_hz(rb.pll_out_hz(cfg), 20) == 24e6


# --- el PHY: tres valores legales y punto ------------------------------------

def test_la_referencia_del_PHY_solo_admite_tres_valores() -> None:
    """RM0486 Rev 4, USBPHYC_CR.FSEL, p. 3929. Citado ya en usb.rs:41-42."""
    assert set(rb.PHY_REF_LEGALES_HZ) == {19.2e6, 20e6, 24e6}
    assert rb.CONSUMIDORES["OTGPHY1"].forzada is True


def test_la_guarda_muerde_si_la_referencia_del_PHY_se_sale() -> None:
    """La mutacion que pide el #150: mover el divisor del PHY fuera de
    19,2/20/24 y ver que falla. Por biseccion, no a mano: un valor frontera
    escrito a mano se queda viejo el dia que la cadena se mueva."""
    p = rb.parametros()
    borde_rojo(rb.guarda_reloj, p, "phy_ref_hz", 24e6, 40e6, "PHY")


def test_la_guarda_muerde_si_un_consumidor_pasa_de_su_techo() -> None:
    """El techo de kernel de la Tabla 72 no es una sugerencia.

    El LTDC lo tiene en 86 MHz, y el papel de la pantalla habla de un techo
    de 150 Mpx/s (DS sec.3.28): son dos cosas distintas y la que ata el
    arbol es la de 86."""
    assert rb.CONSUMIDORES["LTDC"].techo_hz == 86e6
    p = rb.parametros()
    borde_rojo(rb.guarda_reloj, p, "ltdc_px_hz", 30e6, 200e6, "techo")


# --- lo exacto y lo que cuesta ----------------------------------------------

def test_las_dos_familias_de_audio_salen_del_HSI_sin_cristal() -> None:
    """CALCULADO, no supuesto, y contra la intuicion.

    La premisa comoda era "un reloj de audio exacto necesita cristal". La
    busqueda dice que no: el HSI de 64 MHz llega a las dos familias en modo
    entero, porque el DIVM admite factores de 5 (64/5 = 12,8 MHz de PFD es
    perfectamente legal) y de ahi sale el 125 que hace falta.

    Si esta busqueda se vacia, el arbol cambia de conclusion y el papel del
    audio se queda sin su parrafo: eso se lleva a Samuel, no se parchea."""
    for f_mclk in (12.288e6, 24.576e6, 49.152e6):      # 48 kHz x256, x512, x1024
        cfg = rb.busca_entero(rb.HSI_HZ, f_mclk)
        assert cfg is not None, f"{f_mclk} deberia salir en entero del HSI"
        assert rb.pll_ilegal(cfg) == []
    for f_mclk in (11.2896e6, 22.5792e6):              # 44,1 kHz x256, x512
        assert rb.busca_entero(rb.HSI_HZ, f_mclk) is not None


def test_el_44k1_a_1024_fs_no_sale_en_entero_y_eso_restringe_al_codec() -> None:
    """El unico hercio de audio que el oscilador interno no alcanza.

    45,1584 MHz = 1024 x 44,1 kHz. Cero soluciones enteras desde el HSI, con
    los cuatro divisores barridos enteros y el VCO en 800..3200 MHz.

    No es una curiosidad aritmetica: es una RESTRICCION DE COMPRA sobre una
    pieza que nadie ha elegido. Un codec que exija MCLK = 1024 fs y tenga
    que dar 44,1 kHz obliga a una de tres: cristal de audio en HSE, modo
    fraccionario (y su jitter, +-11,9 ps contra +-6,6), o renunciar al
    44,1 kHz. El papel del audio no dice cual, porque no sabia que hubiera
    que elegir."""
    assert rb.busca_entero(rb.HSI_HZ, 45.1584e6) is None, (
        "si esto encuentra solucion, la restriccion sobre el codec no "
        "existe y hay que reescribir la conclusion del guion")
    assert rb.MCLK_1024FS_44K1_HZ == 45.1584e6
    assert rb.CODEC_ELEGIDO is False
    # Desde un cristal de la familia si sale, y esa es la salida declarada.
    cfg = rb.busca_entero(22.5792e6, 45.1584e6)
    assert cfg is not None
    assert rb.pll_ilegal(cfg) == []


def test_el_modo_fraccionario_esta_declarado_con_su_precio() -> None:
    """DS14791 Rev 10, Tabla 58, p. 166: jitter integrado 10 kHz-20 MHz."""
    assert rb.JITTER_ENTERO_PS == 6.6
    assert rb.JITTER_FRAC_PS == 11.9
    assert rb.JITTER_FRAC_PS > rb.JITTER_ENTERO_PS


# --- los huecos: lo que no esta elegido no se inventa ------------------------

def test_el_reloj_de_pixel_sigue_siendo_ESTIMADO_porque_no_hay_panel() -> None:
    """pantalla-motor sec.5: "clase ~33 MHz -- ESTIMADO hasta pieza".

    Un guion que publique un reloj de pixel exacto sin panel elegido esta
    fabricando el dato mas caro del arbol."""
    assert rb.PANEL_ELEGIDO is False
    assert rb.LTDC_PX_ESTIMADO is True


def test_el_cristal_HSE_no_esta_decidido_en_ningun_papel() -> None:
    """El firmware corre el PHY desde el HSI. Nadie ha escrito si el hub
    lleva cristal, ni de cuanto, y hoy no hay ningun consumidor suyo que lo
    exija: el hercio que obligaria a cristal es de audio, y el audio se fue
    al cuarto chip. Queda sin duena igual -- el HSE tambien decide el
    arranque, el CSS y la deriva, y de eso no se ha escrito nada."""
    assert rb.HSE_HZ is None


def test_los_otros_tres_chips_no_tienen_arbol_y_el_guion_lo_dice() -> None:
    """La firma del 2026-09-09 puso cuatro N657 (acta en el papel del hub
    sec.0). El mago y el cuarto no tienen censo de pines, y la Voz tiene el
    suyo pero no un arbol: ninguno de los tres se calcula aqui."""
    assert rb.ACTA_CUATRO_CHIPS == "2026-09-09"
    assert set(rb.ARBOLES_PENDIENTES) == {"voz", "mago", "interfaz-audio"}


def test_el_censo_sale_hueco_mientras_falten_las_piezas() -> None:
    """Exit 2, no 0. Un hueco visible vale mas que un fallo invisible."""
    assert rb.main() == 2, (
        "si esto sale 0, o se eligio panel, codec y cristal, o el guion "
        "esta cerrando un hueco que sigue abierto")


def _tests():
    return [(n, f) for n, f in sorted(globals().items())
            if n.startswith("test_") and callable(f)]


def main() -> int:
    fallos = 0
    for nombre, f in _tests():
        try:
            f()
            print(f"  ok    {nombre}")
        except AssertionError as e:
            fallos += 1
            print(f"  FALLA {nombre}\n        {e}")
    print(f"\n{len(_tests()) - fallos}/{len(_tests())} verdes")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
