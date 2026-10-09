# Junta de la fuente v5 — D-V1 a D-V5, antes de la firma

**Fecha**: 2026-09-08 · **Estado**: **junta, no firma**. Este papel no decide
nada: dictamina sobre lo que `2026-09-05-fuente-v5-ladrillo-design.md` pone a
firmar ·
**Revisa**: `docs/superpowers/specs/2026-09-05-fuente-v5-ladrillo-design.md` §9
(D-V1 a D-V5), contra el papel FIRMADO `2026-09-03-fuente-v4-liston-design.md` ·
**Panel**: tres lentes disjuntos (contradicciones con lo firmado · modos de fallo
en marcha · complejidad accidental) ·
**No toca**: ninguna D-V se firma ni se tumba aquí; ninguna D-F\* se mueve

> **El orden es brief → papel → junta → firma.** Ya pasó una vez que se pidió la
> firma primero: la junta posterior cambió 6 de 11 mecanismos. Por eso esto va
> antes.

**Veredicto: 1 firmable tal cual · 3 firmables con condición · 1 no firmable
aún · ninguna a tumbar.**

---

## 1. En cristiano

Lo decidido el 05-09 es el **qué**: la etapa AC-DC sale de la caja. Eso no se
discute aquí. Lo que se juzga es el **cómo**: un ladrillo de catálogo de 24 V
afuera, un cordón de dos hilos, y convertidores adentro que hacen los rieles.

De las cinco piezas de ese plan:

- **Comprar el ladrillo hecho** en vez de construir una caja de red propia está
  listo para firmar. Nadie le puso pero.
- **Tres** —la tensión de 24 V, el crudo a 15,5 V y el cordón de dos hilos— solo
  necesitan que se escriba un contrato que hoy no está escrito: qué rango
  aguanta, qué conector, qué pasa si se conecta al revés o con el adaptador
  equivocado. No falta descubrir nada; falta anotarlo.
- **La de los convertidores de adentro no está lista**, y es la del corazón.

**Por qué esa no está lista, en una frase:** los módulos Mean Well traían varios
trabajos de seguridad incluidos en el precio, y al sacarlos **nadie hizo la lista
de esos trabajos ni dijo quién los hereda**.

Dos en concreto:

1. **La protección por riel.** Cada IRM se apaga solo si le entra sobretensión o
   un corto, y no se lleva a los demás. Con un ladrillo único alimentando todo,
   nadie escribió qué pasa cuando el rack hace un corto. El #334 ya dice que una
   pieza no sobrevive a su propia protección; esto es lo mismo a escala de
   arquitectura.
2. **El aislamiento de la tierra digital.** El +5 digital está firmado como
   flotante, con más de 1 MΩ contra las masas de audio. Es lo que impide que la
   basura digital entre al sonido. El plan nuevo cuelga el convertidor digital y
   los positivos del rack de la misma entrada, y no dice si comparten retorno.
   Si lo comparten, ese aislamiento se acabó — y es justo lo que protege los
   0,8 µVrms por los que existe la cascada entera.

---

## 2. Las cinco fichas

### D-V1 — la etapa AC-DC es pieza de catálogo certificada, fuera de la caja

| | |
|---|---|
| **Qué cierra** | El **#130** pierde sujeto: no hay entrada de red en el chasis. Evita diseñar, acabar y **certificar** un cajón AC-DC propio |
| **Qué cuesta** | Un ladrillo. **64,22 W** de salida, **8,76 W** disipados fuera, **72,98 W** pedidos a la red con rendimiento **0,88 ESTIMADO** (`ladrillo_budget.py:93`). Precio y referencia: **HUECO** |
| **Qué hueco deja** | «Certificada» no dice clase, aislamiento, fuga, protecciones ni carga capacitiva admisible |
| **Contra qué choca** | Retira **D-F7** (`PS5` = IRM-45-5) y las piezas de **D-F5** (Y2 de modo común por módulo). Sus obligaciones necesitan relevo en D-V4/D-V5 |
| **Veredicto** | **FIRMABLE.** El «0 W» comparativo contra un cajón externo multirriel no está calculado y no sostiene el voto — pero el voto se sostiene sin él |

