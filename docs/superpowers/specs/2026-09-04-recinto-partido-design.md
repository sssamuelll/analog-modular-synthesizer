# El recinto partido — R cerrada, C a la vista — **PROPUESTA SIN FIRMAR**

**Fecha**: 2026-09-04 · **Estado**: **propuesta. No firmada, sin junta.**
Nada de este papel se ha implementado y **ningún fichero se ha tocado** ·
**Depende de**: la fuente v4 (`2026-09-03-fuente-v4-liston-design.md`), cuyas
decisiones D-F1 a D-F7 esta propuesta **no toca ninguna** ·
**Reabriría, si se firma**: la spec del chasis §3.1/§3.3, `case/cad/params.scad`
(el bloque del chasis de acero, l.1720-1782), `calor_budget.py`, el §8 y el §10
de la v4, y el encargo del #289 ·
**Origen**: encargo de Samuel el 2026-09-04, sobre una observación de la sesión
del case. Los datos de partida son suyos; la verificación y el papel, míos.

> **QUÉ ES ESTE DOCUMENTO Y QUÉ NO ES.** Es una propuesta para leer y romper.
> No lleva firma, no ha pasado junta, y **rehace la arquitectura mecánica de la
> fuente** — que en este repo es exactamente la clase de cambio que no se hace
> al vuelo. Los cinco HUECOS del §6 no son formalidades: **el tercero puede
> matarla entera**, y hasta que se mida no se sabe.

---

## 1. La razón que fijó el material del chasis murió con la pieza que la causaba

`case/cad/params.scad`, l.1727-1729, verbatim:

> *«ACERO Y NO ALUMINIO, decidido el 2026-08-18: el aluminio no blinda campo
> magnetico a 100 Hz y el acero si. Casi toda caja de catalogo es de aluminio
> fundido -- seguridad y RF si, zumbido cero.»*

**Ese campo de 100 Hz era del toroide.** La v4 no tiene toroide: tiene seis
módulos encapsulados que conmutan a 65 kHz, donde el aluminio blinda de sobra.

Lo que hace fuerte al argumento no es que sea nuevo — **es que este papel ya lo
hizo, y la junta lo aceptó, sobre otra cifra.** §8, l.812:

> *«la junta señaló que ese número se derivó para un lazo rectificador de
> 6,81 cm² a 100 Hz, y transplantarlo a seis conmutadores encapsulados de
> 65 kHz es conservar la cifra y cambiar la física.»*

Con eso se retiró el «≥ 80 mm» de `revisar_diagonal()`. **La misma frase, palabra
por palabra, se aplica al acero, y nadie la aplicó.** El §1 de este papel dice
«acero, sin toroide» en la columna de la v4: se arrastró el material sin volver
a preguntar por qué estaba.

Y hay un segundo arrastre en la misma zona, éste dimensional. `params.scad`
l.1738 deriva el largo del chasis así:

```
// 332 = 10 + 200 (PCB) + 15 (cableado) + 97 (toroide con su holgura) + 10
```

**97 de los 332 mm son holgura para una pieza que la v4 borró**, y la caja se
describe a sí misma (l.1724) como la que contiene «J3 F1 RV1 NT1 J4 y **TR1**».
El §8 ya declara que «el chasis pierde el toroide» y lo delega al papel del case
§10; esta propuesta es una forma de cobrar esa deuda, no de descubrirla.

---

## 2. La partición: los cinco trabajos del chasis, y dónde cae cada uno

El comentario de `params.scad` l.1720-1736 le da a la caja **cinco trabajos**.
La pregunta que ordena esta propuesta no es «¿de qué material?», es **«¿cuántos
de los cinco necesitan una caja cerrada?»**

| # | Trabajo | Hoy | Dónde caería |
|---|---|---|---|
| 1 | Blindar campo magnético de 100 Hz | la caja | **ya no aplica** — no hay toroide |
| 2 | Disipador de los tres TO-220 (Tj de U2, 101 → 61 °C) | la pared de `y = 0` | **disipador de aletas en placa** |
| 3 | Contener 230 V | la caja | **R, y no se negocia** |
| 4 | Referencia de PE, todo bondado a un espárrago | la caja | **R** |
| 5 | EMI de los conmutadores | la caja | **R**, que es donde están |

**Los tres innegociables viven todos en R. Los dos móviles, en C.** Y la
partición no hay que inventarla: **el §8 ya la hizo**, por razones de prueba y
de campo, y con la tabla de qué lleva cada placa ya escrita.

Propuesta, en una línea: **R cerrada** (red, seis IRM, LC, detector, crowbar,
telemetría, nodo ★, PE) y **C a la vista sobre el acrílico**, con su disipador
de aletas, como la A-100 PSU3 de la foto de referencia.

