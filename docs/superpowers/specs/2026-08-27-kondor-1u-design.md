# SAM17 — KONDOR 1U

**Fecha:** 2026-08-27  
**Estado:** decisión de formato cerrada; montaje de riel y margen de fabricación
pendientes  
**Complementa:**
[`2026-08-27-case-esqueleto-visible-design.md`](2026-08-27-case-esqueleto-visible-design.md)

---

> **Superada el 2026-08-27, el mismo día.** Samuel decidió ir al estándar
> Intellijel 1U (39.65 de panel, 33.65 entre centros) alargando el valle 1.47 mm,
> en vez de un formato propio: a la altura que la boca permitía, el KONDOR 1U
> habría medido menos que el de mercado y costado dibujar cada tile. Lo que sigue
> vivo de este documento: el defecto del canto de 3 mm (§1), el montaje de rieles y
> los diez puntos sin verificar (§9). Implementado en el commit «El valle deja de
> ser tapa y pasa a ser una fila 1U de Intellijel».

## 1. La decisión

Samuel decide que la cara horizontal del valle sea una tercera fila de módulos
propia, **KONDOR 1U**, y no Intellijel ni Pulp Logic: el SAM17 se vende como un
instrumento completo, así que la compatibilidad con tiles de terceros no compra
nada y la identidad sí.

## 2. El formato KONDOR 1U

KONDOR 1U conserva el paso longitudinal del instrumento: **1 HP = 5,08 mm** y
el riel sigue siendo de **104 HP = 528,32 mm** dentro de los 528,62 mm útiles
del case. Cambiar ese paso rompería el registro de los módulos y de la
ventilación sin comprar compatibilidad útil.

La regla de riel ya comprobada en las filas 3U del repo es
`S = H - 2 × inset_er`, con `inset_er = 3,00 mm`. Como el riel mide 10,00 mm
a lo largo de la cara, su envolvente entre extremos es
`C = S + 10,00 = H + 4,00`. El montaje de §4 deja dos envolventes candidatas:

| montaje | alto de panel `H` | centros de riel `S` | envolvente de riel `C` |
|---|---:|---:|---:|
| rieles en las caras interiores de las alas | **38,18 mm** | **32,18 mm** | 42,18 mm |
| rieles sobre pestañas hacia fuera — envolvente condicionada | **44,18 mm** | **38,18 mm** | 48,18 mm |

Son dos candidatos, no una elección tomada. **La elección le corresponde al
dueño, no a este documento.** El primero es un máximo geométrico; el segundo es
la envolvente aritmética que reserva la banda, todavía condicionada a fijar los
datums reales de los rieles sobre las pestañas. La cota nominal queda
**SIN VERIFICAR** hasta escoger montaje, vuelo de pestaña y tolerancia.

El fondo geométrico máximo de componentes es **58,40 mm desde el dorso de un
panel de 1,60 mm**, condicionado a dejar su cara visible en el plano actual del
valle. No es todavía profundidad instalada: no reserva conector, curva de
cable, tolerancia ni el asiento que falta en §6.

## 3. Cuánto puede crecer la boca de la bahía

**No crece.** La boca de hoy es **48,18 mm** y la mayor boca que deja
`cb.main()` entero en verde también es **48,18 mm**. Con esa cota las dos filas
existentes abren **180,0°**; la apertura no pone el techo.

El techo lo pone el paso horizontal entre los dos rieles del valle. Al intentar
crecer, `guarda_escalon()` detiene la corrida con el diagnóstico:

> la bahía no cabe entre los dos rieles del valle: va centrado en x=134,32 y su
> ventana es [130,03, 134,32]

La cota mínima que conserva todas las puertas verdes es **20,80 mm**. A
**20,79 mm** la corrida se detiene porque **el M3 de la pestaña cae fuera de la
pestaña acortada**. El intervalo medido de boca es por tanto **20,80–48,18 mm**;
el extremo superior coincide con la pieza actual.

La medición anterior salió mal porque llamó solo a `guarda_tapa()` y además
tragó su `AssertionError`. Mientras esa función decía «sin topar», otra puerta
ya estaba roja. **Una puerta callada a la fuerza no es una puerta.** Todas las
cotas barridas de esta revisión —boca, retornos y térmica— corren `cb.main()`
completo, con el `AssertionError` dejado subir y verde únicamente cuando termina
la corrida entera; H y S se derivan después de esas geometrías.

