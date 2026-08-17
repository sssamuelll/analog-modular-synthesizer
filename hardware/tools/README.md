# Herramientas de hardware

## Correr las puertas de calidad

```
python hardware/tools/gates.py
```

Ejecuta **todos** los `check_*.py`, todos los `*_budget.py`, todo lo de
`simulations/*/` y `netdiff.py`, y suma. Tarda ~2 s con KiCad instalado.

> **Córrelo a mano antes de cada PR.** El job existe en
> `.github/workflows/ci.yml`, pero **GitHub Actions está deshabilitado en este
> repositorio** (comprobado 2026-08-17): hoy no corre solo. Para activarlo:
> `gh api -X PUT repos/:owner/:repo/actions/permissions -f enabled=true`.

Un gate nuevo se añade **escribiendo el fichero** con uno de esos nombres. No
hay lista que actualizar aquí: si la hubiera, el día que a alguien se le olvide
ampliarla el gate nace sin correr.

Tres estados, y el del medio es el que importa:

| | |
|---|---|
| `OK` | pasó |
| `HUECO` | no se pudo comprobar, **con el motivo escrito**. No rompe el CI, sale en el resumen y se cuenta |
| `FALLO` | rojo. No se cierra la tanda |

Un `HUECO` es el Principio V aplicado a la propia herramienta: un `skip`
silencioso consigue no correr *y* que no te enteres, las dos cosas a la vez.
Hoy hay tres, los tres declarados — dos necesitan KiCad (`pcbnew`,
`ngspice.dll`) y el tercero espera a que exista la placa del módulo 3.

Para probar en local la rama que corre el CI (máquina sin KiCad):

```
KICAD_PYTHON=none python hardware/tools/gates.py
```

## La firma de conectividad (`netdiff.py`)

```
python hardware/tools/netdiff.py            compara contra los .netgold
python hardware/tools/netdiff.py --write    los regenera
```

`check_netlist.py` comprueba los invariantes que **alguien declaró** a mano.
Lo que nadie declaró se rompía en silencio. `netdiff.py` cubre el resto por
fuerza bruta: reduce cada netlist a un texto canónico (`*.netgold`, sin UUIDs
ni fechas) y cualquier red que se mueva sale **en el diff del PR**, con nombre
y pines.

Es lo que permite tocar un módulo cerrado sin apostar. Si el cambio es
intencional: `--write` y el golden se commitea junto al diseño, de forma que la
revisión ve el cambio de conectividad al lado del cambio de script.

**Corolario que sale gratis: es también el test de determinismo de la
regeneración.** Corre `build_schematic.py` y después `netdiff.py`; si el golden
pasa, el script reproduce exactamente el artefacto commiteado. Si no, uno de
los dos miente.

Y cruza además el esquemático contra la placa, que antes no lo hacía nadie: los
nombres de red reales tienen que coincidir, y una huella que esté en la placa y
no en el netlist tiene que tener **cero redes** en sus pads — es lo que
distingue un agujero de montaje de un componente que alguien añadió sin pasar
por el esquemático.

---

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
- `add_schematic_component` **acepta `mirrorY` y lo ignora**, sin error ni
  aviso: el componente se coloca sin espejar y los pines siguen donde estaban.
  Para voltear un símbolo hay que usar `rotate_schematic_component` con 180,
  que sí funciona — teniendo en cuenta que 180 invierte también el orden
  vertical de los pines, cosa que el espejo no haría.
- `add_schematic_text` escribe el texto **doble-codificado**: un `§` sale como
  `Â§` en el PDF. El cajetín no tiene el problema porque se escribe por texto
  plano directamente en el fichero. Mantén las anotaciones de hoja en ASCII.
- `create_project` **trunca el `.kicad_sch` que ya exista con ese nombre**, sin
  avisar y devolviendo `success: true`. Deja la hoja en ~200 bytes y con cero
  componentes — y el ERC de esa hoja vacía sale limpio, así que no te enteras
  por ahí. Crea el proyecto **antes** de generar el esquemático, o regenera
  después. Aquí no costó nada porque `build_schematic.py` reconstruye la hoja
  entera desde cero; en un flujo con la hoja dibujada a mano habría sido el
  trabajo de una tarde.

## Verificar el trazado, no solo el ERC

KiCad da por conectado un pin si hay un extremo de cable a menos de ~1 mm, así
que **el ERC pasa igual con un trazado torcido**. En este repo eso escondió
durante una revisión entera que `J3`/`J4` estuvieran cableados a 0.36 mm de sus
pines reales. Por eso `build_schematic.py` comprueba, antes de dibujar nada, que
cada pin tenga un vértice de `WIRES` **exacto** (<0.01 mm) y aborta si no.

Si escribes un `build_schematic.py` para otro módulo, cópiate esa comprobación.
Es la diferencia entre un esquemático que funciona y uno que funciona por ahora.
