# Pliego de fabricación — cuerpo del SAM17

> **rev. 21 (2026-08-27).** Dejó de ser «el pliego de acrílico»: el case
> pasó a estructura de aluminio y el acrílico bajó a piel. Son **cinco**
> materiales y cinco talleres — acrílico, chapa de aluminio plegada, acero,
> madera y los rieles comprados. Cada sección dice a cuál va.

Este documento **acompaña a los DXF y no es opcional**. Un DXF solo es media
pieza: lleva la geometría de corte y no dice material, espesor, acabado,
profundidad de cajeado ni qué cara es la exterior. Sin esto, esos huecos los
rellena el taller con sus supuestos.

Para elegir taller antes de pedir, ver [`RFQ.md`](RFQ.md).

---

## 1. Material

- **PMMA COLADO (GS)**, naranja translúcido. **NO extruido (XT)**: el
  extruido trae tensión interna de fábrica y craquela solo.
- Espesor: **8 mm**, y es el único. Hubo dos hasta el 2026-08-25: los 5 mm
  existían para una sola pieza —la tapa del valle— y esa pieza pasó a
  **chapa de aluminio**, así que no entra en este pliego (§6).
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
| `costado_2d` | 8 | **2** | canto visible completo, diamantado. **Sin un solo taladro** desde el 2026-08-27 |
| `piel_trasera_2d` | 8 | 1 | **+ `kondor_cajeado_2d` a 4 mm en la cara exterior** (§4, §5) |
| `remate_sup_2d` | 8 | 1 | |
| `coupon.dxf` | 8 | 1 | pieza de calibración — **sin acabado, sin recocer** |

**`bandeja_base_2d` SALIÓ de este pliego el 2026-08-27.** Era el suelo, de
acrílico de 8. Ahora es una **tabla de madera maciza de 18 mm** que va bajo el
marco y hace de suelo y de zócalo a la vez. Va al carpintero, §6.2.

**Y el costado dejó de llevar taladros.** Tenía cuatro M4 de riel y cuatro M5 de
larguero; los ocho se fueron a la costilla de aluminio. La pieza es ahora
**piel**: queda capturada entre las dos alas de la costilla, sin tornillo. Al
taller le llega un contorno y nada más — menos operaciones y menos sitios por
donde el PMMA raja.

**`lienzo_2d.dxf` es solo previsualización de nesteado: NO SE CORTA.**

### Lo que NO va a este taller

Seis DXF de `case/plans/` **no son de acrílico** y no entran aquí:

| DXF | material | proceso |
|---|---|---|
| `chasis_cuerpo_2d`, `chasis_tapa_2d`, `chasis_refuerzo_2d` | acero | corte + **plegado** |
| `costilla_2d` | **aluminio, 3 mm** | corte + **plegado** |
| `tapa_valle_2d` | **aluminio, 3 mm** | corte + **plegado** |
| `bandeja_base_2d` | **madera maciza, 18 mm** | corte + ranuras alargadas |

**`costilla_2d` y `tapa_valle_2d` son DESARROLLOS PLANOS, no contornos.** Igual
que las tres del chasis: el DXF trae el recorte, y la pieza doblada mide menos.
Cortar el contorno de la pieza montada da un fichero válido e inservible.

Las tres del chasis llevan su propio plano de plegado
([`renders/chasis-plano-plegado.png`](renders/chasis-plano-plegado.png)),
porque un DXF de corte no dice de dónde doblar.

**La costilla es la pieza portante del case** desde el 2026-08-26. Es una banda
de 24 mm que sigue el contorno del costado, con la ventana vaciada en el centro
y un ala de 12 mm doblada a 90° en 4 de sus 7 tramos. Lleva **todos los
tornillos estructurales**: los 4 M4 de riel, los 6 M5 de transversal y el M3 de
la pestaña del valle. El acrílico que va detrás no sostiene nada.

**La tapa del valle** era acrílico de 5 mm hasta el 2026-08-25 y es la
superficie horizontal entre las dos filas de módulos. Cambió de material
porque el 70 % de su fondo está en voladizo —vuela 23.24 mm a cada lado de
su larguero— y en PMMA de 5 fluía a 90 N, con lo que era la pieza más floja
del case y a la vez donde se apoya quien se levanta.

Desde el 2026-08-27 **tampoco es plana**: lleva una pestaña de 21 mm doblada a
90° en cada punta, con un M3 que la atornilla a la costilla. Eso ata las dos
costillas entre sí y convierte la tapa en diafragma a media altura.

**Ninguna de las tres de aluminio lleva nada de §3**: ni recocido, ni
diamantado, ni el chaflán de 0.5. Esas tres cosas son del PMMA. Canto
desbarbado y basta.

**Aleación: 5754 o mejor.** La puerta del modelo va contra `Rp0.2` = 130 MPa,
que es lo que da un 5754 H22; un 6082-T6 da ~250 y sobra. Si el taller
suministra una aleación más blanda, **avisar antes de cortar**.

### 6.2 La tabla — al carpintero

`bandeja_base_2d`, **madera maciza de 18 mm, 570.62 × 328.94**. Es el suelo
interior del case **y** el zócalo que sobresale: una sola pieza. El cuerpo se le
apoya encima y las cuatro paticas van atornilladas por debajo.

**La veta corre a lo largo** (los 570 mm). No es decoración: fija en qué
dirección se mueve la tabla, y de ahí salen las ranuras.

**Las ranuras alargadas NO son opcionales y NO se pueden cambiar por agujeros
redondos.** Son la fijación a un marco de aluminio que no se mueve, y la tabla
sí: a contraveta, del orden de 3 mm sobre los 329 mm de fondo entre un invierno
seco y un verano húmedo. El dibujo trae, en cada una de las dos filas:

- **un agujero REDONDO, el del medio** — es el punto fijo,
- **dos RANURAS de 10.5 × 5.5**, alargadas en el fondo.

Con todos redondos, la tabla se raja por la fila o suelta los tornillos. Con
todos alargados, se arrastra hacia un extremo y el vuelo del zócalo deja de ser
simétrico.

**Especie sin elegir.** Las cuentas del modelo van contra E = 11 000 MPa a favor
de veta (nogal o arce). Roble da ~12 000 y sobra; un contrachapado da ~8 000 y
pediría 20 mm. **Decir qué especie se suministra antes de cortar.**

**Acabado y sentido de la cara vista**: la cara de arriba es el suelo que se ve
por dentro del case a través del acrílico; el canto es lo que se ve por fuera.
Las dos cuentan.

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
| tapa del valle, aluminio 3 mm | `t_valle` | `guarda_valle()` |
