"""Reintentos con abandono y persistencia en FRAM del vigilante M5 (T24).

    python recuperacion_budget.py

Resuelve la parte gobernable de **T24 / M5 / H-V2-RECUPERACION** (firmada en
D-V4 el 2026-09-08 y detallada en `2026-10-22-fuente-v5-piezas-propuesta.md`
sec. 9.2) con piezas versionadas en `docs/reference/datasheets/`:

  1. **Interruptor de entrada en serie (24 V):** eFuse **TI TPS26631**
     (`tps2663.pdf` p. 6-8, 22) en modo latch, precedido por el controlador de
     bloqueo de polaridad inversa **TI LM74502** (`lm74502.pdf` p. 1, -65 V).
     - `RON_max = 53 mohm` entre -40 y +125 C (`tps2663.pdf` p. 7).
     - Limite de corriente programado con `R_ILIM = 3,74 kohm` (E96 1 %):
       segunda ecuacion de diseno `I_OL = 18,1 / R_ILIM(kohm) = 4,84 A` nominal
       (`tps2663.pdf` p. 22 ec. 5), con banda de exactitud de `+-7 %` (la hoja
       la da a 3 y a 4,02 kohm, p. 7): `4,50 A .. 5,18 A`. El minimo pasa 1,5
       veces la corriente del cordon con el ladrillo en sus 24 V nominales
       (`ladrillo_budget.py`: `2,98 A`) y el maximo queda por debajo de los
       `7,5 A/pin` del conector Kycon.
     - A diferencia del TPS26630, el TPS26631 deja pasar hasta `2 x I_OL`
       durante `tCB(dly) = 25,5 ms` (con PGOOD alto) antes de regular a `I_OL`,
       y su comparador rapido corta a `3 x I_OL` (`tps2663.pdf` p. 7, 23): ese
       pico, `2 x 5,18 = 10,36 A`, tambien cabe en el conector.
     - El de riel `U19` limita con `R34`: su minimo tiene que pasar la rama
       `U1` con la carga en su techo (`ladrillo_budget.corriente_thn_a`). A
       ~1 A la hoja da `+-10 %` (30 kohm) y `+-8 %` (9 kohm): se toma el 10.
     - La ventana de entrada la pone el divisor `R12/R13/R14` de la placa
       (`V(UVLOR)`, `V(UVLOF)`, `V(OVPR)`, `V(OVPF)`, p. 6): se lee de bom.csv.
     - Pin `SHDN` con pull-down `R83` al retorno DC: su pull-up interno da hasta
       `10 uA` (p. 7), y `47 kohm` lo dejan por debajo de `V(SHUTF) = 0,8 V`
       mientras el MCU no este vivo y autorice.

  2. **Decisor con memoria no volatil instantanea:** **TI MSP430FR2111**
     (`msp430fr2111.pdf` p. 1, 7, 20, 35):
     - `3,75 KB` de FRAM sin borrado previo de pagina y con `10^15` ciclos de
       escritura (`msp430fr2111.pdf` p. 35): escribe "intento PENDIENTE" +
       `CRC16` ANTES de levantar `SHDN`, en microsegundos.
     - El intento se da por sano si la placa sigue viva y sin `FLT` pasado
       `T_CONFIRMA_SANO_S`; si el MCU muere antes (el corto tumba la entrada),
       al volver a arrancar encuentra el PENDIENTE y lo cuenta como fallido. El
       firmware nunca sabe de antemano si un pulso va a fallar.
     - Supervisor de alimentacion `SVS` integrado (`1,71..1,99 V`, p. 20).
     - Si al arrancar el `CRC16` de la FRAM no es valido, entra directamente en
       estado `ABANDONADO` (fallo seguro).

  3. **Politica verificada por maquina de estados + 5 mutantes de autoprueba:**
     - `N_REINTENTOS = 3` (4 pulsos de intento en total: 1 inicial + 3 reintentos).
     - `T_ESPERA_REINTENTO_S = 1,0 s` entre intentos.
     - `T_FILTRO_REBOTE_S = 0,100 s` (100 ms): desconexiones o rebotes del
       enchufe de menos de 100 ms o caidas de red no gastan cupo de intentos.
     - `T_REARME_SANO_S = 60,0 s`: 60 s continuos sin fallo ponen la cuenta a 0.
     - **Fallo de riel** (`FLT` del eFuse `U19`, leido en P1.2): gasta un
       intento, como la sobrecarga de un riel en sec. 9.2. El `FLT` de `U19`
       tambien baja mientras su entrada arranca (UVLO, `tps2663.pdf` p. 19, y
       hasta `700 us` despues, p. 8): el MCU lo ignora los primeros
       `T_IGNORA_FLT_U19_S` tras cada cierre de `U16`, que cubren el arranque
       entero de la cadena. Cierre es tanto el del MCU por `SHDN` como el que
       `U16` hace solo al salir de un bajon de entrada (p. 19): ese lo ve por el
       `FLT` de `U16` (`FLT_M5`), que baja en el UVLO y se suelta al cerrar.
     - **Un bajon de entrada que no tumba al MCU no gasta intento.**
     - **Un abandono NO se borra desenchufando:** persiste en FRAM y solo se
       suelta manteniendo pulsado el boton dedicado durante `>= 2,0 s` con la
       entrada de 24 V dentro de la ventana valida.

  4. **Alcance honesto (T24):**
     - Un corto en el cordon del ladrillo *aguas arriba* del vigilante M5 no
       pasa por el `TPS26631`; depende del hiccup nativo del ladrillo
       (`H-PL-ABANDONO-FUENTE`).
     - El `FLT` de `U19` es el mismo para sobretension, sobrecarga, UVLO y
       temperatura (`tps2663.pdf` p. 27), y el MCU no ve la tension del riel:
       una sobretension de riel gasta intentos como una sobrecarga y abandona
       al agotar el cupo, no en el primer pulso como pide sec. 9.2. En cada
       intento `U19` abre el riel por si solo (OVP, p. 20).
     - Los crowbars de rack (D-F6) no tienen camino al MCU (#476).
     - Desenchufar durante los `T_CONFIRMA_SANO_S` de un intento lo cuenta como
       fallido: desde el MCU no se distingue de un corto que tumba la entrada.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

from bom_valores import valor  # noqa: E402


def _ladrillo():
    spec = importlib.util.spec_from_file_location("_v5_ladrillo_budget",
                                                  os.path.join(DIR, "ladrillo_budget.py"))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LADRILLO = _ladrillo()

# --- Parametros electricos de hoja (tps2663.pdf y msp430fr2111.pdf) ---------
R_ILIM_KOHM = valor("R11") / 1e3
K_ILIM_TPS26631_A_KOHM = 18.1             # tps2663.pdf p. 22 ec. (5): R = 18,1 / I_OL
TOL_ILIM_TPS26631_FRAC = 0.07             # +-7 % en tps2663.pdf p. 7
TOL_ILIM_U19_FRAC = 0.10                  # p. 7: +-10 % a 30 kohm, +-8 % a 9 kohm
MARGEN_ILIM = 1.5                         # sobre la corriente del cordon a 24 V nominales
I_CORDON_CONTINUA_A = LADRILLO.corriente_del_cordon_a()
I_CORDON_NOMINAL_A = LADRILLO.entrada_dcdc_w() / LADRILLO.V_LADRILLO
I_RIEL_U19_A = LADRILLO.corriente_thn_a("U1")
I_MAX_CONECTOR_POR_POLO_A = 15.0          # Kycon KPJX-PM-4S / KPPX-4P: 2 x 7,5 A

# Umbrales del TPS26631 (tps2663.pdf p. 6), nominales y su +-2 %.
V_UVLOR_V, V_UVLOF_V = 1.200, 1.122
V_OVPR_V, V_OVPF_V = 1.200, 1.122
TOL_UMBRAL_FRAC = 0.02
V_MAX_DCDC_V = 36.0                       # entrada maxima de THN, URB y K78 (hojas p. 1-2)
V_SHUTF_MAX_V = 0.80                      # tps2663.pdf p. 7
I_SHDN_MAX_A = 10e-6                      # tps2663.pdf p. 7: pull-up interno de SHDN
SVS_MSP430_MAX_V = 1.99                   # msp430fr2111.pdf p. 20
CICLOS_FRAM_MIN = 10**15                  # msp430fr2111.pdf p. 35

# --- Arranque de la cadena: cuanto puede tardar el FLT de U19 en soltarse ---
I_DVDT_MIN_A = 1.775e-6                   # tps2663.pdf p. 7
GAIN_DVDT_MIN = 23.5                      # tps2663.pdf p. 7
TOL_C_X7R_FRAC = 0.10                     # C11/C13: X7R "K" (+-10 %)
T_ARRANQUE_THN_MAX_S = 30e-3              # traco_thn20wi.pdf p. 2: start-up 30 ms max
T_UVLO_FLT_MAX_S = 700e-6                 # tps2663.pdf p. 8: UVLO -> FLT alto
T_CB_MAX_S = 31e-3                        # tps2663.pdf p. 8: tCB(dly) a 2 x I_OL

# --- Parametros temporales de la maquina de estados -------------------------
N_REINTENTOS = 3                          # 1 intento inicial + 3 reintentos = 4 pulsos
N_PULSOS_MAX = 1 + N_REINTENTOS
T_ESPERA_REINTENTO_S = 1.0
T_FILTRO_REBOTE_S = 0.100
T_REARME_SANO_S = 60.0
T_BOTON_REARME_S = 2.0
T_IGNORA_FLT_U19_S = 0.100
T_CONFIRMA_SANO_S = 0.200


def ventana_entrada_v() -> dict[str, float]:
    """La ventana que pone el divisor R12/R13/R14 de U16, en voltios de entrada."""
    total = valor("R12") + valor("R13") + valor("R14")
    uv = total / (valor("R13") + valor("R14"))
    ov = total / valor("R14")
    return {"arranca": V_UVLOR_V * uv, "apaga": V_UVLOF_V * uv,
            "sobretension": V_OVPR_V * ov, "vuelve": V_OVPF_V * ov}


def _rampa_s(c_ref: str, v_final: float) -> float:
    """Rampa de salida del TPS26631 con su C(dVdT), en el peor caso."""
    pendiente = I_DVDT_MIN_A * GAIN_DVDT_MIN / (valor(c_ref) * (1.0 + TOL_C_X7R_FRAC))
    return v_final / pendiente


def arranque_cadena_max_s() -> float:
    """De levantar SHDN a que el FLT de U19 puede soltarse: rampa de U16 hasta
    el maximo de la ventana, arranque del THN, rampa de U19 y su retardo."""
    v = ventana_entrada_v()["sobretension"]
    return (_rampa_s("C11", v) + T_ARRANQUE_THN_MAX_S
            + _rampa_s("C13", 15.5 * (1.0 + 0.025)) + T_UVLO_FLT_MAX_S)


def corriente_limite_tps26631_a(ref: str = "R11",
                                tol: float = TOL_ILIM_TPS26631_FRAC) -> tuple[float, float, float]:
    """Devuelve (min_a, nom_a, max_a) del limite de corriente que pone `ref`."""
    nom = K_ILIM_TPS26631_A_KOHM / (valor(ref) / 1e3)
    return nom * (1.0 - tol), nom, nom * (1.0 + tol)


def _crc16_ccitt(intentos: int, pendiente: bool, abandonado: bool) -> int:
    datos = bytes([intentos & 0xFF, 1 if pendiente else 0, 1 if abandonado else 0])
    crc = 0xFFFF
    for b in datos:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


@dataclass
class ImagenFRAM:
    intentos_gastados: int = 0
    pendiente: bool = False
    abandonado: bool = False
    crc: int = _crc16_ccitt(0, False, False)

    def escribir(self, intentos: int, pendiente: bool, abandonado: bool) -> None:
        self.intentos_gastados = intentos
        self.pendiente = pendiente
        self.abandonado = abandonado
        self.crc = _crc16_ccitt(intentos, pendiente, abandonado)

    def es_valida(self) -> bool:
        return self.crc == _crc16_ccitt(self.intentos_gastados, self.pendiente, self.abandonado)


class VigilanteM5:
    """Simulador discreto del vigilante M5 (TPS26631 + MSP430FR2111 FRAM).

    Solo decide con lo que el firmware puede saber en cada momento: si un
    pulso falla lo sabe DESPUES (por FLT, o porque al volver a arrancar
    encuentra su intento pendiente), nunca antes de levantar SHDN."""

    def __init__(self, fram: ImagenFRAM | None = None, *,
                 persiste_en_fram: bool = True,
                 filtra_rebote: bool = True,
                 flt_u19_gasta_intento: bool = True,
                 exige_crc_valido: bool = True,
                 ignora_flt_u19_en_arranque: bool = True,
                 reinicia_ventana_tras_uvlo: bool = True) -> None:
        self.fram = fram if fram is not None else ImagenFRAM()
        self.persiste_en_fram = persiste_en_fram
        self.filtra_rebote = filtra_rebote
        self.flt_u19_gasta_intento = flt_u19_gasta_intento
        self.exige_crc_valido = exige_crc_valido
        self.ignora_flt_u19_en_arranque = ignora_flt_u19_en_arranque
        self.reinicia_ventana_tras_uvlo = reinicia_ventana_tras_uvlo
        self.ahora_s = 0.0
        self.t_cierre_s = 0.0

        self.intentos_ram = 0
        self.pendiente_ram = False
        self.abandonado_ram = False
        self.efuse_habilitado = False
        self.pulsos_emitidos = 0
        self.tiempo_sano_acumulado_s = 0.0
        self._arrancar_mcu()

    def _arrancar_mcu(self) -> None:
        """Arranque en frio o tras apagon: lee FRAM ANTES de tocar SHDN."""
        self.efuse_habilitado = False
        if self.exige_crc_valido and not self.fram.es_valida():
            self.intentos_ram = N_PULSOS_MAX
            self.pendiente_ram = False
            self.abandonado_ram = True
            return
        if not self.persiste_en_fram:
            self.intentos_ram, self.pendiente_ram, self.abandonado_ram = 0, False, False
            return
        self.intentos_ram = self.fram.intentos_gastados
        self.pendiente_ram = self.fram.pendiente
        self.abandonado_ram = self.fram.abandonado
        if self.pendiente_ram:
            # El ultimo pulso no llego a confirmarse: la entrada cayo con el.
            self.intentos_ram += 1
            self.pendiente_ram = False
            if self.intentos_ram >= N_PULSOS_MAX:
                self.abandonado_ram = True
            self._sincronizar_fram()

    def _sincronizar_fram(self) -> None:
        if self.persiste_en_fram:
            self.fram.escribir(self.intentos_ram, self.pendiente_ram, self.abandonado_ram)

    def _en_ventana(self, v_in: float) -> bool:
        v = ventana_entrada_v()
        return v["arranca"] <= v_in < v["sobretension"]

    def apagon_de_entrada(self) -> None:
        """Se cae el ladrillo o se desenchufa el cordon: la RAM muere."""
        self.efuse_habilitado = False
        self.tiempo_sano_acumulado_s = 0.0
        self._arrancar_mcu()

    def rebote_conector(self, duracion_s: float, v_in: float = 24.0) -> None:
        """Un rebote mecanico al enchufar (< 100 ms) no es un fallo de carga."""
        if self.filtra_rebote and duracion_s < T_FILTRO_REBOTE_S:
            return
        # Mutante sin filtro de rebote: confunde el rebote con un intento fallido
        self.intento_energizar(v_in=v_in, fallo="sobrecorriente")

    def intento_energizar(self, *, v_in: float = 24.0,
                          fallo: str | None = None,
                          cae_alimentacion_en_corto: bool = False) -> bool:
        """Un intento de cierre del TPS26631, si la politica lo autoriza.

        `fallo` es lo que le pasa a la placa, no algo que el firmware sepa al
        decidir: solo se mira despues de cerrar."""
        if self.abandonado_ram or not self._en_ventana(v_in):
            self.efuse_habilitado = False
            return False

        # PENDIENTE en FRAM antes de cerrar el interruptor:
        self.pendiente_ram = True
        self._sincronizar_fram()
        self.pulsos_emitidos += 1
        self.efuse_habilitado = True
        self.t_cierre_s = self.ahora_s

        if fallo is None:
            # Viva y sin FLT pasados T_CONFIRMA_SANO_S: el intento no gasta cupo.
            self.pendiente_ram = False
            self._sincronizar_fram()
            return True

        self.efuse_habilitado = False
        self.tiempo_sano_acumulado_s = 0.0
        if cae_alimentacion_en_corto:
            # El MCU muere antes de ver nada: queda el PENDIENTE en la FRAM.
            self.apagon_de_entrada()
            return False
        self.pendiente_ram = False
        self.intentos_ram += 1
        if self.intentos_ram >= N_PULSOS_MAX:
            self.abandonado_ram = True
        self._sincronizar_fram()
        return False

    def esperar(self, duracion_s: float) -> None:
        self.ahora_s += duracion_s

    def bajon_de_entrada(self, duracion_s: float) -> None:
        """La entrada baja del UVLO de U16 sin tumbar al MCU (U18 sigue vivo).

        U16 abre y su FLT (FLT_M5) baja; al volver la entrada U16 cierra solo
        (tps2663.pdf p. 19) y FLT_M5 se suelta. El firmware toma ese flanco
        como un cierre nuevo: no gasta intento."""
        self.esperar(duracion_s)
        if self.efuse_habilitado and self.reinicia_ventana_tras_uvlo:
            self.t_cierre_s = self.ahora_s

    def flt_u19(self) -> None:
        """El FLT de U19 baja con el eFuse de entrada cerrado."""
        if not self.efuse_habilitado or self.abandonado_ram:
            return
        if (self.ignora_flt_u19_en_arranque
                and self.ahora_s - self.t_cierre_s < T_IGNORA_FLT_U19_S):
            return            # UVLO de U19 mientras su entrada sube: no es un fallo
        self.efuse_habilitado = False
        self.tiempo_sano_acumulado_s = 0.0
        self.pendiente_ram = False
        if self.flt_u19_gasta_intento:
            self.intentos_ram += 1
            if self.intentos_ram >= N_PULSOS_MAX:
                self.abandonado_ram = True
        else:
            # Mutante con la politica vieja: abandona en el primer FLT.
            self.abandonado_ram = True
        self._sincronizar_fram()

    def marcha_sana(self, duracion_s: float) -> None:
        self.esperar(duracion_s)
        if not self.efuse_habilitado or self.abandonado_ram:
            return
        self.tiempo_sano_acumulado_s += duracion_s
        if self.tiempo_sano_acumulado_s >= T_REARME_SANO_S:
            self.intentos_ram = 0
            self._sincronizar_fram()

    def pulsar_boton_rearme(self, duracion_s: float, *, v_in: float = 24.0) -> bool:
        if duracion_s >= T_BOTON_REARME_S and self._en_ventana(v_in):
            self.intentos_ram = 0
            self.pendiente_ram = False
            self.abandonado_ram = False
            self._sincronizar_fram()
            return True
        return False


def _verifica_politica(cls_kwargs: dict) -> None:
    """Bateria de propiedades exigidas al vigilante M5."""
    # Propiedad 1: corto persistente con colapso de alimentacion en cada pulso
    # debe dar EXACTAMENTE 4 pulsos y quedar en ABANDONADO incluso tras desenchufar.
    v = VigilanteM5(**cls_kwargs)
    for _ in range(10):
        v.intento_energizar(v_in=24.0, fallo="sobrecorriente",
                            cae_alimentacion_en_corto=True)
    assert v.pulsos_emitidos == N_PULSOS_MAX, (
        f"esperaba {N_PULSOS_MAX} pulsos ante corto con caida de V_in y dio {v.pulsos_emitidos}")
    assert v.abandonado_ram, "no quedo en ABANDONADO tras agotar el cupo"
    v.apagon_de_entrada()
    assert not v.intento_energizar(v_in=24.0, fallo=None), (
        "desenchufar y volver a enchufar borro el estado ABANDONADO")

    # Propiedad 2: 5 rebotes de 20 ms al enchufar no deben gastar ni un intento.
    v2 = VigilanteM5(**cls_kwargs)
    for _ in range(5):
        v2.rebote_conector(0.020)
    assert v2.intentos_ram == 0 and not v2.abandonado_ram, (
        "el rebote de contacto gasto intentos o abandono la fuente")

    # Propiedad 3: un fallo de riel (FLT de U19 con la cadena ya arrancada)
    # gasta un intento y reintenta; si persiste, 4 pulsos y ABANDONADO.
    v3 = VigilanteM5(**cls_kwargs)
    v3.intento_energizar(v_in=24.0)
    v3.esperar(1.0)
    v3.flt_u19()
    assert v3.intentos_ram == 1 and not v3.abandonado_ram, (
        "el primer FLT de U19 abandono la fuente: la sobrecarga de un riel gasta un intento (sec. 9.2)")
    for _ in range(10):
        if v3.intento_energizar(v_in=24.0):
            v3.esperar(1.0)
            v3.flt_u19()
    assert v3.pulsos_emitidos == N_PULSOS_MAX and v3.abandonado_ram, (
        f"fallo de riel persistente: {v3.pulsos_emitidos} pulsos en vez de {N_PULSOS_MAX} y abandono")

    # Propiedad 4: FRAM con CRC corrupto al arrancar entra en ABANDONADO sin pulsar.
    fram_rota = ImagenFRAM(intentos_gastados=0, pendiente=False, abandonado=False, crc=0x0000)
    v4 = VigilanteM5(fram=fram_rota, **cls_kwargs)
    assert v4.abandonado_ram and not v4.intento_energizar(v_in=24.0), (
        "arranco con CRC de FRAM corrupto sin ir a fallo seguro")

    # Propiedad 5: el FLT de U19 durante el arranque (su UVLO) no abandona.
    v5 = VigilanteM5(**cls_kwargs)
    v5.intento_energizar(v_in=24.0)
    v5.esperar(0.010)
    v5.flt_u19()
    assert v5.efuse_habilitado and not v5.abandonado_ram, (
        "el FLT de U19 del arranque abandono la fuente: no arrancaria nunca")

    # Propiedad 6: un bajon de entrada con la fuente en marcha no gasta intento:
    # U16 vuelve a cerrar solo y el FLT de U19 de ese arranque cae en la ventana.
    v6 = VigilanteM5(**cls_kwargs)
    v6.intento_energizar(v_in=24.0)
    v6.marcha_sana(5.0)
    v6.bajon_de_entrada(0.050)
    v6.esperar(0.010)
    v6.flt_u19()
    assert v6.efuse_habilitado and v6.intentos_ram == 0 and not v6.abandonado_ram, (
        "un bajon de entrada gasto un intento: el FLT de U19 del rearranque de U16 "
        "cayo fuera de la ventana")


def _autocomprobacion() -> None:
    # 1. El limite de corriente del TPS26631 deja pasar 1,5 veces la corriente
    #    del cordon a 24 V nominales y protege el conector (15 A/polo). El 1,5x
    #    cubre lo que ladrillo_budget.no_cubre() deja fuera, no solo el
    #    ladrillo al -5 %: por eso se mide sobre la nominal y no sobre el peor caso.
    i_min, i_nom, i_max = corriente_limite_tps26631_a()
    assert i_min > MARGEN_ILIM * I_CORDON_NOMINAL_A, (
        f"banda baja de ILIM ({i_min:.2f} A) por debajo de {MARGEN_ILIM} x "
        f"{I_CORDON_NOMINAL_A:.2f} A (cordon a 24 V nominales)")
    assert i_min > I_CORDON_CONTINUA_A, (
        f"banda baja de ILIM ({i_min:.2f} A) por debajo del cordon en su peor caso "
        f"({I_CORDON_CONTINUA_A:.2f} A): U16 cortaria con la carga de diseno")
    # El de U19 deja pasar su rama con la carga en su techo.
    u19_min, _, _ = corriente_limite_tps26631_a("R34", TOL_ILIM_U19_FRAC)
    assert u19_min > I_RIEL_U19_A, (
        f"banda baja de ILIM de U19 ({u19_min:.3f} A, R34) por debajo de la rama U1 "
        f"({I_RIEL_U19_A:.3f} A): U19 cortaria el riel con la carga de diseno")
    assert i_max < I_MAX_CONECTOR_POR_POLO_A, (
        f"banda alta de ILIM ({i_max:.2f} A) supera el conector ({I_MAX_CONECTOR_POR_POLO_A:.1f} A)")
    # El TPS26631 deja pasar hasta 2 x I_OL durante 25,5 ms antes de regular
    # (tps2663.pdf p. 7, 23): tambien ese pico tiene que caber en el conector.
    assert 2 * i_max < I_MAX_CONECTOR_POR_POLO_A, (
        f"pico de 2 x ILIM ({2 * i_max:.2f} A) supera el conector ({I_MAX_CONECTOR_POR_POLO_A:.1f} A)")

    # 2. La ventana de la placa: arranca con el ladrillo en su minimo y el
    #    cordon cargado, y corta antes de que los DC-DC pasen de 36 V.
    v = ventana_entrada_v()
    v_min = LADRILLO.V_LADRILLO * (1.0 - LADRILLO.TOL_LADRILLO) - LADRILLO.caida_entrada_completa_v()
    assert v["arranca"] * (1.0 + TOL_UMBRAL_FRAC) < v_min, (
        f"UVLO de U16 ({v['arranca'] * (1 + TOL_UMBRAL_FRAC):.2f} V max) por encima del "
        f"ladrillo en su minimo ({v_min:.2f} V)")
    v_max = LADRILLO.V_LADRILLO * (1.0 + LADRILLO.TOL_LADRILLO)
    assert v["vuelve"] * (1.0 - TOL_UMBRAL_FRAC) > v_max, (
        f"OVP de U16 ({v['vuelve'] * (1 - TOL_UMBRAL_FRAC):.2f} V min) dentro del ladrillo sano")
    assert v["sobretension"] * (1.0 + TOL_UMBRAL_FRAC) < V_MAX_DCDC_V, (
        f"OVP de U16 ({v['sobretension'] * (1 + TOL_UMBRAL_FRAC):.2f} V max) deja pasar mas "
        f"de {V_MAX_DCDC_V:.0f} V a los DC-DC")

    # 3. Los tiempos del firmware cubren lo que tarda la placa.
    assert T_IGNORA_FLT_U19_S >= arranque_cadena_max_s(), (
        f"el FLT de U19 puede seguir bajo {arranque_cadena_max_s() * 1e3:.1f} ms tras cerrar "
        f"U16 y el MCU solo lo ignora {T_IGNORA_FLT_U19_S * 1e3:.0f} ms")
    assert T_CONFIRMA_SANO_S >= _rampa_s("C11", v["sobretension"]) + T_CB_MAX_S, (
        "T_CONFIRMA_SANO_S no cubre la rampa de U16 mas su tCB")

    # 4. La realizacion nominal pasa las 6 propiedades.
    _verifica_politica({})

    # 5. Los 6 mutantes DEBEN fallar (prueba de que la bateria tiene dientes).
    mutantes = (
        {"persiste_en_fram": False},
        {"filtra_rebote": False},
        {"flt_u19_gasta_intento": False},
        {"exige_crc_valido": False},
        {"ignora_flt_u19_en_arranque": False},
        {"reinicia_ventana_tras_uvlo": False},
    )
    for m in mutantes:
        try:
            _verifica_politica(m)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"el mutante {m} paso sin saltar")


def demo() -> int:
    print("recuperacion_budget v5: vigilante de entrada M5 (TPS26631 + LM74502 + MSP430FR2111)\n")
    i_min, i_nom, i_max = corriente_limite_tps26631_a()
    v = ventana_entrada_v()
    print("  1. Dimensionado del eFuse de entrada TI TPS26631 (tps2663.pdf p. 6, 7, 22):")
    print(f"    R_ILIM = {R_ILIM_KOHM:.2f} kohm (1 %) -> I_OL = {i_nom:.2f} A nom "
          f"(banda +-7 %: {i_min:.2f} .. {i_max:.2f} A)")
    print(f"    corriente del cordon a 24 V nominales: {I_CORDON_NOMINAL_A:.2f} A "
          f"(minimo de ILIM {i_min / I_CORDON_NOMINAL_A:.2f} x, se pide {MARGEN_ILIM} x); "
          f"en su peor caso {I_CORDON_CONTINUA_A:.2f} A ({i_min / I_CORDON_CONTINUA_A:.2f} x)")
    u19_min, u19_nom, u19_max = corriente_limite_tps26631_a("R34", TOL_ILIM_U19_FRAC)
    print(f"    U19: R34 = {valor('R34') / 1e3:.1f} kohm -> I_OL = {u19_nom:.3f} A nom "
          f"(banda +-10 %: {u19_min:.3f} .. {u19_max:.3f} A) contra la rama U1 en su techo "
          f"{I_RIEL_U19_A:.3f} A ({u19_min / I_RIEL_U19_A:.2f} x)")
    print(f"    corriente maxima del conector Kycon (2 pines/polo): {I_MAX_CONECTOR_POR_POLO_A:.1f} A")
    print(f"    ventana de R12/R13/R14: arranca {v['arranca']:.2f} V, apaga {v['apaga']:.2f} V, "
          f"sobretension {v['sobretension']:.2f} V (vuelve a {v['vuelve']:.2f} V)")
    print(f"    SHDN con R83 = {valor('R83') / 1e3:.0f}k: {valor('R83') * I_SHDN_MAX_A:.2f} V "
          f"< V(SHUTF) {V_SHUTF_MAX_V:.1f} V con el MCU sin levantarlo\n")
    assert valor("R83") * I_SHDN_MAX_A < V_SHUTF_MAX_V, "R83 no mantiene U16 apagado"

    print("  2. Persistencia en FRAM (TI MSP430FR2111, msp430fr2111.pdf p. 7, 20, 35):")
    print(f"    3,75 KB FRAM, {CICLOS_FRAM_MIN:.0e} ciclos, SVS <= {SVS_MSP430_MAX_V:.2f} V")
    print(f"    cupo: {N_REINTENTOS} reintentos ({N_PULSOS_MAX} pulsos max), "
          f"espera {T_ESPERA_REINTENTO_S:.1f} s, filtro de rebote {T_FILTRO_REBOTE_S*1000:.0f} ms")
    print(f"    intento confirmado sano a los {T_CONFIRMA_SANO_S * 1e3:.0f} ms; FLT de U19 "
          f"ignorado {T_IGNORA_FLT_U19_S * 1e3:.0f} ms (arranque de la cadena <= "
          f"{arranque_cadena_max_s() * 1e3:.1f} ms)")
    print(f"    rearme sano tras {T_REARME_SANO_S:.0f} s; rearme de abandono solo por "
          f"boton dedicado >= {T_BOTON_REARME_S:.1f} s\n")

    _autocomprobacion()
    print("  3. Autoprueba de maquina de estados y 6 mutantes:")
    print("    [verde] corto con colapso de V_in: 4 pulsos exactos y ABANDONADO persistente")
    print("    [verde] rebotes de < 100 ms: 0 intentos gastados")
    print("    [verde] fallo de riel (FLT de U19 por P1.2): gasta un intento; persistente, "
          "4 pulsos y ABANDONADO")
    print("    [verde] FRAM con CRC16 corrupto: arranca en ABANDONADO (fallo seguro)")
    print("    [verde] FLT de U19 durante su arranque: no abandona")
    print("    [verde] bajon de entrada con U16 cerrando solo: 0 intentos gastados")
    print("    [verde] los 6 mutantes (sin FRAM, sin antirrebote, abandono al 1er FLT de U19, "
          "sin CRC, sin ventana de arranque, ventana sin reiniciar tras UVLO) saltan\n")

    print("OK: recuperacion_budget.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
