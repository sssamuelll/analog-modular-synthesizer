#!/usr/bin/env python3
"""El arbol de relojes del hub: una mesa que cabe no es una placa sellada.

    python hardware/02-midi-cv/reloj_budget.py

El #150 perdio el RP2350, pero no el problema: varias funciones piden relojes
al mismo silicio. El unico arbol programado esta en software/nucleo/fw/src/
usb.rs. Este censo conserva su PLL4 y prueba si la mesa del hub cabe a su
lado. La salida distingue FALLO de reparto, HUECO de pieza y cuenta exacta.

LA MESA SALE DEL CENSO DEL HUB

  micro_budget.py:1115, _demandas_hub: seis maestros J2 en SPI1-6, LTDC de
  24 bits, PSRAM del framebuffer por XSPI1, descubrimiento y tactil en I2C1,
  pedal y entrada del mux de perillas en ADC12. Se suman USB con sus pines
  dedicados y los alimentadores SYS_*. RGMII sigue condicionado a D9 EN
  CUARENTENA: se cobra por defecto; resuelve(rgmii=False) libera ETH1/ic12.

  Las capturas TIM1-5 del afinado y los tres DAC de CV pertenecen a la Voz.
  A-10, 2026-09-09, le dio un cuarto N657 a la interfaz de audio: SAI1 sale
  del hub. El escenario + audio de micro_budget.py:1289 sigue obsoleto.

UNA PLL NO ES UN PERIFERICO

  RM0486 Rev 4, p. 435 llama a su reparto "A typical allocation is:".
  Es una sugerencia. ICxSEL[1:0] elige cualquiera de las cuatro PLL para
  CADA IC (RM0486 Rev 4, RCC_ICxCFGR, p. 507). El comentario del #150 del
  2026-09-08 y usb.rs:53 leen una reserva donde el silicio trae un MUX.
  El LTDC no obliga a tomar PLL4: obliga a pasar por ic16 (Tabla 72, p. 448).
  El PHY pasa por ic15 (Tabla 72, p. 449). Pueden elegir PLL distintas.

  La escasez esta despues: un IC es UN divisor y tiene UN hercio para todos
  sus clientes. SPI1/2/3/6 ven ic8/ic9; SPI4/5, ic9/ic14 (RM0486 Rev 4,
  Tabla 72, p. 451-452). Los seis maestros J2 pueden compartir ic9: el techo
  comun es min(200, 200, 200, 133, 133, 200) = 133 MHz. Lo impone SPI4/5;
  es una consecuencia del reparto, no una fila adicional de la Tabla 72.
  El buscador prefiere compartir IC entre clientes del mismo trabajo y Hz,
  y luego busca salidas de PLL compartibles. No crea una PLL por cliente.

UNA SOLA CUENTA, Y QUE SEA EXACTA

  pfd_hz -> vco_hz -> pll_out_hz -> ic_hz implementan la cadena del RM0486
  Rev 4, p. 436-437 y 507-508. El barrido, la guarda y el informe usan esa
  misma cuenta con Fraction. Las divisiones inversas del buscador despejan
  el divisor; cada testigo se comprueba recorriendo la cadena hacia delante.

  Se barren DIVM, DIVN y ambos PDIV completos. Para cada salida, el unico
  ICINT posible para un objetivo exacto se despeja y se comprueba: esto es
  equivalente a probar todos los ICINT, sin repetir divisiones inutiles.
  Dos pares PDIV distintos cuentan como dos configuraciones, aunque tengan
  el mismo producto. El catalogo conserva su multiplicidad, no solo el Hz.

  Manda DS14791 Rev 10, Tabla 58, p. 166: fPLL_IN no es fPFD. El rotulo
  "5 to 1200 MHz" del dibujo del RM0486 Rev 4, p. 436 no sustituye a esa
  tabla. usb.rs:47 aplica aquel intervalo al resultado de DIVM. El HSI
  nominal esta en el techo de entrada: el censo no demuestra su tolerancia
  real ni convierte una razon racional exacta en precision de cristal.

LO QUE NO COMPRA EL CIERRE

  Pixel y codec del cuarto chip siguen sin pieza; HSE sigue sin decision.
  Los objetivos elegidos para probar convivencia son ESTIMADOS, no registros aprobados
  para el firmware. Un kernel SPI no es SCK; un kernel SAI no fija MCLK ni
  FS sin programar el SAI y conocer el codec. Tampoco son un ensayo de DMA,
  jitter de placa, fases, duty cycle ni caudal de memoria.

  La Tabla 58 caracteriza jitter a una pareja concreta de VCO/PFD. No se
  promete ese maximo para todas las configuraciones que encuentra el censo.
  La ausencia de una frecuencia entera se calcula; no demuestra por si sola
  que fracN la reproduzca EXACTAMENTE con su registro finito. Aqui no hay
  buscador fraccionario ni eleccion de cristal.

  HUECO VARIOS SIN RELOJ CENSADO: los 32 GPIO de micro_budget.py:1168 no
  enumeran kernels. Faltan las dos ranuras por USART sincrono (D3), MIDI DIN
  por UART, ESP32-S3 por UART, radio ESB por SPI o UART y PWM del backlight.
  Sin piezas ni frecuencias elegidas, no se inventan sus consumidores.
  Esta completo LO ENUMERADO, no el arbol completo del hub.

  Acta A-10 del 2026-09-09, hub S0/S6.2: NPU y camara del mago; interfaz de
  audio multicanal en un cuarto N657. Los otros tres arboles siguen pendientes.
  El barrido de audio sigue siendo util por compartir silicio: 44,1 kHz
  x1024 = 45,1584 MHz no sale entero del HSI. Esa restriccion corresponde al
  papel del CUARTO chip, que elegira codec; no reserva una PLL en el hub.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from functools import lru_cache
from typing import NamedTuple

# --- limites de caracterizacion, no los rotulos del dibujo -----------------
PLL_IN_HZ = (5_000_000, 64_000_000)  # DS14791 Rev 10, Tabla 58, p. 166: normal.
PLL_IN_SIGMA_HZ = (10_000_000, 64_000_000)  # DS14791 Rev 10, Tabla 58, p. 166.
PFD_HZ = (5_000_000, 50_000_000)  # DS14791 Rev 10, Tabla 58, p. 166: normal.
# Sigma-delta: PFD 10..min(50, fVCO/20) MHz (DS14791 Rev 10, Tabla 58, p. 166).
VCO_HZ = (800_000_000, 3_200_000_000)  # DS14791 Rev 10, Tabla 58, p. 166.
FOUT_HZ = (16_320_000, 3_200_000_000)  # DS14791 Rev 10, Tabla 58, p. 166.
DIVM = (1, 63)  # RM0486 Rev 4, p. 436, DIVM[5:0], RCC_PLLxCFGR1.
DIVN_ENTERO = (16, 640)  # RM0486 Rev 4, p. 437, DIVN[11:0].
DIVN_FRAC = (20, 320)  # RM0486 Rev 4, p. 437, DIVN[11:0] en modo fraccionario.
PDIV = (1, 7)  # RM0486 Rev 4, p. 436-437: cada POSTDIV[2:0]; arranque != rango.
ICINT = (1, 256)  # RM0486 Rev 4, p. 507-508: divisor = ICxINT[7:0] + 1.
N_PLL = 4  # RM0486 Rev 4, sec. 14.6.5, p. 435.
HSI_HZ = 64_000_000  # RM0486 Rev 4, sec. 14.6.2, p. 430; usb.rs:46.
HSI_AL_BORDE = HSI_HZ == PLL_IN_HZ[1]  # DERIVADO: margen nominal fPLL_IN.
HSE_HZ = None  # HUECO: ningun papel elige cristal para el hub (#150).
JITTER_ENTERO_TYP_PS = 2.7  # DS14791 Rev 10, Tabla 58, p. 166: +-ps RMS.
JITTER_ENTERO_PS = 6.6  # DS14791 Rev 10, Tabla 58, p. 166: max +-ps RMS.
JITTER_FRAC_PS = 11.9  # DS14791 Rev 10, Tabla 58, p. 166: max +-ps RMS.
JITTER_BANDA_HZ = (10_000, 20_000_000)  # DS14791 Rev 10, Tabla 58, p. 166.
JITTER_VCO_HZ = 3_200_000_000  # DS14791 Rev 10, Tabla 58, p. 166: condicion.
JITTER_PFD_HZ = 25_000_000  # DS14791 Rev 10, Tabla 58, p. 166: condicion.
PHY_REF_LEGALES_HZ = (19_200_000, 20_000_000, 24_000_000)  # RM0486 Rev 4, p. 3929, FSEL.
PHY_ICINT_FIRMWARE = 20  # software/nucleo/fw/src/usb.rs:80, Icint::Div20.
OTG_KERNEL_HZ = 60_000_000  # RM0486 Rev 4, Tabla 72, p. 449, phyclock.
MCLK_1024FS_44K1_HZ = 44_100 * 1024  # #150: DERIVADO, familia 44,1 kHz x1024.
PANEL_ELEGIDO = False  # HUECO: pantalla-motor S5/S8, panel sin hoja elegida.
CODEC_ELEGIDO = False  # HUECO: interfaz-audio S3.2; codec del CUARTO chip, acta A-10.
LTDC_PX_ESTIMADO = True  # pantalla-motor S5: clase ~33 MHz, ESTIMADO hasta pieza.
ACTA_CUATRO_CHIPS = "2026-09-09"  # hub S0/S6.2, firma y enmienda A-10.
ARBOLES_PENDIENTES = ("voz", "mago", "interfaz-audio")  # Acta, hub S0/S10.
MESA_RECONCILIADA = True  # Mesa del hub; excluye Voz y audio del cuarto chip.
CENSO_FUENTE = "micro_budget.py:1115"
AUDIO_EN_EL_HUB = False  # acta A-10, 2026-09-09.
VARIOS_SIN_RELOJ_CENSADO = (  # micro_budget.py:1137-1149, 32 GPIO en :1168-1175.
    "dos ranuras por USART sincrono (D3)",
    "MIDI DIN por UART",
    "ESP32-S3 por UART",
    "radio ESB por SPI o UART",
    "PWM del backlight del tactil",
)


class ConfigPLL(NamedTuple):
    f_in_hz: Fraction | int
    divm: int
    divn: int
    pdiv1: int
    pdiv2: int


class Consumidor(NamedTuple):
    mux: tuple[str, ...]
    techo_hz: int
    trabajo: str
    forzada: bool = False
    otras_fuentes: tuple[str, ...] = ()


class Asignacion(NamedTuple):
    pll: int  # Indice en sol.plls; el nombre fisico esta en sol.nombres_pll.
    ic: str
    icint: int  # Divisor efectivo; el registro ICxINT se escribe divisor - 1.
    f_hz: Fraction


class Solucion(NamedTuple):
    plls: list[ConfigPLL]
    asignaciones: dict[str, Asignacion]
    nombres_pll: tuple[str, ...]
    derivadas: dict[str, Fraction]


class Opcion(NamedTuple):
    cfg: ConfigPLL
    icint: int
    cantidad: int  # Configuraciones completas con esta misma salida de PLL.


CFG_PHY_DEL_FIRMWARE = ConfigPLL(
    HSI_HZ,  # software/nucleo/fw/src/usb.rs:71, Pllsel::Hsi.
    4,  # software/nucleo/fw/src/usb.rs:72, Plldivm::Div4.
    60,  # software/nucleo/fw/src/usb.rs:74, divn.
    2,  # software/nucleo/fw/src/usb.rs:75, Pllpdiv::Div2.
    1,  # software/nucleo/fw/src/usb.rs:76, Pllpdiv::Div1.
)

# mux SOLO contiene ICs. Las fuentes de bus y per_ck se declaran aparte.
# SYS_* son alimentadores, no filas de kernel de la Tabla 72. SYS_C y
# SYS_BUS2 deben habilitarse junto a SYS_BUS al seleccionar SYSSW (p. 440).
# No se les asigna carga de NPU ni de camara: solo se conserva la coherencia
# de ese selector comun. La CPU puede seguir en HSI por CPUSW independiente.
CONSUMIDORES = {
    "OTGPHY1": Consumidor(("ic15",), 48_000_000, "usb", True, ("hse_div2_ck", "per_ck", "hse_div2_osc_ck")),  # RM0486 Rev 4, Tabla 72, p. 449.
    "LTDC": Consumidor(("ic16",), 86_000_000, "pantalla", False, ("pclk5", "per_ck", "hsi_div_ck")),  # RM0486 Rev 4, Tabla 72, p. 448.
    "SPI1": Consumidor(("ic8", "ic9"), 200_000_000, "J2", False, ("pclk2", "per_ck", "msi_ck", "hsi_div_ck", "I2S_CKIN")),  # RM0486 Rev 4, Tabla 72, p. 451.
    "SPI2": Consumidor(("ic8", "ic9"), 200_000_000, "J2", False, ("pclk1", "per_ck", "msi_ck", "hsi_div_ck", "I2S_CKIN")),  # RM0486 Rev 4, Tabla 72, p. 451.
    "SPI3": Consumidor(("ic8", "ic9"), 200_000_000, "J2", False, ("pclk1", "per_ck", "msi_ck", "hsi_div_ck", "I2S_CKIN")),  # RM0486 Rev 4, Tabla 72, p. 451.
    "SPI4": Consumidor(("ic9", "ic14"), 133_000_000, "J2", False, ("pclk2", "per_ck", "msi_ck", "hsi_div_ck", "hse_ck")),  # RM0486 Rev 4, Tabla 72, p. 451.
    "SPI5": Consumidor(("ic9", "ic14"), 133_000_000, "J2", False, ("pclk2", "per_ck", "msi_ck", "hsi_div_ck", "hse_ck")),  # RM0486 Rev 4, Tabla 72, p. 451.
    "SPI6": Consumidor(("ic8", "ic9"), 200_000_000, "J2", False, ("pclk4", "per_ck", "msi_ck", "hsi_div_ck", "I2S_CKIN")),  # RM0486 Rev 4, Tabla 72, p. 452.
    "XSPI1": Consumidor(("ic3", "ic4"), 200_000_000, "framebuffer", False, ("hclk5", "per_ck")),  # RM0486 Rev 4, Tabla 72, p. 453.
    "ETH1": Consumidor(("ic12",), 125_000_000, "RGMII", False, ("sys_bus2_ck", "per_ck", "hse_ck")),  # RM0486 Rev 4, Tabla 72, p. 446, ETH1CLKSEL; D9 EN CUARENTENA, cobrado por defecto.
    "ADC12": Consumidor(("ic7", "ic8"), 125_000_000, "pedal", False, ("hclk1", "per_ck", "msi_ck", "hsi_div_ck", "I2S_CKIN", "timg_ck")),  # RM0486 Rev 4, Tabla 72, p. 445; tambien entrada del mux de perillas.
    "I2C1": Consumidor(("ic10", "ic15"), 100_000_000, "descubrimiento", False, ("pclk1", "per_ck", "msi_ck", "hsi_div_ck")),  # RM0486 Rev 4, Tabla 72, p. 447; tactil comparte bus.
    "SYS_BUS": Consumidor(("ic2",), 400_000_000, "bus"),  # RM0486 Rev 4, p. 440-442 y Tabla 72, p. 445, sys_bus_ck.
    "SYS_C": Consumidor(("ic6",), 1_000_000_000, "bus"),  # RM0486 Rev 4, p. 440-442 y Tabla 72, p. 449; alimentador, NPU fuera.
    "SYS_BUS2": Consumidor(("ic11",), 200_000_000, "bus"),  # RM0486 Rev 4, p. 440-442 y Tabla 72, p. 449, sys_bus2_ck.
    "OTG1": Consumidor((), OTG_KERNEL_HZ, "usb", True, ("phyclock",)),  # RM0486 Rev 4, Tabla 72, p. 449; NO recibe los 24 MHz del PHY.
}

CLAVES = {
    "OTGPHY1": "phy_ref_hz", "LTDC": "ltdc_px_hz",
    "SPI1": "spi1_kernel_hz", "SPI2": "spi2_kernel_hz", "SPI3": "spi3_kernel_hz",
    "SPI4": "spi4_kernel_hz", "SPI5": "spi5_kernel_hz", "SPI6": "spi6_kernel_hz",
    "XSPI1": "xspi1_kernel_hz",
    "ETH1": "eth1_kernel_hz", "ADC12": "adc12_kernel_hz", "I2C1": "i2c1_kernel_hz",
    "SYS_BUS": "sys_bus_hz", "SYS_C": "sys_c_hz", "SYS_BUS2": "sys_bus2_hz",
}
SYS_BUS_ESTIMADO_HZ = 200_000_000  # Conserva objetivo de bus; no depende del afinado de la Voz.
J2_KERNEL_ESTIMADO_HZ = 100_000_000  # Conserva objetivo J2, ahora para seis maestros; hub S2.2, clase 34,5 MHz con SCK/timing pendientes.
HPRE_DIV = 1  # ESTIMADO de reparto: hclk = sys_bus; RM0486 Rev 4, p. 440-442.
PPRE_DIV = 2  # ESTIMADO de reparto: APB a media frecuencia; RM0486 Rev 4, p. 442.


def _exacto(valor) -> Fraction:
    # Un float externo se interpreta como su decimal escrito. Dentro no hay
    # floats: ni epsilons ni tolerancias para que una frecuencia quepa.
    return Fraction(str(valor)) if isinstance(valor, float) else Fraction(valor)


def pfd_hz(cfg: ConfigPLL) -> Fraction:
    return _exacto(cfg.f_in_hz) / _exacto(cfg.divm)


def vco_hz(cfg: ConfigPLL) -> Fraction:
    return pfd_hz(cfg) * _exacto(cfg.divn)


def pll_out_hz(cfg: ConfigPLL) -> Fraction:
    return vco_hz(cfg) / _exacto(cfg.pdiv1) / _exacto(cfg.pdiv2)


def ic_hz(fout, icint) -> Fraction:
    """Division exacta; icint es el divisor, NO el campo codificado."""
    return _exacto(fout) / _exacto(icint)


def _en_rango(valor, limites) -> bool:
    return limites[0] <= valor <= limites[1]


def pll_ilegal(cfg: ConfigPLL) -> list[str]:
    """Juez del modo ENTERO. Los limites fracN se declaran, no se simulan.

    Incluso un divisor nulo devuelve razones, nunca ZeroDivisionError. No
    se evalua una etapa si sus registros no permiten calcularla.
    """
    razones = []
    if not _en_rango(cfg.f_in_hz, PLL_IN_HZ):
        razones.append(f"fPLL_IN fuera de {PLL_IN_HZ} Hz")
    registros = (("DIVM", cfg.divm, DIVM), ("DIVN", cfg.divn, DIVN_ENTERO),
                 ("PDIV1", cfg.pdiv1, PDIV), ("PDIV2", cfg.pdiv2, PDIV))
    for nombre, valor, limites in registros:
        if _exacto(valor).denominator != 1 or not _en_rango(valor, limites):
            razones.append(f"{nombre} fuera del rango entero {limites}")
    if cfg.divm > 0:
        if not _en_rango(pfd_hz(cfg), PFD_HZ):
            razones.append(f"PFD fuera de {PFD_HZ} Hz")
        if not _en_rango(vco_hz(cfg), VCO_HZ):
            razones.append(f"VCO fuera de {VCO_HZ} Hz")
        if cfg.pdiv1 > 0 and cfg.pdiv2 > 0:
            if not _en_rango(pll_out_hz(cfg), FOUT_HZ):
                razones.append(f"FOUTPOSTDIV fuera de {FOUT_HZ} Hz")
    return razones


@lru_cache(maxsize=None)
def _catalogo_entero(f_in: Fraction) -> dict[Fraction, tuple[ConfigPLL, int]]:
    """Todas las salidas legales, con testigo y numero de configuraciones.

    Las podas PFD/VCO solo evitan probar descendientes imposibles. TODO
    candidato emitido pasa ademas por pll_ilegal(), el mismo juez de guarda.
    El cache contiene datos del silicio, nunca soluciones mutables del hub.
    """
    catalogo = {}
    if not _en_rango(f_in, PLL_IN_HZ):
        return catalogo
    for divm in range(DIVM[0], DIVM[1] + 1):
        base = ConfigPLL(f_in, divm, DIVN_ENTERO[0], PDIV[0], PDIV[0])
        if not _en_rango(pfd_hz(base), PFD_HZ):
            continue
        for divn in range(DIVN_ENTERO[0], DIVN_ENTERO[1] + 1):
            base = base._replace(divn=divn)
            if not _en_rango(vco_hz(base), VCO_HZ):
                continue
            for pdiv1 in range(PDIV[0], PDIV[1] + 1):
                for pdiv2 in range(PDIV[0], PDIV[1] + 1):
                    cfg = base._replace(pdiv1=pdiv1, pdiv2=pdiv2)
                    if pll_ilegal(cfg):
                        continue
                    fout = pll_out_hz(cfg)
                    anterior, cantidad = catalogo.get(fout, (cfg, 0))
                    catalogo[fout] = (anterior, cantidad + 1)
    return catalogo


def _divisor_ic(fout: Fraction, objetivo: Fraction) -> int | None:
    if objetivo <= 0:
        return None
    divisor = fout / objetivo  # Inversa para buscar; no otra cadena de reloj.
    if divisor.denominator != 1 or not _en_rango(divisor, ICINT):
        return None
    entero = int(divisor)
    assert ic_hz(fout, entero) == objetivo, "el testigo IC no reproduce su objetivo"
    return entero


@lru_cache(maxsize=None)
def _opciones_enteras(f_in: Fraction, objetivo: Fraction) -> tuple[Opcion, ...]:
    opciones = []
    for fout, (cfg, cantidad) in _catalogo_entero(f_in).items():
        divisor = _divisor_ic(fout, objetivo)
        if divisor is not None:
            opciones.append(Opcion(cfg, divisor, cantidad))
    return tuple(opciones)


def cuenta_enteras(f_in, f_obj) -> int:
    """Cuenta tuplas completas, incluidos PDIV1/2 ordenados e ICINT."""
    return sum(o.cantidad for o in _opciones_enteras(_exacto(f_in), _exacto(f_obj)))


def busca_entero(f_in, f_obj) -> ConfigPLL | None:
    opciones = _opciones_enteras(_exacto(f_in), _exacto(f_obj))
    return opciones[0].cfg if opciones else None


def parametros() -> dict:
    phy = ic_hz(pll_out_hz(CFG_PHY_DEL_FIRMWARE), PHY_ICINT_FIRMWARE)
    return {
        "phy_ref_hz": phy,  # DERIVADO del firmware usb.rs:71-83, no otra cuenta.
        "ltdc_px_hz": 33_000_000,  # ESTIMADO: pantalla-motor S5, sin panel elegido.
        **{CLAVES[n]: J2_KERNEL_ESTIMADO_HZ for n, c in CONSUMIDORES.items()
           if c.trabajo == "J2"},  # Seis maestros del mismo trabajo y clase de velocidad.
        "xspi1_kernel_hz": 200_000_000,  # psram_budget.py:46, DS14791 Rev 2, Tabla 77, p. 182: DTR con DQS; no pieza elegida.
        "eth1_kernel_hz": 125_000_000,  # RM0486 Rev 4, Tabla 72, p. 446: reserva RGMII, D9 en cuarentena.
        "adc12_kernel_hz": 100_000_000,  # ESTIMADO: pedal y mux de perillas; conversion/adquisicion pendientes.
        "i2c1_kernel_hz": phy,  # ESTIMADO: reutilizar ic15; SCL/TIMINGR para descubrimiento y tactil pendientes.
        "sys_bus_hz": SYS_BUS_ESTIMADO_HZ,  # ESTIMADO: RM0486 Rev 4, p. 440-442.
        "sys_c_hz": SYS_BUS_ESTIMADO_HZ,  # ESTIMADO: habilitar ic6 para SYSSW, RM0486 Rev 4, p. 440.
        "sys_bus2_hz": SYS_BUS_ESTIMADO_HZ,  # ESTIMADO: habilitar ic11 para SYSSW, RM0486 Rev 4, p. 440.
    }


def _peticiones(p: dict, *, rgmii: bool = True) -> dict[str, Fraction]:
    pedidos = {n: _exacto(p[c]) for n, c in CLAVES.items() if rgmii or n != "ETH1"}
    assert pedidos["OTGPHY1"] in PHY_REF_LEGALES_HZ, (
        f"PHY: referencia {pedidos['OTGPHY1']} Hz fuera de FSEL {PHY_REF_LEGALES_HZ}")
    for nombre, hz in pedidos.items():
        consumidor = CONSUMIDORES[nombre]
        assert 0 < hz <= consumidor.techo_hz, (
            f"{nombre}: {hz} Hz fuera del techo kernel {consumidor.techo_hz} Hz")
    return pedidos


def _reparte_ics(pedidos: dict[str, Fraction]) -> dict[str, str]:
    """Backtracking de MUX: compartir solo cuando el Hz es identico."""
    asignados: dict[str, str] = {}
    ocupados: dict[str, Fraction] = {}

    def busca() -> bool:
        if len(asignados) == len(pedidos):
            return True
        candidatos = {
            n: [ic for ic in CONSUMIDORES[n].mux
                if ic not in ocupados or ocupados[ic] == hz]
            for n, hz in pedidos.items() if n not in asignados
        }
        nombre = min(candidatos, key=lambda n: (len(candidatos[n]), n))
        # Entre IC libres, preferir el que sirva a mas clientes del mismo
        # trabajo y Hz. Los seis J2 convergen en ic9 sin fijarlo a mano.
        companeros = [n for n in candidatos
                      if CONSUMIDORES[n].trabajo == CONSUMIDORES[nombre].trabajo
                      and pedidos[n] == pedidos[nombre]]
        for ic in sorted(candidatos[nombre], key=lambda c: (
                c not in ocupados, -sum(c in candidatos[n] for n in companeros), c)):
            nuevo = ic not in ocupados
            ocupados[ic] = pedidos[nombre]
            asignados[nombre] = ic
            if busca():
                return True
            del asignados[nombre]
            if nuevo:
                del ocupados[ic]
        return False

    assert busca(), "no cierra el MUX: IC compartido con frecuencias distintas; " + "; ".join(
        f"{n}={hz} Hz ve {CONSUMIDORES[n].mux}" for n, hz in pedidos.items())
    return asignados


def _reparte_plls(pedidos: dict[str, Fraction]):
    """Cobertura exacta: una PLL alimenta todos los objetivos que puede dividir.

    El PHY conserva su PLL4; las restantes se prueban como recursos libres.
    Reutilizar una PLL para un Hz no consume otro recurso: el IC ya se
    reservo. Por eso se pueden resolver MUX y PLL en estas dos etapas sin
    perder soluciones. Se exploran alternativas si la primera pide de mas.
    """
    assert not pll_ilegal(CFG_PHY_DEL_FIRMWARE), "PLL4 del firmware ilegal"
    objetivos = set(pedidos.values())
    opciones = {hz: _opciones_enteras(_exacto(HSI_HZ), hz) for hz in objetivos}
    faltantes = [hz for hz, ops in opciones.items() if not ops]
    assert not faltantes, (
        f"no cierra: sin solucion entera desde HSI para {sorted(faltantes)} Hz; "
        "revisar objetivo, fuente HSE o modo fraccionario")

    def busca(plls, pendientes, rutas):
        pendientes, rutas = set(pendientes), dict(rutas)
        for hz in sorted(pendientes):
            for indice, cfg in enumerate(plls):
                divisor = _divisor_ic(pll_out_hz(cfg), hz)
                if divisor is not None:
                    rutas[hz] = (indice, divisor)
                    pendientes.remove(hz)
                    break
        if not pendientes:
            return plls, rutas
        if len(plls) >= N_PLL:
            return None
        hz = min(pendientes, key=lambda f: (len(opciones[f]), f))

        def prioridad(opcion):
            cfg = opcion.cfg
            cobertura = sum(_divisor_ic(pll_out_hz(cfg), f) is not None
                            for f in pendientes)
            return (-cobertura, cfg.pdiv1 * cfg.pdiv2, cfg.divm, cfg.divn,
                    cfg.pdiv1, cfg.pdiv2)

        for opcion in sorted(opciones[hz], key=prioridad):
            resultado = busca(plls + [opcion.cfg], pendientes, rutas)
            if resultado is not None:
                return resultado
        return None

    resultado = busca([CFG_PHY_DEL_FIRMWARE], objetivos, {})
    assert resultado is not None, (
        f"no cierra: no existe cobertura con {N_PLL} PLL, incluida PLL4 del PHY, "
        f"para {sorted(objetivos)} Hz; cada objetivo aislado si tiene solucion")
    return resultado


def _derivadas(asignaciones: dict[str, Asignacion]) -> dict[str, Fraction]:
    bus = asignaciones["SYS_BUS"].f_hz
    hclk = ic_hz(bus, HPRE_DIV)  # RM0486 Rev 4, p. 440-442: HPRE.
    pclk = ic_hz(hclk, PPRE_DIV)  # RM0486 Rev 4, p. 442: PPRE1/2/4/5.
    return {"hclk": hclk, "pclk": pclk, "CPU": _exacto(HSI_HZ),
            "OTG1": _exacto(OTG_KERNEL_HZ)}


def _verifica_solucion(sol: Solucion, pedidos: dict[str, Fraction]) -> None:
    assert set(sol.asignaciones) == set(pedidos), "faltan consumidores en el reparto"
    assert 0 < len(sol.plls) <= N_PLL, "no cierra: numero de PLL fuera del silicio"
    for cfg in sol.plls:
        assert not pll_ilegal(cfg), f"PLL ilegal: {pll_ilegal(cfg)}"
    ocupados = {}
    for nombre, asig in sol.asignaciones.items():
        assert asig.ic in CONSUMIDORES[nombre].mux, f"{nombre}: IC fuera del MUX"
        assert _en_rango(asig.icint, ICINT), f"{nombre}: ICINT fuera de registro"
        real = ic_hz(pll_out_hz(sol.plls[asig.pll]), asig.icint)
        assert real == asig.f_hz == pedidos[nombre], f"{nombre}: dos cuentas del reloj"
        assert real <= CONSUMIDORES[nombre].techo_hz, f"{nombre}: techo de kernel"
        ruta = (asig.pll, asig.icint, real)
        assert ocupados.setdefault(asig.ic, ruta) == ruta, f"{asig.ic}: dos configuraciones"
    phy = sol.asignaciones["OTGPHY1"]
    assert sol.plls[phy.pll] == CFG_PHY_DEL_FIRMWARE, "PHY perdio su PLL de firmware"
    assert sol.nombres_pll[phy.pll] == "PLL4", "PHY perdio la PLL4 fisica"
    assert phy.f_hz in PHY_REF_LEGALES_HZ, "PHY fuera de FSEL"
    assert sol.derivadas["hclk"] <= 200_000_000, "techo hclk"  # RM0486 Rev 4, Tabla 72, p. 445-453.
    assert sol.derivadas["pclk"] <= 100_000_000, "techo APB/I2C1"  # RM0486 Rev 4, Tabla 72, p. 447.


def _resuelve(p: dict, *, rgmii: bool = True) -> Solucion:
    pedidos = _peticiones(p, rgmii=rgmii)
    ics = _reparte_ics(pedidos)
    plls, rutas = _reparte_plls(pedidos)
    asignaciones = {}
    for nombre, hz in pedidos.items():
        indice, divisor = rutas[hz]
        real = ic_hz(pll_out_hz(plls[indice]), divisor)
        asignaciones[nombre] = Asignacion(indice, ics[nombre], divisor, real)
    nombres = ("PLL4",) + tuple(f"PLL{i}" for i in range(1, len(plls)))
    sol = Solucion(plls, asignaciones, nombres, _derivadas(asignaciones))
    _verifica_solucion(sol, pedidos)
    return sol


def resuelve(*, rgmii: bool = True) -> Solucion:
    """Mesa del hub; D9 EN CUARENTENA se cobra por defecto y se puede soltar."""
    return _resuelve(parametros(), rgmii=rgmii)


def guarda_reloj(p: dict) -> None:
    # Se comprueban FSEL y techos ANTES de buscar: un Hz absurdo no debe
    # esconder el limite violado detras de un diagnostico de falta de PLL.
    _resuelve(p)


def _mhz(hz) -> str:
    # Solo formato decimal. El float nunca vuelve a la cuenta ni a la guarda.
    return f"{float(_exacto(hz) / 1_000_000):.6f}".rstrip("0").rstrip(".")


def _cadena(cfg: ConfigPLL) -> str:
    return (f"entrada {_mhz(cfg.f_in_hz)} /M{cfg.divm} -> PFD {_mhz(pfd_hz(cfg))} "
            f"xN{cfg.divn} -> VCO {_mhz(vco_hz(cfg))} /P{cfg.pdiv1} /P{cfg.pdiv2} "
            f"-> {_mhz(pll_out_hz(cfg))} MHz")


def huecos() -> list[str]:
    pendientes = []
    if not PANEL_ELEGIDO or LTDC_PX_ESTIMADO:
        pendientes.append("panel sin elegir: pixel clase ~33 MHz ESTIMADO, pantalla-motor S5")
    if not CODEC_ELEGIDO:
        pendientes.append("codec del CUARTO chip sin elegir: interfaz-audio, faltan MCLK/FS y divisores SAI (A-10)")
    if HSE_HZ is None:
        pendientes.append("HSE sin decidir: el barrido de cristal es una alternativa, no una compra")
    if not MESA_RECONCILIADA:
        pendientes.append(f"mesa sin reconciliar con {CENSO_FUENTE}")
    if VARIOS_SIN_RELOJ_CENSADO:
        pendientes.append("VARIOS SIN RELOJ CENSADO: 32 GPIO del censo de pines; "
                          + "; ".join(VARIOS_SIN_RELOJ_CENSADO)
                          + ". Sin piezas ni frecuencias elegidas; arbol del hub incompleto")
    pendientes.extend(f"arbol pendiente: {n} (acta {ACTA_CUATRO_CHIPS})"
                      for n in ARBOLES_PENDIENTES)
    return pendientes


def demo() -> int:
    sol = resuelve()
    print(f"EL CENSO DE RELOJES DEL HUB -- mesa reconciliada: {CENSO_FUENTE}\n")
    print(f"  AUDIO_EN_EL_HUB={AUDIO_EN_EL_HUB}; acta A-10, {ACTA_CUATRO_CHIPS}.")
    print("  Caracterizacion: DS14791 Rev 10, Tabla 58, p. 166.")
    for nombre, limites in (("fPLL_IN", PLL_IN_HZ), ("PFD", PFD_HZ),
                            ("VCO", VCO_HZ), ("FOUTPOSTDIV", FOUT_HZ)):
        print(f"    {nombre:12s} {_mhz(limites[0])}..{_mhz(limites[1])} MHz")
    print(f"  HSI={_mhz(HSI_HZ)} MHz; HSI_AL_BORDE={HSI_AL_BORDE}.")
    print("  Cero margen nominal de entrada. Precision/deriva del HSI no medidas.")
    print("  usb.rs:47 nombra fPLL_IN donde calcula PFD; la cuenta pasa,")
    print("  pero la cita 5..1200 del RM no comprueba el limite del producto.")
    print("  PLL1..4 son intercambiables ante cada ICxSEL (RM Rev 4, p. 507).")
    print("  La asignacion tipica de p. 435 no reserva PLL4 a pantalla/camara.")
    print(f"\n  REPARTO CALCULADO: {len(sol.plls)} de {N_PLL} PLL, todas enteras.")
    for nombre, cfg in zip(sol.nombres_pll, sol.plls):
        print(f"    {nombre}: {_cadena(cfg)}")
    print("\n  consumidor | trabajo | PLL | IC /divisor (ICxINT registro) | kernel MHz")
    for nombre, asig in sol.asignaciones.items():
        print(f"    {nombre:10s} {CONSUMIDORES[nombre].trabajo:15s} "
              f"{sol.nombres_pll[asig.pll]}  {asig.ic:4s} "
              f"/{asig.icint:<3d} (0x{asig.icint - 1:02X})  {_mhz(asig.f_hz)}")
    por_ic: dict[str, list[str]] = {}
    for nombre, asig in sol.asignaciones.items():
        por_ic.setdefault(asig.ic, []).append(nombre)
    print("\n  Cada IC compartido conserva PLL, divisor y Hz; manda el techo menor:")
    for ic, quienes in por_ic.items():
        if len(quienes) < 2:
            continue
        techos = [CONSUMIDORES[n].techo_hz for n in quienes]
        hz = sol.asignaciones[quienes[0]].f_hz
        print(f"    {ic}: {', '.join(quienes)} a {_mhz(hz)} MHz; "
              f"techo comun min({', '.join(_mhz(t) for t in techos)}) "
              f"= {_mhz(min(techos))} MHz; margen {_mhz(min(techos) - hz)} MHz.")
    print("  Los seis maestros J2 comparten ic9: el techo de SPI4/5 limita al grupo.")
    print("  J2 clase 34,5 MHz: kernel ESTIMADO; faltan SCK y timing de las seis ranuras.")
    print("  XSPI1: framebuffer; kernel al techo DTR con DQS, sin certificar caudal.")
    print("  ETH1: cobrado por defecto; D9 EN CUARENTENA, PTP/PHY externos sin pieza.")
    print("  resuelve(rgmii=False) retira ETH1 y libera ic12 antes de buscar PLL.")
    print("  ADC12: pedal y entrada del mux de perillas; adquisicion pendiente.")
    print("  I2C1: descubrimiento y tactil en ic15; SCL/TIMINGR pendientes.")
    print("\n  Fuera del MUX de kernel por IC (RM0486 Rev 4, p. 440-442/449):")
    for nombre, hz in sol.derivadas.items():
        print(f"    {nombre:10s} {_mhz(hz)} MHz")
    print("  TIM1-5 del afinado pertenecen a la Voz (autotune_budget.py).")
    print("  El objetivo de bus conserva 200 MHz ESTIMADOS, sin importar el afinado.")
    print("  SYS_C/ic6 y SYS_BUS2/ic11 habilitados junto a ic2 por SYSSW;")
    print("  CPU sigue en HSI. Esto no asigna trabajos a la NPU ni a la camara.")
    print("  OTG1 recibe phyclock de la PLL INTERNA del PHY, no su referencia.")
    print("\n  BARRIDO ENTERO COMPLETO: configuraciones distintas desde HSI")
    print("  Audio: estudio del mismo silicio para el CUARTO chip, no carga del hub.")
    objetivos = (
        (48_000 * 1024, "48 kHz x1024"),  # #150: frecuencia de audio a explorar.
        (48_000 * 512, "48 kHz x512"),  # #150: frecuencia de audio a explorar.
        (48_000 * 256, "48 kHz x256"),  # #150: frecuencia de audio a explorar.
        (44_100 * 512, "44,1 kHz x512"),  # #150: frecuencia de audio a explorar.
        (44_100 * 256, "44,1 kHz x256"),  # #150: frecuencia de audio a explorar.
        (MCLK_1024FS_44K1_HZ, "44,1 kHz x1024"),
        (parametros()["ltdc_px_hz"], "pixel ESTIMADO"),
    )
    for hz, etiqueta in objetivos:
        cfg = busca_entero(HSI_HZ, hz)
        cantidad = cuenta_enteras(HSI_HZ, hz)
        print(f"    {_mhz(hz):>8s} MHz {etiqueta:16s}: {cantidad} soluciones")
        if cfg is not None:
            divisor = _divisor_ic(pll_out_hz(cfg), _exacto(hz))
            print(f"      {_cadena(cfg)}; IC /{divisor} -> "
                  f"{_mhz(ic_hz(pll_out_hz(cfg), divisor))} MHz")
    cristal_candidato = 22_579_200  # #150: alternativa de familia 44,1 kHz; NO HSE elegido.
    alternativas = cuenta_enteras(cristal_candidato, MCLK_1024FS_44K1_HZ)
    print(f"  Desde cristal CANDIDATO {_mhz(cristal_candidato)} MHz: "
          f"{alternativas} soluciones para {_mhz(MCLK_1024FS_44K1_HZ)} MHz.")
    if busca_entero(HSI_HZ, MCLK_1024FS_44K1_HZ) is None:
        print("  CALCULADO: 44,1 kHz x1024 no sale entero del HSI. El CUARTO chip")
        print("  que elija un codec que lo exija debe estudiar cristal, fracN o retirar")
        print("  ese modo. Las demas combinaciones se juzgan en la tabla anterior.")
    else:
        print("  CALCULADO: 44,1 kHz x1024 SI sale entero; releer la restriccion del #150.")
    print(f"  Jitter entero typ +-{JITTER_ENTERO_TYP_PS}, max +-{JITTER_ENTERO_PS}; "
          f"fracN max +-{JITTER_FRAC_PS} ps RMS.")
    print(f"  DS14791 Rev 10, Tabla 58, p. 166: banda {JITTER_BANDA_HZ} Hz,")
    print(f"  VCO {_mhz(JITTER_VCO_HZ)} MHz, PFD {_mhz(JITTER_PFD_HZ)} MHz.")
    print("  Son condiciones de caracterizacion, no jitter medido de esta placa.")
    print("  Exactitud racional respecto a HSI nominal no asegura precision absoluta.")
    print(f"\n  CIERRA lo ENUMERADO del hub con {len(sol.plls)} PLL y sus ESTIMADOS.")
    print("  El arbol completo del hub sigue abierto: varios sin reloj censado y piezas pendientes.")
    pendientes = huecos()
    for pendiente in pendientes:
        print(f"  HUECO: {pendiente}")
    if pendientes:
        print("HUECO: faltan piezas, relojes de los varios y arboles de los otros chips")
    return 2 if pendientes else 0


def main() -> int:
    try:
        return demo()
    except AssertionError as exc:
        print(f"FALLO: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
