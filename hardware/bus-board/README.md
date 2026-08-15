# Bus board — distribución de ±12 V

Reparte los rieles del [módulo 1](../01-power-supply/) a los módulos. Sustituye
al daisy-chain con cables jumper de la tesis, que era la fuente de ruido y de
desafinación que la propia tesis reportó.

Se construyen **dos segmentos idénticos** de 320 × 60 mm. Cada uno lleva 6
slots y se alimenta con su propio par de cables desde el punto de estrella.

## Qué decide esta placa

No es un problema de corriente, es de **afinación**. A 1 V/octava, **1 mV de
diferencia de masa entre dos módulos son 1.2 cents** de error de tono. El
objetivo es ≤ 2 cents entre los cuatro módulos de la cadena de tono, y de ahí
sale todo lo demás.

| | |
|---|---|
| Presupuesto de masa medido | **1.21 cents** ([`ground_budget.py`](ground_budget.py)) |
| Masa | **plano sólido en B.Cu** — con pista de 5 mm serían +7.1 cents |
| Vías | **0** — una vía de señal le abre una ranura al plano |
| De dónde venimos | daisy-chain de la tesis: 6.3–30 cents |

El resultado que no esperaba: **el plano aporta solo 0.20 cents; el resto se lo
come el cable de bajada**. Y dentro del cable manda el contacto crimpado, no el
cobre. Detalle en [`notes/design-notes.md`](notes/design-notes.md).

## Por slot

- **Peine Eurorack 2×8 sin llave** — Doepfer prohíbe expresamente los headers
  con caja y código en un bus board. La franja roja va al par **−12 V**,
  serigrafiado. El +5 V, CV y Gate quedan **NC a propósito** (§9 de las notas).
- **Peine SAM17 KK-254 de 4 pines, con llave** — el mismo `J2` del módulo 1.
- **Dos PTC de 0.25 A**, uno por riel. **Nunca en masa**: ahí serían 94 cents.
- **Dos LED con 4k7** en paralelo con cada PTC. Apagados en marcha, encendidos
  cuando ese fusible dispara. Señalan el conector y el riel culpables.

## Estructura

```
bus-board/
├── ground_budget.py     El presupuesto de masa, ejecutable y con aserciones
├── bom.csv
├── kicad/
│   ├── symlib.py            Extrae simbolos de las librerias de KiCad
│   ├── build_schematic.py   Genera sam17-bus.kicad_sch (sin MCP: kicad-cli)
│   ├── check_netlist.py     Netlist contra el diseño declarado a mano
│   ├── check_bom.py         Cruce esquemático <-> bom.csv
│   ├── build_pcb.py         Genera sam17-bus.kicad_pcb (pcbnew directo)
│   └── sam17.pretty/        Huella propia del PTC (admite dos encapsulados)
├── schematics/ pcb/ fab/
└── notes/design-notes.md
```

## Estado

- [x] Presupuesto de masa cerrado y ejecutable — **1.21 cents** de 2
- [x] Esquemático — 49 componentes, **ERC 0 infracciones**
- [x] Netlist verificado contra el diseño: 27 redes, 160 pines, uno a uno
- [x] PCB — 320 × 60 mm, 2 capas, **DRC 0 infracciones, 0 sin conectar, 0 vías**
- [x] Masa en B.Cu verificada por id de capa (el nombre de capa engaña)
- [x] Gerbers y taladros en [`fab/`](fab/)
- [ ] **Antes de fabricar**: verificar con polímetro el orden de filas del peine
      Eurorack contra un cable Doepfer real. Está confirmado que la franja roja
      es −12 V; el orden del bloque central sale de fuentes secundarias
      ([§12.1](notes/design-notes.md))
- [ ] Medir la resistencia de contacto real del crimpado — es el término que más
      pesa del presupuesto y el valor usado es de manual
- [ ] Medir la diferencia de masa entre slots con los módulos montados

## Reglas de montaje que no se pueden saltar

1. **La cadena de tono (MIDI/CV + VCO1..3) va entera en el mismo segmento.**
   Repartida entre los dos, el desequilibrio entre sus cables de alimentación se
   les suma completo.
2. **Los dos hilos de masa del cable SAM17 se crimpan siempre.** Con uno solo el
   presupuesto se sale de los 2 cents.
3. **Cables de bajada ≤ 150 mm.** A 500 mm se añade ~1 cent.
4. **Separadores de nylon, no metálicos.** El puente chasis-masa es uno y está
   en el módulo 1 ([§13](../01-power-supply/notes/design-notes.md)).
5. **Cada segmento se alimenta desde el punto de estrella**, con pares de
   2.5 mm² de longitud parecida. No encadenar un segmento del otro.
6. **Franja roja del cable al par serigrafiado −12 V.** Siempre.
