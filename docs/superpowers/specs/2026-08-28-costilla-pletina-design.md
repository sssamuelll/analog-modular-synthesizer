# La costilla de pletina mecanizada

**Fecha:** 2026-08-28 · **Estado:** propuesta, pendiente de aprobación por secciones ·
**Sustituye** la costilla de chapa plegada de `2026-08-26-case-esqueleto-aluminio` y la
inversión del apilado de `2026-08-27-case-esqueleto-visible` §3 (casquillo + junta).
**No toca** la silueta, los ángulos, las tres filas (104 HP ×2 + 1U Intellijel), la
bahía, la tabla ni la trasera.

## 1. En una línea

La costilla —el anillo que sigue la silueta escalonada y carga todo el case— deja de
ser chapa plegada de 1.5 mm con una banda vista de 27 y pasa a ser un **anillo fresado
de pletina de aluminio de 14 mm**: cara vista de 20, rebaje por detrás donde el acrílico
del costado asienta **coplanar**, chaflán de 1.5 × 45° en las dos aristas, y **ni un
tornillo en la cara vista**.

## 2. Por qué: lo que la chapa no puede dar

El 2026-08-28 Samuel vio el render de la chapa plegada y lo rechazó: *«parece que el
acrílico estuviera envuelto en un sándwich de aluminio»*. La revisión adversarial
(Iris Tane, Elke Brandt, Marcus Halberg vía codex, comparando su foto de referencia con
nuestro render **al mismo ángulo**) confirmó el diagnóstico en cinco pasos: banda plana
de 27 sobre la **cara** del acrílico, junta de 4 que deja 5.5 mm de rehundido con una
línea naranja continua, ala de 16 que termina en un filo de 1.5 y no se lee como
profundidad. Ancha + plana + sin canto = sándwich.

La referencia se lee como **perfil**: cara estrecha (ESTIMADO 12–24 mm escalando la
foto al ancho del SAM17), sección compacta (ESTIMADO 12–25 de fondo), canto con chaflán
o radio (ESTIMADO 1–3) que atrapa la luz, esquinas sin alivios a la vista, y el panel
capturado **dentro** del canto. Tres de esas cuatro cosas no existen en una chapa de
1.5: no hay arista que chaflanar, cada esquina convexa lleva un alivio de 4.5 y la
cóncava P3 exige soldadura.

De las seis familias de proceso que Halberg clasificó, el anillo mecanizado sale
**primero en fidelidad visual y primero en viabilidad para una unidad**, con el riesgo
técnico más bajo (bajo–medio: planitud tras el vaciado). Samuel eligió esa: *«vamos a
hacer esto con pletina mecanizada»*.

## 3. La sección del anillo — cada cota con su origen

| cota | valor | de dónde sale |
|---|---|---|
| `t_anillo` — espesor (Z) | **14** | El PMMA de 8 viene ±1.2 (Schaeffer AG, ya en el repo): el peor caso mide 9.2. Detrás del labio hacen falta 9.2 + 1 de junta de asiento + 0.5 de holgura = 10.7 ≤ `t_anillo − rehundido`. Con 12 el rebaje queda a **−0.2**; con 14 sobra 0.3. **No es gusto: es la tolerancia del acrílico.** |
| `cara_anillo` — cara vista (en el plano) | **20** | Dentro del rango ESTIMADO 12–24. El mínimo lo pone la franja interior donde asientan las placas de anclaje (§5): `cara_anillo − rebaje_anillo ≥ 3 × d_M4_paso = 13.5` → `cara ≥ 19.5` → 20. |
| `rebaje_anillo` — cuánto solapa el acrílico (en el plano) | **6** | Retención por el labio con margen; lo comprueba `guarda_costado()` como vano libre. |
| `rehundido_acrilico` — cuánto queda atrás la cara del PMMA | **3** | Rango ESTIMADO 3–7 de la foto; el mínimo, para que el labio tenga cuerpo (3 mm de aluminio sobre el acrílico). |
| `chaflan_anillo` | **1.5 × 45°** | Rango ESTIMADO 1–3. En las dos aristas de la cara vista: la exterior (silueta) y la de la ventana. |

