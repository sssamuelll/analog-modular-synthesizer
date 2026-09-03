"""El censo del crosspoint: que cabe en las dos AD75019 de la bahia asignable.

    python bahia_budget.py

Lo mando motor-digital sec.8.4 punto 4 el 2026-08-26, con estas palabras:

    "4. **Censo del crosspoint** (D-P1/D-P4): fuentes nuevas (la boca) **y el
    destino hacia los oidos**, sin quitarle jack a nadie -- enmienda a
    voz-total sec.5."

Y voz-total sec.5.1 lo repitio como condicion de que aquellas dos enmiendas
valgan:

    "la bahia necesita **censo** -- fuentes nuevas y destinos nuevos contra
    las 16x16 de los dos AD75019, que no son infinitas. El censo esta mandado
    en motor-digital sec.8.4; **no esta hecho**, y hasta que corra nadie sabe si
    las dos vias caben a la vez."

Ocho dias sin correr. Aqui esta.

LO QUE ES LA BAHIA, con su cita (voz-total sec.5.1, l. 439-444):

    "**8 entradas + 8 salidas** en jacks Thonkiconn (TN conectado, sensado de
    ocupacion, LED por jack), ruteadas por **dos AD75019** (crosspoint 16x16,
    +-12 V, carga serie): entradas -> los 16 nodos de suma; las 16 salidas
    post-VCA -> salidas."

De esa frase sale el modelo de abajo: DOS chips en serie con las voces en
medio, no dos chips en paralelo. Uno mira hacia las voces (sus 16 salidas Y
son los 16 nodos de suma) y otro mira desde las voces (sus 16 entradas X son
las 16 salidas post-VCA). Es la unica lectura que hace que la frase cierre
con 16 voces y dos chips de 16x16 -- pero es una LECTURA, y va marcada como
tal: si el esquematico los cablea de otro modo (por ejemplo en paralelo para
un 16x32), este guion se rehace. Ver TOPOLOGIA_SUPUESTA abajo.

EL HALLAZGO, y es el que contesta la pregunta que nadie habia hecho correr:
las dos enmiendas del 2026-08-26 CABEN con holgura, pero **los lados que dan
a las voces estan exactamente llenos**: 16 de 16 en los dos chips, cero
libres, por construccion y para siempre. O sea que la bahia puede admitir
mas cosas DEL MUNDO y mas cosas HACIA EL MUNDO, y no puede admitir ni un
destino interno mas. Cualquier parametro que quiera recibir un CV externo
por esta via se encuentra la puerta cerrada, y no por poco: por cero.

Eso no es un defecto del diseno. Es la frontera que dice que el crosspoint
es para senal de audio, y que un CV que quiere gobernar un parametro tiene
otro camino (el digital: ADC en la entrada, mapeo en el cerebro, DAC del
modulo que ya existe por architecture-poly sec.8). Este guion lo mide para que
la frontera este escrita en numeros y no en prosa.
"""
from __future__ import annotations

import os
import re

_AQUI = os.path.dirname(os.path.abspath(__file__))

# --- el chip, contra su hoja pendiente ----------------------------------
#
# AD75019: 16x16, +-12 V, carga serie de 256 bits con commit global.
# El 16x16 y los 256 bits son coherentes entre si (16*16 = 256) y los dos
# salen de voz-total sec.5.1 y sec.5.3 (H-CF2: "el AD75019 carga 256 bits y aplica
# todo a la vez"). La HOJA no esta en el arbol -- es el #267, que bloquea la
# serializacion. Lo que este guion usa del chip son sus dimensiones, que la
# spec ya declara; NO usa ni una cifra electrica suya. Cuando la hoja entre,
# lo que hay que anadir aqui es la resistencia de paso y la diafonia, no el
# tamano.
X_POR_CHIP = 16
Y_POR_CHIP = 16
N_CHIPS = 2

