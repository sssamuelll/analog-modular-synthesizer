"""Firma de conectividad de cada modulo: el golden test del hardware.

    python netdiff.py              compara contra los .netgold commiteados
    python netdiff.py --write      regenera los .netgold (revisalo en el diff)
    python netdiff.py --coherencia solo el cruce esquematico <-> placa

Existe por un hueco concreto: `check_netlist.py` comprueba los invariantes que
ALGUIEN declaro a mano. Lo que nadie declaro se puede romper en silencio. Este
fichero cubre el resto por fuerza bruta: reduce el netlist entero a un texto
canonico, lo guarda al lado del modulo, y cualquier red que se mueva sale en el
diff del PR.

Es lo que faltaba para poder tocar un modulo cerrado sin miedo. Antes: "creo
que no cambie nada". Ahora: 152 redes, 0 distintas, o la lista de las que si.

Caso que lo motivo: el commit e4238b5 revirtio un valor de resistencia y su
mensaje afirmaba "netlist semanticamente identica". Era cierto -- pero era
PROSA, y el Principio II del repo prohibe exactamente eso. Ahora es un fichero.

## Por que el golden es texto y no un hash

Un hash te dice que algo cambio. Un texto ordenado te dice QUE cambio, en el
diff del propio PR, sin herramientas. El fichero es feo de leer entero y util
de leer en diff, que es justo cuando se lee.

## Que se normaliza y por que

El generador re-crea UUIDs y fecha en cada corrida, asi que el `.net` cambia
byte a byte aunque el diseno sea identico. La forma canonica se queda solo con
lo que es el diseno: nombre de red -> conjunto ordenado de REF-PIN. Se tira el
`code` (es un contador de orden de escritura, no informacion) y la `/` inicial
de las redes de hoja raiz.

Corolario que sale gratis: **esto es tambien el test de determinismo de la
regeneracion**. Corre `build_schematic.py` y luego este script; si el golden
pasa, el script reproduce el artefacto commiteado. Si no, uno de los dos miente.

## La coherencia esquematico <-> placa

Segundo hueco, y este ya se materializo: el `.kicad_pcb` del modulo 3 se genero
a las 07:11 y el esquematico se regenero a las 11:01. Nada en el repo cruzaba
los dos, asi que una placa construida contra un netlist viejo se veia igual de
verde que una al dia.

Dos reglas, las dos sin lista de excepciones:

  * los nombres de red reales (sin `unconnected-*`) tienen que ser el MISMO
    conjunto en el `.net` y en el `.kicad_pcb`;
  * una huella que este en la placa y no en el netlist tiene que tener CERO
    redes en sus pads. Es lo que distingue un agujero de montaje (mecanico, sin
    cobre asignado) de un componente que alguien anadio a la placa sin pasar
    por el esquematico.

La segunda regla es a proposito una regla y no una lista de designadores: una
lista hay que mantenerla y se convierte en el sitio donde se esconden las
excepciones.
"""
from __future__ import annotations

import difflib
import glob
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_RE_RED = re.compile(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)')
_RE_NODO = re.compile(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)')
_RE_PCB_RED = re.compile(r'\(net "([^"]*)"\)')
_RE_PCB_REF = re.compile(r'\(property "Reference" "([^"]+)"')


def canonica(texto: str) -> dict[str, frozenset[str]]:
    """Netlist -> {nombre de red: {REF-PIN}}. Sin UUIDs, sin codes, sin fecha."""
    cab = list(_RE_RED.finditer(texto))
    assert cab, "netlist ilegible o vacio: corre build_schematic.py primero"
    out: dict[str, frozenset[str]] = {}
    for i, m in enumerate(cab):
        fin = cab[i + 1].start() if i + 1 < len(cab) else len(texto)
        out[m.group(1).lstrip("/")] = frozenset(
            f"{a}-{b}" for a, b in _RE_NODO.findall(texto[m.end():fin]))
    return out


def firma(canon: dict[str, frozenset[str]], nombre: str) -> str:
    """Forma canonica en texto, estable y diffeable."""
    nodos = sum(len(v) for v in canon.values())
    lineas = [f"# firma de conectividad de {nombre}",
              f"# generado por hardware/tools/netdiff.py -- NO editar a mano",
              f"# {len(canon)} redes, {nodos} nodos"]
    for red in sorted(canon):
        lineas.append(f"{red}: {' '.join(sorted(canon[red]))}")
    return "\n".join(lineas) + "\n"