---

## 3. Los números

Corridos con `calor_budget.py` y el `_tiro()` de `clearance_budget.py`.
**Verificados contra los guiones, no citados de la propuesta original.**

### 3.1 El calor del recinto se parte en tres, y dos tercios se quedan

```
P_RECINTO_MAX          31.25 W
  franja de red         3.70 W   (NTC 2,75 + choke 0,95)   -> R
  los seis IRM         14.75 W                             -> R
  cascada y resto      12.80 W                             -> C, y sale
                       -----
  sólo R               18.45 W    -41 %
```

### 3.2 El volumen

```
hoy      332 x 170 x 61 = 3.44 L
sólo R   235 x 170 x 56 = 2.24 L    -35 %
```

Los 235 son los 332 menos los 97 del toroide del §1, por el criterio de
largo/fondo/alto del propio `params.scad`.

**El cajón entero no pierde un vatio.** El calor no desaparece: cambia de sitio.
Lo que cambia es que **12,80 W dejan de estar dentro de una caja cerrada** y
pasan a disipar al aire del cajón, que es lo que el #289 está dimensionando de
todas formas. Si esto se firma, **el encargo del #289 hay que recalcularlo**: no
baja por arte de magia, se reparte distinto entre los dos lazos convectivos.

### 3.3 Lo que desbloquea — RETIRADO EL MISMO DÍA, y hay que decirlo

**Esta sección se escribió como el argumento que más me servía a mí, y unas
horas después dejó de ser cierta. Se queda escrita, tachada, porque una
propuesta que borra sus razones caídas se lee mejor de lo que es.**

Lo que decía: si C sale del chasis, sus TO-220 dejan de atornillarse a la
pared, se caen los cuatro `chasis_to220_*` de `params.scad` (l.1777-1782) y
`revisar_to220_coplanares()` (`build_pcb.py:2614`) se queda sin sujeto — y con
ellos **la restricción de encapsulado sobre la opción (b)**, porque *«las
referencias buenas viven en encapsulados que no tienen tab»*.

**Esa última frase era una suposición, y es falsa.** El **LT1963A Rev G** —
declarado en `docs/references.md` el 2026-09-04, PR #317 — es **5-lead TO-220
con tab**, tiene `ADJ` de 1,174–1,246 V sobre temperatura y 0,55 V de dropout
garantizado, y **da +330 mV de margen en `U1` sin mover un solo parámetro del
chasis**. La (b) se resuelve dentro de la restricción que esta sección quería
levantar.

Lo que sobrevive es más pequeño y más honesto: la partición **amplía el
catálogo** de piezas elegibles para `U1` y `U2`, y eso vale sobre todo para
`U2`, que sigue **sin sustituto y en −170 mV** con los candidatos de hoy. Pero
**no es un desbloqueo, y esta propuesta ya no puede apoyarse en él.**

---

## 4. Lo que esta propuesta NO propone

- **No toca ninguna decisión firmada.** D-F1 a D-F7 siguen igual: mismo listón,
  mismos seis módulos, misma cascada, misma fila de invitados con sus rieles
  propios.
- **No propone quitar silicio.** La fuente sigue haciendo tres cosas con seis
  módulos.
- **No propone aluminio para R.** R sigue conteniendo 230 V y PE; de qué
  material sea es una pregunta separada y posterior, y el §1 sólo dice que **la
  razón escrita ya no es la que la sostiene**, no que el acero esté mal.
- **No cambia el material del case.** El acrílico naranja se queda.

---

## 5. Reparto de territorio

| Qué | De quién |
|---|---|
| Este papel, el §8 y el §10 de la v4, `calor_budget.py`, la placa C | **de la fuente (yo)** |
| `params.scad`, el DXF, el reparto del chasis, la puerta del PMMA, el #289 | **del case** |

Nada de la columna derecha se toca desde aquí. Si esto se firma, lo que sale de
este papel hacia el case es **un encargo escrito**, no un commit.

---

## 6. Los cinco HUECOS, y el tercero puede matarla

1. **Que un disipador en placa dé los 61 °C con 12,80 W en tres dispositivos.**
   Sin verificar. Hoy esos 61 °C los da una pared de acero de 332 × 170; un
   disipador de aletas en placa es otro problema térmico, no el mismo más
   pequeño. **Hasta que alguien corra ese número, el §3.1 es un reparto de
   vatios y no una solución.**

2. **PMMA y calor.** El acrílico reblandece muy por debajo de lo que alcanza un
   disipador cargado, y **no existe ninguna puerta que vigile esa distancia**.
   Un disipador a 12,8 W apoyado sobre —o cerca de— una lámina de PMMA es un
   modo de fallo nuevo que el repo no mide hoy. La sesión del case se ofrece a
   escribir esa puerta; **sin ella esta propuesta no debería firmarse.**