# Numero de canales de voz.
#
# NO se escribe aqui: se LEE de `core/src/bahia.rs`, que es la imagen sombra
# que el firmware de verdad shiftea al chip. Es la misma disciplina que R-MJ4
# le impone al presupuesto del J2, y por el mismo motivo: la v1 de este guion
# aseveraba `_ocupacion(B_X_FUENTES) == N_VOCES` sobre una lista que contenia
# literalmente `N_VOCES`, o sea `N_VOCES == N_VOCES`. Serrano lo cazo: era
# imposible que fallara. Un aserto que solo mira sus propias constantes no es
# una puerta, es un adorno -- el patron "puerta verde, sujeto muerto" que este
# repo ya pago una vez.
_BAHIA_RS = os.path.join(_AQUI, "..", "..", "software", "nucleo", "core",
                         "src", "bahia.rs")


def _const_del_rust(nombre: str, ruta: str = _BAHIA_RS) -> int:
    with open(ruta, encoding="utf-8") as f:
        m = re.search(rf"pub const {nombre}: u8 = (\d+);", f.read())
    if not m:
        raise SystemExit(
            f"bahia.rs no expone `pub const {nombre}: u8`. Este guion LEE del "
            "artefacto que shiftea el chip; si el Rust cambio de forma, "
            "arregla el guion. NO copies el numero aqui.")
    return int(m.group(1))


N_VOCES = _const_del_rust("CANALES")
LINEAS_RS = _const_del_rust("LINEAS")

TOPOLOGIA_SUPUESTA = (
    "dos chips EN SERIE con las voces en medio: A.Y = los 16 nodos de suma, "
    "B.X = las 16 salidas post-VCA. Lectura de voz-total sec.5.1, no del "
    "esquematico -- que no existe"
)

# --- quien pide sitio, con su fuente ------------------------------------
#
# Cada fila: (nombre, cuantos, de donde sale, si es de la v1 o enmienda).
# "puerto" dice en que lado del que chip se sienta.

# CHIP A -- del mundo hacia las voces.
A_X_FUENTES = [
    ("jacks de entrada de la bahia", 8,
     "voz-total sec.5.1: '8 entradas ... en jacks Thonkiconn'", "v1"),
    ("boca del codec (estereo en v1)", 2,
     "motor-digital D-P1: 'Las salidas del codec (estereo en v1) se conectan "
     "como fuentes del crosspoint'", "enmienda 2026-08-26"),
]
A_Y_DESTINOS = [
    ("nodos de suma de los canales", N_VOCES,
     "voz-total sec.5.1: 'entradas -> los 16 nodos de suma'", "v1"),
]

# CHIP B -- de las voces hacia el mundo.
B_X_FUENTES = [
    ("salidas post-VCA de los canales", N_VOCES,
     "voz-total sec.5.1: 'las 16 salidas post-VCA -> salidas'", "v1"),
]
B_Y_DESTINOS = [
    ("jacks de salida de la bahia", 8,
     "voz-total sec.5.1: '8 ... salidas en jacks Thonkiconn'", "v1"),
    ("oidos ruteables (mono; ver HUECO)", 1,
     "motor-digital D-P4: 'los oidos ganan una **entrada ruteable desde el "
     "crosspoint** (destino nuevo; censo en sec.8.4)'", "enmienda 2026-08-26"),
]

# El D-P4 no dice si la entrada ruteable de los oidos es mono o estereo. El
# modulo 4 lleva "codec 24 bits + FFT" (architecture-poly sec.2) y la via rapida
# alternativa es "ADC rapido del micro (12 bits, 5 Msps)", que es UNA entrada.
# Se cuenta 1 y se asevera que 2 tambien cabria: asi el HUECO no cambia el
# veredicto y queda dicho que no lo cambia.
OIDOS_PEOR_CASO = 2


def _ocupacion(filas):
    return sum(n for _, n, _, _ in filas)


def puerto(nombre, filas, tope):
    """Un lado de un chip: cuanto se pide, cuanto entra, cuanto sobra."""
    usado = _ocupacion(filas)
    return {
        "nombre": nombre,
        "usado": usado,
        "tope": tope,
        "libres": tope - usado,
        "filas": filas,
    }


def censo():
    return [
        puerto("A.X  del mundo -> (fuentes)", A_X_FUENTES, X_POR_CHIP),
        puerto("A.Y  -> nodos de suma", A_Y_DESTINOS, Y_POR_CHIP),
        puerto("B.X  post-VCA -> (fuentes)", B_X_FUENTES, X_POR_CHIP),
        puerto("B.Y  -> hacia el mundo", B_Y_DESTINOS, Y_POR_CHIP),
    ]


