# Pliego de fabricación — cuerpo del SAM17

> **rev. 22 (2026-08-28).** La costilla deja de ser **chapa de aluminio
> plegada** y pasa a **anillo de pletina mecanizada** (§6.1): una pieza
> sólida por lado, sin soldadura ni ala doblada, con roscas ciegas donde
> antes había tornillo pasante. Son **seis** talleres, no cinco — acrílico,
> chapa de aluminio (miembros con bridas, placas, clips, escuadras y la
> tapa del valle), **mecanizado de aluminio** (el anillo, taller nuevo),
> acero, madera y los rieles comprados. Cada sección dice a cuál va.
>
> **rev. 21 (2026-08-27).** Dejó de ser «el pliego de acrílico»: el case
> pasó a estructura de aluminio y el acrílico bajó a piel.

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
| `coupon.dxf` | 8 | 1 | pieza de calibración — **sin acabado, sin recocer** |

**`remate_sup_2d` NO EXISTE.** Hasta el 2026-08-27 era la tapa de remate en
acrílico, atornillada de canto al larguero de remate trasero; ese día la
meseta del techo pasó a ser el ala del propio miembro trasero alto (doblada
de su blank, `marco_sup`), no una plancha aparte. `remate_sup()` y
`remate_sup_2d()` se borraron del `.scad` en el fix round 1 de esta tarea
(2026-08-28, sin llamador confirmado por grep). No es un pendiente de
`export.ps1`: la pieza no está en el diseño.

**`bandeja_base_2d` SALIÓ de este pliego el 2026-08-27.** Era el suelo, de
acrílico de 8. Ahora es una **tabla de madera maciza de 18 mm** que va bajo el
marco y hace de suelo y de zócalo a la vez. Va al carpintero, §6.2.

**Y el costado dejó de llevar taladros.** Tenía cuatro M4 de riel y cuatro M5 de
larguero; los ocho se fueron al anillo de aluminio. La pieza es ahora
**piel**: entra por detrás y asienta en el rebaje del anillo (§6.1), sobre una
junta de EPDM de 1 mm, sin tocarlo con ningún tornillo — la retención hacia
dentro la hacen las placas, los clips y la escuadra de la trasera, todos
atornillados al aluminio, nunca al acrílico. Al taller le llega un contorno y
nada más — menos operaciones y menos sitios por donde el PMMA raja.

**`lienzo_2d.dxf` es solo previsualización de nesteado: NO SE CORTA.**

### Lo que NO va a este taller

Once DXF de `case/plans/` **no son de acrílico** y no entran aquí. Se reparten
entre DOS talleres — chapa y mecanizado (§6.1) — que **no son el mismo** desde
el 2026-08-28:

