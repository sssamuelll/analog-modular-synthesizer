import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(DIR, "sam17-power-v5.kicad_sch")

if not os.path.exists(SCH):
    print(f"HUECO: {SCH} no existe (ejecutar build_schematic.py primero)")
    sys.exit(0)

with open(SCH, encoding="utf-8") as f:
    txt = f.read()

labels = re.findall(r'\(label "([^"]+)"\s+\(at ([-\d.]+) ([-\d.]+) \d+\)', txt)
print(f"Total labels in sch: {len(labels)}")
coords = {}
collisions = 0
for name, x, y in labels:
    pt = (round(float(x), 2), round(float(y), 2))
    if pt in coords and coords[pt] != name:
        print(f"COLLISION at {pt}: '{coords[pt]}' and '{name}'")
        collisions += 1
    coords[pt] = name

print(f"Total label collisions: {collisions}")

# Check wires
wires = re.findall(r'\(wire\s+\(pts\s+\(xy ([-\d.]+) ([-\d.]+)\)\s+\(xy ([-\d.]+) ([-\d.]+)\)\)', txt)
print(f"Total wires in sch: {len(wires)}")
wire_collisions = 0
for x1, y1, x2, y2 in wires:
    p1 = (round(float(x1), 2), round(float(y1), 2))
    p2 = (round(float(x2), 2), round(float(y2), 2))
    l1 = coords.get(p1)
    l2 = coords.get(p2)
    if l1 and l2 and l1 != l2:
        print(f"WIRE connects different labels: '{l1}' at {p1} <-> '{l2}' at {p2}")
        wire_collisions += 1

if collisions > 0 or wire_collisions > 0:
    print(f"FALLO: {collisions} colisiones de etiqueta, {wire_collisions} cables en cortocircuito")
    sys.exit(1)

print("OK: check_collisions v5")
sys.exit(0)
