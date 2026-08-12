"""Genera sam17-power.kicad_sch a partir de las notas de diseno del modulo.

Fuente: ../notes/design-notes.md (topologia, valores, presupuesto de
corriente). Trazado con cables reales sobre coordenadas de pin, no con
etiquetas de red — ver convenciones abajo.

Uso (requiere hardware/tools/kicad_mcp_client.py y un KiCAD-MCP-Server
corriendo/instalado, ver hardware/tools/README.md):

    python build_schematic.py

Es destructivo por diseno: create_schematic sobreescribe el .kicad_sch. Volver
a correrlo reconstruye la hoja desde cero a partir de este archivo, que es la
fuente de verdad real.

Convenciones del dibujo:
  - Flujo izquierda->derecha: J1 -> F1 -> BR1 -> reguladores -> J2.
  - Riel positivo arriba, negativo abajo, puente centrado entre ambos.
  - GND no es un bus largo: cada retorno es un stub corto a un simbolo power:GND
    (todos son la misma net). Los del riel negativo van girados 180 para que el
    grafico apunte hacia arriba.
  - Hoja A3: en A4 las parejas de condensadores quedaban a 12.7 mm y un valor
    como "4700uF/25V" mide ~15 mm, asi que los textos se solapaban. Con 25.4 mm
    de separacion la colocacion automatica de campos ya no choca.

Reglas de KiCad que mandan sobre el trazado, descubiertas midiendo (no estan
documentadas en el server):
  1. Un pin solo conecta si un cable TERMINA en el. Que el riel le pase por
     encima no conecta nada -> los rieles van partidos pin a pin.
  2. Aterrizar a media linea es fragil. Por eso los rieles se cortan tambien en
     cada punto donde entra un ramal, y cada union queda extremo contra extremo.
  3. KiCad SUMA la rotacion del simbolo al angulo de sus campos: un componente
     girado 90/270 necesita el angulo complementario en Reference/Value o el
     texto sale vertical y las dos etiquetas se pisan.
Todo en multiplos de 1.27 mm: un extremo fuera de rejilla envenena las uniones
de toda la hoja.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
from kicad_mcp_client import Client  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SCH = f"{DIR}/sam17-power.kicad_sch"

YP, YN = 66.04, 167.64          # rieles positivo / negativo
YMID = 116.84                   # eje del puente y del conector de entrada
YG_P, YG_N = 86.36, 147.32      # fila de simbolos GND (arriba / abajo)
XU = 180.34                     # columna de los reguladores
YOFF = 25.4                     # baja todo el dibujo para centrarlo en A3
DATE, REV = "2026-08-12", "A"

PARTS = [
    ("J1",  "Connector:Conn_01x03_Pin",       30.48, YMID,    0, "12VAC CT 2A"),
    ("F1",  "Device:Fuse",                    60.96, 104.14, 90, "500mA T"),
    ("BR1", "Device:D_Bridge_+-AA",           91.44, YMID,   90, "KBP206"),
    # --- riel +12V ---
    ("C1",  "Device:C_Polarized",            121.92, 69.85,   0, "4700uF/25V"),
    ("C3",  "Device:C",                      147.32, 69.85,   0, "0.33uF"),
    ("U1",  "Regulator_Linear:LM7812_TO220",    XU, YP,       0, "LM7812"),
    ("C5",  "Device:C_Polarized",            213.36, 69.85,   0, "100uF"),
    ("C7",  "Device:C",                      238.76, 69.85,   0, "0.1uF"),
    ("D1",  "Diode:1N4001",                     XU, 45.72,    0, "1N4001"),
    ("R1",  "Device:R",                      271.78, 69.85,   0, "2k2"),
    ("D3",  "Device:LED",                    271.78, 85.09,  90, "GRN"),
    # --- riel -12V ---
    ("C2",  "Device:C_Polarized",            121.92, 163.83,  0, "4700uF/25V"),
    ("C4",  "Device:C",                      147.32, 163.83,  0, "0.33uF"),
    ("U2",  "Regulator_Linear:LM7912_TO220",    XU, YN,       0, "LM7912"),
    ("C6",  "Device:C_Polarized",            213.36, 163.83,  0, "100uF"),
    ("C8",  "Device:C",                      238.76, 163.83,  0, "0.1uF"),
    ("D2",  "Diode:1N4001",                     XU, 187.96, 180, "1N4001"),
    ("R2",  "Device:R",                      271.78, 144.78,  0, "2k2"),
    ("D4",  "Device:LED",                    271.78, 160.02, 90, "RED"),
    ("J2",  "Connector:Conn_01x04_Pin",      320.04, 116.84, 180, "BUS +12/G/G/-12"),
]

POWER = [
    ("#G1",  "power:GND",  43.18, 124.46,   0),
    ("#G2",  "power:GND", 121.92, YG_P,     0),
    ("#G3",  "power:GND", 147.32, YG_P,     0),
    ("#G4",  "power:GND",     XU, YG_P,     0),
    ("#G5",  "power:GND", 213.36, YG_P,     0),
    ("#G6",  "power:GND", 238.76, YG_P,     0),
    ("#G7",  "power:GND", 271.78,  95.25,   0),
    ("#G8",  "power:GND", 121.92, YG_N,   180),
    ("#G9",  "power:GND", 147.32, YG_N,   180),
    ("#G10", "power:GND",     XU, YG_N,   180),
    ("#G11", "power:GND", 213.36, YG_N,   180),
    ("#G12", "power:GND", 238.76, YG_N,   180),
    ("#G13", "power:GND", 271.78, 138.43, 180),
    ("#G14", "power:GND", 302.26, 115.57, 270),
    ("#P1",  "power:+12V", 254.00,  53.34,  0),
    ("#N1",  "power:-12V", 254.00, 180.34, 180),
    ("#FLG1", "power:PWR_FLAG", 106.68,  53.34,   0),
    ("#FLG2", "power:PWR_FLAG", 106.68, 180.34, 180),
    ("#FLG3", "power:PWR_FLAG", 195.58, YG_P,     0),
]

# nombra los rieles crudos; sin esto el netlist los llama Net-(BR1-+)
LABELS = [("VRAW+", 99.06, YP), ("VRAW-", 99.06, YN)]


def side_fields(ref: str, x: float, y: float) -> list:
    """Campos a la derecha de un componente vertical (C, R, LED girado).

    +7.62 en x: centrados a +3.81 el texto de "4700uF/25V" pisaba su propio
    simbolo, y a 25.4 mm del vecino todavia sobra sitio.
    """
    return [(ref, "Reference", x + 7.62, y - 2.54), (ref, "Value", x + 7.62, y + 2.54)]


# La colocacion automatica da campos verticales solapados en los simbolos
# girados (F1, BR1, D3, D4), asi que aqui va cada campo a mano.
FIELDS: list = []
for _r, _x, _y in [("C1", 121.92, 69.85), ("C3", 147.32, 69.85), ("C5", 213.36, 69.85),
                   ("C7", 238.76, 69.85), ("C2", 121.92, 163.83), ("C4", 147.32, 163.83),
                   ("C6", 213.36, 163.83), ("C8", 238.76, 163.83),
                   ("R1", 271.78, 69.85), ("D3", 271.78, 85.09),
                   ("R2", 271.78, 144.78), ("D4", 271.78, 160.02)]:
    FIELDS += side_fields(_r, _x, _y)
FIELDS += [
    ("J1",  "Value",     30.48, 107.95), ("J1",  "Reference",  30.48, 125.73),
    ("F1",  "Reference", 60.96,  99.06), ("F1",  "Value",      60.96, 109.22),
    ("BR1", "Reference", 78.74, 128.27), ("BR1", "Value",      78.74, 132.08),
    ("U1",  "Value",       XU,   52.07), ("U1",  "Reference",    XU,   55.88),
    ("U2",  "Reference",   XU,  177.80), ("U2",  "Value",        XU,  181.61),
    ("D1",  "Reference",   XU,   38.10), ("D1",  "Value",        XU,   41.91),
    ("D2",  "Value",       XU,  191.77), ("D2",  "Reference",    XU,  195.58),
    ("J2",  "Value",    320.04, 106.68), ("J2",  "Reference", 320.04, 127.00),
    ("#G14", "Value",   299.72, 111.76),
]

ROT = {p[0]: p[4] for p in PARTS} | {p[0]: p[4] for p in POWER}


def rail(y: float, xs: list[float], tag: str) -> list:
    """Riel horizontal partido en cada `xs`: todo corte es un punto de union."""
    return [(f"{tag}{i}", [[xs[i], y], [xs[i + 1], y]]) for i in range(len(xs) - 1)]


WIRES: list = [
    # --- entrada AC ---
    ("AC1",      [[35.56, 114.30], [45.72, 114.30], [45.72, 104.14], [57.15, 104.14]]),
    ("AC1F",     [[64.77, 104.14], [83.82, 104.14], [83.82, YMID]]),
    ("AC2",      [[35.56, 119.38], [50.80, 119.38], [50.80, 135.89],
                  [99.06, 135.89], [99.06, YMID]]),
    ("CT->GND",  [[35.56, YMID], [43.18, YMID], [43.18, 124.46]]),
    ("BR+ sube", [[91.44, 109.22], [91.44, YP]]),
    ("BR- baja", [[91.44, 124.46], [91.44, YN]]),
]
# cortes: FLG | C bulk | C ceramico | ramal D | entrada del regulador
WIRES += rail(YP, [91.44, 106.68, 121.92, 147.32, 160.02, 172.72], "VRAW_P ")
WIRES += rail(YN, [91.44, 106.68, 121.92, 147.32, 160.02, 172.72], "VRAW_N ")
# cortes: ramal D | C electrolitico | C ceramico | simbolo de riel | indicador
WIRES += rail(YP, [187.96, 195.58, 213.36, 238.76, 254.00, 271.78, 292.10], "+12V ")
WIRES += rail(YN, [187.96, 195.58, 213.36, 238.76, 254.00, 271.78, 288.29], "-12V ")
WIRES += [
    ("+12V->J2", [[292.10, YP], [292.10, 111.76], [314.96, 111.76]]),
    ("-12V->J2", [[288.29, YN], [288.29, 119.38], [314.96, 119.38]]),
    # --- retornos a GND (cada uno acaba en el pin del simbolo) ---
    ("C1 gnd",   [[121.92, 73.66], [121.92, YG_P]]),
    ("C3 gnd",   [[147.32, 73.66], [147.32, YG_P]]),
    ("U1 gnd",   [[XU, 73.66], [XU, YG_P]]),
    ("FLG3",     [[XU, YG_P], [195.58, YG_P]]),
    ("C5 gnd",   [[213.36, 73.66], [213.36, YG_P]]),
    ("C7 gnd",   [[238.76, 73.66], [238.76, YG_P]]),
    ("C2 gnd",   [[121.92, 160.02], [121.92, YG_N]]),
    ("C4 gnd",   [[147.32, 160.02], [147.32, YG_N]]),
    ("U2 gnd",   [[XU, 160.02], [XU, YG_N]]),
    ("C6 gnd",   [[213.36, 160.02], [213.36, YG_N]]),
    ("C8 gnd",   [[238.76, 160.02], [238.76, YG_N]]),
    # --- diodos de proteccion: el pin va de ultimo waypoint ---
    ("D1 izq",   [[160.02, YP], [160.02, 45.72], [176.53, 45.72]]),
    ("D1 der",   [[195.58, YP], [195.58, 45.72], [184.15, 45.72]]),
    ("D2 izq",   [[160.02, YN], [160.02, 187.96], [176.53, 187.96]]),
    ("D2 der",   [[195.58, YN], [195.58, 187.96], [184.15, 187.96]]),
    # --- simbolos de riel y PWR_FLAG ---
    ("FLG1",     [[106.68, YP], [106.68, 53.34]]),
    ("FLG2",     [[106.68, YN], [106.68, 180.34]]),
    ("+12V sym", [[254.00, YP], [254.00, 53.34]]),
    ("-12V sym", [[254.00, YN], [254.00, 180.34]]),
    # --- indicadores LED ---
    ("R1->D3",   [[271.78, 73.66], [271.78, 81.28]]),
    ("D3 gnd",   [[271.78, 88.90], [271.78, 95.25]]),
    ("R2 gnd",   [[271.78, 140.97], [271.78, 138.43]]),
    ("R2->D4",   [[271.78, 148.59], [271.78, 156.21]]),
    ("D4->riel", [[271.78, 163.83], [271.78, YN]]),
    # --- GND del conector de salida ---
    ("J2 gnd a", [[314.96, 114.30], [306.07, 114.30], [306.07, 115.57]]),
    ("J2 gnd b", [[306.07, 115.57], [306.07, 116.84], [314.96, 116.84]]),
    ("J2 gnd c", [[306.07, 115.57], [302.26, 115.57]]),
]


def main() -> None:
    c = Client()
    try:
        c.call("create_schematic", {"name": "sam17-power", "path": DIR})
        # A3: la plantilla nace en A4 y no hay tool para el tamano de hoja.
        # El cajetin es un (title_block ...) de nivel superior y tampoco tiene
        # tool; ambos se escriben aqui mismo por texto plano.
        with open(SCH, encoding="utf-8") as fh:
            txt = fh.read()
        title_block = (
            '(paper "A3")\n'
            "\t(title_block\n"
            '\t\t(title "Modulo 01 — Alimentacion ±12 V")\n'
            f'\t\t(date "{DATE}")\n'
            f'\t\t(rev "{REV}")\n'
            '\t\t(company "SAM17 — Sintetizador analogico modular")\n'
            '\t\t(comment 1 "Trafo 12 VAC CT 2 A externo. Rieles ±12 V — ver '
            'notes/design-notes.md §10 para +5V/NTC/MOV, pendientes en esta hoja")\n'
            "\t)"
        )
        with open(SCH, "w", encoding="utf-8") as fh:
            fh.write(txt.replace('(paper "A4")', title_block, 1))

        for ref, sym, x, y, rot, val in PARTS:
            c.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": sym, "reference": ref,
                "value": val, "position": {"x": x, "y": y + YOFF, "unit": "mm"}})
            if rot:
                c.call("rotate_schematic_component",
                       {"schematicPath": SCH, "reference": ref, "angle": rot})
        for ref, sym, x, y, rot in POWER:
            c.call("add_schematic_component", {
                "schematicPath": SCH, "symbol": sym, "reference": ref,
                "value": sym.split(":")[1],
                "position": {"x": x, "y": y + YOFF, "unit": "mm"}})
            if rot:
                c.call("rotate_schematic_component",
                       {"schematicPath": SCH, "reference": ref, "angle": rot})
        print(f"colocados {len(PARTS)} componentes + {len(POWER)} simbolos de potencia")

        offgrid = []
        for ref in [p[0] for p in PARTS] + [p[0] for p in POWER]:
            txt = str(c.call("get_schematic_pin_locations",
                             {"schematicPath": SCH, "reference": ref}))
            for n, _nm, x, y in re.findall(
                    r"Pin (\d) \(([^)]+)\): x=([\d.]+), y=([\d.]+)", txt.replace("\\n", "\n")):
                for v in (float(x), float(y)):
                    if abs(round(v / 1.27) * 1.27 - v) > 0.01:
                        offgrid.append((ref, n, x, y))
        print(f"pines fuera de rejilla: {len(offgrid)} {offgrid[:5]}")

        bad = 0
        for label, wp in WIRES:
            shifted = [[wx, wy + YOFF] for wx, wy in wp]
            r = str(c.call("add_schematic_wire",
                           {"schematicPath": SCH, "waypoints": shifted}))
            if "success" not in r.lower():
                bad += 1
                print(f"  WIRE FAIL {label}: {r[:160]}")
        print(f"cables: {len(WIRES) - bad}/{len(WIRES)} OK")

        # position es un ARRAY [x, y] aqui, no un objeto: pasarlo como objeto
        # se acepta sin error pero la etiqueta no se coloca.
        for name, x, y in LABELS:
            r = str(c.call("add_schematic_net_label", {
                "schematicPath": SCH, "netName": name, "position": [x, y + YOFF]}))
            print(f"  label {name}: {r[:80]}")

        r = str(c.call("batch_set_schematic_property_positions", {
            "schematicPath": SCH,
            # KiCad SUMA la rotacion del simbolo al angulo del campo (regla 3
            # de arriba), asi que un 0 aqui sale vertical en F1/BR1/D3/D4 y
            # referencia y valor acaban uno encima del otro.
            "updates": [{"reference": ref, "property": prop,
                         "x": x, "y": y + YOFF,
                         "angle": (360 - ROT.get(ref, 0)) % 360
                                  if ROT.get(ref) in (90, 270) else 0}
                        for ref, prop, x, y in FIELDS]}))
        print(f"campos: {r[:90]}")
        print(str(c.call("lint_schematic_cosmetic", {
            "schematicPath": SCH, "passes": ["hide_pin_names"]}))[:80])

        erc = str(c.call("run_erc", {"schematicPath": SCH}))
        print(f"ERC: {erc[:110]}")
        for tool, ext in [("export_schematic_svg", "svg"), ("export_schematic_pdf", "pdf")]:
            out = f"{DIR}/../schematics/sam17-power.{ext}"
            c.call(tool, {"schematicPath": SCH, "outputPath": out})
        print("exportado a ../schematics/sam17-power.{svg,pdf}")
    finally:
        c.close()


if __name__ == "__main__":
    main()