### D-V2 — el ladrillo son 24 V

| | |
|---|---|
| **Qué cierra** | Fija el nominal de transporte. **2,68 A** por el cordón (`ladrillo_budget.py:169`) |
| **Qué cuesta** | Precio incremental de elegir 24 V y piezas asociadas: **HUECO** |
| **Qué hueco deja** | «Queda más margen para el arranque» no trae ventana de entrada, umbral de subtensión, transitorios, reserva de arranque ni recuperación |
| **Contra qué choca** | Ninguna D-F\* fija esta interfaz nueva. **Pero los ±20 V de entrada máxima de `U1` (D-F8) siguen limitando el nodo posterior al DC-DC: 24 V en el cordón NO son 24 V en `U1`** |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: definir el contrato de entrada válido y los límites de fallo y arranque de la cadena completa. La referencia comercial puede quedar para el plan (v4 §11) |

### D-V3 — el crudo de la cascada son 15,5 V

| | |
|---|---|
| **Qué cierra** | Holgura en `U1`: **+330 → +811 mV**. El detector de ventana de D-F4 tenía **+40 mV útiles** |
| **Qué cuesta** | **+0,33 W en `U1` y +0,33 W en `U2`**, más **+0,12 W** de conversión = **+0,78 W dentro de la caja**. El calor pasa de 63,43 a 64,22 W. **Los «+0,33 W» publicados solo cuentan `U2`** |
| **Qué hueco deja** | El máximo de fallo del crudo nuevo y sus transitorios siguen sin cota: **el #334 no queda cerrado** |
| **Contra qué choca** | La fila a firmar todavía dice «`U2` +311 mV» y razona sobre el LM2991. **D-F9 firmó el LT3015**, cuyo margen a 15,5 V es **+1017 mV**. 15,5 V no contradice a D-F9; el sujeto de su justificación sí |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: reescribir su finalidad —ya no cierra `U2`, compra holgura a `U1` y a D-F4— y aceptar el coste completo. **No se tumba por redundante: esa holgura sí hace trabajo** |

### D-V4 — los rieles se derivan dentro con DC-DC; la cascada no se toca

| | |
|---|---|
| **Qué cierra** | Deriva los seis rieles adentro. Permite un +12 compartido por pantalla y fila, con cables y retornos separados |
| **Qué cuesta** | **56,23 W entregados y 7,99 W de pérdida interior**, con tres rendimientos ESTIMADOS. **Seis salidas presupuestadas no son seis convertidores físicos**: el guion presupone un flyback de doble salida para los crudos. Piezas, euros y trabajo de protección: **HUECO** |
| **Qué hueco deja** | Aislamiento y retornos, límites de fallo por riel, coordinación crowbar/corte, secuencia, rizado y capacidad sostenida de los sustitutos. **«Cascada intacta» no hereda la prueba de ruido**: `rizado_budget.py` sigue con IRM a 65 kHz y `U1` = LM2941, que D-F8 retiró |
| **Contra qué choca** | **D-F4** y **D-F6** — ver §4.2 y §4.3 |
| **Veredicto** | **NO FIRMABLE AÚN.** Falta el contrato eléctrico y de fallos, con relevo explícito de D-F4/D-F6, del aislamiento, del ruido y del sostenido. **Conservar la cascada no conserva automáticamente esas funciones** |

### D-V5 — el cordón es de dos hilos

