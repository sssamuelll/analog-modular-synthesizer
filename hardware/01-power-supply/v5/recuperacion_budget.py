"""Reintentos con abandono y persistencia en FRAM del vigilante M5 (T24).

    python recuperacion_budget.py

Resuelve la parte gobernable de **T24 / M5 / H-V2-RECUPERACION** (firmada en
D-V4 el 2026-09-08 y detallada en `2026-10-22-fuente-v5-piezas-propuesta.md`
sec. 9.2) con piezas versionadas en `docs/reference/datasheets/`:

  1. **Interruptor de entrada en serie (24 V):** eFuse **TI TPS26630**
     (`tps2663.pdf` p. 6-8, 22) en modo latch, precedido por el controlador de
     bloqueo de polaridad inversa **TI LM74502** (`lm74502.pdf` p. 1, -65 V).
     - `RON_max = 53 mohm` entre -40 y +125 C (`tps2663.pdf` p. 7).
     - Limite de corriente programado con `R_ILIM = 4,02 kohm` (E96 1 %):
       segunda ecuacion de diseno `I_OL = 18,1 / R_ILIM(kohm) = 4,502 A` nominal
       (`tps2663.pdf` p. 22 ec. 5), con banda de exactitud de `+-7 %` a 4,5 A
       (`tps2663.pdf` p. 7: `4,185 A .. 4,815 A`), por encima de los `2,69 A`
       continuos del cordon y por debajo de los `7,5 A/pin` del conector Kycon.
     - Pin `SHDN` con pull-down al retorno DC (`V(SHUTF) = 0,8 V` max, p. 7):
       mientras el MCU no este vivo y autorice, el eFuse permanece apagado.

  2. **Decisor con memoria no volatil instantanea:** **TI MSP430FR2111**
     (`msp430fr2111.pdf` p. 1, 7, 20, 35):
     - `3,75 KB` de FRAM sin borrado previo de pagina y con `10^15` ciclos de
       escritura (`msp430fr2111.pdf` p. 35): escribe la cuenta de intentos y la
       bandera `ABANDONADO` + `CRC16` ANTES de levantar `SHDN`, en microsegundos.
     - Supervisor de alimentacion `SVS` integrado (`1,71..1,99 V`, p. 20).
     - Si al arrancar el `CRC16` de la FRAM no es valido, entra directamente en
       estado `ABANDONADO` (fallo seguro).

  3. **Politica verificada por maquina de estados + 4 mutantes de autoprueba:**
     - `N_REINTENTOS = 3` (4 pulsos de intento en total: 1 inicial + 3 reintentos).
     - `T_ESPERA_REINTENTO_S = 1,0 s` entre intentos.
     - `T_FILTRO_REBOTE_S = 0,100 s` (100 ms): desconexiones o rebotes del
       enchufe de menos de 100 ms o caidas de red no gastan cupo de intentos.
     - `T_REARME_SANO_S = 60,0 s`: 60 s continuos sin fallo ponen la cuenta a 0.
     - **Sobretension de riel** (`FLT` del eFuse OVP de `U1` o crowbar de rack):
       abandono inmediato en el primer pulso, sin reintentos.
     - **Un abandono NO se borra desenchufando:** persiste en FRAM y solo se
       suelta manteniendo pulsado el boton dedicado durante `>= 2,0 s` con la
       entrada de 24 V dentro de la ventana valida (`20..30 V`).

  4. **Alcance honesto (T24):** un corto en el cordon del ladrillo *aguas arriba*
     del vigilante M5 no pasa por el `TPS26630`; depende del hiccup nativo del
     ladrillo (`H-PL-ABANDONO-FUENTE`).
"""
from __future__ import annotations

from dataclasses import dataclass

# --- Parametros electricos de hoja (tps2663.pdf y msp430fr2111.pdf) ---------
R_ILIM_KOHM = 4.02                        # E96 1 %
K_ILIM_TPS26630_A_KOHM = 18.1             # tps2663.pdf p. 22 ec. (5): R = 18,1 / I_OL
TOL_ILIM_TPS26630_FRAC = 0.07             # +-7 % en tps2663.pdf p. 7
I_CORDON_CONTINUA_A = 2.691               # de ladrillo_budget.py (64,58 W / 24 V)
I_MAX_CONECTOR_POR_POLO_A = 15.0          # Kycon KPJX-PM-4S / KPPX-4P: 2 x 7,5 A

