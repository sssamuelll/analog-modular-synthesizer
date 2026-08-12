# Generación de esquemáticos vía KiCAD-MCP-Server

Los `.kicad_sch` de cada módulo se generan con un script Python
(`<modulo>/kicad/build_schematic.py`) que habla el protocolo MCP con un
[KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) local. El
`.kicad_sch` resultante es el artefacto real — el script es la receta para
regenerarlo o ajustarlo, no algo que haya que ejecutar para usar el diseño.

## Por qué existe

Las tools de esquemático del server editan el fichero directamente
(`kicad-skip`/`kicad-cli`, sin necesidad de la GUI de KiCad), pero no dibujan
solas: hay que darles coordenadas de pin, y KiCad tiene un puñado de reglas de
conectividad que no están documentadas y que cada `build_schematic.py` anota
en su docstring según se van descubriendo (p. ej. que un cable solo conecta si
*termina* en un pin, no si pasa por encima).

## Setup

1. Clonar y compilar el server:
   ```
   git clone https://github.com/mixelpixx/KiCAD-MCP-Server
   cd KiCAD-MCP-Server && npm install && npm run build
   ```
2. Crear un venv **desde el Python que trae KiCad** (no el del sistema — el
   server necesita `pcbnew`, que solo existe ahí):
   ```
   "C:\Program Files\KiCad\10.0\bin\python.exe" -m venv --system-site-packages .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Apuntar `kicad_mcp_client.py` a esa instalación (o dejar los defaults, que
   asumen `~\.claude\mcp-servers\kicad-mcp-server`):
   ```
   set KICAD_MCP_SERVER_DIST=C:\ruta\a\KiCAD-MCP-Server\dist\index.js
   set KICAD_MCP_SERVER_VENV=C:\ruta\a\KiCAD-MCP-Server\.venv\Scripts\python.exe
   ```
4. Correr el script del módulo:
   ```
   python hardware\01-power-supply\kicad\build_schematic.py
   ```

## Notas conocidas del server (KiCad 10, medido 2026-08-12)

- `search_symbols` / `list_library_symbols` / `list_symbol_libraries` pueden
  superar el timeout de 30 s por defecto con una instalación completa de
  KiCad (~220 librerías). Si tu clon no trae el parche, resuelve los nombres
  de símbolo con `grep` directo sobre
  `<KiCad>/share/kicad/symbols/*.kicad_sym` en vez de las tools de búsqueda.
- Los símbolos de potencia (`power:GND`, `power:+12V`, `power:-12V`, …) rompían
  la carga del `.kicad_sch` en `kicad-cli` por comillas sin escapar en su
  campo `Description`. Y la referencia de cualquier símbolo `#`-prefijado
  (virtual) salía visible en el dibujo en vez de ocultarse. Ambos son bugs del
  server, no del diseño — si tu clon los reproduce, son ~10 líneas de parche
  en `python/commands/dynamic_symbol_loader.py`.
