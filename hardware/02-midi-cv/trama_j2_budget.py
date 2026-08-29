"""El J2 punto a punto, enlace por enlace: lo declarado cabe en lo sancionado.

    python trama_j2_budget.py

NACE CON OFICIO NUEVO. La ficha vieja (orquestacion S10, issue #180) lo
describia como "el arbitro que suma todos los modulos con su tasa declarada
contra un techo comun". Ese oficio murio antes de nacer: el J2 punto a punto
(docs/superpowers/specs/2026-08-25-j2-punto-a-punto-design.md, D6) convierte
cada ranura en un enlace privado con su propio reloj, y R-P1 lo dice sin
rodeos: "Un guion que sume ocupaciones de enlaces distintos contra un techo
comun esta reconstruyendo el bus que este papel mata".

Lo que hace este guion, en una linea: POR ENLACE, asevera que la tasa
declarada por trama cabe en el techo de ocupacion del enlace AL RELOJ AL QUE
ESE ENLACE CORRE HOY. No publica ninguna suma global, a proposito.

--- El reloj de cada enlace (D2) ---------------------------------------------

  reloj = min(lo que da el maestro, lo que declara el esclavo, lo sancionado)

  * MAESTRO: constante del diseno del cerebro, por ranura (D3). El chip del
    cerebro NO esta sellado (#210 S0.1, premisa 1; #209). Sin hoja no hay
    cifra, y aqui no se inventa: el minimo se toma sobre los otros dos
    terminos y el guion lo dice en la salida.
  * DECLARADO: lo trae el esclavo en su EEPROM de identidad (campo nuevo, D2).
    Hoy solo la Voz tiene papel del que derivarlo: D8 la lleva al limite
    electrico del esclavo, la fila "target full duplex" de la Tabla 99 del
    N657 LEIDA CON SU NOTA (2) -- 34,5 MHz, no los 50 de portada. La cuenta
    vive en enlace_budget.py (F_PELDANO_2_HZ) y de ahi se importa.
  * SANCIONADO: propiedad de la RANURA, no del modulo. Lo escribe el bring-up
    del cerebro con osciloscopio (R-P4) en la tabla de sancion del firmware
    del cerebro, versionada en el repo: software/nucleo/fw/sancion_j2.csv.
    Este guion la LEE, no la duplica. Una ranura sin fila corre al PISO
    LEGADO.

--- El piso legado (D2) ------------------------------------------------------

No son "10 MHz" a secas: es el MENOR entre los 10 MHz del contrato de j2.rs y
el reloj que el bring-up del modulo 3 ADOPTO, si esta registrado -- Paso 8 de
check_bringup.py: "ESTE numero es el contrato, no el <=10 del spec". Se lee de
hardware/03-vco/notes/medidas.csv. Hoy la fila esta vacia: piso = 10 MHz.

--- Codigos de salida (convencion del repo, gates.py) ------------------------

  0  VERDE: toda ranura activa tiene papel, reloj declarado y fila de sancion,
     y lo declarado cabe.
  2  HUECO: lo declarado cabe al reloj al que el enlace corre HOY, pero falta
     la medida (ranura activa sin fila de sancion, R-P4) o falta el papel
     (ranura activa asignada a un modulo que todavia no existe). Es "trabajo
     a medias", no fallo -- la misma convencion que check_bringup.py mientras
     falten medidas.
  1  ROJO: lo declarado NO cabe al reloj de operacion; o un modulo CON papel
     no declara reloj (R-P2: "falla si un modulo no declara reloj"); o un
     mensaje declarado dura mas de lo que R-E1 permite.

--- Lo que NO esta confirmado ------------------------------------------------

  * La cadencia del estado de compuerta (R-E10) la elige el oido, no el
    presupuesto (R-E11, evento S4). Su fila esta RESERVADA aqui con cadencia
    sin decidir, como el papel del evento manda ("R-E11 nace con su linea
    reservada en ese guion"), y se imprime lo que costaria a las tres
    candidatas de aquel papel.
  * La subida (MISO privado, D4): sondeo de jacks a 20 Hz y salud a 1 Hz
    tienen cadencia declarada (orquestacion S7.1) pero NO tamano declarado.
    Se listan sin bits: cuentan cero y se dice. Es la advertencia de C8 del
    evento que sobrevivio: "el piso sigue siendo optimista porque sigue sin
    contar la telemetria ni el sondeo de jacks".
  * La subida se cuenta APARTE de la bajada, que es conservador: D4 permite
    que viaje en el mismo giro, y entonces sobra lo que aqui se suma.
  * El SPI privado de la Voz cuenta el tono a 1 kHz (voz-total S3.1, que es
    el minimo de R-M4); el lazo lo manda a 8 kHz. No es de este guion: lo
    recorre spi_privado_budget.py en la tanda 2 del #214.
"""
from __future__ import annotations

