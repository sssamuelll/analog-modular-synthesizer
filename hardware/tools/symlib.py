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
    "KICAD_SYMBOLS", r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
    if os.name == "nt" else "/usr/share/kicad/symbols")

# Sitios donde buscar una libreria, en orden. Un modulo que necesite un simbolo
# que KiCad no trae (el AD5686R del modulo 2, por ejemplo) mete su .kicad_sym
# propio aqui con anadir_ruta() y lo encuentra igual que uno del sistema.
RUTAS: list[str] = [KICAD_SYMS]

_cache: dict[str, str] = {}


def anadir_ruta(ruta: str) -> None:
    """Antepone un directorio de librerias propias al de KiCad."""
    if ruta not in RUTAS:
        RUTAS.insert(0, ruta)


def _texto(lib: str) -> str:
    if lib not in _cache:
        for base in RUTAS:
            camino = os.path.join(base, f"{lib}.kicad_sym")
            if os.path.isfile(camino):
                with open(camino, encoding="utf-8") as fh:
                    _cache[lib] = fh.read()
                break
        else:
            raise FileNotFoundError(f"{lib}.kicad_sym no esta en {RUTAS}")
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


def _crudo(lib: str, nombre: str) -> str:
    txt = _texto(lib)
    m = re.search(r'\(symbol\s+"' + re.escape(nombre) + r'"', txt)
    if not m:
        raise KeyError(f"{lib}:{nombre} no esta en {lib}.kicad_sym")
    return _bloque(txt, m.start())


def extraer(lib_id: str) -> str:
    """Devuelve el (symbol "Lib:Nombre" ...) listo para meter en lib_symbols.

    Resuelve la herencia. Media libreria de KiCad son simbolos DERIVADOS: el
    TL074 no dibuja nada, solo pone `(extends "LM2902")` y cambia el nombre.
    Copiado tal cual a una hoja, ese bloque no tiene ni patillas ni cuerpo, y
    el resultado es un componente fantasma que el ERC ni menciona. En una hoja
    KiCad escribe siempre el simbolo APLANADO, asi que aqui se aplana igual:
    el dibujo y las patillas del padre, las propiedades del hijo.
    """
    lib, nombre = lib_id.split(":")
    bloque = _crudo(lib, nombre)
    padre = re.search(r'\(extends\s+"([^"]+)"\)', bloque)
    if padre:
        # Se parte del PADRE entero (dibujo, patillas y propiedades) y se le
        # pisan solo las propiedades que el hijo redefine. Al reves — quedarse
        # con el hijo y anadirle el dibujo — se pierden ki_keywords y
        # ki_fp_filters, y KiCad canta un lib_symbol_mismatch por cada
        # instancia: el simbolo de la hoja deja de ser igual al de la libreria.
        propios = {m.group(1): _bloque(bloque, m.start()) for m in
                   re.finditer(r'\(property\s+"([^"]+)"', bloque)}
        fusion = _crudo(lib, padre.group(1))
        for clave, texto in propios.items():
            m = re.search(r'\(property\s+"' + re.escape(clave) + r'"', fusion)
            if m:
                fusion = fusion.replace(_bloque(fusion, m.start()), texto, 1)
            else:
                i = fusion.index("\n") + 1
                fusion = fusion[:i] + texto + "\n" + fusion[i:]
        # los sub-simbolos van con el nombre PELADO del simbolo que los aloja
        fusion = fusion.replace(f'(symbol "{padre.group(1)}_',
                                f'(symbol "{nombre}_')
        bloque = fusion.replace(f'(symbol "{padre.group(1)}"',
                                f'(symbol "{nombre}"', 1)
    return bloque.replace(f'(symbol "{nombre}"', f'(symbol "{lib_id}"', 1)


def unidades(lib_id: str) -> set[int]:
    """Unidades que tienen patillas. Un TL074 son 5: cuatro amplificadores y
    una quinta que solo lleva la alimentacion."""
    bloque = extraer(lib_id)
    nombre = lib_id.split(":")[1]
    out = set()
    for m in re.finditer(r'\(symbol\s+"' + re.escape(nombre) + r'_(\d+)_\d+"', bloque):
        i = m.start()
        if "(pin " in _bloque(bloque, i):
            out.add(int(m.group(1)))
    return out


def pines(lib_id: str, unidad: int | None = None) -> dict[str, tuple[float, float, float]]:
    """{numero de pin: (x, y, angulo)} en coordenadas del SIMBOLO (Y hacia arriba).

    El (at ...) de un pin en KiCad es su punto de CONEXION — la punta donde se
    engancha el cable — no el arranque contra el cuerpo.

    Con `unidad`, devuelve solo las patillas de esa unidad. Hace falta para los
    multi-unidad: pedirle a un TL074 "todas sus patillas" son las 14 del chip,
    no las 3 del amplificador que se esta colocando.
    """
    bloque = extraer(lib_id)
    if unidad is not None:
        nombre = lib_id.split(":")[1]
        # La unidad 0 es la COMUN a todas: ahi es donde muchos simbolos de una
        # sola unidad guardan sus patillas (Switch:SW_Push, por ejemplo). Pedir
        # solo la unidad N y no encontrar nada no significa que el simbolo este
        # mal, significa que sus patillas son comunes.
        trozos = [_bloque(bloque, m.start()) for u in (unidad, 0) for m in
                  re.finditer(r'\(symbol\s+"' + re.escape(nombre)
                              + rf'_{u}_\d+"', bloque)]
        assert trozos, f"{lib_id} no tiene ni unidad {unidad} ni unidad comun"
        bloque = "\n".join(trozos)
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



def pin_dir(lib_id: str, num: str, rot: int = 0,
            unidad: int | None = None) -> tuple[float, float]:
    """Vector unitario en el que hay que sacar el cable de un pin, en la HOJA.

    El angulo que guarda KiCad apunta del punto de conexion HACIA EL CUERPO del
    simbolo, asi que el cable sale justo al reves. Sirve para colgar stubs sin
    tener que acordarse de por que lado mira cada pin de cada simbolo.
    """
    import math
    _x, _y, ang = pines(lib_id, unidad)[num]
    a = math.radians(ang + 180 + (rot % 360))
    return (round(math.cos(a), 6), round(-math.sin(a), 6))

if __name__ == "__main__":
    for s in ("Device:R", "Device:LED", "Device:Polyfuse",
              "Connector_Generic:Conn_02x08_Odd_Even",
              "Connector:Conn_01x04_Pin", "power:GND", "power:+12V"):
        p = pines(s)
        print(f"{s:42s} {len(p):2d} pines")
        for k in sorted(p, key=lambda z: (len(z), z))[:6]:
            print(f"    {k:>3s} at {p[k]}")