## 4. Las dos formas de montar los rieles

Las dos formas eliminan un defecto, no lo tapan. Hoy los **10 M3** de la tapa
intentan atravesar alas de **3,00 mm** con un paso de **3,40 mm**. El DXF retira
cada centro **0,40 mm** del eje del ala, pero el círculo todavía desborda un
canto **0,60 mm**: no queda un agujero cerrado, sino una muesca. Con KONDOR 1U
los rieles se fijan sobre una cara nacida de las alas de **60,00 mm**; el
tornillo deja de intentar morder el canto.

### 4.1 Rieles en la cara interior de las alas

La boca entre caras interiores es
`48,18 - 2 × 3,00 = 42,18 mm`. La orientación del riel no se supuso: en
`rails()` la transformación es `Rz(-a) · Rx(90°)`, cuya parte lineal es

```text
[  cos(a)   0  -sin(a) ]
[ -sin(a)   0  -cos(a) ]
[    0      1      0   ]
```

El eje X local lleva `rail_er_fondo = 23,80 mm` y la matriz lo pone sobre la
normal interior de la cara. El eje Z local lleva `rail_er_alto = 10,00 mm` y
queda a lo largo de la cara; para la cara horizontal KONDOR, **los 10,00 mm son
los que comen boca** y los 23,80 mm entran hacia el fondo de la bahía.

La envolvente entre extremos de los dos rieles es
`C = S + 10,00 = H + 4,00`. Al imponer `C = 42,18` salen
**S = 32,18 mm** y **H = 38,18 mm**. Detrás del panel, el cuerpo del módulo
tiene que pasar entre los dos perfiles: `42,18 - 2 × 10,00 = 22,18 mm`. Esa
cota limita el **ancho del cuerpo del módulo**, no el alto del panel.

### 4.2 Pestañas hacia fuera con los rieles encima

La pestaña hacia dentro muere: invade la boca de §4.1 y la empeora. La variante
que queda para estudiar dobla cada pestaña hacia fuera, hacia el vuelo, y pone
el riel encima. Así la envolvente de la fila deja de estar limitada por la boca
libre y pasa a la cara del valle reservada fuera de la banda ranurada:
`66,4786 - 18,2956 = 48,1830 mm`. Con `C = H + 4,00` salen
**H = 44,18 mm** y **S = 38,18 mm** como **envolvente candidata**. Esta resta
asigna la cara disponible a la envolvente de los perfiles; no fija dónde cae el
centro de cada riel respecto al doblez ni cuánto puede volar sobre la pestaña.
Si esos datums obligan a sacar un perfil de la cara reservada, el par H/S deja
de valer. La colocación fabricable sigue **SIN VERIFICAR**.

Para medir las pestañas se retiraron **solo en memoria** la tapa vieja del valle
y sus pestañas de punta, y se añadieron a `_cajas_solidas()` los dos retornos de
3,00 mm inmediatamente bajo la cara superior de las alas. Cada candidato corrió
`cb.main()` entero, sin capturar excepciones. El retorno delantero se comprueba
contra el barrido que construye `_radio_giro_riel()`: es el mismo conflicto del
riel inferior que en la tanda anterior obligó a retirar el ala.

- **Delantera: 14,6740 mm es el máximo muestreado en verde.** A 14,6741 mm la
  fila inferior topa con el retorno a 52,2° y el `AssertionError` sube porque la
  puerta exige al menos 60°. Con 14,6740 mm ambas filas llegan a 180,0°.
- **Trasera: 4,0000 mm es el máximo verde.** A 4,0010 mm aparece solape estático
  con `cara_sup valle`. Los 4,0000 mm son contacto numérico, no holgura ni cota
  de corte.

Con ambos máximos presentes a la vez, `cb.main()` también termina en verde.

Esos vuelos son techos de colisión, no dimensiones elegidas ni prueba de la
unión. El plano de apoyo, los agujeros, el radio, los alivios y el margen de
fabricación del riel KONDOR siguen **SIN VERIFICAR**. Además, el máximo delantero
no puede heredarse sin más: invade el campo ranurado de §5.

## 5. Dónde cabe la banda ranurada