import csv
import os
import sys
from dataclasses import dataclass, field

from enlace_budget import F_PELDANO_2_HZ

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV_SANCION = os.path.join(AQUI, "..", "..", "software", "nucleo", "fw",
                           "sancion_j2.csv")
CSV_MEDIDAS_VCO = os.path.join(AQUI, "..", "03-vco", "notes", "medidas.csv")

# --- citado ------------------------------------------------------------------
F_CONTRATO_HZ = 10e6            # j2.rs cabecera: "SPI modo 1, <=10 MHz". Con
                                # #210 D2 deja de ser techo global y pasa a
                                # ser el PISO LEGADO de una ranura sin sancion
TECHO_OCUPACION_ENLACE = 0.50   # D6: "mientras no derive uno mejor, hereda
                                # el 50 % -- por enlace, como piso conservador
                                # con origen citado". El origen es
                                # latencia_mano_budget.py, TECHO_OCUPACION
T_MENSAJE_MAX_S = 100e-6        # R-E1 (evento D4): "Ningun mensaje del J2
                                # puede durar mas de 100 us". Deriva de
                                # tiempo_budget.py: 0,1 x OBJETIVO_S (1 ms).
                                # tiempo_budget.py lo comprueba contra esto
F_LAZO_HZ = 8_000.0             # latencia_mano_budget.py, lazo desacoplado
                                # (2026-08-24). Aquel guion lo RECALCULA contra
                                # este enlace y asevera que sale este mismo
                                # numero: si cambia alla, canta alla
BITS_BLOQUE_TONO = 288          # orquestacion R-M4: 16 x 16 bits + cabecera
BITS_ESTADO_COMPUERTA = 16      # evento R-E10: "16 bits por modulo"
BITS_EVENTO = 16 + 2 + 16 + 16  # evento S3: destino 16, borde 2, tono 16, y
                                # fuerza 16 (derivada en #230 contra
                                # M2-115-U). SIN cabecera declarada: la pone
                                # el codec del cambio 1 cuando exista
BITS_CROSSPOINT = 256           # issue #171: "los 256 bits del crosspoint";
                                # viaja por el enlace de la Voz (E-3)
BITS_SONDEO_PANEL = 256         # latencia_mano_budget.py: "bloque de vuelta
                                # del panel: deltas + cabecera"
CADENCIAS_R_E11_HZ = (20.0, 100.0, 200.0)   # evento S4, la tabla de R-E11
F_JACKS_HZ = 20.0               # orquestacion S7.1: "Sondeo cada 50 ms"
F_SALUD_HZ = 1.0                # orquestacion S7.1: "1 Hz"


@dataclass(frozen=True)
class Fila:
    """Un flujo declarado de UN enlace. bits=None: cadencia sin tamano."""
    que: str
    bits: int | None
    hz: float | None            # None: no periodico (al ocurrir) o sin decidir
    fuente: str
    subida: bool = False

    def bit_s(self) -> float:
        if self.bits is None or self.hz is None:
            return 0.0
        return self.bits * self.hz


@dataclass(frozen=True)
class Ranura:
    fisica: int | None          # numero del IDC en el cerebro; None: sin
                                # asignar (se elige por longitud, #210 S4.2)
    modulo: str
    estado: str                 # activa | reservada | libre
    papel: str | None           # de donde sale lo declarado; None: no existe
    reloj_declarado_hz: float | None
    trafico: tuple[Fila, ...] = field(default_factory=tuple)


F_MAESTRO_HZ: float | None = None   # #210 S0.1 premisa 1: el chip del cerebro
                                    # esta "dirigida, no sellada". Sin hoja
                                    # no hay cifra. NO es un 0, es un hueco

