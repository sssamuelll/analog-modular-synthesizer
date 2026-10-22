# Ficheros de fabricacion -- Modulo 1, version 5 (fuente ladrillo 24V)

Generados con `kicad-cli` desde `../kicad/sam17-power-v5.kicad_pcb`. Para
regenerarlos, ver el final de este fichero.

## Estado: ruteada y con DRC en cero

```
DRC (kicad-cli, --severity-all)   0 infracciones   0 sin conectar   0 paridad
placa                             200 x 150 mm Eurocard, FR-4 1,6 mm, 1 oz cobre
aislamiento digital (GNDD)        Barrera de 3 mm sobre B.Cu cruzada por aislador ISO1541
zonas de masa B.Cu                24147 mm2 de cobre relleno (GNDA y GNDD)
huellas propias                   6 en sam17.pretty, todas contra datasheets de fabricante
```

## Arquitectura de potencia externa 24V

A diferencia de la v3 (que montaba un transformador toroidal interno de 230 VAC y
necesitaba una ranura de aislamiento de 6 mm para red electrica), la v5 se alimenta
de un ladrillo de escritorio externo de 24 VDC / 90-120 W (TE90A2403F01 / GST120A24 /
GSM120A24) mediante un conector Kycon KPJX-PM-4S con seguro:

  * Toda la tension de entrada es SELV (<60 VDC).
  * Proteccion M5 activa con eFuse TI TPS26630 (corte <100 ns en sobrecorriente,
    bloqueo OVP/UVLO) y MCU MSP430FR2111 para registro FRAM de eventos.
  * Diodo ideal TI LM74502 y MOSFET de canal N para proteccion contra polaridad inversa.
  * Aislamiento galvanico completo del canal digital (+5V_DIG, GNDD, bus I2C digital J8)
    mediante convertidor Mornsun URB2405YMD-20WR3 y aislador digital TI ISO1541.
  * Reguladores LDO lineales de ultra-bajo ruido LT3045 y LT3094 para los rieles
    analogicos criticos (+-12V_ULTRA).

## Que se sube a JLCPCB (tres ficheros)

| fichero | donde va | se genera con |
|---|---|---|
| `sam17-power-v5-jlcpcb.zip` | "Add gerber file" | bloque de empaquetado al final |
| `sam17-power-v5-bom-jlc.csv` | "Add BOM File" | `python ../kicad/bom_jlc.py` |
| `sam17-power-v5-cpl-jlc.csv` | "Add CPL File" | `python ../kicad/cpl_jlc.py` |

**Nota sobre CPL**: `sam17-power-v5-pos.csv` es la salida cruda de `kicad-cli pcb export pos`.
`cpl_jlc.py` traduce las cabeceras al formato de JLCPCB (`Designator,Mid X,Mid Y,Layer,Rotation`),
redondea a 2 decimales y filtra solo los componentes con codigo LCSC que monta la maquina.

## Regenerar el paquete completo

Desde la raiz del repositorio:

```bash
# 1. Regenerar PCB y rellenar planos de masa
& "C:\Program Files\KiCad\10.0\bin\python.exe" hardware/01-power-supply/v5/kicad/build_pcb.py

# 2. Exportar Gerbers y taladros
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export gerbers --output hardware/01-power-supply/v5/fab/ --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,Edge.Cuts --no-x2 hardware/01-power-supply/v5/kicad/sam17-power-v5.kicad_pcb
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export drill --output hardware/01-power-supply/v5/fab/ --format excellon --excellon-units mm hardware/01-power-supply/v5/kicad/sam17-power-v5.kicad_pcb
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export pos --format csv --units mm --side front --output hardware/01-power-supply/v5/fab/sam17-power-v5-pos.csv hardware/01-power-supply/v5/kicad/sam17-power-v5.kicad_pcb

# 3. Generar BOM y CPL de ensamblaje
python hardware/01-power-supply/v5/kicad/bom_jlc.py
python hardware/01-power-supply/v5/kicad/cpl_jlc.py

# 4. Validar el paquete
python hardware/01-power-supply/v5/check_fab.py
```
