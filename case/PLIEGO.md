# Pliego de fabricación — cuerpo de acrílico del SAM17

Este documento **acompaña a los DXF y no es opcional**. Un DXF solo es media
pieza: lleva la geometría de corte y no dice material, espesor, acabado,
profundidad de cajeado ni qué cara es la exterior. Sin esto, esos huecos los
rellena el taller con sus supuestos.

Para elegir taller antes de pedir, ver [`RFQ.md`](RFQ.md).

---

## 1. Material

- **PMMA COLADO (GS)**, naranja translúcido. **NO extruido (XT)**: el
  extruido trae tensión interna de fábrica y craquela solo.
- Espesores: **8 mm** y **5 mm**. Ver §6 qué pieza en qué espesor.
- Tolerancia de espesor conocida y aceptada: **±(0.4 + 0.1 × espesor)**, o
  sea ±1.2 mm en 8. Confirmada por escrito por Schaeffer AG el 2026-08-18.
- **Comunicar el espesor real medido del lote ANTES de cortar.** No es
  cortesía: hay cotas del diseño derivadas del espesor. `marco_sup` **es** el
  espesor de una plancha, y de él cuelga una junta que el modelo exige que
  valga exactamente cero.

## 2. Proceso

- **Fresado CNC.** No láser: deja canto cónico en 8 mm y microfisura en los
  bordes cargados.
- Fresa asumida **⌀3 mm** (radio interior 1.5). **Avisar si se usa otra**:
  hay geometría acotada contra ese número, incluido el relieve de §4.
- Los DXF están **a cota final**: el CAM compensa el radio de herramienta
  como parte normal del trabajo. **No aplicar sobre-medida.**
- Unidades de los DXF: **milímetros** (implícitas en el fichero).
- Tolerancia de posición requerida entre filas de agujeros de una misma
  placa: **±0.05 mm**. El separador de una placa es uno solo, así que dos
  filas que no apoyen a la misma distancia dejan una atornillada al aire.

## 3. Acabados — los tres que hacen el producto

### 3.1 RECOCIDO (annealing) — obligatorio

**Después de mecanizar y de pulir.** El fresado deja tensión atrapada
alrededor de cada agujero y cada canto; sin recocer, el PMMA craquela en
meses — una telaraña de grietas finas que empieza por los taladros y se
acelera donde hay un tornillo apretado o donde tocó un limpiador. No se ve
al desembalar.

**Indicar temperatura y rampa empleadas** en el albarán.

### 3.2 Canto

| dónde | acabado |
|---|---|
| **canto visible** (contorno exterior de las piezas, ~7.5 m) | **PULIDO DIAMANTADO en máquina** |
| **canto interior** (ranuras, ondas, taladros, ~10 m) | tal cual sale de fresa |

**PULIDO A LLAMA PROHIBIDO.** Mete tensión superficial y deshace el
recocido; en colado craquela cerca de los agujeros.

El acrílico es translúcido: la luz viaja por dentro de la plancha y sale por
el canto. Un canto áspero se lee como una línea blanca lechosa rodeando cada
pieza; uno diamantado se enciende del color del cuerpo.

### 3.3 Chaflán

**0.5 × 45° en toda arista vista**, mecanizado (no lijado a mano).

Incluye **las dos esquinas traseras del costado**, que van a **arista viva
por diseño** (radio 0) para que la trasera empotre a ras. Arista viva más
canto pulido se desportilla al primer roce, y la de abajo va a ras del suelo.

## 4. Cajeado ciego — la operación que el DXF no describe

`kondor_cajeado_2d.dxf` **no es un recorte**: es un **vaciado a 4.0 mm de
profundidad** en la **cara exterior** de `piel_trasera_2d`. **No atraviesa**
la plancha de 8 mm.

- El fichero está dibujado **tal como debe verse desde fuera**: la palabra se
  lee del derecho.
- La letra es Franklin Gothic Medium; el contorno ya viene convertido a
  curvas en el DXF, no hace falta la fuente.
- Trazo mínimo verificado contra fresa de 3 mm. Si se usa fresa mayor de
  4 mm, **avisar antes de cortar**.

## 5. Orientación — la trasera tiene cara

`piel_trasera_2d` **tiene cara exterior y cara interior** desde que lleva el
cajeado. **La cara exterior es la del vaciado.** Montada al revés, el relieve
queda hacia dentro y la palabra se lee invertida.

Las demás piezas son indiferentes al lado.

## 6. Piezas

| DXF | espesor | uds | notas |
|---|---|---|---|
| `costado_2d` | 8 | **2** | canto visible completo, diamantado |
| `bandeja_base_2d` | 8 | 1 | |
| `piel_trasera_2d` | 8 | 1 | **+ `kondor_cajeado_2d` a 4 mm en la cara exterior** (§4, §5) |
| `tapa_valle_2d` | **5** | 1 | única pieza en 5 mm |
| `remate_sup_2d` | 8 | 1 | |
| `coupon.dxf` | 8 | 1 | pieza de calibración — **sin acabado, sin recocer** |

**`lienzo_2d.dxf` es solo previsualización de nesteado: NO SE CORTA.**

Las tres piezas `chasis_*` son de **acero** y van a otro taller, con otro
proceso (corte + plegado). Llevan su propio plano de plegado
([`renders/chasis-plano-plegado.png`](renders/chasis-plano-plegado.png)),
porque un DXF de corte no dice de dónde doblar.

## 7. Manipulación y limpieza — para nosotros, no para el taller

Esta sección no es del pedido: es de lo que pasa **después**, y es donde se
estropea un acabado que llegó bien.

- **Prohibido alcohol y limpiacristales con amoníaco**: craquelan el PMMA.
  Agua tibia con jabón neutro y paño de microfibra.
- **El film protector se quita al FINAL del montaje**, no al recibir. El
  acrílico llega perfecto y se raya durante el ensamblaje: al deslizarlo por
  la mesa, al apoyar una herramienta, al girar una pieza sobre otra.
- **Apriete de los 30 M3: 1.0 N·m, con arandela ancha d16 y ROSCA SECA.**
  Engrasar la rosca baja el coeficiente par-precarga de 0.2 a ~0.15, o sea
  que el mismo par mete un 30 % más de precarga — y sobre acrílico eso
  fisura. Destornillador dinamométrico, no muñeca.
- **Paticas**: goma con casquillo roscado, **atornilladas, nunca pegadas**.
  El case no lleva ninguna junta irreversible desde el 2026-08-21.

## 8. De dónde salen estos números

Todo lo cotado aquí vive en [`cad/params.scad`](cad/params.scad) con su
puerta en [`clearance_budget.py`](clearance_budget.py) o
[`check_dxf.py`](check_dxf.py). **Si este documento y el modelo se
contradicen, el equivocado es este documento.**

| aquí | parámetro | puerta |
|---|---|---|
| chaflán 0.5 × 45° | `chaflan` | `guarda_chaflan()` |
| cajeado 4.0 mm | `kondor_prof` | `guarda_kondor()` |
| apriete 1.0 N·m / d16 | `par_m3`, `d_arandela` | `guarda_apriete()` |
| flecha de patica 0.25 mm | `flecha_pie` | `guarda_paticas()` |
| fresa ⌀3 mm | `fresa_d` | `guarda_fresado()` |