**Sección resultante**, flexión fuera del plano por tramo (viga biempotrada, la misma
hipótesis de `guarda_costilla()`): tramo macizo de (20 − 6) × 14 más el labio 6 × 3.
A mano, con W = 18 y T = 14 dio I = 3 249 mm⁴ contra 1 673 de la L plegada (1.9×); con
W = 20 sube. **La cifra que vale es la de `guarda_anillo()`**, no esta.

**Peso:** 214 mm² × ~1.10 m de perímetro × 2.70 g/cm³ ≈ **0.58 kg por costilla**, contra
0.04 de la chapa. +1.2 kg al aparato. Se asume. (Decía 186 mm² y 0.55 kg, de cuando la
sección se estimó a mano con el rebaje de 6 × 3; el rebaje real es 6 × 11. Aquí vale lo
mismo que arriba: **la cifra que manda es la que imprime `guarda_anillo()`** en cada
corrida — hoy `I = 3714 mm⁴, 214 mm², 0.58 kg por costilla` —, no la de este papel.)

**Anchura del case:** las placas de anclaje se meten entre el riel y el anillo (§5), y
el anillo es más grueso que el apilado viejo:
`ancho_util = largo_riel + hol_riel + 2·t_placa = 528.62 + 12 = 540.62` y
`ancho_total = ancho_util + 2·t_anillo = 568.62`. Hoy 550.62: **+18 mm**.

> **Enmienda de la Tarea 1 (2026-08-28), ruling R1 del plan.** Este párrafo decía
> `2·t_placa = 8` → `ancho_util 536.62`, `ancho_total 564.62`, **+14 mm**, con la placa
> de anclaje en 4. La placa sube a **6** (ver la enmienda de §5) y el case se ensancha
> 4 mm más. El 4 no se borra: era la cota correcta mientras nadie había mirado la
> cabeza del tornillo del riel. Las dos cifras vivas las imprime el budget:
> `perfil: ... ancho_util=541` y `ancho_total = 568.62`.

**`t_costilla` no muere: cambia de dueño.** El inventario encontró que lo comparten los
tres miembros de chapa (canales trasero bajo, trasero alto y bahía) en ~140 sitios.
Sigue valiendo 1.5 y pasa a significar «espesor de la chapa de los miembros»; su
comentario lo dice y el nombre se queda, porque renombrar 140 sitios es un riesgo sin
premio. Lo mismo `radio_doblez_costilla`, que `_bd_miembro()` usa para los pliegues de
los miembros.

## 4. El acrílico del costado: coplanar en la ventana, no apilado detrás

Hoy el costado va **detrás** de la costilla: chapa 1.5 → junta 4 → PMMA 8, y el M4 del
riel lo cruza dentro de un casquillo. Eso nació para que el apriete nunca tocara el
acrílico (spec 2026-08-27 §3.2) y era correcto para ese apilado. Con el anillo, el
apilado desaparece:

- El acrílico se recorta a la silueta **retranqueada `cara_anillo − rebaje_anillo`
  = 14 mm** por todo el contorno (más 0.5 de holgura), entra **por detrás** y asienta
  en el rebaje. Su cara exterior queda 3 mm detrás de la cara del anillo. Desde fuera se
  ve la cara del anillo (20) y, en la ventana, el acrílico rehundido.
- Entre el labio y el PMMA va una **junta de asiento de EPDM de 1 mm** — nunca aluminio
  contra acrílico. La tolerancia del espesor la absorbe la profundidad del rebaje, no
  la junta: **#98 sigue siendo cosmético**, ninguna cota funcional depende del espesor
  real del PMMA.