RANURAS: tuple[Ranura, ...] = (
    Ranura(
        fisica=1,               # cerebro S4: los pines 9-12 "solo se cablean
                                # en la ranura 1, rotulada VCO / TUNE"; D9 los
                                # usa para la autopista del enlace de la Voz
        modulo="Voz total",
        estado="activa",
        papel="voz-total (E-3: una sola bajada) + #210 D8",
        reloj_declarado_hz=F_PELDANO_2_HZ,
        trafico=(
            Fila("bloque de tono, 16x16 + cabecera", BITS_BLOQUE_TONO,
                 F_LAZO_HZ, "R-M4 + latencia_mano (lazo 8 kHz)"),
            Fila("estado de compuerta (R-E10)", BITS_ESTADO_COMPUERTA, None,
                 "R-E11: cadencia RESERVADA, la elige el oido"),
            Fila("evento de nota", BITS_EVENTO, None,
                 "evento S3: al ocurrir, sin tasa declarada"),
            Fila("bajada del crosspoint (bahia)", BITS_CROSSPOINT, None,
                 "#171 + orquestacion S7.1: al cambiar"),
            Fila("estado del patch / sondeo de jacks", None, F_JACKS_HZ,
                 "orquestacion S7.1: sin tamano declarado", subida=True),
            Fila("salud (T, VREF, identidad)", None, F_SALUD_HZ,
                 "orquestacion S7.1: sin tamano declarado", subida=True),
        ),
    ),
    Ranura(
        fisica=None,            # "la ranura que E-3 libero"; cual de las
                                # ocho es, lo decide el layout de fila
        modulo="modulo de mandos (#178)",
        estado="activa",
        papel=None,             # #178 abierto: ni micro ni papel todavia
        reloj_declarado_hz=None,
        trafico=(
            Fila("sondeo del panel, deltas + cabecera", BITS_SONDEO_PANEL,
                 F_LAZO_HZ, "latencia_mano: el canal de vuelta que #178 "
                 "tiene que crear", subida=True),
        ),
    ),
    Ranura(None, "modulo 8 (reserva)", "reservada", None, None),
    Ranura(None, "modulo 9 (reserva)", "reservada", None, None),
    Ranura(None, "libre", "libre", None, None),
    Ranura(None, "libre", "libre", None, None),
    Ranura(None, "libre", "libre", None, None),
    Ranura(None, "libre", "libre", None, None),
)
assert len(RANURAS) == 8, "cerebro S3: 'Enlace J2 x8 -- Ocho IDC 2x6'"


# --- lo que se lee del repo, no se declara -----------------------------------
def leer_sancion(ruta: str = CSV_SANCION) -> dict[int, dict[str, str]]:
    """La tabla de sancion (D2): una fila por ranura fisica. Vacia hoy."""
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as fh:
        lineas = [ln for ln in fh if ln.strip() and not ln.startswith("#")]
    filas = {}
    for f in csv.DictReader(lineas):
        if not (f.get("ranura") or "").strip():
            continue
        filas[int(f["ranura"])] = f
    return filas


def piso_legado_hz(ruta_medidas: str = CSV_MEDIDAS_VCO) -> float:
    """D2: min(10 MHz del contrato, reloj adoptado en el bring-up del modulo 3).

    La fila es la del Paso 8 de check_bringup.py, "reloj_SPI_adoptado". Si no
    hay medida, manda el contrato.
    """
    adoptado = None
    if os.path.exists(ruta_medidas):
        with open(ruta_medidas, encoding="utf-8") as fh:
            for f in csv.DictReader(fh):
                if f.get("magnitud") == "reloj_SPI_adoptado" and \
                        (f.get("medido") or "").strip():
                    adoptado = float(f["medido"]) * 1e6
    return F_CONTRATO_HZ if adoptado is None else min(F_CONTRATO_HZ, adoptado)