def cabe_un_destino_interno_mas():
    """La pregunta de Samuel del 2026-09-03, en una funcion.

    "van muchas cosas alli, no solamente los jacks de las voces. tambien van
    otros parametros."

    Un parametro que reciba CV externo POR EL CROSSPOINT necesita una salida
    Y del chip A, que es el unico lado que mira hacia adentro del
    instrumento. Esta funcion dice cuantas hay.
    """
    a_y = puerto("A.Y", A_Y_DESTINOS, Y_POR_CHIP)
    return a_y["libres"]


def demo():
    print(__doc__.split("\n")[0])
    print(f"\n  topologia SUPUESTA: {TOPOLOGIA_SUPUESTA}")
    print(f"  {N_CHIPS} x AD75019 de {X_POR_CHIP}x{Y_POR_CHIP}, "
          f"{N_VOCES} canales de voz")

    print("\nEL CENSO, lado por lado\n")
    for p in censo():
        estado = "LLENO" if p["libres"] == 0 else f"{p['libres']:2d} libres"
        print(f"  {p['nombre']:30s} {p['usado']:2d}/{p['tope']:2d}   {estado}")
        for nombre, n, fuente, origen in p["filas"]:
            marca = "  " if origen == "v1" else "+ "
            print(f"        {marca}{n:2d}  {nombre}")

    # --- lo que el censo estaba mandado a contestar ----------------------
    print("\nLO QUE sec.8.4 MANDO CONTESTAR (motor-digital, 2026-08-26)\n")

    a_x = puerto("", A_X_FUENTES, X_POR_CHIP)
    b_y = puerto("", B_Y_DESTINOS, Y_POR_CHIP)

    print(f"  D-P1  la boca del codec como fuente     "
          f"{'CABE' if a_x['libres'] >= 0 else 'NO CABE'}"
          f"   (A.X: {a_x['usado']}/{X_POR_CHIP}, "
          f"{a_x['libres']} libres despues)")
    print(f"  D-P4  los oidos como destino ruteable   "
          f"{'CABE' if b_y['libres'] >= 0 else 'NO CABE'}"
          f"   (B.Y: {b_y['usado']}/{Y_POR_CHIP}, "
          f"{b_y['libres']} libres despues)")

    # El peor caso del HUECO de los oidos, para que el veredicto no dependa
    # de una suposicion que el papel no fijo.
    b_y_peor = _ocupacion(B_Y_DESTINOS) - 1 + OIDOS_PEOR_CASO
    print(f"        con oidos en ESTEREO (peor caso del HUECO): "
          f"{b_y_peor}/{Y_POR_CHIP}, "
          f"{'sigue cabiendo' if b_y_peor <= Y_POR_CHIP else 'NO CABE'}")

    print("\n  -> las dos enmiendas del 2026-08-26 CABEN, y sin quitarle "
          "jack a nadie.")
    print("     El fallback declarado de D-P1 ('si el censo del crosspoint "
          "da rojo,")
    print("     la boca entra directo al bus del mixer') NO hace falta.")

    # --- el hallazgo -----------------------------------------------------
    print("\nEL HALLAZGO, que el censo no venia a buscar\n")

    libres_dentro = cabe_un_destino_interno_mas()
    print(f"  destinos internos libres (A.Y): {libres_dentro}")
    print("  Los dos lados que dan a las voces estan llenos por "
          "construccion:")
    print(f"    A.Y = {N_VOCES} nodos de suma  = {Y_POR_CHIP}/{Y_POR_CHIP}")
    print(f"    B.X = {N_VOCES} salidas post-VCA = {X_POR_CHIP}/{X_POR_CHIP}")
    print("  No es que quede poco: queda CERO, y queda cero para siempre "
          "mientras")
    print("  haya 16 canales y dos chips de 16x16.")
    print()
    print("  Consecuencia, dicha entera: por el crosspoint NO puede entrar un")
    print("  CV externo a gobernar un parametro (corte, resonancia, tiempo de")
    print("  envolvente...). No hay donde sentarlo. Un parametro que quiera")
    print("  CV externo lo recibe por el camino DIGITAL -- ADC en la entrada,")
    print("  mapeo en el cerebro, y el DAC que ese parametro ya tiene en su")
    print("  modulo (architecture-poly sec.8) -- que ademas es mas capaz: un")
    print("  mismo CV puede gobernar varios parametros a la vez, con escala")
    print("  y curva propias, cosa que un cruce analogico no sabe hacer.")

    # --- la otra frontera, corregida por la junta ------------------------
    print("\n  Y una segunda, de la misma topologia: una senal que entra por")
    print("  A.X solo puede llegar a nodos de suma. Para salir al mundo tiene")
    print("  que atravesar un canal de voz. NO hay camino entrada-a-salida")
    print("  directo: la bahia no sabe hacer de PUENTE pasivo.")
    print()
    print("  Lo que si sabe hacer, y la v1 de este guion negaba por error: un")
    print("  crosspoint cierra una misma X contra VARIAS Y a la vez, asi que")
    print("  una entrada SI se reparte a varios nodos de suma. Eso es un")
    print("  multiple hacia adentro, y sale gratis.")
    print()
    print("  Y el puente ya esta legislado, con acta: voz-total sec.0.3, rol")
    print("  `conducto` -- 'su oscilador esta silenciado y hay senal externa")
    print("  activa en su nodo de suma: suena lo externo por su filtro y su")
    print("  VCA. El caso DJ'. Cuesta un canal de voz, y ese costo esta")
    print("  contado alli. Lo unico que no existe es el puente SIN gastar")
    print("  canal.")

    # --- lo que este guion NO mide --------------------------------------
    print("\nLO QUE ESTE GUION NO MIDE (y por que no lo finge)\n")
    print("  * Resistencia de paso, diafonia y ancho de banda del AD75019:")
    print("    su hoja no esta en el arbol (#267). Aqui solo se usan sus")
    print("    DIMENSIONES, que voz-total ya declara.")
    print("  * El nivel de la etapa de acople de la boca del codec: D-P1 la")
    print("    manda y dice que 'el numero exacto no lo fija este papel'.")
    print("  * Si los oidos son mono o estereo: HUECO de D-P4, acotado")
    print("    arriba (con 2 sigue cabiendo).")

    # --- las aserciones --------------------------------------------------
    for p in censo():
        assert p["libres"] >= 0, (
            f"{p['nombre']} pide {p['usado']} de {p['tope']}: el censo NO "
            f"cierra y el fallback de D-P1 tendria que ejecutarse")

    assert b_y_peor <= Y_POR_CHIP, (
        "con los oidos en estereo B.Y se desborda: el HUECO de D-P4 pasaria "
        "a decidir el veredicto, y hoy no lo decide")

    # Esta es la asercion que guarda el hallazgo. Si alguien anade un destino
    # interno sin anadir chip, salta aqui y no en el laboratorio.
    # Los dos asertos que SI miran fuera de este archivo: las dimensiones que
    # el guion supone tienen que coincidir con las que el firmware shiftea.
    assert LINEAS_RS == Y_POR_CHIP, (
        f"bahia.rs dice LINEAS={LINEAS_RS} y este guion supone "
        f"{Y_POR_CHIP}: uno de los dos describe otro chip")

    assert cabe_un_destino_interno_mas() == 0, (
        f"A.Y ya no esta lleno. `bahia.rs` dice CANALES={N_VOCES} y "
        f"LINEAS={LINEAS_RS}; mientras sean iguales, los nodos de suma llenan "
        "el chip y no cabe ni un destino interno mas. Si el firmware cambio y "
        "de verdad hay sitio dentro, la frontera 'el crosspoint es para audio, "
        "el parametro va por numero' hay que volver a argumentarla -- no "
        "heredarla. Y conviene saber que esa frontera se sostiene en un "
        "CONTEO, no en una ontologia: las cuatro ventajas del camino digital "
        "(varios destinos, curva, cabe en el preset, no gasta cruces) "
        "sobreviven a un tercer chip; la urgencia no")

    print("\nOK: censo cerrado. Las dos enmiendas caben; los lados internos "
          "estan llenos.")


if __name__ == "__main__":
    demo()
