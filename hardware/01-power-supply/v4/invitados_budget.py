"""Cuatro corrientes distintas que se llamaban igual, puestas en cuatro columnas.

    python invitados_budget.py

## Por que existe

Desde la fuente v4 el rack tiene CUATRO numeros que se dicen "corriente" y que
no son el mismo. Sin un guion que los ponga en fila, el que se cita en una
conversacion es el mas grande:

  1. MODULO_A    lo que el modulo Mean Well puede dar (su placa, hoja p. 2)
  2. PLACA_A     lo que el instrumento DECLARA por riel (D-F1, papel sec.1)
  3. SOSTENIDO   lo que el calor deja sostener (calor_budget.py, punto fijo)
  4. el censo    lo que una fila de 104 HP de modulos reales pide

El liston firmado dice "a la altura de la A-100PSU3 o superior". Esa frase se
puede comprobar en la columna 2 (donde es holgada) o en la 3 (donde es justa),
y solo la 3 es la que el dueno va a vivir. calor_budget.py hace esa pregunta
desde el calor; este guion la hace desde el otro lado --desde lo que se le
promete al dueno-- y ademas la traduce a las unidades en las que el dueno
compra: MILIAMPERIOS POR HP.

## El relevo de una puerta retirada

Hasta el 2026-09-03, `hardware/03-vco/consumo_total_budget.py` aseveraba una
RESERVA_INVITADOS >= 120 mA/riel. Existia porque hasta la v3 la fila de abajo
se alimentaba del riel del INSTRUMENTO, y ese aserto era el unico sitio del
arbol donde ese compromiso estaba escrito. La v4 (D-F1) le da rieles PROPIOS,
asi que la reserva vigilaba un sujeto muerto y se retiro. Aquel guion salio en
HUECO desde entonces, apuntando a este fichero por su nombre (#169). Este es
el relevo: con el aqui, aquella puerta se pone verde sola.

## Lo que este guion NO decide

  * El bus board de invitados (#169): peines, sitio, y el VALOR del PTC por
    slot. Aqui esta el censo que ese PTC tiene que dejar pasar, no el PTC.
  * El liston. Se firmo el 2026-09-03 y aqui solo se comprueba.
  * Que modulos comprara el dueno. El censo son cuatro piezas reales del papel
    sec.4.3 y sirven de cota, no de prediccion.

## La cifra incomoda, dicha aqui y no en una nota al pie

Una fila entera de 104 HP del modulo mas glotron del censo (Disting EX, 28,6
mA/HP en +12) CABE EN PLACA y NO CABE SOSTENIDA. El papel ya lo decia --"una
fila entera de Disting EX es absurda, y cabe en placa; cuanto cabe SOSTENIDO
lo dice sec.6"-- y aqui esta el numero: caben ocho, 64 de los 104 HP. En una
A-100PSU3 caben los mismos ocho. Que el liston se cumpla no significa que la
fila mas cara quepa: significa que no cabe en ninguna de las dos, y que esta
no es peor.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

DIR = os.path.dirname(os.path.abspath(__file__))
for _ruta in (DIR, os.path.join(DIR, "..", "..", "tools")):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
from calor_budget import MODULO_A, PLACA_A, PSU3_A, SOSTENIDO  # noqa: E402
from canario import borde_rojo  # noqa: E402

# --- de donde sale cada cifra del censo ------------------------------------
CITADO = "CITADO"              # ficha del fabricante, leida y con URL
AUSENTE = "AUSENTE"            # el fabricante no publica esa columna

# #169: la fila de abajo del SAM17.
FILA_HP = 104

# Los rieles de rack, con el nombre que usan calor_budget.py y el papel.
RIELES = ("rack+12", "rack-12", "rack+5")


@dataclass(frozen=True)
class Modulo:
    """Un modulo invitado del censo del papel sec.4.3, con su ficha."""

    nombre: str
    hp: int
    ma_12p: float
    ma_12n: float
    ma_5: float
    origen_5: str
    fuente: str

    def ma(self, riel: str) -> float:
        return {"rack+12": self.ma_12p,
                "rack-12": self.ma_12n,
                "rack+5": self.ma_5}[riel]

    def ma_por_hp(self, riel: str) -> float:
        return self.ma(riel) / self.hp


# Las cuatro piezas de la tabla del papel sec.4.3, cada una contra SU ficha,
# leidas el 2026-09-04. El papel solo publica la columna de +12 V; las de -12
# y +5 se fueron a buscar para esta tarea, y DOS NO COINCIDIAN con el borrador
# del plan (que traia Morphagene -65 mA y Disting EX -40 mA):
CENSO = (
    Modulo("Doepfer A-101-1", 16, 30.0, 30.0, 0.0, AUSENTE,
           "doepfer.de/a1011.htm: '+30mA (+12V) / -30mA (-12V)', "
           "'16TE / 16HP / 80.9 mm'; leido 2026-09-04"),
    Modulo("Mutable Clouds", 18, 120.0, 10.0, 0.0, AUSENTE,
           "pichenettes.github.io/mutable-instruments-documentation/modules/"
           "clouds/: '+12V current: 120mA', '-12V current: 10mA', '18HP'; "
           "leido 2026-09-04"),
    Modulo("Make Noise Morphagene", 20, 165.0, 20.0, 0.0, AUSENTE,
           "makenoisemusic.com/modules/morphagene: '165mA @ +12V', "
           "'20mA @ -12V', 'Width: 20hp'; leido 2026-09-04. El borrador del "
           "plan traia 65 mA en -12 y la ficha dice 20"),
    Modulo("Expert Sleepers Disting EX", 8, 229.0, 50.0, 0.0, AUSENTE,
           "expert-sleepers.co.uk/distingEX.html: 'Current draw: 229mA on the "
           "+12V rail, 50mA on the -12V rail', 'Panel width: 8HP'; leido "
           "2026-09-04. El borrador del plan traia 40 mA en -12 y la ficha "
           "dice 50"),
)

# Las cuatro fichas publican DOS rieles. Ninguna publica +5 V, y en Eurorack
# un modulo que usa el +5 lo declara siempre (es el riel que muchas fuentes no
# traen). Por eso el censo lleva 0,0 mA en +5 con origen AUSENTE y no CITADO:
# la cifra es una lectura de la ausencia, no de la ficha. Lo que la hace
# defendible es que el +5 de rack es el unico riel donde SOSTENIDO iguala a
# PLACA_A y a la PSU3 a la vez (4,0 A): si manana entra un modulo que declare
# +5, este censo cambia y el que decide sigue siendo el mismo aserto.
NOTA_CINCO_V = (
    "ninguna de las cuatro fichas publica columna de +5 V; el censo toma 0,0 "
    "mA con origen AUSENTE, no CITADO")


def por_hp(riel: str) -> Modulo:
    """El modulo del censo que mas pide POR HP en ese riel.

    Por HP y no en absoluto: la fila se mide en HP, y un modulo glotron y
    ancho ocupa el sitio de dos que juntos piden mas."""
    return max(CENSO, key=lambda m: m.ma_por_hp(riel))


def fila_a(ma_por_hp: float, hp: int = FILA_HP) -> float:
    """Amperios que pide una fila de `hp` a esa densidad de consumo."""
    return ma_por_hp * hp / 1000.0


def fila_peor_caso(hp: int = FILA_HP) -> dict[str, float]:
    """Amperios por riel de una fila entera del modulo mas glotron DE CADA
    RIEL. Es conservador a proposito: los tres maximos pueden ser de modulos
    distintos, asi que esta fila no existe como compra. Lo que acota es lo que
    ningun reparto del censo puede superar."""
    return {riel: fila_a(por_hp(riel).ma_por_hp(riel), hp) for riel in RIELES}


def limite_ma_hp(amperios: float, hp: int = FILA_HP) -> float:
    """La densidad de consumo que llena exactamente ese riel con esa fila."""
    return amperios * 1000.0 / hp


def caben(modulo: Modulo, amperios: float, riel: str = "rack+12") -> int:
    """Cuantas unidades enteras de ese modulo caben en esos amperios."""
    if modulo.ma(riel) <= 0.0:
        return 0
    return int(amperios * 1000.0 // modulo.ma(riel))


def _guarda_censo(p: dict[str, float]) -> None:
    """Puerta del censo contra el sostenido; su texto alimenta al canario.

    LOS DOS LADOS. Por arriba: una fila a esa densidad tiene que caber en lo
    que el calor sostiene. Por abajo: un censo a cero mA/HP no es una fila
    vacia, es una fila SIN LEER, y dejarlo pasar convierte a esta puerta en
    verde por vacio (Principio VIII)."""
    densidad = p["mas_glotron_ma_por_hp"]
    assert densidad > 0.0, (
        f"censo sin leer: {densidad:.3f} mA/HP. Cero no es una fila vacia, es "
        f"una fila que nadie censo, y con ella esta puerta pasa siempre")
    pide = fila_a(densidad)
    assert pide <= SOSTENIDO["rack+12"], (
        f"no cabe sostenida: una fila de {FILA_HP} HP a {densidad:.1f} mA/HP "
        f"pide {pide:.2f} A en +12 y el rack sostiene "
        f"{SOSTENIDO['rack+12']:.2f} A")


def _autocomprobacion() -> None:
    # 1. El orden de las columnas no es opinable: el calor solo puede
    #    RECORTAR lo declarado, nunca ampliarlo.
    for riel in RIELES:
        assert SOSTENIDO[riel] <= PLACA_A[riel] + 1e-9, (
            f"{riel}: sostenido {SOSTENIDO[riel]:.3f} A por encima de los "
            f"{PLACA_A[riel]:.3f} declarados. El derating recorta, no amplia")
        assert PLACA_A[riel] <= MODULO_A[riel] + 1e-9, (
            f"{riel}: se declaran {PLACA_A[riel]:.3f} A y el modulo da "
            f"{MODULO_A[riel]:.3f} de placa: se esta prometiendo hoja ajena")

    # 2. El liston, hecho desde el lado del dueno. Es la MISMA pregunta que
    #    guarda_liston() de calor_budget.py --alli desde el calor, aqui
    #    desde lo prometido-- y esta duplicada a proposito: si un dia una de
    #    las dos se retira, la otra sigue de pie.
    for riel, psu3 in PSU3_A.items():
        assert SOSTENIDO[riel] >= psu3, (
            f"{riel}: el instrumento promete {SOSTENIDO[riel]:.3f} A "
            f"sostenidos y la A-100PSU3 da {psu3:.3f}. El liston firmado dice "
            f"'a la altura de la PSU3 o superior', y esta por debajo")

    # 3. La fila mas cara del censo tiene que caber EN PLACA. Es lo que se
    #    compro (papel sec.4.3: "cabe en placa"), y si no cupiera, el liston
    #    se dimensiono contra un censo que nadie miro.
    peor = fila_peor_caso()
    for riel in RIELES:
        assert peor[riel] <= PLACA_A[riel], (
            f"{riel}: una fila de {FILA_HP} HP del modulo mas glotron pide "
            f"{peor[riel]:.2f} A y se declaran {PLACA_A[riel]:.2f}: el liston "
            f"se compro contra un censo que no se miro")
    # Y EL DE +5 V NO PUEDE FALLAR, porque el censo de ese riel es CERO: las
    # cuatro fichas publican dos rieles y ninguna publica +5. Aseverar 0,00
    # contra 4,00 no vigila nada, asi que lo que se asevera es la CAUSA --que
    # el censo de +5 es una ausencia declarada y no una lectura-- para que
    # nadie lea ese verde como si midiera algo. El dia que un invitado declare
    # +5, esta comprobacion salta y el aserto de arriba pasa a tener dientes.
    assert all(m.origen_5 == AUSENTE and m.ma_5 == 0.0 for m in CENSO), (
        "algun modulo del censo declara +5 V. Entonces el aserto de la fila en "
        "+5 deja de comparar 0,00 contra 4,00 y empieza a medir: quita esta "
        "comprobacion, que solo existe para decir que hoy no mide nada")
    assert peor["rack+5"] == 0.0, (
        f"la fila peor en +5 V pide {peor['rack+5']:.2f} A y el censo de ese "
        f"riel es cero: una de las dos cosas es mentira")

    # 4. El liston, traducido a las unidades de la fila. LOS DOS LADOS: por
    #    abajo no puede quedar por debajo de lo que da la PSU3 en esa misma
    #    fila --es el liston otra vez-- y por arriba no puede superar lo
    #    declarado, que seria prometer sostenido lo que ni en placa hay.
    limite = limite_ma_hp(SOSTENIDO["rack+12"])
    limite_psu3 = limite_ma_hp(PSU3_A["rack+12"])
    limite_placa = limite_ma_hp(PLACA_A["rack+12"])
    assert limite >= limite_psu3, (
        f"la fila aguanta {limite:.2f} mA/HP sostenidos y en una PSU3 "
        f"aguantaria {limite_psu3:.2f}: el liston no se cumple en la unidad "
        f"en la que el dueno compra modulos")
    assert limite <= limite_placa, (
        f"la fila aguantaria {limite:.2f} mA/HP sostenidos contra "
        f"{limite_placa:.2f} de placa: sostenido por encima de placa es un "
        f"signo cambiado en el derating")

    # 5. Y el canario, por biseccion y por el texto del aserto: que esa
    #    puerta muerde de verdad en algun punto del rango censable.
    v = borde_rojo(_guarda_censo, {"mas_glotron_ma_por_hp": 1.0},
                   "mas_glotron_ma_por_hp", 1.0, 200.0, "no cabe sostenida")
    assert abs(v - limite) < 0.5, (
        f"el canario encuentra el borde en {v:.2f} mA/HP y la cuenta directa "
        f"da {limite:.2f}: la guarda y el modelo no miden lo mismo")
    print(f"  canario: por encima de {v:.1f} mA/HP la fila de {FILA_HP} HP no "
          f"cabe sostenida")

    # 6. Y el otro lado del canario: que la guarda tambien muerde por abajo,
    #    con su propio texto, si alguien deja el censo sin leer.
    w = borde_rojo(_guarda_censo, {"mas_glotron_ma_por_hp": 1.0},
                   "mas_glotron_ma_por_hp", -1.0, 1.0, "censo sin leer")
    assert w <= 0.0, f"el borde de abajo tenia que estar en 0, no en {w:.3f}"


def demo() -> None:
    print("invitados_budget: cuatro corrientes del rack, en cuatro columnas\n")

    print(f"censo del papel sec.4.3 ({len(CENSO)} modulos reales):")
    print(f"  {'modulo':28s} {'HP':>3s} {'+12':>6s} {'-12':>6s} {'+5':>5s}"
          f"  {'mA/HP +12':>9s}")
    for m in CENSO:
        print(f"  {m.nombre:28s} {m.hp:3d} {m.ma_12p:6.0f} {m.ma_12n:6.0f} "
              f"{m.ma_5:5.0f}  {m.ma_por_hp('rack+12'):9.1f}")
    print(f"  ({NOTA_CINCO_V})")

    print(f"\nlas cuatro columnas, por riel (fila de {FILA_HP} HP):")
    print(f"  {'riel':10s} {'modulo':>7s} {'declara':>8s} {'sostiene':>9s} "
          f"{'PSU3':>6s} {'censo peor':>11s}")
    peor = fila_peor_caso()
    for riel in RIELES:
        psu3 = PSU3_A.get(riel)
        texto_psu3 = "---" if psu3 is None else f"{psu3:.2f}"
        print(f"  {riel:10s} {MODULO_A[riel]:7.2f} {PLACA_A[riel]:8.2f} "
              f"{SOSTENIDO[riel]:9.3f} {texto_psu3:>6s} {peor[riel]:11.2f}")
    for riel in RIELES:
        g = por_hp(riel)
        print(f"  el peor de {riel}: {g.nombre} a "
              f"{g.ma_por_hp(riel):.2f} mA/HP")
    print("  (la columna 'censo peor' toma el peor de CADA riel por separado:")
    print("   esa fila no existe como compra, es una cota que nadie supera)")

    limite = limite_ma_hp(SOSTENIDO["rack+12"])
    glotron = por_hp("rack+12")
    print("\nel liston en la unidad en la que se compran modulos:")
    print(f"  sostenido        {limite:6.2f} mA/HP en +12 sobre {FILA_HP} HP")
    print(f"  A-100PSU3        {limite_ma_hp(PSU3_A['rack+12']):6.2f} mA/HP  "
          f"<- el liston firmado")
    print(f"  declarado        {limite_ma_hp(PLACA_A['rack+12']):6.2f} mA/HP")
    print(f"  el mas glotron   {glotron.ma_por_hp('rack+12'):6.2f} mA/HP  "
          f"({glotron.nombre})")

    caben_sost = caben(glotron, SOSTENIDO["rack+12"])
    caben_psu3 = caben(glotron, PSU3_A["rack+12"])
    caben_placa = min(caben(glotron, PLACA_A["rack+12"]), FILA_HP // glotron.hp)
    print(f"\n  una fila entera de {glotron.nombre} son "
          f"{FILA_HP // glotron.hp} modulos y "
          f"{fila_a(glotron.ma_por_hp('rack+12')):.2f} A:")
    print(f"    en placa    caben {caben_placa:2d} "
          f"({caben_placa * glotron.hp:3d} HP)  <- la fila entera")
    print(f"    sostenidos  caben {caben_sost:2d} "
          f"({caben_sost * glotron.hp:3d} HP)")
    print(f"    en una PSU3 caben {caben_psu3:2d} "
          f"({caben_psu3 * glotron.hp:3d} HP)")
    print("  No cabe sostenida, y tampoco cabria en una PSU3. El liston no")
    print("  promete que quepa: promete no ser peor, y no lo es.")

    ausentes = sum(1 for m in CENSO if m.origen_5 == AUSENTE)
    print(f"\n  CITADO: {len(CENSO)} modulos en +-12 con su URL; "
          f"AUSENTE: {ausentes} columnas de +5 V sin publicar")
    print("  Dos cifras del borrador del plan no coincidian con la ficha:")
    print("  Morphagene -12 (65 -> 20 mA) y Disting EX -12 (40 -> 50 mA).")

    _autocomprobacion()
    print("\nOK: invitados_budget.py")


if __name__ == "__main__":
    demo()