3. **C queda con la isla analógica más sensible del instrumento sin apantallar,
   a centímetros de seis conmutadores.** Éste es el que puede matarla. Todo el
   §4.2 de la v4 —el LC amortiguado, las ferritas, los Y2 de modo común, el
   enlace trenzado— existe para que la cascada vea 200 mVp-p a 65 kHz. Sacar la
   cascada de la caja de acero cambia el problema de acoplo conducido a uno de
   acoplo **radiado**, que es el que nadie ha modelado. Y el §8 ya avisaba de
   que *«el campo de un IRM encapsulado no lo publica nadie»*.

4. **La medida con el LNA pasa de recomendable a obligatoria.** El §8 la pedía
   al montar, con la caja de por medio. Sin caja, es la única evidencia que
   habría. **Y es una medida que no se puede hacer antes de construir**, o sea
   que esta propuesta se firma sabiendo que su riesgo principal se resuelve
   tarde.

5. **El hilo de la estrella se alarga, y era la variable de arreglo.**
   `fuga_budget.py` encontró la antirresonancia de 7,48 MHz de D-F5 y dice que
   **no se arregla amortiguando el Y2 sino acortando el hilo de la estrella**.
   El nodo ★ vive en R (§8). Si C se aleja de R, el retorno de C se alarga —
   justo la variable que el guion nombró como la única palanca. **No lo he
   modelado y no sé cuánto pesa**; lo dejo escrito porque es la interacción que
   la propuesta original no listaba y sale de un guion que ya está en verde.

**Un hueco de procedencia, aparte de los cinco técnicos:** la tabla de
pre-reguladores candidatos que acompañaba a esta propuesta (LT1963A, MIC29152)
**no la he podido verificar**: sus hojas no están en el árbol
(`docs/reference/datasheets/`) y el guion que las leyó vive fuera de este
worktree. Los dos casos conocidos que sí puedo cruzar —LM2941 0,658 V y LM2991
0,640 V— los reproduce exacto, que es la forma correcta de validar un modelo:
contra un caso cuya respuesta ya se conoce. **Pero por la regla de la casa,
ningún número entra en un papel sin su hoja en el árbol**, así que esas dos
piezas aquí son candidatas nombradas y nada más.

---

## 7. Lo que pide esta propuesta

**Una junta antes que una firma**, y en este orden:

1. Que alguien corra el **§6.1** (disipador en placa a 12,80 W). Si no da los
   61 °C, la propuesta se cae aquí y no hace falta discutir el resto.
2. Que la sesión del case escriba la **puerta del PMMA** (§6.2). Sin ella no hay
   forma de saber si el diseño está cerca del fallo.
3. Que la junta decida si el **§6.3** —la isla sin apantallar— es un riesgo
   aceptable a cambio de −41 % de calor encerrado y de soltar el encapsulado del
   pre-regulador. **Es la pregunta de verdad**, y no es térmica ni mecánica: es
   si estamos dispuestos a apostar la limpieza del instrumento a una medida que
   sólo se puede hacer después de construir.

Si la junta pasa, entonces la firma; y sólo entonces el encargo al case.

---

## 8. Enmiendas que esta propuesta haría, si se firmara

| Papel / fichero | Tipo | Qué |
|---|---|---|
| v4 §1 (tabla comparativa) | Patch | «acero, sin toroide» → el material deja de estar justificado por el 100 Hz |
| v4 §6 | Rewrite | el calor del recinto se parte: 18,45 W dentro, 12,80 al aire del cajón |
| v4 §8 | Expand | la tabla R/C gana una columna: qué queda dentro del acero |
| v4 §10 | Update | el encargo al case pasa de «una caja más pequeña» a «una caja más pequeña **y** una superficie para C» |
| spec del chasis §3.1, §3.3 | Rewrite | los cinco trabajos y su reparto |
| `params.scad` l.1720-1782 | Rewrite | **del case, por encargo** |
| `calor_budget.py` | Patch | `_CONSTANTE_RECINTO_W` pierde los 12,80 de la cascada, que pasan al cajón |
| `build_pcb.py` | Patch | `revisar_to220_coplanares()` se queda sin sujeto; **se retira y se dice**, como se hizo con la reserva de invitados |
| #289 | Update | el encargo se recalcula: dos lazos convectivos en vez de uno |
| `margen_budget.py` | — | **no cambia**: el margen sigue siendo −388 mV hasta que la (b) se decida. Esta propuesta le quita una restricción de encapsulado, no le resuelve el problema |