- Hacia dentro lo retienen **clips de retención**: pletinas de 4 mm atornilladas a la
  franja interior del anillo con M4 a rosca ciega, solapando 4 mm sobre el acrílico. La
  cantidad la decide `guarda_costado()` por vano libre; se parte de 6 por costado.
  - *Enmienda (Tarea 4, 2026-08-28):* esos 4 mm sobre el acrílico serían `clip_fondo`
    = 18.5, y ahí el clip muere **dentro del rebaje**, pisando sólo la ceja que ya está
    encajonada entre el labio y la pared. Se fija `clip_fondo` = **24** — ruling de la
    tarea, no de esta spec —: pasa el canto de la ventana (20) y muerde 4 mm de acrílico
    **volado**, 9.5 mm de acrílico en total. Y la cantidad la decidió la puerta:
    **2 por costado**, no 6 (§9).
- **El costado vuelve a cero agujeros.** Es piel. Los cuatro pasos de casquillo de la
  Tarea 3 se van, `taladros_costado()` muere por segunda vez y `agujeros_donde_toca()`
  recupera su censo de «costado CERO».
- Mueren `L_casquillo` y `t_junta`; entra `t_junta_asiento = 1`. Muere
  `guarda_apilado()`; entra `guarda_rebaje()` (§8).

## 5. Anclaje de rieles y miembros: placas interiores, roscas ciegas, cara limpia

Medido en el modelo: el eje del M4 de cada riel 3U cae a **15.90 mm** del contorno de la
silueta. Para que ese tornillo atravesara la cara vista con canto, la cara tendría que
medir ≥ 15.90 + 1.5 × 4.5 = **22.65**, que es exactamente por qué la banda de chapa
medía 27. Samuel decidió la otra vía: **nada atraviesa la cara**.

**Placa de anclaje del riel** (×6): pletina de aluminio de **6 mm**, ~40 × 22, con un
agujero **cajeado por el lado del anillo** para el M4 del riel y dos pasos para M4 a
**roscas ciegas** en la franja interior del anillo (14 de pletina → 10 de rosca útil).

> **Enmienda (2026-08-28), decisión A del dueño.** Decía **×12**, una placa por punta de
> riel. Son **6: tres por costado**, y cada una es el marco de UNA FILA — recoge las dos
> puntas de riel de su tramo (`cara_inf`, `valle`, `cara_sup`) en una sola pieza. Por eso
> los DXF son tres contornos distintos y no doce iguales: `placa_cara_inf_2d`,
> `placa_valle_2d` y `placa_cara_sup_2d`. Lo cuenta `check_dxf` en cada corrida.

> **Enmienda de la Tarea 1 (2026-08-28), ruling R1 del plan.** Decía **4 mm**, y a 4 no
> cabía: la cabeza del M4 del riel (botón ISO 7380, 2.2 de alto) tiene que quedar
> DENTRO de la placa, porque debajo hay acrílico hasta z = 13.2 y una cabeza que asome
> lo pinza. Con un cajeado de 8 × 2.5 quedan 3.5 de placa bajo la cabeza. `t_placa = 6`,
> y con él `ancho_total` sube 4 mm más de lo que decía §3.
Orden de montaje obligado, y va al README: **primero el riel a la placa** (la cabeza
queda en el cajeado, del lado que después mira al anillo), **después la placa al
anillo** desde dentro. Al revés no se puede apretar.

**Miembros** (×3): el alma del canal se prolonga y se dobla 90° en cada punta como
**brida de extremo** de la misma chapa de 1.5, con dos **M4** a roscas ciegas en la
franja. Resuelve el bloqueo que Halberg encontró: hoy el M5 axial entra en un canal
**abierto** y no muerde en nada.

> **Enmienda (2026-08-28), ruling de la Tarea 3.** Decía **dos M5**. Bajaron a **M4**:
> la franja de 14 mm no admite a la vez el paso M5 en la brida y la broca de rosca M5 en
> el anillo con 1.5 D de margen. Son 8 M4 de brida en total (2 por punta × 2 puntas × 2
> miembros traseros); el tercer miembro, la bahía, ancla a la placa del valle (ruling
> R3), no al anillo.