# --- el modelo: por enlace, sin suma ------------------------------------------
@dataclass(frozen=True)
class Enlace:
    ranura: Ranura
    sancionado_hz: float | None
    piso_hz: float

    def reloj_operacion_hz(self) -> float:
        """D2. Sin fila de sancion, R-P4: el enlace corre al piso legado."""
        terminos = [t for t in (F_MAESTRO_HZ, self.ranura.reloj_declarado_hz,
                                self.sancionado_hz) if t]
        if self.sancionado_hz is None:
            declarado = self.ranura.reloj_declarado_hz
            return min(self.piso_hz, declarado) if declarado else self.piso_hz
        return min(terminos)

    def ocupacion(self, f_hz: float | None = None) -> float:
        """Bits por segundo declarados sobre los que el reloj da. Solo ESTE
        enlace: aqui no entra ninguna fila de otra ranura (R-P1)."""
        f = self.reloj_operacion_hz() if f_hz is None else f_hz
        return sum(x.bit_s() for x in self.ranura.trafico) / f

    def trama_mas_larga_bits(self) -> int:
        return max((x.bits for x in self.ranura.trafico if x.bits), default=0)

    def t_trama_mas_larga_s(self) -> float:
        return self.trama_mas_larga_bits() / self.reloj_operacion_hz()

    def techo_lazo_hz(self, bits_por_giro: int) -> float:
        """A que cadencia un flujo de `bits_por_giro` toca el techo de ESTE
        enlace. Es el heredero del '9,19 kHz' que D6 mando recalcular."""
        return TECHO_OCUPACION_ENLACE * self.reloj_operacion_hz() / bits_por_giro


def enlaces(ranuras: tuple[Ranura, ...] = RANURAS,
            sancion: dict[int, dict[str, str]] | None = None,
            piso_hz: float | None = None) -> list[Enlace]:
    sancion = leer_sancion() if sancion is None else sancion
    piso = piso_legado_hz() if piso_hz is None else piso_hz
    out = []
    for r in ranuras:
        fila = sancion.get(r.fisica) if r.fisica is not None else None
        s = float(fila["reloj_sancionado_MHz"]) * 1e6 if fila else None
        out.append(Enlace(r, s, piso))
    return out


def enlace(modulo: str) -> Enlace:
    """El enlace de un modulo por nombre. Lo usan latencia_mano y tiempo."""
    for e in enlaces():
        if e.ranura.modulo.startswith(modulo):
            return e
    raise KeyError(modulo)


def evaluar(lista: list[Enlace]) -> tuple[list[str], list[str]]:
    """(fallos, huecos). Puro: lo mismo que decide el codigo de salida se puede
    correr sobre ranuras de mentira en la autocomprobacion."""
    fallos, huecos = [], []
    for e in lista:
        r = e.ranura
        if r.estado != "activa":
            continue
        if r.papel is None:
            huecos.append(f"{r.modulo}: ranura activa sin papel -- ni reloj "
                          "declarado ni dialecto; corre al piso legado")
        elif r.reloj_declarado_hz is None:
            fallos.append(f"{r.modulo}: tiene papel y NO declara reloj (R-P2)")
        if e.sancionado_hz is None:
            huecos.append(f"{r.modulo}: sin fila de sancion (R-P4) -- piso "
                          f"legado de {e.piso_hz/1e6:.0f} MHz en vigor")
        ocu = e.ocupacion()
        if ocu > TECHO_OCUPACION_ENLACE:
            fallos.append(f"{r.modulo}: {ocu:.1%} de ocupacion a "
                          f"{e.reloj_operacion_hz()/1e6:.1f} MHz contra un "
                          f"techo del {TECHO_OCUPACION_ENLACE:.0%}")
        for x in r.trafico:
            if x.bits and x.bits / e.reloj_operacion_hz() > T_MENSAJE_MAX_S:
                fallos.append(f"{r.modulo}: '{x.que}' dura "
                              f"{x.bits/e.reloj_operacion_hz()*1e6:.0f} us "
                              f"y R-E1 permite {T_MENSAJE_MAX_S*1e6:.0f}")
    return fallos, huecos