La franja delantera entre el inicio de la cara del valle y el ala delantera fija
mide **18,2956 mm**. En la geometría actual el vuelo trasero es **0,00 mm**. Al
aplicarle sin cambios `valle_margen`, `valle_espina`, `vent_ancho_ranura` y
`valle_paso_hp`, dentro de esa franja delantera solo sobrevive un campo entre
6,00 y 11,7956 mm: **5,7956 mm** de banda.

Entran **51 ranuras** de 4,00 mm, una por cada línea HP par. Sus extremos
redondos dejan un área abierta nominal de CAD de **1.007,19 mm²**. No son los
18,30 mm enteros convertidos en rejilla: margen y espina consumen el resto.

Al sustituir `_rejilla_valle()` **solo en memoria** por ese campo y correr las
ecuaciones de `guarda_aire()`, el sistema da **11,42 K** sobre ambiente. Según
la tabla de dimensionado, el área queda entre la fila de **11 K**, que pide
1.192 mm², y la de **12 K**, que pide 786 mm²: alcanza 12 K, no 11 K. El único
aserto vigente es 15 K, y esta corrida lo pasa con **3,58 K** de margen.

Ese 11,42 no es una propiedad aislada de la banda ni sale de interpolar áreas.
La corrida conserva la entrada de **7.616 mm²**, las dos ondas traseras con
**2.443 mm²** y los supuestos de la puerta —caja cerrada, tiro natural,
`C_D = 0,65`, aire a 293 K y 6,33 W del PSU—. Al recalcular el centroide de
salida deja el tiro en **66,15 mm**; por eso incorpora la caída de altura que
una regla de tres escondería. El repo todavía no contiene esta configuración
KONDOR como estado normal de `guarda_aire()`.

Esta corrida se conserva sin cambios para §4.1, pero **no se transfiere
automáticamente a §4.2**. Dentro de la banda, el campo medido ocupa
`6,0000..11,7956 mm`; el retorno delantero máximo de §4.2 ocupa
`3,6216..18,2956 mm` y lo tapa entero. Para conservar aquel campo, el vuelo
delantero tendría que ser como máximo **6,5000 mm**, todavía sin margen. La
temperatura y el tiro del montaje §4.2 quedan **SIN VERIFICAR** hasta fijar el
vuelo real y volver a correr `cb.main()` con esa geometría.

## 6. Fondo útil para los módulos

El modelo coloca el plano exterior actual del valle en `y = 146,5829` y la cara
superior del suelo de la bahía en `y = 86,5829`: hay **60,00 mm** desde la cara
visible hasta el primer obstáculo.

Los paneles de módulo del modelo miden **1,60 mm**. Conservando la cara visible
en el mismo plano, el dorso queda en `y = 144,9829` y el fondo útil de
componentes es **58,40 mm**. Esa es la cota de formato de §2.

La bahía todavía está construida contra la tapa vieja de 3,00 mm. Un panel de
1,60 mm enrasado por fuera deja su dorso **1,40 mm** por encima del canto actual
de las alas; por eso 58,40 mm es una envolvente geométrica condicionada y no una
profundidad de montaje ya cerrada.

Lo primero que estorba es el **suelo de la propia bahía**, no el chasis del PSU.
La cara inferior de ese suelo queda todavía **17,58 mm** por encima del techo
del chasis, situado en `y = 66,00`.

## 7. Qué puertas cambian

| puerta | cambio de sujeto o criterio |
|---|---|
| `guarda_aire()` | Pierde la rejilla fija de `tapa_valle_2d()` y tiene que contar la banda obligatoria de §5 más cualquier abertura real de los paneles KONDOR; además, hoy solo presupuesta el calor del PSU. |
| `guarda_tapa()` | Conserva las dos tapas inclinadas, pero el obstáculo central deja de ser la tapa vieja y pasa a ser la fila KONDOR completa: rieles, paneles, retornos y fondo de módulo. |
| `solapes()` | La caja de `tapa_valle` deja de tener sujeto; deben entrar las cajas de los dos rieles KONDOR, sus paneles y la envolvente de componentes. |
| `alineacion()` | Sus dos filas M3 de tapa contra alas dejan de existir; el criterio pasa a ser que las fijaciones de cada riel caigan en la cara elegida en §4. |
| `apoyo()` | Ya no tiene que probar que una tapa apoya igual sobre dos cantos; debe probar que cada riel tiene cara continua y suficiente bajo su fijación. |
| `taladros_reticula()` | La retícula de cinco M3 de `bahia_2d` conserva sujeto, pero no prueba el patrón de montaje KONDOR; la puerta debe enlazar el DXF nuevo con los rieles y con esa retícula si se reutiliza. |
| `guarda_apriete()` | Su presupuesto de 1,0 N·m y arandela d16 sobre PMMA no gobierna una junta riel–aluminio; el nuevo tornillo, rosca, apoyo y par necesitan criterio propio. |

