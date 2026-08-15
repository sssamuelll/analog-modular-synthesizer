"""Extrae definiciones de simbolos de las librerias de KiCad y calcula pines.

Existe para que build_schematic.py pueda escribir el .kicad_sch DIRECTAMENTE,
sin KiCAD-MCP-Server. Motivo: en este proyecto el server ya trunco un
sam17-power.kicad_sch a 215 bytes devolviendo success:true, y una hoja vacia
pasa el ERC con 0 avisos (hardware/tools/README.md). Escribiendo el fichero
aqui, el unico intermediario es kicad-cli, que es la herramienta oficial.

Un .kicad_sch tiene que llevar EMPOTRADA la definicion de cada simbolo que usa,
en su bloque (lib_symbols ...). Eso es lo que saca extraer().
"""
from __future__ import annotations

import os
import re

KICAD_SYMS = os.environ.get(
    "KICAD_SYMBOLS", r"C:\Program Files\KiCad\10.0\share\kicad\symbols")

_cache: dict[str, str] = {}


def _texto(lib: str) -> str:
    if lib not in _cache:
        with open(os.path.join(KICAD_SYMS, f"{lib}.kicad_sym"), encoding="utf-8") as fh:
            _cache[lib] = fh.read()
    return _cache[lib]


def _bloque(txt: str, inicio: int) -> str:
    """Devuelve el s-expr completo que empieza en el '(' de la posicion dada.

    Cuenta parentesis saltandose los que van dentro de cadenas: hay simbolos
    con parentesis en la descripcion y un contador ingenuo corta a mitad.
    """
    nivel, i, en_cadena, escapado = 0, inicio, False, False
    while i < len(txt):
        c = txt[i]
        if escapado:
            escapado = False
        elif c == "\\":
            escapado = True
        elif c == '"':
            en_cadena = not en_cadena
        elif not en_cadena:
            if c == "(":
                nivel += 1
            elif c == ")":
                nivel -= 1
                if nivel == 0:
                    return txt[inicio:i + 1]
        i += 1
    raise ValueError("s-expr sin cerrar")


def extraer(lib_id: str) -> str:
    """Devuelve el (symbol "Lib:Nombre" ...) listo para meter en lib_symbols."""
    lib, nombre = lib_id.split(":")
    txt = _texto(lib)
    m = re.search(r'\(symbol\s+"' + re.escape(nombre) + r'"', txt)
    if not m:
        raise KeyError(f"{lib_id} no esta en {lib}.kicad_sym")
    bloque = _bloque(txt, m.start())
    # dentro de la libreria el simbolo se llama "R"; dentro de la hoja tiene
    # que llamarse "Device:R" o KiCad no lo resuelve
    return bloque.replace(f'(symbol "{nombre}"', f'(symbol "{lib_id}"', 1)


def pines(lib_id: str) -> dict[str, tuple[float, float, float]]:
    """{numero de pin: (x, y, angulo)} en coordenadas del SIMBOLO (Y hacia arriba).

    El (at ...) de un pin en KiCad es su punto de CONEXION — la punta donde se
    engancha el cable — no el arranque contra el cuerpo.
    """
    bloque = extraer(lib_id)
    out: dict[str, tuple[float, float, float]] = {}
    for m in re.finditer(r"\(pin\s+\w+\s+\w+\s*\n?\s*\(at\s+"
                         r"(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)", bloque):
        x, y, ang = float(m.group(1)), float(m.group(2)), float(m.group(3))
        resto = bloque[m.end():m.end() + 400]
        n = re.search(r'\(number\s+"([^"]+)"', resto)
        if n:
            out[n.group(1)] = (x, y, ang)
    return out


def pin_abs(lib_id: str, num: str, ox: float, oy: float,
            rot: int = 0) -> tuple[float, float]:
    """Posicion absoluta de un pin en la HOJA (Y hacia abajo).

    La libreria tiene Y hacia arriba y la hoja Y hacia abajo, asi que hay una
    inversion de signo ademas de la rotacion. Giro antihorario en el marco
    Y-arriba y despues se voltea Y:

        0   -> ( px, -py)      180 -> (-px,  py)
        90  -> (-py, -px)      270 -> ( py,  px)
    """
    px, py, _ = pines(lib_id)[num]
    dx, dy = {0: (px, -py), 90: (-py, -px),
              180: (-px, py), 270: (py, px)}[rot % 360]
    return (round(ox + dx, 3), round(oy + dy, 3))


if __name__ == "__main__":
    for s in ("Device:R", "Device:LED", "Device:Polyfuse",
              "Connector_Generic:Conn_02x08_Odd_Even",
              "Connector:Conn_01x04_Pin", "power:GND", "power:+12V"):
        p = pines(s)
        print(f"{s:42s} {len(p):2d} pines")
        for k in sorted(p, key=lambda z: (len(z), z))[:6]:
            print(f"    {k:>3s} at {p[k]}")