# --- autocomprobacion: que muerda, sobre ranuras de mentira -------------------
def autocomprobacion() -> None:
    fila = Fila("x", 288, 8_000.0, "a mano")
    sola = Ranura(1, "A", "activa", "papel", 20e6, (fila,))
    # 288 bits x 8 kHz = 2,304 Mb/s; a 10 MHz son el 23,04 %.
    e = Enlace(sola, None, 10e6)
    assert abs(e.ocupacion() - 0.2304) < 1e-6, e.ocupacion()
    assert e.reloj_operacion_hz() == 10e6, "sin sancion manda el piso"
    # Con sancion, manda el minimo de D2 (declarado 20, sancionado 15).
    assert Enlace(sola, 15e6, 10e6).reloj_operacion_hz() == 15e6
    assert Enlace(sola, 30e6, 10e6).reloj_operacion_hz() == 20e6
    # R-P1: las filas de OTRA ranura no mueven la ocupacion de esta.
    # 900 bits x 8 kHz a 10 MHz = 72 % (revienta el techo) y 90 us por
    # trama (cabe en R-E1): un fallo, y solo uno, por la razon correcta.
    gorda = Ranura(2, "B", "activa", "papel", 20e6,
                   (Fila("y", 900, 8_000.0, "a mano"),))
    assert Enlace(sola, None, 10e6).ocupacion() == e.ocupacion()
    assert Enlace(gorda, None, 10e6).ocupacion() > TECHO_OCUPACION_ENLACE
    # El juez: sin sancion es HUECO, no fallo; reventar el techo es FALLO;
    # papel sin reloj es FALLO (R-P2); activa sin papel es HUECO.
    f, h = evaluar([Enlace(sola, None, 10e6)])
    assert not f and len(h) == 1, (f, h)
    f, h = evaluar([Enlace(gorda, 10e6, 10e6)])   # sancionada a 10: 72 %
    assert len(f) == 1 and not h, (f, h)
    # Y la misma ranura sancionada a 20 MHz cabe (36 %): el juez mira el
    # reloj de operacion, no el piso.
    assert evaluar([Enlace(gorda, 20e6, 10e6)]) == ([], [])
    muda = Ranura(3, "C", "activa", "papel", None, (fila,))
    f, _ = evaluar([Enlace(muda, 10e6, 10e6)])
    assert any("R-P2" in x for x in f), f
    huerfana = Ranura(None, "D", "activa", None, None, ())
    f, h = evaluar([Enlace(huerfana, None, 10e6)])
    assert not f and len(h) == 2, (f, h)
    # R-E1: un mensaje de 1001 bits a 10 MHz dura 100,1 us y no pasa.
    larga = Ranura(4, "E", "activa", "papel", 10e6,
                   (Fila("z", 1001, None, "a mano"),))
    f, _ = evaluar([Enlace(larga, 10e6, 10e6)])
    assert any("R-E1" in x for x in f), f
    # Y las ranuras que no estan activas no juzgan nada.
    assert evaluar([Enlace(Ranura(None, "L", "libre", None, None), None, 10e6)]) == ([], [])
    # El piso legado: un CSV con 6,5 MHz adoptados baja el piso a 6,5.
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("paso,magnitud,unidad,medido,placa,fecha,nota\n"
                 "8,reloj_SPI_adoptado,MHz,6.5,,,\n")
        ruta = fh.name
    try:
        assert piso_legado_hz(ruta) == 6.5e6
    finally:
        os.remove(ruta)
    assert piso_legado_hz(os.devnull) == F_CONTRATO_HZ