## 8. El diafragma

Abrir el valle elimina las pestañas de punta de la tapa corrida y, con ellas,
el diafragma a media altura que declara el PLIEGO.

La corrida vigente de `guarda_miembros()` imprime **I = 184.149 mm⁴**, **32,88
veces** la inercia de referencia del 2020, para la boca actual de 48,18 mm. Como
§3 demuestra que la boca máxima verde es esa misma, no existe una segunda
corrida de crecimiento: **184.149 mm⁴ y 32,88 veces son también el resultado en
el máximo**. Eso prueba que la bandeja sigue siendo un miembro muy rígido a
flexión. No prueba que sustituya un diafragma: la puerta no modela cortante en
el plano, torsión del cajón, rigidez de las uniones a las costillas ni racking
del conjunto.

La bahía **no cubre con una medición** lo que se pierde al abrir la tapa. La
rigidez de diafragma queda **SIN MEDIR**.

## 9. Lo que NO está confirmado

- **SIN VERIFICAR — elección entre los dos montajes.** Las dos envolventes
  aritméticas están acotadas; la elección es de Samuel y este documento no la
  toma.
- **SIN VERIFICAR — geometría definitiva de las pestañas hacia fuera.** Los
  techos de colisión de §4.2 se midieron con cajas añadidas solo en memoria; no
  existen todavía en `params.scad` ni en `bahia_2d()`. Faltan vuelo elegido,
  posición del riel, radio, alivios, agujeros y crecimiento del desarrollo.
- **SIN VERIFICAR — asiento vertical de un panel KONDOR de 1,60 mm.** El modelo
  todavía dibuja una tapa de 3,00 mm apoyada en las alas; el fondo de 58,40 mm
  supone una cara exterior enrasada y deja **1,40 mm** hasta las alas actuales,
  sin decidir el asiento que salva esa diferencia.
- **SIN VERIFICAR — una geometría CAD única para boca, cara y banda.** La boca
  no puede crecer. En §4.2 la cara actual tiene que repartirse entre banda,
  retornos, rieles y panel, pero solo los retornos se inyectaron en memoria; no
  existe todavía una superficie CAD única que cierre ese reparto.
- **SIN VERIFICAR — colisiones de la fila nueva completa.** §4.2 mide los
  retornos contra las puertas existentes, pero todavía no existen sólidos de
  riel, panel, PCB ni conectores KONDOR; además, `guarda_tapa()` muestrea el giro
  cada 0,25°.
- **SIN VERIFICAR — temperatura con módulos instalados.** Los 11,42 K usan los
  6,33 W del PSU que ya presupuesta `guarda_aire()`; el repo no tiene la
  disipación de la tercera fila ni las pérdidas del transformador, y `C_D` =
  0,65 tampoco está medido en una pieza fabricada.
- **SIN VERIFICAR — sustitución del diafragma.** La inercia de §8 es de flexión
  de una sección; no existe presupuesto de cortante, torsión o racking.
- **SIN VERIFICAR — unión de los rieles a la bahía.** Al desaparecer los diez
  M3 imposibles del canto desaparece el defecto, pero todavía no están medidos
  diámetro, número, rosca, distancia al borde ni par de la unión nueva.
- **SIN VERIFICAR — contrato completo del módulo KONDOR.** Este documento acota
  dos pares candidatos de H y S y fija HP y fondo; el montaje elegido, el patrón
  longitudinal de ranuras, la rosca, las tolerancias del panel y el datum de
  montaje todavía no existen en el modelo.
- **SIN VERIFICAR — datum de los diez M3 viejos.** El DXF aplica el retiro de
  0,40 mm descrito en §4, mientras `clearance_budget.py` todavía declara las dos
  filas sobre el centro de las alas. El defecto de canto no cambia, pero las dos
  fuentes no describen la misma línea.