V_UVLO_ARRANQUE_V = 20.0                  # arranca con >= 20,0 V
V_UVLO_APAGADO_V = 18.0                   # apaga con <= 18,0 V
V_OVP_ENTRADA_V = 30.0                    # corta por sobretension en >= 30,0 V
V_SHUTF_MAX_V = 0.80                      # tps2663.pdf p. 7
SVS_MSP430_MAX_V = 1.99                   # msp430fr2111.pdf p. 20
CICLOS_FRAM_MIN = 10**15                  # msp430fr2111.pdf p. 35

# --- Parametros temporales de la maquina de estados -------------------------
N_REINTENTOS = 3                          # 1 intento inicial + 3 reintentos = 4 pulsos
N_PULSOS_MAX = 1 + N_REINTENTOS
T_ESPERA_REINTENTO_S = 1.0
T_FILTRO_REBOTE_S = 0.100
T_REARME_SANO_S = 60.0
T_BOTON_REARME_S = 2.0


def corriente_limite_tps26630_a() -> tuple[float, float, float]:
    """Devuelve (min_a, nom_a, max_a) del limite de corriente del TPS26630."""
    nom = K_ILIM_TPS26630_A_KOHM / R_ILIM_KOHM
    return (
        nom * (1.0 - TOL_ILIM_TPS26630_FRAC),
        nom,
        nom * (1.0 + TOL_ILIM_TPS26630_FRAC),
    )


def _crc16_ccitt(intentos: int, abandonado: bool) -> int:
    datos = bytes([intentos & 0xFF, 1 if abandonado else 0])
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
    abandonado: bool = False
    crc: int = _crc16_ccitt(0, False)

    def escribir(self, intentos: int, abandonado: bool) -> None:
        self.intentos_gastados = intentos
        self.abandonado = abandonado
        self.crc = _crc16_ccitt(intentos, abandonado)

    def es_valida(self) -> bool:
        return self.crc == _crc16_ccitt(self.intentos_gastados, self.abandonado)


class VigilanteM5:
    """Simulador discreto del vigilante M5 (TPS26630 + MSP430FR2111 FRAM)."""

    def __init__(self, fram: ImagenFRAM | None = None, *,
                 persiste_en_fram: bool = True,
                 filtra_rebote: bool = True,
                 ovp_abandona_inmediato: bool = True,
                 exige_crc_valido: bool = True) -> None:
        self.fram = fram if fram is not None else ImagenFRAM()
        self.persiste_en_fram = persiste_en_fram
        self.filtra_rebote = filtra_rebote
        self.ovp_abandona_inmediato = ovp_abandona_inmediato
        self.exige_crc_valido = exige_crc_valido

        self.intentos_ram = 0
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
            self.abandonado_ram = True
            return
        if self.persiste_en_fram:
            self.intentos_ram = self.fram.intentos_gastados
            self.abandonado_ram = self.fram.abandonado
        else:
            self.intentos_ram = 0
            self.abandonado_ram = False

    def _sincronizar_fram(self) -> None:
        if self.persiste_en_fram:
            self.fram.escribir(self.intentos_ram, self.abandonado_ram)

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
        """Ejecuta un intento de cierre del TPS26630 si la politica lo autoriza."""
        if self.abandonado_ram:
            self.efuse_habilitado = False
            return False
        if not (V_UVLO_ARRANQUE_V <= v_in < V_OVP_ENTRADA_V):
            self.efuse_habilitado = False
            return False

        # Se anota el intento en FRAM ANTES de cerrar el interruptor:
        self.intentos_ram += 1
        if self.intentos_ram >= N_PULSOS_MAX and fallo is not None:
            self.abandonado_ram = True
        self._sincronizar_fram()

        self.pulsos_emitidos += 1
        self.efuse_habilitado = True

        if fallo is None:
            return True

        # Hubo fallo al cerrar el eFuse:
        self.efuse_habilitado = False
        self.tiempo_sano_acumulado_s = 0.0
        if fallo == "ovp_riel" and self.ovp_abandona_inmediato:
            self.abandonado_ram = True
            self._sincronizar_fram()
        elif self.intentos_ram >= N_PULSOS_MAX:
            self.abandonado_ram = True
            self._sincronizar_fram()

        if cae_alimentacion_en_corto:
            self.apagon_de_entrada()
        return False

    def marcha_sana(self, duracion_s: float) -> None:
        if not self.efuse_habilitado or self.abandonado_ram:
            return
        self.tiempo_sano_acumulado_s += duracion_s
        if self.tiempo_sano_acumulado_s >= T_REARME_SANO_S:
            self.intentos_ram = 0
            self._sincronizar_fram()

    def pulsar_boton_rearme(self, duracion_s: float, *, v_in: float = 24.0) -> bool:
        if duracion_s >= T_BOTON_REARME_S and (V_UVLO_ARRANQUE_V <= v_in < V_OVP_ENTRADA_V):
            self.intentos_ram = 0
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

    # Propiedad 3: sobretension de riel (FLT de #334 o crowbar) abandona al 1er pulso.
    v3 = VigilanteM5(**cls_kwargs)
    for _ in range(4):
        v3.intento_energizar(v_in=24.0, fallo="ovp_riel")
    assert v3.pulsos_emitidos == 1 and v3.abandonado_ram, (
        f"OVP de riel emitio {v3.pulsos_emitidos} pulsos en vez de abandonar al 1ro")

    # Propiedad 4: FRAM con CRC corrupto al arrancar entra en ABANDONADO sin pulsar.
    fram_rota = ImagenFRAM(intentos_gastados=0, abandonado=False, crc=0x0000)
    v4 = VigilanteM5(fram=fram_rota, **cls_kwargs)
    assert v4.abandonado_ram and not v4.intento_energizar(v_in=24.0), (
        "arranco con CRC de FRAM corrupto sin ir a fallo seguro")