**Tabla** (×6): sus M5 suben a **roscas ciegas en el canto inferior del anillo** (14 mm
de canto, rosca de 10). Resuelve el otro bloqueo: la tabla tiene seis agujeros y la
costilla de chapa no tenía contraparte.

Cuenta de roscas ciegas por anillo, la que `check_dxf` imprime hoy: **16 en la cara
interior** — 10 de placa (2 por punta de riel 3U y 2 sobre el primer riel 1U) + 4 de
brida de miembro + 2 de clip — **más 3 M5 en el CANTO inferior** para la tabla, que no
salen en el mismo DXF porque entran por el canto y un dibujo de la cara no sabe
dibujarlos. Todas M4 en la cara y M5 en el canto, en aluminio de 14, sin insertos.
(Decía «24 (rieles) + 6 (miembros) + 6 (tabla) + clips», de cuando cada punta de riel
llevaba su propia placa y las bridas eran M5.)

## 6. Cantos, esquinas, acabado

- **Una pieza.** Sin esquinas que unir, sin alivios, sin soldadura en P3. La cóncava P3
  queda como esquina interior fresada: **radio ≥ 3** (fresa de 6), y va en el pliego.
- **Chaflán 1.5 × 45°** en las dos aristas de la cara vista. Las aristas de la cara
  interior solo desbarbadas.
- **Acabado:** anodizado satinado tras el mecanizado. El punto de bonding de PE va
  **enmascarado** antes de anodizar, en la cara interior, uno por anillo — el requisito
  de la spec 2026-08-27 §3.4 no cambia; un anillo monolítico **reduce** el censo de
  piezas a unir (Halberg).
- **Aleación:** de pletina, la que el taller tenga en 14 con planitud garantizada tras
  el vaciado (5083 o 6082 son las corrientes). La puerta calcula con **130 MPa**, el
  conservador de siempre; con I de 3 000+ contra los 1 673 que ya pasaban, no es lo que
  manda.

## 7. Lo que muere, lo que cambia, lo que se queda

Del inventario (`inventario_pletina.md`, 723 líneas, verificado por grep):

**MUERE:** `ala_costilla`, `ala_doblez`, `L_casquillo`, `t_junta`; `costilla_2d()` como
desarrollo, `cost_sb/ba/bd()` para la costilla; `_seccion_L()`, `autocomprobacion_L()`,
`paso_junta_L()` (**ya estaba rota**: cita `AS_M3`, `TAU_M3`, `MU_ALU_SECO`, que no
existen — se borra), `_tramos_costilla()`, `plegado_costilla()`,
`bbox_desarrollo_costilla()`, `guarda_costilla()`, `guarda_apilado()`,
`guarda_canto_visto()`, `taladros_costilla()`, `taladros_costado()`; el párrafo de
`export.ps1` 29–35 que explica por qué el DXF de la costilla «dejó de ser el contorno».

**CAMBIA:** `costilla_2d()` → contorno real del anillo: silueta, ventana, contorno del
rebaje y centros de las roscas ciegas de la cara interior; `costilla()` → sólido con
rebaje y chaflán; `costados()`/`costillas()` → el acrílico dentro de la ventana;
`ancho_total`/`ancho_util` en sus dos copias (`sam17_case.scad:30` y
`clearance_budget.py:102`) y el assert de `leer_params()`; `_cajas_solidas()` z0/z1 →
caras interiores en `t_anillo`, rieles además en `+ t_placa`; `_sobres()` → sobre de
contorno como el del costado; `guarda_costado()` → misma lógica, ventana nueva;
`railes_dentro_del_costado()` → mismos números de entrada nuevos; `guarda_zocalo()` →
offset de la tabla; los miembros `miembro_*_2d()` dejan de llamar `cost_bd()` y usan
`miembro_bd()`; `bom()`.