def huellas_pcb(texto: str) -> dict[str, set[str]]:
    """{REF: {redes de sus pads}} leyendo el .kicad_pcb huella por huella."""
    out: dict[str, set[str]] = {}
    trozos = texto.split("\n\t(footprint ")
    for t in trozos[1:]:
        m = _RE_PCB_REF.search(t)
        if not m:
            continue
        redes = {r.lstrip("/") for r in _RE_PCB_RED.findall(t)}
        redes.discard("")
        out[m.group(1)] = redes
    return out


# ------------------------------------------------------------------ modulos
class Modulo:
    def __init__(self, net: str) -> None:
        self.net = net
        self.nombre = os.path.basename(net)
        self.dir = os.path.dirname(net)
        self.golden = net[:-4] + ".netgold"
        pcb = net[:-4] + ".kicad_pcb"
        self.pcb = pcb if os.path.exists(pcb) else None

    @property
    def rel(self) -> str:
        return os.path.relpath(self.net, RAIZ).replace("\\", "/")


def modulos() -> list[Modulo]:
    """Todos los .net del arbol de hardware, en orden estable."""
    pat = os.path.join(RAIZ, "*", "**", "*.net")
    return [Modulo(p) for p in sorted(glob.glob(pat, recursive=True))]


# ------------------------------------------------------------------ comandos
def cmd_golden(escribir: bool) -> list[str]:
    fallos: list[str] = []
    for m in modulos():
        with open(m.net, encoding="utf-8") as fh:
            nueva = firma(canonica(fh.read()), m.nombre)
        if escribir:
            with open(m.golden, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(nueva)
            print(f"  escrito {os.path.relpath(m.golden, RAIZ)}")
            continue
        if not os.path.exists(m.golden):
            fallos.append(f"{m.rel}: falta el golden. Corre netdiff.py --write")
            continue
        with open(m.golden, encoding="utf-8") as fh:
            vieja = fh.read()
        if vieja == nueva:
            n = nueva.splitlines()[2].split()[1]
            print(f"  OK  {m.rel:52} {n:>4} redes sin cambios")
            continue
        d = list(difflib.unified_diff(
            vieja.splitlines(), nueva.splitlines(),
            fromfile="golden commiteado", tofile="netlist actual", lineterm=""))
        cambios = [l for l in d if l[:1] in "+-" and l[:3] not in ("---", "+++")]
        fallos.append(
            f"{m.rel}: la conectividad cambio ({len(cambios)} lineas).\n"
            + "\n".join("    " + l for l in d[:60])
            + ("\n    ... (diff recortado)" if len(d) > 60 else "")
            + "\n    Si el cambio es intencional: netdiff.py --write y "
              "commitea el golden con el diseno.")
    return fallos


def cmd_coherencia() -> list[str]:
    fallos: list[str] = []
    for m in modulos():
        if not m.pcb:
            print(f"  --  {m.rel:52} sin .kicad_pcb, nada que cruzar")
            continue
        with open(m.net, encoding="utf-8") as fh:
            canon = canonica(fh.read())
        with open(m.pcb, encoding="utf-8") as fh:
            hue = huellas_pcb(fh.read())

        reales = {r for r in canon if not r.startswith("unconnected-")}
        en_pcb = {r for h in hue.values() for r in h
                  if not r.startswith("unconnected-")}
        solo_sch, solo_pcb = sorted(reales - en_pcb), sorted(en_pcb - reales)
        if solo_sch:
            fallos.append(f"{m.rel}: redes en el esquematico y NO en la placa "
                          f"-> la placa se genero de un netlist viejo: {solo_sch}")
        if solo_pcb:
            fallos.append(f"{m.rel}: redes en la placa y NO en el esquematico: "
                          f"{solo_pcb}")

        refs_sch = {n.rsplit("-", 1)[0] for v in canon.values() for n in v}
        colados = {r: sorted(n) for r, n in hue.items()
                   if r not in refs_sch and n}
        if colados:
            fallos.append(
                f"{m.rel}: huellas con cobre asignado que no estan en el "
                f"esquematico: {colados}")
        mecanicas = sorted(r for r in hue if r not in refs_sch)
        faltan = sorted(refs_sch - set(hue))
        if faltan:
            fallos.append(f"{m.rel}: componentes del esquematico sin huella en "
                          f"la placa: {faltan}")
        if not (solo_sch or solo_pcb or colados or faltan):
            print(f"  OK  {m.rel:52} {len(reales):>4} redes, "
                  f"{len(refs_sch):>3} refs"
                  + (f", {len(mecanicas)} mecanicas ({', '.join(mecanicas)})"
                     if mecanicas else ""))
    return fallos


# ----------------------------------------------------------- autocomprobacion
_MINI = """
(export (version "E")
 (nets
  (net (code "1") (name "/GNDA")
   (node (ref "R1") (pin "2")) (node (ref "C1") (pin "1")))
  (net (code "2") (name "VCC")
   (node (ref "R1") (pin "1")))))
"""


def autocomprobacion() -> None:
    """Comprueba que el comparador DETECTA cambios, no solo que no se queja.

    Un comparador que devuelve "todo igual" pase lo que pase pasa el CI para
    siempre (Principio III: una comprobacion que pasa sobre un artefacto vacio
    no es una comprobacion). Aqui se le da un netlist conocido, se le mueve UN
    pin, y se exige que lo cante.
    """
    c = canonica(_MINI)
    assert c == {"GNDA": frozenset({"R1-2", "C1-1"}),
                 "VCC": frozenset({"R1-1"})}, f"parser roto: {c}"
    assert firma(c, "x").splitlines()[2] == "# 2 redes, 3 nodos"

    movido = canonica(_MINI.replace('(ref "C1") (pin "1")',
                                    '(ref "C1") (pin "2")'))
    assert firma(movido, "x") != firma(c, "x"), \
        "mover un pin no cambio la firma: el golden no protege de nada"

    # y el orden de escritura no puede importar: son conjuntos ordenados
    revuelto = _MINI.replace('(node (ref "R1") (pin "2")) (node (ref "C1") (pin "1"))',
                             '(node (ref "C1") (pin "1")) (node (ref "R1") (pin "2"))')
    assert firma(canonica(revuelto), "x") == firma(c, "x"), \
        "la firma depende del orden de escritura: daria falsos positivos"

    # y las huellas de la placa se leen por bloques, no por fichero entero
    h = huellas_pcb('\n\t(footprint "a"\n\t\t(property "Reference" "H1")\n'
                    '\t\t(pad (net ""))\n'
                    '\n\t(footprint "b"\n\t\t(property "Reference" "R1")\n'
                    '\t\t(pad (net "GNDA"))\n')
    assert h == {"H1": set(), "R1": {"GNDA"}}, f"lector de placa roto: {h}"
    print("autocomprobacion OK (parser, deteccion de cambio, orden, huellas)")


def main(argv: list[str]) -> int:
    autocomprobacion()
    solo_coh = "--coherencia" in argv
    escribir = "--write" in argv
    fallos: list[str] = []

    if not solo_coh:
        print("\nfirma de conectividad contra el golden commiteado:")
        fallos += cmd_golden(escribir)
    # La coherencia esquematico <-> placa corre SIEMPRE, tambien con --write.
    #
    # Antes se saltaba con --write, y el razonamiento estaba justo al reves:
    # el instante posterior a regenerar los goldens es cuando la placa tiene
    # MAS probabilidad de estar vieja -- acabas de cambiar el esquematico. Ahi
    # imprimia "netdiff: VERDE" con cuatro redes y ocho huellas sin llegar a la
    # placa. El flujo real (toco el esquematico -> --write -> veo VERDE -> doy
    # la tanda por buena) tenia su unica red de seguridad apagada exactamente
    # en el paso donde hace falta.
    print("\ncoherencia esquematico <-> placa:")
    fallos += cmd_coherencia()

    for f in fallos:
        print("\nFALLO:", f)
    if fallos:
        print(f"\n{len(fallos)} fallo(s).")
        return 1
    print("\nnetdiff: VERDE")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