| DXF | material | taller | proceso |
|---|---|---|---|
| `chasis_cuerpo_2d`, `chasis_tapa_2d`, `chasis_refuerzo_2d` | acero | chapa | corte + **plegado** |
| `miembro_bajo_2d`, `miembro_alto_2d`, `bahia_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado** + brida de extremo |
| `escuadra_trasera_2d` | aluminio 6082-T6, 1.5 mm | chapa | corte + **plegado** |
| `tapa_valle_2d` | aluminio, 3 mm | chapa | corte + **plegado** |
| `costilla_2d`, `costilla_dorso_2d` | **aluminio, pletina de 14 mm** | **mecanizado** (§6.1) | **fresado CNC**, sin plegar, sin soldar |
| `bandeja_base_2d` | madera maciza, 18 mm | carpintería | corte + ranuras alargadas |

**`costilla_2d` y `costilla_dorso_2d` son CONTORNOS REALES, no desarrollos** —
al revés de como era hasta el 2026-08-27. La pieza ya no se dobla: lo que corta
la fresa es lo que sale. `costilla_2d` trae la silueta, la ventana y el
contorno del rebaje (cara vista); `costilla_dorso_2d` trae la misma silueta
vista desde la cara interior, con los centros de las roscas ciegas a diámetro
de broca (§6.1).

**`miembro_bajo_2d`, `miembro_alto_2d`, `bahia_2d`, `escuadra_trasera_2d` y
`tapa_valle_2d` SÍ son DESARROLLOS PLANOS, no contornos** — igual que las tres
del chasis: el DXF trae el recorte, y la pieza doblada mide menos. Cortar el
contorno de la pieza montada da un fichero válido e inservible.

**Las placas de anclaje (×6, una por tramo y por costado) y los clips de
retención (×4, dos por costado) son piezas de este mismo taller de chapa y
NO TIENEN DXF PROPIO todavía** — el modelo las dibuja en 3D
(`placas_riel()`, `clips_costado()`) pero `export.ps1` no las exporta como
plancha aparte. Hasta que exista ese DXF, el taller trabaja del plano de
`params.scad`/`clearance_budget.py`: placa de pletina de `t_placa` = 6 mm
(fondo 26 las de 3U, 42.3 la del valle, cajeado de 8 × 2.5 por el lado del
anillo, un M4 de paso por riel + dos M4 a rosca ciega); clip de pletina de
`t_clip` = 4 mm × `clip_largo` = 20 mm, un M4 a rosca ciega, muerde
`clip_fondo` = 24 mm de acrílico. Es un pendiente real, no un olvido: queda
anotado para no mandar a cortar de memoria.

Las tres del chasis llevan su propio plano de plegado
([`renders/chasis-plano-plegado.png`](renders/chasis-plano-plegado.png)),
porque un DXF de corte no dice de dónde doblar. Los cinco desarrollos de
aluminio (miembros, bahía, escuadra, tapa del valle) no tienen plano de
plegado dedicado — `renders/plano_chasis.py` cubre solo el acero — y siguen
sin necesitarlo si el taller ya trabaja de los mismos DXF que el chasis.

**La tapa del valle** era acrílico de 5 mm hasta el 2026-08-25 y es la
superficie horizontal entre las dos filas de módulos. Cambió de material
porque el 70 % de su fondo está en voladizo —vuela 23.24 mm a cada lado de
su larguero— y en PMMA de 5 fluía a 90 N, con lo que era la pieza más floja
del case y a la vez donde se apoya quien se levanta.

Desde el 2026-08-27 **tampoco es plana**: lleva una pestaña de 21 mm doblada a
90° en cada punta. **Desde el 2026-08-28 esa pestaña ya NO se atornilla al
anillo**: se rosca pasante en la PLACA del valle (6 mm de pletina, ruling
R3), porque su rosca caería a 13.7 mm del plano del valle y la franja del
anillo solo admite hasta 10.25 antes de salir por la pared del rebaje. Sigue
atando la banda a las dos placas del valle y convirtiéndola en diafragma a
media altura — el ancla cambió de pieza, no la función.

**Ninguna pieza de aluminio o de acero lleva nada de §3**: ni recocido, ni
diamantado, ni el chaflán de 0.5. Esas tres cosas son del PMMA. Canto
desbarbado y basta — salvo el anillo, que tiene su propio acabado (anodizado
satinado, §6.1) y tampoco lleva recocido ni diamantado.

### 6.1 Taller de mecanizado: el anillo

**Taller nuevo desde el 2026-08-28.** Hasta esa fecha la costilla era chapa
de aluminio plegada y entraba en el pliego de chapa; el render de esa pieza
se leía «como un sándwich de aluminio envolviendo el acrílico» y Samuel lo
rechazó. El anillo que la sustituye no se pliega ni se suelda: es una pletina
maciza, vaciada por el centro con fresadora CNC.

- **Material y blank.** Pletina de aluminio de **14 mm** de espesor
  (`t_anillo`). Blank aproximado **330 × 270 mm** (spec de diseño §9; el
  contorno real mide 307.4 × 256.2 mm, `costilla_2d`, con margen de sujeción
  y desbaste).
- **Contorno + ventana.** Corte de la silueta exterior y de la ventana
  central — láser o agua y luego fresa, o todo fresa: lo decide el taller,
  siempre que el acabado final sea el fresado de §6.1.
- **Rebaje**, por detrás de la cara vista, donde asienta el costado: **6 mm**
  de ancho en el plano (`rebaje_anillo`) × **11 mm** de profundidad
  (`t_anillo − rehundido_acrilico`, 14 − 3). Sin él el acrílico no tiene
  dónde entrar y asoma por delante del anillo.
- **Chaflán 1.5 × 45°** (`chaflan_anillo`) en las DOS aristas de la cara
  vista: la exterior (silueta) y la de la ventana. Es lo que lee como
  «perfil» en vez de «banda plana» — la razón entera del cambio de diseño.
- **Radio ≥ 3 mm** en la esquina interior de P3, el único vértice cóncavo
  del contorno — pide una fresa de **⌀6 mm** para ESA esquina puntual, más
  gruesa que la de contorno general (`fresa_d` = ⌀3 mm, §8): dos útiles
  distintos para dos operaciones distintas, no una contradicción. Es
  esquina fresada, no esquina de plegado: no lleva alivio en V ni cierre
  soldado — esas dos cosas mueren con la chapa plegada.
- **Roscas ciegas M4/M5** en la cara interior (el dorso), a diámetro de
  broca según `costilla_dorso_2d.dxf`: broca **3.3 mm para M4**, broca
  **4.2 mm para M5**, **10 mm de profundidad útil** (14 mm de pletina menos
  el margen que deja la puerta de anclajes). Son **16 roscas M4 por anillo**
  — la cuenta que imprime `taladros_anillo()` sobre este mismo DXF: dos por
  riel 3U, dos sobre el primer riel 1U, dos por brida de miembro trasero y
  una por clip de retención — más **3 roscas M5 por anillo (6 en total, 2
  filas de 3) en el CANTO INFERIOR** para la tabla: esas NO salen en el DXF
  del dorso porque entran por el canto, no por la cara, así que van descritas
  aquí y no en el plano: al medio de los 14 mm de espesor, broca 4.2.
- **Acabado: anodizado satinado**, después de mecanizar. El punto de bonding
  de PE va **enmascarado antes de anodizar**, en la cara interior, uno por
  anillo — el anodizado es aislante y ese punto tiene que quedar metal
  desnudo.
- **Cupón antes de cortar los dos anillos.** Las cotas de la cara vista
  (chaflán, rebaje, rehundido) salieron de escalar una foto de referencia y
  están marcadas ESTIMADO en la spec de diseño. Mecanizar y anodizar un
  **cupón de 100 mm del perfil** — mismo chaflán, mismo rebaje, mismo
  acabado — y compararlo contra la referencia ANTES de cortar el material
  para los dos anillos completos. Es la misma lógica que el cupón de kerf
  del acrílico (§ «Procedimiento del cupón» en el README): medir sobre la
  pieza real, no sobre el render.
- **Aleación: recomendada, no obligatoria.** La puerta (`guarda_anillo()`)
  calcula con **Rp0.2 = 130 MPa**, el conservador de siempre, y con la
  sección de este anillo (I = 3714 mm⁴, 214 mm², contra 1673 mm⁴ de la vieja
  L plegada) el **5754 H22 pasa con margen de sobra**. El taller puede
  ofrecer 6082-T6 o 5083 por planitud de la pletina tras el vaciado del
  centro — el riesgo técnico real de esta pieza, no la resistencia — pero no
  es un requisito de cálculo.

**Pregunta eliminatoria para este taller** (va también al RFQ, §D):
**planitud garantizada después de vaciar el centro de una pletina de 14 mm.**
Vaciar el centro de una placa gruesa libera tensión interna del material y
puede alabearla; si el taller no puede darla plana, no es el taller.

**Muere de este taller** lo que era del pliego de chapa: los seis alivios
convexos de 4.5 mm, el rip bisector de P3 y su soldadura lineal de 14.5 mm
por costilla — el anillo es una pieza, no siete tramos cerrados a soldadura.

### 6.2 La tabla — al carpintero

`bandeja_base_2d`, **madera maciza de 18 mm, 588.62 × 327.41** (creció desde
570.62 × 328.94 el 2026-08-28: el anillo es más grueso que la vieja costilla
de chapa y la tabla vuela `vuelo_zocalo` = 10 mm más allá de él por los cuatro
lados). Es el suelo interior del case **y** el zócalo que sobresale: una sola
pieza. El cuerpo se le apoya encima y las cuatro paticas van atornilladas por
debajo.

**La veta corre a lo largo** (los 588 mm). No es decoración: fija en qué
dirección se mueve la tabla, y de ahí salen las ranuras.

**Las ranuras alargadas NO son opcionales y NO se pueden cambiar por agujeros
redondos.** Son la fijación al anillo de aluminio, que no se mueve, y la tabla
sí: a contraveta, del orden de 3 mm sobre los 307 mm de fondo entre un invierno
seco y un verano húmedo. **Van a rosca ciega en el canto inferior del anillo**
(al medio de sus 14 mm, broca 4.2 — §6.1), no a un larguero. El dibujo trae,
en cada una de las dos filas (una por anillo, 3 tornillos cada una):

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
- **Apriete de los 20 M3 sobre acrílico: 1.0 N·m, con arandela ancha d16 y ROSCA SECA.**
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
| chaflán 0.5 × 45° (PMMA) | `chaflan` | `guarda_chaflan()` |
| cajeado 4.0 mm | `kondor_prof` | `guarda_kondor()` |
| apriete 1.0 N·m / d16 | `par_m3`, `d_arandela` | `guarda_apriete()` |
| flecha de patica 0.25 mm | `flecha_pie` | `guarda_paticas()` |
| fresa ⌀3 mm | `fresa_d` | `guarda_fresado()` |
| tapa del valle, aluminio 3 mm | `t_valle` | `guarda_valle()` |
| anillo: espesor 14, cara 20, rebaje 6, rehundido 3, chaflán 1.5 × 45° | `t_anillo`, `cara_anillo`, `rebaje_anillo`, `rehundido_acrilico`, `chaflan_anillo` | `guarda_anillo()`, `guarda_rebaje()` |
| roscas ciegas del anillo, broca M4 3.3 / M5 4.2 | `d_M4_rosca`, `d_M5_rosca` | `guarda_anclajes()`, `taladros_anillo()` |
| junta de asiento EPDM 1 mm | `t_junta_asiento` | `guarda_rebaje()` |