**SE QUEDA:** `guarda_miembros()`, `guarda_fila_1u()`, `guarda_agarre()`,
`taladros_reticula()`, `_bd_miembro()`, `guarda_meseta_es_chapa()` (compara la meseta
con la chapa de los miembros, que sigue siendo `t_costilla`), la comprobación cruzada
de `E_aluminio` (el anillo sigue derivándose por flecha).

## 8. Las puertas nuevas — se escriben antes que el modelo

- **`guarda_anillo(p)`**: por tramo, viga biempotrada con la sección de §3, flecha ≤
  `flecha_costado_max` (0.60) y tensión ≤ 130 MPa bajo `carga_mano`. Imprime I, A y kg.
- **`guarda_rebaje(p)`**: `t_anillo − rehundido ≥ t_cheek·(1 + tol) + t_junta_asiento +
  0.5`; `cara_anillo − rebaje_anillo ≥ 3·d_M4_paso`; `rebaje_anillo ≥ 5`;
  `rehundido ≥ 3`. Sustituye a `guarda_apilado()` y a `guarda_canto_visto()`: con el
  acrílico dentro de la ventana, el anillo cubre su canto **por construcción** en todo
  el perímetro, y esta puerta es lo que garantiza que el rebaje sea más hondo que el
  PMMA más grueso.
- **`taladros_anillo()`** (check_dxf): los centros de rosca ciega de la cara interior
  salen en el DXF como círculos (la profundidad va en el pliego); se cuentan — **16 por
  anillo**: 10 de placa + 4 de brida + 2 de clip — y se exige 1.5 D contra la ventana y
  contra la silueta, dentro de la franja.
- **`agujeros_donde_toca()`**: vuelve la sección «costado: CERO agujeros».
- Cada tarea del plan termina con **los dos renders** regenerados: es como Samuel
  decide.

## 9. Lo que cambia para el taller

- **Costilla: taller de mecanizado**, no de plegado. Pletina de 14, blank ~330 × 270,
  contorno + ventana (láser o agua, y luego fresa; o todo fresa: lo decide el taller),
  rebaje de 6 × 11 por detrás, chaflán 1.5, roscas ciegas M4/M5 en la cara interior y
  M5 en el canto inferior, radio ≥ 3 en P3. Anodizado satinado con enmascarado del punto
  de bonding. **Pregunta eliminatoria nueva al RFQ:** planitud garantizada tras vaciar el
  centro de una pletina de 14 (el riesgo que Halberg marcó).
- **Placas de anclaje ×12:** pletina de **6** (era 4; ver la enmienda de §5), corte +
  roscado. **Clips ×4:** pletina de 4, que ahí sí vale — eran ×12 en la propuesta y la
  puerta dejó 4 (2 por costado, los dos en el canto del suelo): de los cuatro tramos sin
  placa, sólo el suelo tiene franja libre donde atornillar, y con esos dos
  `guarda_costado()` da verde. Piezas nuevas de BOM.
- **Miembros:** mismo taller de chapa, con bridas de extremo.
- **Acrílico:** el costado cambia de contorno (retranqueado 14) y vuelve a cero
  taladros. La trasera no cambia aquí.
- Mueren del pliego: casquillos, junta de 4, el plano de plegado de la costilla (que,
  por cierto, **nunca existió**: `plano_chasis.py` solo cubre el chasis de acero).

## 10. Lo que este documento NO cierra