| | |
|---|---|
| **Qué cierra** | Evita transportar rieles hechos y que la caída del cordón se reste del margen de `U1`/`U2` |
| **Qué cuesta** | **2,68 A**; a 16 AWG y 2 m son **141 mV, el 0,6 %** del nominal (`ladrillo_budget.py:173`). Conector, resistencia de contactos y euros: **HUECO** |
| **Qué hueco deja** | No fija conector, polaridad, retención ni calibre vinculante. Tampoco inversión, conexión alimentada, reconexión, corto del cordón ni adaptador incompatible |
| **Contra qué choca** | **D-F5** cerraba modo común por chasis → PE → primario, y la v4 llevaba PE y `J5` al espárrago. **Dos hilos no transportan ese PE separado**, y el sustituto no está identificado |
| **Veredicto** | **FIRMABLE CON CONDICIÓN**: resolver retorno/chasis/PE y las obligaciones de protección y conexión DC. La menor caída no demuestra esos comportamientos |

---

## 3. Los dos bloqueantes de D-V4

Son **silencios**, no HUECOS declarados. Un hueco declarado al menos tiene a
alguien mirándolo; un silencio no.

### 3.1 Supervivencia y corte por riel — **NADIE**

**Qué cubría la v4**: rangos de OVP y sobrecarga, hiccup por módulo, **D-F6**, y
PTC por slot. El #334 identifica los **±20 V** de `U1`. El digital sin crowbar
exigía soportar **6,75 V**; el SCR seguía sin pieza (`check_absmax.py:310`, `:110`).

**Quién lo cubre en la v5**: nadie define límites de fallo ni coordinación del
sustituto.

**Qué pasa si nadie lo cubre**: no se demuestra supervivencia ni que el crowbar
interrumpa. **La limitación del ladrillo común no acredita la función del hiccup
individual retirado.**

### 3.2 Separación de GNDD — **NADIE**

**Qué cubría la v4**: +5 digital flotante, GNDD fuera de la estrella, y
aceptación de **>1 MΩ entre GNDA y GNDD** dentro de la fuente (v4 §4.1, §9.1).

**Quién lo cubre en la v5**: nadie define barreras ni retornos. El presupuesto
asigna el buck al digital y los positivos del rack **desde la entrada común**
(`ladrillo_budget.py:99`, `:128`).

**Qué pasa si nadie lo cubre**: si comparten retorno, se rompe el aislamiento
firmado y cambian los caminos de corriente. **Es un contrato ausente, no una
netlist ya demostrada incorrecta** — se cierra escribiéndolo, no rediseñando.

---

## 4. Tres defectos ejecutables

No son opiniones sobre la propuesta: son cosas que están mal en el árbol hoy.
Cada uno lleva su issue.

### 4.1 El aserto que sostiene el papel no puede fallar

`hardware/01-power-supply/v5/ladrillo_budget.py:253` vigila lo que su propio
comentario llama «la identidad que sostiene el papel entero»:

```python
assert abs(calor_del_cajon_w() - salida_ladrillo_w()) < 1e-12, (
    "el calor del cajon dejo de ser la salida del ladrillo: ...")
```

y en `:160`:

```python
def calor_del_cajon_w() -> float:
    return salida_ladrillo_w()
```

**La función devuelve aquello contra lo que se compara.** El comentario promete
que «si algún día alguien mete aquí un término que no baje por el cordón, esto
salta», y no puede saltar nunca. Es un detector de humo cableado a su propio
botón de prueba.

Y dos agravantes: ~~**ninguna puerta corre este guion** (nada en `.githooks/`
ni en `scripts/` lo nombra)~~ **— falso, ver enmienda**, y **el guion sale con
código 2**.