def _autocomprobacion() -> None:
    # 1. El limite de corriente del TPS26630 (R_ILIM = 4,02 kohm) deja pasar la
    #    corriente continua del cordon (2,69 A) y protege el conector (15 A/polo).
    i_min, i_nom, i_max = corriente_limite_tps26630_a()
    assert i_min > I_CORDON_CONTINUA_A * 1.5, (
        f"banda baja de ILIM ({i_min:.2f} A) demasiado cerca de {I_CORDON_CONTINUA_A:.2f} A")
    assert i_max < I_MAX_CONECTOR_POR_POLO_A, (
        f"banda alta de ILIM ({i_max:.2f} A) supera el conector ({I_MAX_CONECTOR_POR_POLO_A:.1f} A)")

    # 2. La realizacion nominal pasa las 4 propiedades.
    _verifica_politica({})

    # 3. Los 4 mutantes DEBEN fallar (prueba de que la bateria tiene dientes).
    mutantes = (
        {"persiste_en_fram": False},
        {"filtra_rebote": False},
        {"ovp_abandona_inmediato": False},
        {"exige_crc_valido": False},
    )
    for m in mutantes:
        try:
            _verifica_politica(m)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"el mutante {m} paso sin saltar")


def demo() -> int:
    print("recuperacion_budget v5: vigilante de entrada M5 (TPS26630 + LM74502 + MSP430FR2111)\n")
    i_min, i_nom, i_max = corriente_limite_tps26630_a()
    print("  1. Dimensionado del eFuse de entrada TI TPS26630 (tps2663.pdf p. 7, 22):")
    print(f"    R_ILIM = {R_ILIM_KOHM:.2f} kohm (1 %) -> I_OL = {i_nom:.2f} A nom "
          f"(banda +-7 %: {i_min:.2f} .. {i_max:.2f} A)")
    print(f"    corriente continua del cordon: {I_CORDON_CONTINUA_A:.2f} A "
          f"(holgura al minimo de ILIM: +{i_min - I_CORDON_CONTINUA_A:.2f} A)")
    print(f"    corriente maxima del conector Kycon (2 pines/polo): {I_MAX_CONECTOR_POR_POLO_A:.1f} A\n")

    print("  2. Persistencia en FRAM (TI MSP430FR2111, msp430fr2111.pdf p. 7, 20, 35):")
    print(f"    3,75 KB FRAM, {CICLOS_FRAM_MIN:.0e} ciclos, SVS <= {SVS_MSP430_MAX_V:.2f} V")
    print(f"    cupo: {N_REINTENTOS} reintentos ({N_PULSOS_MAX} pulsos max), "
          f"espera {T_ESPERA_REINTENTO_S:.1f} s, filtro de rebote {T_FILTRO_REBOTE_S*1000:.0f} ms")
    print(f"    rearme sano tras {T_REARME_SANO_S:.0f} s; rearme de abandono solo por "
          f"boton dedicado >= {T_BOTON_REARME_S:.1f} s\n")

    _autocomprobacion()
    print("  3. Autoprueba de maquina de estados y 4 mutantes:")
    print("    [verde] corto con colapso de V_in: 4 pulsos exactos y ABANDONADO persistente")
    print("    [verde] rebotes de < 100 ms: 0 intentos gastados")
    print("    [verde] sobretension de riel (FLT #334 / crowbar): abandono en el 1er pulso")
    print("    [verde] FRAM con CRC16 corrupto: arranca en ABANDONADO (fallo seguro)")
    print("    [verde] los 4 mutantes (sin FRAM, sin antirrebote, OVP con reintento, sin CRC) saltan\n")

    print("OK: recuperacion_budget.py v5")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo())