- ~~**La trasera sigue enseñando canto**~~ — **CERRADO el 2026-08-29 (#234).** Era el
  25.6 % del contorno medido el 28-08, y los 260 puntos estaban todos en la misma
  pieza: sus cantos superior e inferior, 540 mm cada uno sin metal encima, y el de
  arriba eran además los últimos 8 mm del pico. La salida no fue la que apuntaba esta
  sección — los miembros traseros no pueden hacer de marco sin una T, y una T no se
  pliega de un blank —, sino **dos bandas de la misma chapa**: `marco_trasera_sup_2d`
  (angular, banda vista de 20 y ala de 9.5 que muere en el doblez de la meseta) y
  `marco_trasera_inf_2d` (pletina plana de 20; sin ala porque ese canto apoya en la
  tabla). La trasera se rehunde `t_costilla` para que el marco quede a ras. Lo paga
  `prof_sup`, que baja de 29 a 27.5 — no el inset, cuyo acantilado está en 12.8. Lo
  vigila `guarda_marco_trasera()`. De paso salió una gemela desincronizada 1.5 mm
  desde el 27-08: el `.scad` cortaba la plancha en la cara de abajo de la meseta y
  `clearance_budget` la declaraba llegando al pico.
- ~~**El canto trasero del acrílico no tiene retención hacia dentro**~~ — **CERRADO el
  28-08 con la salida (a): la escuadra de la trasera (Tarea 4b, commit `2e46ff8`).** Eran
  **227 mm** de canto libre (x = 292.91, y de 14.5 a 241.68) sin un solo apoyo hacia
  dentro — en la franja trasera no cabe clip, la ocupa el canto de `piel_trasera` — y el
  punto peor del barrido caía en **(292.8, 117.5)**, a menos de 1 mm de ese canto, donde
  la fórmula de placa **empotrada** no vale. Samuel eligió (a) y está construida: un
  angular de chapa de 1.5 atornillado a la trasera con 3 M3 por costado, cuya ala asoma
  5.5 mm sobre el canto y lo pisa por dentro en el **91 %** de su largo libre. El punto
  peor se mudó a **(221, 84)** — centro del panel, donde el modelo sí vale — y el vano
  de dentro bajó de 95.5 a **65.0 mm**, con lo que ahora manda el de fuera (69.4). Las
  otras dos salidas quedan como historia de la decisión: **(b)** recortar `piel_trasera`
  para que quepa un clip en la franja trasera; **(c)** aceptarlo y cerrarlo cargando el
  prototipo.
- **La meseta se lee como repisa** (Iris): 27.5 mm de chapa horizontal perforada
  (eran 29 hasta la rev. 23). Se juzga en render con el anillo puesto — y desde el
  29-08 no acaba en el canto del acrílico sino en el ala del marco trasero, o sea
  que lo que se juzga es una repisa de metal entera.
- **La banda del valle fluye a ~27 N si se levanta el case por ahí** y la puerta lo
  imprime sin fallar. Hay que apoyarla o convertirlo en assert.
- ~~**Pies sin taladro en la tabla**~~ — **CERRADO en la Tarea 6 (2026-08-28)**: la
  tabla lleva sus cuatro taladros y `check_dxf` los cuenta en cada corrida
  («`bandeja_base_2d`: 4 taladros de pie d=4.50 mm en las posiciones de `paticas()`»).
- **Secuencia de montaje sin demostrar, racking sin medir (#203)** — los bloqueos de
  Halberg que no dependen de la pletina, y estos siguen abiertos.
- Los rangos de la foto siguen siendo ESTIMADOS y **el cupón sigue sin cortarse**
  (#237) — eso no lo cierra ningún fichero. Lo que sí entró el 2026-08-29 es lo que
  faltaba para poder pedirlo: **`cupon_anillo_2d`**, la sección del perfil, que es el
  único plano del anillo con profundidades (los otros dos son vistas de planta y no
  saben decir «14 de pletina» ni «1.5 × 45»), verificada por `seccion_del_cupon()`; y
  el PLIEGO convertido en **punto de parada**, con la tabla de qué se mide cuando el
  cupón vuelve y qué se cambia si no pasa.
- Desincronizaciones de papel que la revisión encontró: el BOM aún dice «transversal
  2020», la spec del 27 dice chapa de 3, `params.scad` llama «portantes» a los costados.
  Van con la Tarea 6 de los papeles.