> **ENMIENDA (2026-09-08). El primer agravante era falso**, y lo era por mirar
> en dos sitios cuando el corredor vive en un tercero.
>
> `hardware/tools/gates.py` **descubre por patrón, no por lista**: su tupla
> `PATRONES` (`:56`) incluye `hardware/**/*_budget.py` (`:58`), que recoge
> `ladrillo_budget.py`. Un `grep` contra `.githooks/` y `scripts/` no lo
> encuentra porque **el guion no se nombra en ningún sitio, y eso es el
> diseño**: «una lista de scripts hay que acordarse de ampliarla, y el día que
> a alguien se le olvida el gate nuevo nace ya sin correr» (`:17`).
>
> El segundo agravante es cierto y tampoco pesa lo que parecía: `gates.py`
> trata el **código 2 como HUECO declarado, no como fallo** (`:166-167`), por
> convención del repo. El guion corre, y su hueco se imprime en el resumen de
> la tanda. No es un fallo invisible.
>
> **El hallazgo central no se mueve:** el aserto sigue comparando una función
> contra lo que ella misma devuelve y sigue sin poder saltar. Lo que se cae es
> la agravante, no el defecto. El **#338** hereda la corrección: su criterio de
> cierre pedía «que una puerta corra el guion», y esa mitad ya estaba hecha
> antes de pedirla.
>
> Es el mismo patrón que ya costó un hallazgo falso en este árbol: **las reglas
> viven en más de un sitio**, y buscar solo en el que uno recuerda da un
> negativo que parece evidencia.

### 4.2 D-F4 se retira por un sujeto equivocado

El papel v5, l.246:

> | **D-F4** (secuenciador) | usaba los pines ON/OFF de los Mean Well, que ya no están dentro |

La tabla firmada de la v4, l.281:

> | **D-F4** | **secuenciador** por los pines ON/OFF, **en la cascada y en el rack** | §4.2, §4.3 |

**La cascada no se va** — el propio papel v5 lo repite en §7. Son dos ON/OFF
distintos con el mismo nombre, y se está dando por muerta una decisión firmada
cuyos actuadores se quedan. D-F9 acaba de recuperar precisamente esa propiedad
(el LT3015 habilita en alto igual que el LT1963A).

### 4.3 D-F6 quedó huérfana en silencio

**`D-F6` no aparece ni una vez en el papel v5.** Está firmada, y dependía del
hiccup y el OVP de cada IRM — que son justo lo que se va. Nadie declara su
relevo.

---

## 5. El cruce de las siete secciones que la v5 dice reabrir

| Sección v4 | Qué pasa de verdad |
|---|---|
| **§1** (D-F1) | Ya sustituida por **D-B2 = 0,5 A/riel**, firmada. No pide otra firma D-V |
| **§3** (D-F7) | `PS5` = IRM-45-5 **sí pierde sujeto**. Sus protecciones, aislamiento, rizado y arranque necesitan sucesor: no son propiedades genéricas de cualquier DC-DC |
| **§4.1** | Contiene el invariante firmado de masas y GNDD flotante. **«Seis fugas menos» no redefine ★, `J5`, GNDD ni la referencia del chasis** |
| **§4.2** | **D-F4 permanece como obligación.** D-F8/D-F9 conservan los pre-reguladores firmados |
| **§5** | **D-F5 se revoca expresamente.** **D-F6 sigue firmada** y pierde aquello de lo que dependía; la v5 no declara su relevo |
| **§6** | **D-F3 sigue compatible** (convección natural, sin ventilador). Cambian recinto y modelo; falta sustituto para el sostenido y la evacuación local |
| **§7** | **D-F2 sigue exigiendo `U13`/`U14` poblados.** La v5 dice `PS3`/`PS4`, pero la v4 asigna `U13` a +12/`PS3` y `U14` a +5/`PS5`, **no a −12/`PS4`** |

---

## 6. Qué falta para firmar

| | |
|---|---|
| **Hoy** | **D-V1** se puede firmar tal cual. No compromete ni los 24 V ni el reparto interior |
| **Una tarde** | **D-V2, D-V3 y D-V5**: escribir el contrato que les falta. D-V3 además necesita reescribir su finalidad contra D-F9 |
| **Trabajo de verdad** | **D-V4**: el censo de los trabajos que hacían los Mean Well, y quién hereda cada uno. Los dos bloqueantes del §3 son ese censo |

**Mientras D-V4 no esté firmada**, `calor_budget.py`, el venteo del #289, los
parámetros del case y el #334 se siguen calculando en la caja que se decidió
dejar el 05-09.