def main() -> int:
    autocomprobacion()
    lista = enlaces()
    piso = lista[0].piso_hz

    print("TRAMA DEL J2 -- por enlace, sin suma global (R-P1)\n")
    print(f"  piso legado (D2)        {piso/1e6:5.1f} MHz   min(contrato j2.rs, "
          "adoptado en bring-up del modulo 3)")
    m = "SIN SELLAR (#209): no acota" if F_MAESTRO_HZ is None else f"{F_MAESTRO_HZ/1e6:.1f} MHz"
    print(f"  maestro (cerebro)       {m}")
    print(f"  techo por enlace (D6)   {TECHO_OCUPACION_ENLACE:.0%}")
    print(f"  tabla de sancion        {os.path.relpath(CSV_SANCION, AQUI)}"
          f"  ({len(leer_sancion())} filas)\n")

    print(f"  {'ranura':>6}  {'modulo':26}  {'estado':9}  {'declarado':>9}  "
          f"{'sancion':>8}  {'corre a':>8}  {'ocupacion':>9}")
    for e in lista:
        r = e.ranura
        if r.estado == "libre":
            continue
        dec = f"{r.reloj_declarado_hz/1e6:.1f} MHz" if r.reloj_declarado_hz else "--"
        san = f"{e.sancionado_hz/1e6:.1f} MHz" if e.sancionado_hz else "--"
        ocu = f"{e.ocupacion():.1%}" if r.trafico else "--"
        fis = str(r.fisica) if r.fisica else "?"
        print(f"  {fis:>6}  {r.modulo:26}  {r.estado:9}  {dec:>9}  {san:>8}  "
              f"{e.reloj_operacion_hz()/1e6:5.1f} MHz  {ocu:>9}")

    voz = enlace("Voz total")
    print("\nel enlace de la Voz, fila por fila:\n")
    print(f"  {'flujo':40}  {'bits':>5}  {'cadencia':>9}  {'bit/s':>9}  "
          f"{'% a ' + f'{voz.reloj_operacion_hz()/1e6:.0f}':>8}")
    for x in voz.ranura.trafico:
        b = f"{x.bits}" if x.bits else "sin tam."
        hz = f"{x.hz:.0f} Hz" if x.hz else ("al ocurrir" if x.bits else "")
        if x.hz is None and x.bits and "R-E11" in x.fuente:
            hz = "RESERVADA"
        pct = f"{x.bit_s()/voz.reloj_operacion_hz():.2%}" if x.bit_s() else "0"
        dirc = "^" if x.subida else "v"
        print(f"  {dirc} {x.que:38}  {b:>5}  {hz:>9}  {x.bit_s():9.0f}  {pct:>8}")
    print(f"  {'':40}  {'':>5}  {'':>9}  {'':>9}  {voz.ocupacion():>8.2%}")

    print("\n  la fila reservada de R-E11, a las tres cadencias del papel del evento:")
    for hz in CADENCIAS_R_E11_HZ:
        extra = BITS_ESTADO_COMPUERTA * hz
        print(f"    {hz:5.0f} Hz  ->  {extra:6.0f} bit/s  =  "
              f"+{extra/voz.reloj_operacion_hz():.4%} del enlace")
    print("  A cualquiera de las tres es ruido de redondeo: el presupuesto no")
    print("  elige la cadencia, la elige el oido (corolario de R-E11).")

    print("\nlo que el enlace de la Voz aguanta, y lo que aguantaria sancionado:\n")
    for nombre, f in (("al piso legado (hoy)", voz.reloj_operacion_hz()),
                      ("a lo que declara (D8)", voz.ranura.reloj_declarado_hz)):
        print(f"  {nombre:24}  {f/1e6:5.1f} MHz  ocupacion {voz.ocupacion(f):6.2%}"
              f"   techo del lazo con {BITS_BLOQUE_TONO} bits: "
              f"{TECHO_OCUPACION_ENLACE*f/BITS_BLOQUE_TONO/1e3:5.1f} kHz")
    print(f"\n  El '9,19 kHz' del bus compartido esta muerto (D6). Con el enlace")
    print(f"  privado y {BITS_BLOQUE_TONO} bits por giro, el techo POR BUS del lazo es")
    print(f"  {voz.techo_lazo_hz(BITS_BLOQUE_TONO)/1e3:.1f} kHz al piso. Cual cadencia se adopta lo")
    print("  decide latencia_mano_budget.py contra los EXTREMOS, no este techo.")
    print(f"  La trama mas larga declarada, {voz.trama_mas_larga_bits()} bits, dura "
          f"{voz.t_trama_mas_larga_s()*1e6:.1f} us al piso: {voz.t_trama_mas_larga_s()/T_MENSAJE_MAX_S:.0%} "
          "de R-E1.")

    fallos, huecos = evaluar(lista)
    print()
    for x in fallos:
        print(f"  ROJO   {x}")
    for x in huecos:
        print(f"  HUECO  {x}")
    if fallos:
        print("\nROJO: lo declarado no cabe, o un modulo con papel calla su reloj.")
        return 1
    if huecos:
        print("\nHUECO: lo declarado cabe al reloj al que cada enlace corre HOY,")
        print("  pero ninguna ranura activa esta sancionada (R-P4) y el modulo de")
        print("  mandos no tiene papel. La medida la pone el bring-up del cerebro")
        print("  (#210 S8, riesgo 1); el papel, el #178.")
        return 2
    print("\nOK: todo enlace activo sancionado, y lo declarado cabe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
