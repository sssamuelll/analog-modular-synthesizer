# Fuente v4 — el listón de la PSU3, seis módulos encapsulados y la cascada intacta — firmada (v3, tras la junta y la firma)

**Fecha**: 2026-09-03 · **Estado**: **firmado — D-F1 a D-F7 decididas (§14); `calor_budget.py` corrió y la columna «sostenido» de §1 está rellena. Lo que queda es de otros papeles: el venteo mínimo (#289) y la bahía (#290)** ·
**Listón firmado**: 2026-09-03 («firmo el listón», Samuel) — como **corriente de placa**; y **re-firmado el mismo día como corriente sostenida** por `calor_budget.py` con D-F3 = A y D-F7: **2,0 / 2,0 / 4,0 A de rack y 4,2 A digital con 20 600 mm² de venteo nuevo**, el mínimo que el modelo despeja (corregido de 16 900 el mismo día: §6) ·
**Cierra**: nada todavía. **Entrega**: los rieles de #169 (§4.3) ·
**Mata por desaparición del sujeto** (cuando la v4 se adopte): #141, #280, #106, #56, #57 ·
**Reabre**: `design-notes` §13 y §18, la spec del chasis (§3.1, §3.2, §3.3), `clearance_budget.py::guarda_aire()`, `consumo_total_budget.py`, `power_budget.py`, `ground_budget.py`, el papel de la bahía

> **Lo que la junta cambió (Serrano, Halberg, Voronov, 03-09).** La v1 de este
> papel tenía tres errores que movían decisiones, y los tres estaban en hojas
> que ya estaban en el árbol: (1) las corrientes del listón son de placa, y las
> curvas de derating de la p. 3 de cada hoja las dejan a la mitad o menos dentro
> de un recinto cerrado a 45 °C de ambiente de diseño; (2) la corriente de red
> es la fila «AC CURRENT» de la hoja —**3,9 A rms** típicos con los seis a
> nominal—, no los 0,94 A que salían de dividir vatios entre voltios; (3) la
> masa es un solo nodo, y una regla sobre una rama no gobierna por dónde vuelve
> la corriente de un invitado. Además: la frecuencia de conmutación **sí está
> publicada** (65 kHz), el «LC de la v3» era un choke de red y no un filtro DC,
> el inrush de la IRM-30 son 45 A y no 4, y el rendimiento de la IRM-45 se lee
> sin ambigüedad. Todo eso está corregido abajo; lo que la junta no pudo cerrar
> es decisión de Samuel (§14).

> **Lo que Samuel firmó (03-09).** Las seis, en el orden en que se toman:
>
> | | Qué | Dónde vive |
> |---|---|---|
> | **D-F1** | el listón, **como corriente de placa**: 3,8 / 2,5 / 4,0 A de rack, 8,0 A digital, 650 mA de ultra | §1 |
> | **D-F3** | **A: ventilar** el recinto y el cajón por convección natural, **sin ventilador** | §6 |
> | **D-F2** | telemetría de rack **poblada**: `U13` y `U14` montados en R, no `DNP` | §7 |
> | **D-F4** | **secuenciador** por los pines ON/OFF, en la cascada y en el rack | §4.2, §4.3 |
> | **D-F5** | **Y2 de modo común** por módulo, del borne de ★ al chasis | §5 |
> | **D-F6** | **crowbar** en los rieles de rack, y solo ahí | §4.3 |
> | **D-F7** | `PS5` pasa de IRM-20-5 a **IRM-45-5**; el listón del +5 V de rack sigue en 4,0 A declarados | §3, §6 |
>
> Y una séptima que no es ninguna de esas seis: **cuando `calor_budget.py`
> corra con el recinto ventilado, el listón se vuelve a firmar en corriente
> sostenida**, que es la que el instrumento promete a quien le enchufa un
> módulo. La columna «sostenido» de §1 sigue vacía a propósito hasta entonces:
> se firma un número calculado y medido, no una intención.
>
> D-F4, D-F5 y D-F6 se firman **como consecuencia, no como mejora**. Los tres
> son modos de falla que la v3 no tenía porque tenía un solo transformador, y
> los tres se pagan en céntimos. Lo caro es no ponerlos: un riel crudo solo en
> cada encendido y cada microcorte (D-F4), el modo común de seis conmutadores
> volviendo por los hilos de la cascada (D-F5), y 16,2 V sobre una fila de
> módulos ajenos (D-F6).

---

## 0. Por qué existe este papel

La v3 está dibujada, ruteada y con DRC en cero, y **no se pide**. No porque le
falte una puerta: porque el listón cambió.

El 2026-09-03 salieron tres cosas a la vez, y las tres tienen número:

1. **El instrumento es digital y su +5 V ya está en rojo.** `power_budget.py`
   (módulo 2) importa un techo **derrateado** de **14,1 W a 52,3 °C** —2,82 A de
   la IRM-15-5, y 2,50 A de tope de arbitraje— y con cuatro N657 a máximo más
   el host USB las cargas duras solas son **2,895 A**. Con la cadena de LEDs al
   tope del #104 son **4,935 A**. Y eso sin la NPU, que no tiene cifra en
   DS14791.
2. **La fila de abajo es rack de verdad (#169) y no tiene corriente.**
   `consumo_total_budget.py` deja **160 mA por riel** para invitados. Un solo
   Disting EX come 229 mA en +12 V (expert-sleepers.co.uk, leído 2026-09-03).
3. **Samuel fijó el listón: «a la altura de la A-100PSU3 o superior».** La PSU3
   da +12 V/2000 mA, −12 V/1200 mA, +5 V/4000 mA (doepfer.de/a100_man/a100t_e.htm,
   leído 2026-09-03). La v3 da 650/650 en ±12 V —**exactamente lo que daba la
   primera fuente de Doepfer, la A-100NT12, retirada en el año 2000**— y ningún
   +5 V de rack.

La topología lineal de red de la v3 —toroide de 120 VA, puente, 9400 µF— no
puede crecer hasta ahí sin volverse un ladrillo de dos kilos, y el propio §18 de
la v1 midió que **el mayor emisor de zumbido de la caja es el mazo del
secundario del toroide** (~40 cm², ~29 µV inducidos). Este papel cambia la
entrada de red por módulos AC-DC encapsulados y **deja la cascada de regulación
como está**, porque es de la cascada de donde sale el 0,8 µVrms, no del toroide.

> **Sobre la regla «nunca con una v4» de la v3.** Se escribió para que lo
> indeciso saliera con huella y `DNP` en vez de con otra versión de papel. Este
> papel **no la reexpide**: sus huecos (§6, §12) no son huellas —son chapa,
> fusible, una placa entera— y una regla que no puede aplicarse a sí misma no
> gobierna. Lo que este papel se impone en su lugar es más duro y verificable:
> **nada de la v4 se manda a fabricar con un ítem de §12 abierto**, y eso lo
> hacen cumplir las puertas de §9, no una frase.

---

## 1. El listón (D-F1, FIRMADO 2026-09-03 como corriente de placa)

| Riel | A-100PSU3 | SAM17 v4, **de placa** (firmado) | **Sostenido** en el recinto | Masa |
|---|---|---|---|---|
| **±12 V ultra** — Voz, VCF, VCA, envolventes, bahía | no tiene | **650 mA/riel, 0,8 µVrms**, cascada intacta | 650 mA: los IRM de 15 V van al 24 % de carga | `GNDA` |
| **+12 V invitados** — fila de abajo, 104 HP | 2,0 A | **3,8 A** | **2,0 A** con el venteo mínimo (20 600 mm² nuevos, §6); es el riel que fija ese mínimo | rack |
| **−12 V invitados** | 1,2 A | **2,5 A** (3,8 de placa del módulo) | **2,0 A** | rack |
| **+5 V invitados** | 4,0 A | **4,0 A** declarados (8,0 de placa del módulo, D-F7) | **4,0 A**: la IRM-45-5 da 4,2 a esa temperatura y se declara 4,0 | rack |
| **+5 V digital** — N657 ×4, pantalla, LEDs, host USB | (dentro de los 4 A) | **8,0 A** | **4,2 A** = 21 W: **el techo nuevo que `power_budget.py` importa** (era 14,1 W) | `GNDD` |
| **1,8 V** de los N657 | — | del 3,3 V, aguas abajo del +5 V digital; **no se decide aquí** (§4.5) | | `GNDD` |

La columna «de placa» es lo que se compra. La columna «sostenido» es lo que el
instrumento **promete**, y la rellenó `calor_budget.py` el 03-09 con D-F3 = A
y D-F7: es la corriente en el **punto fijo** —la que el rack puede dar
calienta el cajón, y el calor recorta la que puede dar— con el **venteo
mínimo** que el modelo despeja, **20 600 mm² nuevos**; a esa abertura el aire
del recinto son 68,9 °C. Con más abertura, más corriente; con la caja de hoy,
cerrada, **cero**: a 86,7 °C se acabó la curva de la hoja y no opera ningún
módulo del rack. El modelo es pesimista a sabiendas (§6): hereda de
`guarda_aire()` que el cajón solo evacúa por chimenea. Lo que sí es cierto con cualquier venteo:

**El instrumento y los invitados no se prestan un miliamperio de suministro.**
El riel ultra sigue en 650 mA con su 30 % de margen (`consumo_total_budget.py`:
peor riel 340,2 mA → OK), y no reserva nada para la fila de abajo. Un módulo
ajeno con su conmutado no toca el riel de 0,8 µV, y la NPU del mago no deja sin
corriente a un delay de BBD. Lo que **sí** comparten es la masa: §4.1.

**Lo digital del instrumento no carga los ±12 V.** Carga el +5 V digital, y de
ahí baja a 3,3 y a 1,8. Por eso el riel que más crece contra la PSU3 es ese:
**8 A de placa contra 4**, y aun así la cadena de LEDs a blanco pleno (**9,60 A**,
`power_budget.py`) no cabe. El tope por firmware se queda.

---

## 2. Qué se va y qué se queda respecto de la v3

| | v3 | v4 | por qué |
|---|---|---|---|
| **Entrada de red** | toroide Talema 120 VA + `BR1` + 9400 µF | **seis módulos Mean Well IRM** (§3) | el listón; y el toroide era el emisor mayor (§0) |
| **Cascada ±12 V** | LM2941/LM2991 → LT3045 ×2 / LT3094 ×2 | **la misma**, más un secuenciador por sus pines ON/OFF (§4.2) | el 0,8 µVrms sale de ahí; el secuenciador es porque ahora los dos rieles crudos son dos fuentes |
| **Lo que ve la cascada** | VRAW ±20,54 V en vacío, ±15,70 V a 650 mA, rizado de 100 Hz | **±15 V DC ±2,5 % ±0,03 %/°C, rizado de 65 kHz ≤ 200 mVp-p** | §4.2 |
| **El valle de VRAW** | el número del que dependía todo | **no existe** | no hay rectificador |
| **`TR1` con fusible térmico** | condición de compra (#118) | **no hay `TR1`** | los 642 W de un corto del secundario ya no tienen dónde ocurrir |
| **Crowbar** | ninguno (#118) | ninguno en el ultra; **en los rieles de rack** (§4.3, D-F6 firmado) | #118 lo rechazó porque el fusible de red no abría; ahí el interruptor es el *hiccup* del IRM |
| **Fusible de red** | 1,6 A T en el IEC (#130) | en el IEC; **sube** (§5) | 3,9 A rms típicos a nominal, no 0,72 |
| **`NT1`, `L_F`** | 2 A; 0,2 A | **se redimensionan** (§5) | ídem |
| **Disipación** | tres TO-220 contra la pared | los mismos tres contra la pared, con la mitad de calor | entran a 15 V, no a 20 |
| **Chasis** | acero, cerrado, sin ventilación, para un toroide Ø93 × 46 | acero, sin toroide, **ventilado por convección natural, sin ventilador** (D-F3 = A) | §6 |
| **Telemetría** | 5 chips, mide el valle | 5 chips (+2 opcionales, §7), mide los ±15 V y el −12 V de rack | |
| **+5 V digital** | IRM-15-5 «montada fuera de esta placa» (spec v2 §7), 3 A | **IRM-45-5 en la placa de red, 8 A de placa** | #151 sigue abierto: §4.4 dice por qué |
| **Fila de abajo** | 160 mA/riel prestados | **rieles propios** por un bus board de invitados | #169 |
| **Placas** | una, 200 × 150 | **dos** + el bus board de invitados | §8 |

---

## 3. Los seis módulos, contra la hoja

Las cuatro hojas están en el árbol desde esta tanda:
`docs/reference/datasheets/meanwell-irm-{15,20,30,45}-spec-*.pdf` (15, 20 y 45 W
fechadas 2025-11-21; 30 W, 2026-04-03). Todo lo de abajo es de la tabla de
especificación (p. 2) y del diagrama de bloques y la curva de derating (p. 3),
salvo donde se marca.

| Ref. | Módulo | Riel | I placa | Rizado máx. (20 MHz) | Rend. | Inrush frío 230 V | I red típ. a nominal | L × W × H | Peso |
|---|---|---|---|---|---|---|---|---|---|
| `PS1` | IRM-20-15 | +15 V → `U1` | 1,4 A | 200 mVp-p | 84 % (†) | 40 A | 0,4 A | 52,4 × 27,2 × 24 | 50 g |
| `PS2` | IRM-20-15 | −15 V → `U2` (apilada, §4.2) | 1,4 A | 200 mVp-p | 84 % (†) | 40 A | 0,4 A | 52,4 × 27,2 × 24 | 50 g |
| `PS3` | IRM-45-12 | +12 V rack | 3,8 A | 150 mVp-p | 87,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |
| `PS4` | **IRM-45-12** | −12 V rack (apilada) | 3,8 A (2,5 declarados) | 150 mVp-p | 87,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |
| `PS5` | **IRM-45-5** (D-F7) | +5 V rack | 8,0 A (**4,0 declarados**) | **80 mVp-p** | 83,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |
| `PS6` | IRM-45-5 | +5 V digital | 8,0 A | **80 mVp-p** | 83,5 % | 60 A | 0,9 A | 87 × 52 × 29,5 | 195 g |

**`PS5` cambia de IRM-20-5 a IRM-45-5 (D-F7, firmada 2026-09-03).** Motivo:
`calor_budget.py` corrió por primera vez con la IRM-20-5 y el listón del +5 V
de rack **no existía con ningún venteo**: la IRM-20-5 son 20 W a 5 V = **4,0 A
de placa, exactamente la PSU3**, cero margen de derating, y su curva «3.3V,5V»
tiene el codo a **45 °C**, justo la sala de diseño. Con la IRM-45-5 —la misma
pieza que `PS6`, una referencia menos— el riel tiene 8 A de placa y codo a
50 °C; el listón declarado se queda en 4,0 A, y a esa carga la IRM-45-5
disipa **menos** que la IRM-20-5 a placa (3,95 W contra 5,32). Cuesta ~13 €
más y 87 × 52 en R en vez de 52 × 27. **Desde D-F7 el papel distingue dos
números que mezclaba: la placa del módulo (lo que puede dar) y el listón
declarado (lo que el instrumento promete); el sostenido es el menor de los
dos.** El −12 V ya venía así sin decirlo (3,8 A de placa, 2,5 declarados).

(†) La tabla de la IRM-20 da 84 % para 12 V y 15 V. La IRM-45 se lee sin
ambigüedad ya (la v1 de este papel la tenía cruzada): 5 V 83,5 %, 12 V 87,5 %,
15 V 88,5 %, 24 V 89,5 %, 48 V 90,5 %, monótono con la tensión como todo
flyback.

**`PS4` cambia de IRM-30-12 a IRM-45-12** respecto de la v1. Motivo: la IRM-30
entra en *hiccup* al **105 %** de su nominal (p. 2, OVERLOAD «105 ~ 160 %»), o
sea a 2,63 A contra 2,5 A declarados —menos que el arranque de un módulo
digital—; la IRM-45 al 115 %, y con 3,8 A de placa el −12 V de rack queda con
1,3 A de aire sobre lo declarado.

Lo que comparten los seis, de las mismas hojas:

- **Clase II sin pin de tierra** («no FG pin»), aislamiento I/P-O/P **4,2 kVac**.
  Las salidas son flotantes: por eso se pueden apilar (§4.2).
- **Frecuencia de conmutación: 65 kHz**, en el diagrama de bloques de la p. 3
  de las cuatro hojas («fosc : 65KHz»). El repo ya la usaba: `design-notes` v1
  §18.7 y el commit `fec315e`. La v1 de este papel la declaró HUECO por no
  haber leído la p. 3.
- **Curva de derating (p. 3), leída con los ojos el 03-09 (§12.1 hecho,
  `curvas.py`)**: **100 % hasta 50 °C**, **50 % a 70 °C**, y **no acaba ahí**:
  la IRM-45 sigue a 33 % a 80 °C y 25 % a 85; la IRM-20 a 20 % y 5 %. Por
  encima de 85 °C el módulo no opera. Las salidas de **5 V** de la IRM-20 y la
  IRM-30 quiebran a **45 °C** (y la IRM-20-5 está ya al 80 % a 50); **la
  IRM-45 dibuja una sola curva para toda la serie**, también para su 5 V. La
  lectura de la junta («hasta el 50 % a 70 °C», y «las de 5 V a 45 °C» sin
  distinguir familia) era incompleta en los dos sentidos, y es lo que hizo
  nacer D-F7 (§3, `PS5`). Es el número que gobierna §6.
- **EMI Clase B conducida y radiada «sin componentes adicionales»** — para el
  módulo solo; la nota 5 manda re-verificar el equipo final. Aquí son seis
  compartiendo NTC, MOV, choke y PE, con un riel de 0,8 µV al lado: §4.2.
- **Corriente de fuga < 0,25 mA a 277 Vac**, las cuatro hojas.
- **Protecciones**: corto en *hiccup* con recuperación automática; sobrecarga
  105–160 % (IRM-30), 115–160 % (IRM-20/45), 115–190 % (IRM-15); **OVP** que
  corta la salida y la clampa con zéner en **17,25–20,25 V** (modelos de 15 V),
  **12,6–16,2 V** (12 V), **5,25–6,75 V** (5 V).
- **Arranque**: setup **1000 ms típico, sin máximo** (rise 20 ms IRM-20, 30 ms
  IRM-30/45); **hold-up 40 ms** (IRM-20/30) y **50 ms** (IRM-45) a 230 V. Dos
  módulos apilados **no arrancan ni caen juntos por construcción**: §4.2 y §4.3.
- **Consumo sin carga** < 0,1 W (IRM-15/20) y < 0,15 W (IRM-45).
- **Refrigeración «por convección natural»**. Un módulo encapsulado a su
  máximo se calienta **+35 a +80 K sobre su aire** (junta, §6): la curva de
  derating es sobre el aire, y el aire dentro de un recinto cerrado no es el de
  la sala.

Los seis pesan **735 g** y ocupan **178 cm²** de huella; ninguno pasa de
29,5 mm de alto. El toroide de la v3 pesaba 1,20 kg y medía 46 + 4 de alto.

---

## 4. Arquitectura

### 4.1 La masa es un nodo, y el rack la comparte

La v1 de este papel decía «tres dominios de masa y un punto» y dibujaba una
estrella. La junta lo desmontó con una frase que ahora es **el invariante de
esta fuente**:

> **El potencial contra el que se mide la cadena de tono lo fija una sola
> corriente —la del instrumento— para cualquier patch y cualquier chasis.**

Dos subsistemas que se pasan señal asimétrica por un cable de 3,5 mm —cuya
malla es masa en las dos puntas— **son un solo dominio de masa**. Separar la
alimentación no separa la masa. Y la corriente de retorno de un invitado no
obedece a la regla que uno le escriba: vuelve por **todas** las ramas en
paralelo, repartida por impedancia:

| Rama | Qué es | Impedancia |
|---|---|---|
| (a) | el retorno del rack: bus board de invitados → cable → nodo ★ | 2,5 mm² × 300 mm + dos bornes: **~4,2 mΩ** (`ground_budget.py`: 1 mΩ por borne; con sus 10 mΩ por crimpado, 22 mΩ) |
| (b) | N cables de patch → jacks de la bahía → plano del instrumento → `J2` → ★ | ~120 mΩ por cable (dos jacks y un hilo fino), **÷ N** |
| (c) | panel del invitado → riel → anillo → espárrago | indefinida: «la conductividad de los raíles no está confirmada» (case README) |

Con diez patches, (b) son 12 mΩ contra 4,2 de (a): **1,4 A de un retorno de
5,3 A vuelven por el plano del instrumento**; con veinte, 2,2 A. Y aunque
volviera todo por (a), la fila entera queda **I × 4,2 mΩ** por encima de
`GNDA`: a 5,3 A netos (3,8 + 4,0 − 2,5) son **22 mV = 27 cents** de desfase en
cualquier CV que cruce de la fila al 1 V/oct del instrumento; a 1 A, 5 cents.
«Grueso y directo» no lo arregla: para 1 mV a 5,3 A haría falta 0,19 mΩ, que
es una pletina, no un cable.

**Lo que sí cumple el invariante, y es de construcción, no de regla:**

1. **La bahía es el único cruce de señal entre rack e instrumento** (E-4, #167:
   «el frente se unifica»). Si es así —y §12.9 lo verifica: **ningún módulo del
   instrumento expone un jack**—, entonces el problema tiene un solo sitio.
2. **En la bahía, los jacks viven en una isla de masa del rack.** Sus casquillos
   no tocan `GNDA`: tocan la masa del rack, que es la del panel, que es la del
   chasis. La corriente de un patch vuelve por donde vino —al bus board de
   invitados y a ★— y **no existe conductor de `GNDA` que un jack del rack
   pueda tocar**. La rama (b) desaparece, no se calcula.
3. **Cada señal que cruza la bahía hacia el instrumento se recibe en
   diferencial**: un amplificador de diferencia por entrada, que mide el jack
   **contra la masa del rack en ese jack** y lo re-referencia a `GNDA`. Los
   22 mV de desfase se restan en vez de sumarse. Es un amplificador por CV;
   para audio el desfase no importa y puede ir sin él.
4. **El chasis es la masa del rack.** Conduce corriente del rack —a amperios—
   y **nunca del instrumento**, salvo fuga y falta. La regla de la spec del
   chasis §3.2 («conduce calor, nunca corriente») **se reescribe**: era cierta
   para un instrumento cerrado y deja de serlo con un rack dentro. `GNDA` toca
   el chasis en **un** punto: el espárrago, por `J5`, como §13 de la v1.

Los puntos 2 y 3 son **requisitos que este papel entrega al papel de la bahía**
(§10), no mecanismos que diseña. Y el punto 1 es una condición: si aparece un
segundo cruce (un jack en un módulo del instrumento, una toma trasera de CV),
tiene que cumplir la misma isla y el mismo diferencial, o el invariante cae.

**Dónde está ★, y qué es.** Es un **nodo de cobre en la placa R** (§8), donde
aterrizan por pista corta los retornos de `PS1`–`PS5` y el retorno del rack, y
de donde sale `J5` al espárrago M4. §13.3 de la v1 se cumple tal cual: el
espárrago recibe dos anillos, el de PE y el de `J5`. La `GNDA` de la placa C
llega a ★ por **su propio par grueso** (§8), que lleva la corriente de C y
nada más; y **los segmentos del bus board del instrumento salen del nodo
`GNDREF` de C**, como hoy salen «del punto de estrella». Dos nodos de cobre y
un par entre ellos: la junta lo llamó «una barra», y tiene razón en el nombre
y no en la consecuencia. **El invariante es diferencial, no absoluto**: lo que
desafina es una corriente ajena en un conductor **entre dos módulos de la
cadena de tono**, no una caída común a todos ellos. Los dos crimpados del par
C→R están en el camino común de todo el instrumento, y su caída se resta sola.
Lo que no podía estar ahí —una corriente del rack— ya no está, por el punto 2.

**`GNDD` no está en ★.** El +5 V digital de `PS6` sale **flotante**, como salía
la IRM-15-5, y `GNDD` se une a `GNDA` donde el papel del cerebro lo decida, en
un punto. El bring-up de la v3 asevera > 1 MΩ entre `GNDA` y `GNDD` dentro de
la fuente (paso 6.2) y **sigue aseverándolo**: la v1 de este papel dibujó
`GNDD` en la estrella y contradecía esa puerta.

**La fuga de 50 Hz de cada módulo** sale por **el borne que toca ★**, no «por
el negativo»: en `PS2` y `PS4`, apiladas, el borne que toca ★ es el positivo.
Sale por ahí porque es el único camino de baja impedancia a PE; el otro borne
solo tiene condensadores hacia masa (≥ 300 Ω a 50 Hz para 10 µF). El
bring-up lo mide (§9.1). Y esa fuga —seis × < 0,25 mA más las Y2 del filtro,
**~1,4 mA**— es el no-problema: el límite de IEC 62368-1 para Clase I
enchufable está un orden de magnitud por encima (**cifra a leer en la norma**,
§12.5). El problema es lo que vuelve por esos mismos conductores a **65 kHz**:
§4.2.

### 4.2 El riel ultra: ±15 V DC a la misma cascada, con secuenciador

`PS1` y `PS2` se apilan: el negativo de `PS1` y el positivo de `PS2` van a ★
como `GNDA`; el positivo de `PS1` es +15 V y el negativo de `PS2` es −15 V.
Legítimo porque cada salida es flotante (§3).

**Margen de entrada de los pre-reguladores**, contra las hojas del árbol
(`lm2941-snvs770i-2015-01.pdf`, `lm2991-snvs099i-2016-10.pdf`; dropout **máximo
garantizado 1,0 V a 1 A** en los dos, v2 §1.1/§1.2):

```
+15 V  − 2,5 % (tolerancia, nota 3)                = 14,625 V
       − 0,03 %/°C × 50 K (tempco, 25 → 75 °C)     = 14,40 V
setpoint de U1 + dropout máx. a 1 A                = 13,1 + 1,0 = 14,1 V
margen a 1 A, antes del filtro                     = +0,30 V
−15 V: mismo cálculo contra −12,9 − 1,0 = −13,9    = +0,50 V
```

Menos la caída DC del filtro de §4.2 (`DCR × I`) y ±0,1 V de rizado. A 650 mA
el dropout es menor que a 1 A (Fig. 1 de cada hoja), así que el margen real es
mayor; **el número lo pone `margen_budget.py`** (§9), que sustituye a
`valle_budget.py` con un problema sin 100 Hz que integrar.

**El secuenciador (D-F4, FIRMADO 2026-09-03).** Con el toroide, ±VRAW subían y
caían juntos. Ahora son dos módulos con setup de 1000 ms **típico, sin
máximo**, hold-up de 40 ms cada uno, y *hiccup* independiente: en cada
encendido, cada apagado y cada microcorte hay una ventana de **un riel crudo
sin el otro**, de longitud indefinida. Un bus de ±12 V con un solo riel deja
el otro nodo donde lo pongan los clamps de los op-amps. La v3 no tenía este
caso porque no podía tenerlo.

Los dos pre-reguladores traen el pin para esto: **LM2941 `ON/OFF` activo-bajo**
(< 0,8 V habilita; p. 11 de su hoja) y **LM2991 `ON/OFF` activo-alto deshabilita**
(> 2,4 V; p. 9). Un detector de ventana sobre **los dos** rieles crudos —+15
por encima de 14,1 V **y** −15 por debajo de −13,9 V— habilita a `U1` y `U2`
**a la vez**, y los deshabilita a la vez en cuanto uno falta. La cascada sube
junta y cae junta, como con el toroide, y el *hiccup* de un módulo apaga los
dos rieles en vez de dejar uno vivo. Las piezas del detector se nombran en el
plan con hoja; el mecanismo es éste.

**Sobretensión.** Si `PS1` o `PS2` fallan a su OVP, clampan en **20,25 V** como
máximo: el LM2941/LM2991 admiten 26 V de entrada (hojas), y los LT3045/LT3094
no ven nada porque siguen entrando desde los pre-reguladores. `check_absmax.py`
**se reescribe** con ese sujeto (§9): hoy asevera contra un VRAW de 20,54 V que
ya no existe.

**El camino del rizado.** La v3 atenuaba **voltios a 100 Hz**; la v4 atenúa
**200 mVp-p a 65 kHz y sus flancos**. La junta hizo la cuenta que la v1 de este
papel prometía: para dejar ≤ 0,3 µVrms de 71 mVrms (200 mVp-p senoidal) a
65 kHz hacen falta **107 dB**. En serie:

1. **Un filtro LC nuevo a la salida de cada IRM** —la v3 **no tenía ninguno**;
   `fec315e` metió un choke de modo común de 10 mH en la **red de 230 V** hacia
   `J7`, que es otra pieza al otro lado de la barrera. Este LC se diseña en el
   plan: esquina ≤ fosc/10 (un 22 µH / 47 µF da 4,9 kHz y ~45 dB ideales a
   65 kHz), **amortiguado** —un LC sin amortiguar delante de la impedancia de
   entrada negativa de un regulador lineal es el problema de Middlebrook, y
   la v1 de este papel no lo nombraba—, y con su `DCR` en `margen_budget.py`.
2. **El PSRR del pre-regulador**: garantizado solo a 120 Hz (tabla eléctrica);
   a 65 kHz, la curva típica «Ripple Rejection» (Fig. 9 del LM2941, Fig. 8 del
   LM2991): **decenas de dB típicos, cero garantizados**.
3. **El PSRR del LT3045/LT3094** (`lt3045-rev-d.pdf`, `lt3094-rev-b.pdf`, en el
   árbol desde esta tanda): **76 dB / 74 dB a 1 MHz** en portada, y más a
   65 kHz en la curva —**condicionada al headroom**, que aquí es 1,1 V nominal
   (13,1 − 12,0) y no puede bajar (v2 §1.5.1).

Suma típica: **150–170 dB contra 107**. Para el fundamental sobra en papel.
**Lo que no sobra son los flancos**: los 200 mVp-p están medidos a 20 MHz de
ancho de banda, y son sobre todo picos de 1–20 MHz, donde el LC vive por
encima de su resonancia propia, el pre-regulador da ≈ 0 dB y el LT3045 baja de
76 dB. Veinte milivoltios de pico ahí con 60–80 dB totales son **2–20 µV de RF
en el riel**. Y eso queda **fuera** de la banda de 10 Hz–100 kHz de los
0,8 µVrms: **el LNA de #58 puede dar verde con RF entrando a cada op-amp**.

De ahí tres cosas que la v1 no tenía:

- **Ferrita + cerámico en la entrada de cada regulador** para los flancos (el
  LC cuida los 65 kHz; la ferrita, los MHz). Piezas en el plan.
- **El enlace R → C va trenzado y con choke de modo común**: es un lazo de
  cuatro hilos que lleva 200 mVp-p de conmutación hasta `U1`/`U2`, o sea **el
  mismo mazo que §18.3 midió como emisor mayor**, a una frecuencia donde
  dI/dt es peor.
- **El modo común no lo rechaza ningún PSRR** (`design-notes` v1 §18.7: «el
  PSRR no lo rechaza… llega como una corriente que circula por la masa»). La
  corriente de modo común de seis conmutadores a 65 kHz vuelve por ★ y por el
  propio espárrago, y **una estrella es un concepto de DC y 50 Hz: a 65 kHz el
  retorno lo fija la inductancia**. El mecanismo (D-F5, FIRMADO
  2026-09-03): **un condensador Y2 del borne de ★ de cada módulo al chasis, junto al módulo**,
  para que el lazo de modo común se cierre en centímetros (módulo → Y2 →
  chasis → PE → primario) y no por los hilos de ★. No es un puente de masa:
  a 50 Hz son cientos de kΩ. Mean Well lo documenta en «EMI testing of
  component power supplies» (§12.4, hoja por leer).

Nada de esto se presume. La v2 escribió que el 0,8 µVrms «no se presume hasta
medir con el LNA»; la v4 añade que **el LNA no basta**: hace falta mirar el
riel con 20 MHz de ancho de banda (§9.1).

### 4.3 Los rieles de rack

`PS3` (+12 V) y `PS4` (−12 V) apiladas como en §4.2; `PS5` (+5 V) referida al
mismo retorno. Los tres con su LC, y por un conector dimensionado (§8) hacia
**el bus board de invitados** (#169), que es una placa nueva y **no** el bus
board del instrumento: aquél tiene el +5 V «NC a propósito» y **PTC de 0,25 A
por riel y slot**, y un solo Disting EX (229 mA) lo dispararía.

Por qué 3,8 A de placa y no los 2 A de la PSU3, con la fila medida en HP:

| Fila de 104 HP hecha de… | mA/HP en +12 V | Total |
|---|---|---|
| filtros Doepfer (A-101-1: 30 mA / 16 HP) | 1,9 | ~200 mA |
| Clouds (120 mA / 18 HP) | 6,7 | ~690 mA |
| Morphagene (165 mA / 20 HP) | 8,3 | ~860 mA |
| **Disting EX (229 mA / 8 HP)** | 28,6 | **~3,0 A** |

Una fila entera de Disting EX es absurda, y cabe **en placa**. Cuánto cabe
**sostenido** lo dice §6, y ésa es la decisión.

Tres mecanismos que la v1 no tenía, todos por la misma causa —dos fuentes
independientes y un bus ajeno sin límite de falta—:

- **Secuenciador de ±12 V de rack**, mismo detector de ventana que §4.2, sobre
  interruptores de carga en +12 y −12: **los dos o ninguno**. Sin él, un
  *hiccup* de `PS4` deja la fila con +12 V fijo y −12 V ciclando a ~1 Hz.
- **Crowbar en los rieles de rack (D-F6, FIRMADO 2026-09-03).** Si `PS3` falla a su OVP
  clampa hasta **16,2 V** sobre una fila de módulos ajenos con máximos
  absolutos desconocidos. #118 rechazó el crowbar del ultra porque el fusible
  de red de un toroide no abría a tiempo; aquí el interruptor es el propio
  módulo: un SCR a ~14 V pone el riel en corto y el IRM entra en *hiccup* en
  microsegundos. El lazo que en #118 no cerraba, aquí cierra.
- **Corriente de falta por slot: requisito a #169.** Una IRM-45-12 entrega
  **4,4–6,1 A** antes de entrar en *hiccup* (115–160 % × 45 W / 12 V). Un cable
  Eurorack invertido —el fallo habitual— en un slot ve eso, y su cinta no lo
  aguanta. El bus board de invitados **lleva PTC por slot y riel**, de *hold*
  ≥ 2× el módulo más glotón del censo (≥ 0,5 A para 229 mA, ESTIMADO); el
  valor exacto y el sitio son del papel de #169, con su censo. El bus del
  instrumento protege por slot; el de invitados no puede proteger menos.

### 4.4 El +5 V digital: 8 A de placa, y qué cabe

`PS6` (IRM-45-5) sustituye a la IRM-15-5 y **es el riel de menor rizado de la
familia** (80 mVp-p). Sale **flotante** hacia el módulo 2, como hoy.

Contra `power_budget.py`, corrido el 2026-09-03:

| Escenario | Duras | Cadena | Total | Contra 8 A de placa |
|---|---|---|---|---|
| Typ, 4 N657, host USB a tope | 0,965 A | 2,04 A | 3,005 A | sobran 5,0 A |
| Max TJ = 125 °C, 4 N657, host a tope | 2,895 A | 2,04 A | 4,935 A | sobran 3,1 A |
| Blanco pleno de la cadena | — | 9,60 A | — | **no cabe** |

Tres cosas que la junta corrigió:

1. **El techo que `power_budget.py` importa no es de placa: es sostenido a la
   temperatura del recinto.** Hoy son 14,1 W a 52,3 °C. La enmienda (§10) no es
   «8 A menos margen»: es **la corriente sostenida de `PS6` que dé
   `calor_budget.py`** (§6). Con el recinto cerrado y el listón a máximo, la
   junta la estima en **2,33 A**: por debajo de las 2,895 A de cargas duras.
   **#151 sigue abierto**, y ahora se sabe quién responde por su techo: este
   papel, con ese guion.
2. **8 A no pasan por un KK-254** (4 A por contacto) ni por 22 AWG: 20–40 cm de
   ida y vuelta más cuatro contactos son 41–62 mΩ, **0,33–0,50 V** de caída, y
   el módulo 2 recibe 4,4–4,5 V partiendo de 4,875 (−2,5 %). **El host USB
   exige ≥ 4,75 V en el puerto** y el IRM no tiene *sense* remoto. Conector y
   cable dimensionados en §8, y **requisito al módulo 2**: el VBUS del host se
   regula allí, no se fía de la fuente.
3. **Dos medidas del mismo riel no miden lo mismo.** La v1 ponía un INA226 en
   `GNDD` a la salida de `PS6` para «contrastarlo» con el sensor S9.1 del
   cerebro; S9.1 mide **la cadena**, el INA mediría **el riel entero**, y una
   puerta que exige que coincidan falla siempre o se arregla. **Fuera**: el
   cerebro mide su cadena; la fuente entrega el riel y responde por su techo.

**El HUECO #256 deja de bloquear el dimensionado** (se compra para el máximo
a 125 °C: 761 mA/chip) y **pasa a bloquear el calor** de §4.5.

### 4.5 El 1,8 V: no se decide aquí, pero su calor sí se declara

`alimentacion-n657-design.md` §3.2 propone el 1,8 V como **LDO desde el 3,3 V**
y calcula su calor con el típico: (3,3 − 1,8) × 0,413 = **620 mW**. Con el
listón se dimensiona a máximo, y a máximo son 4 × 761,4 mA = 3,046 A:

```
(3,3 − 1,8) × 3,046 = 4,57 W
```

Siete veces más, y **más que todo lo que disipa la cascada a 650 mA**. Eso
puede voltear D-R1 hacia un buck contenido, y **es decisión de aquel papel**.
Este papel carga con las dos cifras en §6 y no elige. Dónde vive físicamente
ese regulador tampoco es de aquí.

---

## 5. La red

Lo que entra por la pared es lo de #130: **IEC C14 Schurter `KM00.1105.11`** con
portafusible cerrado, y tras él, en la placa R, la cadena de la v3 —`RV1` MOV
S20K275, `NT1` NTC, `L_F` choke de modo común con sus Y2— alimentando a los seis
módulos en paralelo. **Las tres piezas se redimensionan**, porque el número que
las gobierna cambió de orden de magnitud:

**La corriente de red es la fila «AC CURRENT (Typ.)» de la hoja, no vatios
entre voltios.** Un flyback con rectificador y condensador tiene factor de
potencia **0,25–0,30**; la fila lo lleva dentro: 0,4 A (IRM-20), 0,5 A (IRM-30),
0,9 A (IRM-45), a 230 V y carga nominal. Con los seis de §3:

```
0,4 + 0,4 + 0,9 + 0,9 + 0,4 + 0,9  =  3,9 A rms      a placa, los seis a nominal
escalado a la carga del listón      ≈  2,7–3,0 A rms  (junta: 2,73 A)
caso típico (§6, ~30 W de entrada)  ≈  0,5 A rms
```

La v1 de este papel decía 0,94 A y «1,7× de margen» para el 1,6 A T. **Es al
revés**: a la carga del listón son **1,7 × In**, y IEC 60127-2 hoja III solo
obliga a un T a abrir por debajo de 30 min a 2,1 In. El 1,6 A T de la v2 se
dimensionó para un toroide de 0,72 A y una IRM: **se va**.

- **Fusible**: clase T, valor de `fusible_budget.py` (§9) con dos términos: el
  permanente de arriba, y el **I²t de rearranque en caliente**, que es el que
  manda y la v1 no tenía. En frío `NT1` limita: seis bancos de entrada (unos
  205 µF ESTIMADO por el hold-up, 10,9 J) a 5 Ω dan ~50 A de pico, τ 1,3 ms,
  **1,66 A²s** —el inrush de placa (285 A sumados) no se ve nunca—. Pero un
  microcorte con `NT1` caliente (~0,5 Ω) da **~159 A y 5,3 A²s**, el 18–53 % del
  I²t de fusión de un 1,6 A T (v2 §3.0.1): fatiga con cada microcorte.
  Hipótesis de trabajo, **ESTIMADO**: 4 A T, cuyo I²t escala con In² y deja el
  rearranque por debajo del 10 %. Lo confirma el guion con la hoja del fusible.
- **`NT1`**: el SL10 5R002 está a 2 A de régimen y aquí son 2,7–3,9. Pasa a la
  talla de **≥ 4 A** de la misma familia (Ametherm SL22, hoja por leer, §12.6),
  y con dos números que hoy no están en ningún papel: **la energía que absorbe
  en cada arranque frío (~8,3 J)** y **la capacidad máxima que admite a 230 V**
  contra esos 205 µF.
- **`L_F`**: el choke de `fec315e` estaba dimensionado «230 V a 0,2 A» para una
  IRM. Pasa a **≥ 4 A**. Su función cambia: ya no hay capacidad entre devanados
  de un toroide que filtrar; es el filtro de conducida de seis módulos, y la
  nota 5 de sus hojas dice que el equipo final tiene que medirlo.
- **Los carriles de 230 V de la v3** (`rutear_red`, 0,72 A) se recalculan para
  3,9 A en `build_pcb.py` de R.

**Crowbar: ninguno en el ultra**, como en #118 y por una razón más: cada IRM
lleva OVP propio. **Uno en cada riel de rack** (§4.3, D-F6).

**`TR1` con fusible térmico: ya no existe la pieza.** Los IRM llevan protección
de corto en *hiccup* y encapsulado UL 94V-0.

**La fuga a PE** (§4.1): ~1,4 mA contra el límite de la norma, `fuga_budget.py`.

---

## 6. Térmica: el listón se compró en un eje que el recinto no tiene

La PSU3 entrega 2 A **en un case abierto, al aire de la sala**. La v4 entrega
3,8 A **en la hoja**, y en un recinto de acero cerrado entrega lo que la curva
de derating diga al aire que haya dentro. Una corriente sostenible no es
propiedad de un módulo: lo es de la terna (módulo, recinto, ambiente). **La v1
de este papel midió «superior» en el eje equivocado**, y la junta lo enseñó con
la cadena entera:

```
sala de diseño                 45 °C     (spec del chasis §3.1: «la habitación para la
                                          que se dimensionó todo lo demás»; NO 25)
+ aire del cajón               +X K      (clearance_budget.py::guarda_aire(): techo de
                                          15 K de subida, hoy con 9,22 W de la fuente)
+ aire del recinto             +Y K      (spec del chasis §3.1: 0,1453 m² × 9 W/m²K)
+ el propio módulo             +35..80 K sobre su aire, a su máximo (junta)
→ curva de derating (p. 3)     100 % hasta 50 °C; −2,5 %/°C hasta el 50 % a 70 °C
```

Las fuentes de calor, con los rendimientos ya corregidos de §3:

| | Típico (instrumento a censo, digital a 3,0 A, rack vacío) | Máximo (todo a placa a la vez) |
|---|---|---|
| `PS1` + `PS2` | (15 × 0,340 + 15 × 0,327) × (1/0,84 − 1) = 1,91 W | 19,5 × 0,19 = 3,71 W |
| `PS6` | 5 × 3,005 × (1/0,835 − 1) = 2,97 W | 24,7 × 0,198 = 4,88 W |
| `PS3` | < 0,15 W | 45,6 × (1/0,875 − 1) = 6,51 W |
| `PS4` | < 0,15 W | 30 × 0,143 = 4,29 W |
| `PS5` (IRM-45-5 desde D-F7, a los 4,0 A declarados) | < 0,1 W | 20 × (1/0,835 − 1) = **3,95 W** (era 5,32 con la IRM-20-5) |
| `U1`, `U2` a 15 V de entrada | 0,65 + 0,69 W | 1,24 + 1,37 W |
| LT ×4 + `U3` | 0,35 + 0,30 W | 1,30 + 0,30 W |
| **Total en el recinto** | **7,2 W** | **27,5 W** (28,9 con la IRM-20-5 en `PS5`, antes de D-F7) |
| + el 1,8 V si vive dentro | +0,62 W | +4,57 W |

Y **fuera del recinto pero dentro del cajón**, lo que el listón permite y
`guarda_aire()` no tiene: la fila de invitados a placa disipa **95,6 W** y el
digital **24,7 W**. El case se cerró (techo macizo, trasera capturada) con 9 W
de fuente en su presupuesto de aire.

**Lo que da el lazo** (junta, sobre el modelo del case y del recinto de hoy;
`calor_budget.py` lo hace suyo en §9):

| Situación | Aire del recinto | Rack sostenido (+12 / −12 / +5) | `PS6` sostenido |
|---|---|---|---|
| Recinto cerrado, solo la fuente en el cajón | ~64 °C | **1,97 / 1,29 / 2,07 A** (52 % del listón) | — |
| Recinto cerrado, con los 120 W de fila y digital en el cajón | ~78 °C | **0,63 / 0,42 / 0,67 A** (17 %) | **2,33 A** < 2,895 A de cargas duras |
| Al 49 °C que la v1 de este papel escribía (con sala a 25) | 49 °C | `PS5` ya en 3,6 A | — |

Las dos primeras filas son **por debajo de la PSU3**. La segunda es por debajo
de la v3.

**Lo que da `calor_budget.py`** (03-09, con las curvas leídas con los ojos,
D-F3 = A y D-F7; **punto fijo**, no carga a placa):

| Situación | Aire del recinto | Rack sostenido (+12 / −12 / +5) | Digital sostenido |
|---|---|---|---|
| Caja de hoy (cerrada), todo lo que el rack pueda dar | **86,7 °C** | **0 / 0 / 0 A** — no hay punto de trabajo | 0 A |
| **Venteo mínimo: 20 600 mm² nuevos** (D-F3 = A) | **68,9 °C** | **2,0 / 2,0 / 4,0 A** — el +12 fija el mínimo | **4,2 A** |
| A placa sin derating, caja de hoy (no es un estado alcanzable) | 145,7 °C | — | — |

Con la IRM-20-5 en `PS5` la segunda fila **no existía**: ningún venteo daba
4,0 A en el +5 V, y de ahí D-F7. Dos cosas del modelo que hay que decir: la
constante que más mueve el sostenido es **`CD_TIRO`** (el coeficiente de
descarga del venteo, supuesto y no medido), y el modelo **hereda de
`guarda_aire()` que el cajón solo evacúa por chimenea** —ignora la convección
de las paredes exteriores—, así que los 20 600 mm² son **pesimistas**.

**Y NO SON EL ENCARGO (Tarea 4, 03-09).** Al meter los 147,83 W en
`guarda_aire()` —27,53 del recinto + 120,3 de fila y digital— salió que el
listón del rack y el criterio del propio case piden cosas distintas, y manda
el segundo:

| Quién pregunta | Qué exige | Venteo efectivo nuevo |
|---|---|---|
| `calor_budget.py` | que los rieles den el listón con la sala a 45 °C | **20 525 mm²** |
| `guarda_aire()` | los **15 K sobre ambiente** de vida del electrolítico | **35 365 mm²** |

Con los 20 525 el case sube **20,7 K**: los rieles llegan y el condensador no.
El encargo a #289 es el **35 365**, y con dos cifras que lo acotan: la pared
exterior (0,507 m² de envolvente sin el suelo) se lleva otros **22,8 W** a ese
techo con `U = 3 W/m²K` supuesto —más que los 12,6 de la chimenea de hoy—, y
contándola bajan a **29 395**; con `C_D = 0,55` suben a **42 394**. Y el
**tiro** es la variable barata: `k` va con la **raíz** de la altura y hoy son
105 mm en un case de 256, así que subir la salida vale más que ensanchar la
rejilla. `guarda_aire()` ya no asevera ese techo —lo publica como HUECO— y se
pone verde sola el día que el papel del case dibuje el venteo.

**Esto no era un hueco: era la decisión (D-F3), y Samuel la tomó el 03-09.**
El listón se firmó como corriente de placa; sostenido, dentro de un recinto
cerrado y este cajón, **no existía**. De los tres caminos se firmó el **A:
ventilar el recinto y el cajón por convección natural, sin ventilador**.

| | A. Ventilar | B. Cerrado y honesto | C. Forzado |
|---|---|---|---|
| **Qué** | el recinto **y el cajón** ganan convección natural: entrada baja, chimenea alta, rejilla; sin ventilador | el recinto sigue cerrado; el listón sostenido es el que dé `calor_budget.py` | ventilador en el recinto |
| **Rack sostenido** | lo que la curva dé al aire de la sala + un salto pequeño: **cerca de placa** | ~1,3–2 A: **nivel PSU2** | cerca de placa |
| **Precio** | revierte la decisión del 18-08 (cerrado); polvo; el papel del case rediseña techo y trasera con un presupuesto de aire nuevo | «superior a la PSU3» se queda en la caja, no en el rack | ruido en un instrumento; un motor que falla |
| **Quién** | el papel del case, con `guarda_aire()` reescrito | este papel, con la columna «sostenido» de §1 rellena | — |

**FIRMADO: A** (Samuel, 2026-09-03). El listón era el punto: un rack que el
calor recorta al 17 % no es «a la altura de la PSU3 o superior», es una cifra
de catálogo. El cerrado se decidió el 18-08 con **9 W** de fuente dentro, y
hoy son **29 W** en el recinto más **120 W** de fila y digital en el cajón: la
decisión vieja se tomó sobre un número que ya no existe. Ni la PSU3 vive en
una caja cerrada.

**Por qué no B ni C.** **B** (cerrado y honesto) deja el listón firmado
significando nivel PSU2 en el rack, que es la mitad de lo que este papel
existe para comprar. **C** (forzado) mete un motor —ruido, y una pieza que
falla— dentro de un instrumento que hasta hoy es silencioso por construcción;
es un precio peor que el de abrir rejillas. Lo que **A** cuesta y se paga: el
papel del case rediseña techo y trasera con un presupuesto de aire nuevo, y
entra polvo. Esos dos se pagan una vez; un rack recortado se paga cada vez que
se enchufa un módulo.

**Lo que ventila y lo que no.** Respiran la zona de los módulos, la cascada y
el cajón. **La franja de 230 V no**: su barrera de 6 mm y su tapa siguen
cerradas, y ninguna abertura puede dar acceso con el dedo de prueba a nada de
la franja de red — es aserción de `check_red_chasis.py` (§9), no una nota. **Con A firmado, además, hay que mirar si los
módulos se montan con la cara contra la pared de acero**: son bloques encapsulados y la
hoja solo habla de convección; conducir por el encapsulado a la chapa es lo
que hoy hacen los TO-220 y podría valer para ellos (§12.7, pregunta a Mean
Well o medida).

Los tres TO-220 **siguen contra la pared** en cualquier camino.

---

## 7. La telemetría

Los cinco chips de la v3 se quedan y **cambian de pregunta**:

| Chip | v3 | v4 |
|---|---|---|
| `U8` INA226 0x40 | +12 V ultra, V e I | igual |
| `U9` INA226 0x41 | +5 V de `U3`, V e I | igual |
| `U10` ADS1115 0x49 | −12 V, VRAW+, VRAW− (V) | −12 V, **+15 V, −15 V**, y el cuarto canal, libre hasta hoy, a **−12 V de rack** |
| `U11` TMP1075 0x48 | aire del recinto | igual, y ahora **es el que vigila la curva de derating** |
| `U12` ISO1541 | barrera GNDA/GNDD | igual |

Los divisores son los de la spec del chasis §4.4: 100 k / 20 k al 0,1 %, 1/6, y
**los canales negativos referidos al +5 V**, no a masa —el ADS1115 tiene
máximo absoluto de −0,3 V en el pin—: −15 V da 5 × 5/6 − 15/6 = **1,67 V**;
+15 V con su divisor a masa, **2,5 V**. El −12 V de rack necesita **su
divisor y su clamp** (hoy AIN3 está «atado a GNDA»); van en el plan. Lo que
muere es la frase «mide por primera vez el valle de VRAW». Lo que nace es
**medir los ±15 V con carga**, que es donde se ve un IRM saliéndose de su
curva.

**D-F2 (FIRMADO 2026-09-03): dos INA226 en los rieles de rack, poblados.** `U13` en
+12 V y `U14` en +5 V de rack, 0x44 y 0x45 (`check_telemetria.py` vigila las
colisiones), **en la placa R**, donde están los shunts. Dan lo que ningún case
Eurorack da: el instrumento le dice al dueño cuánto come su rack. **Cuestan
cuatro hilos más en el enlace R ↔ C** (SDA, SCL y la alimentación de 5 V del
lado `GNDA` de la telemetría, §8), y ese enlace ya los lleva.

Lo que compran no es un adorno. Junto con `U11` (TMP1075), la corriente de
rack es lo que convierte la curva de derating de §6 en algo que el instrumento
**vigila en marcha**: el firmware puede avisar cuando el rack se acerca a su
techo sostenido a la temperatura que hay dentro, en vez de que el dueño lo
descubra por un módulo que se reinicia. Es la contrapartida en telemetría de
haber firmado el listón en corriente sostenida.

**El +5 V digital no se mide en la fuente** (§4.4). Sale flotante; lo mide
quien lo reparte.

---

## 8. Las placas y los conectores

**Dos placas más el bus board de invitados.** La v1 de este papel lo
justificaba con los «≥ 80 mm» de `revisar_diagonal()`; la junta señaló que ese
número se derivó para un lazo rectificador de 6,81 cm² a 100 Hz, y transplantarlo
a seis conmutadores encapsulados de 65 kHz es conservar la cifra y cambiar la
física. Las razones que quedan son otras, y son mejores:

1. **R se prueba sola.** Con cargas ficticias, antes de conectarle un solo
   nodo sensible (§9.1, paso 1). La v3 no podía: su entrada de red y su
   cascada eran la misma placa.
2. **El campo de un IRM encapsulado no lo publica nadie.** Con dos placas, la
   distancia a la isla ultra **se fija al montar y se mide con el LNA**, en vez
   de fijarse en un layout que ya no se puede mover. `params.scad` declara
   dónde va cada placa, y **la puerta del chasis mide la distancia entre las
   dos**; `revisar_diagonal()` en C **se retira** —no hay lazo rectificador que
   medir— y en su lugar C lleva un *keep-out* declarado alrededor de su
   conector de entrada.
3. **C es la v3 menos la red**, y sus puertas valen con cambios de nombre.

| Placa | Lleva | Hereda de |
|---|---|---|
| **R — red** | IEC en la pared, `RV1`, `NT1`, `L_F` + Y2 redimensionados, la franja de 230 V con su barrera, **`PS1`–`PS6`**, seis LC amortiguados, los Y2 de modo común (D-F5), el detector de ventana ×2 y los interruptores de rack, el crowbar de rack (D-F6), `U13`/`U14` (D-F2), el nodo ★ y `J5`; salidas: ±15 V a C, ±12/+5 al bus board de invitados, +5 V digital al módulo 2 | la franja de red de la v3 (`rutear_red`, `NETS_RED`, barrera de 6 mm), recalculada a 3,9 A |
| **C — cascada** | `U1`/`U2` con su ON/OFF cableado al detector, en fila contra la pared; la isla LT3045/LT3094 con `GNDREF`; ferritas de entrada; `U3`; la isla de telemetría; `J2`, `J6`, `J8`; entrada: ±15 V | **la v3 entera menos `TR1`, `BR1`, `C_bulk` y la franja de red** |
| **Bus board de invitados** | #169: peines, PTC por slot, su sitio | el bus board del instrumento, con otro presupuesto de PTC |

**Los conectores los dimensiona la corriente, y de paso se protegen por
geometría** (la doctrina de la spec del chasis §4.3: dos cables que no deben
cruzarse no caben en el mismo conector):

| Enlace | Corriente | Hilos | Familia (a nombrar en el plan con hoja) |
|---|---|---|---|
| R → C, ±15 V | 1,4 A | +15, −15, `GNDA` ×2, **trenzados**; +4 por D-F2 (SDA, SCL, +5 V tele, retorno) | KK-396 o similar: distinto de los KK-254 de C |
| R → bus board de invitados | 3,8 / 3,8 / 4,0 A | +12, −12, +5, retorno ×2, en 2,5 mm² | Mini-Fit Jr o bornera; **no** KK-254 (4 A por contacto) |
| R → módulo 2, +5 V digital | 8,0 A | +5, `GNDD`, en ≥ 16 AWG y corto | Mini-Fit Jr con dos contactos por polo; **no** el KK-254 de `J6` |
| C → módulo 2, `J6` +5 V de `U3` | 30 mA | como hoy | KK-254, como hoy |

Los dos 5 V que llegan al módulo 2 van en **familias distintas** por necesidad
de corriente, y con eso la protección geométrica que la v1 de este papel
abandonaba sin decirlo vuelve sola.

**Tamaños**: los seis IRM ocupan 209 cm² (178 antes de D-F7: la IRM-45-5 de `PS5` son 45 cm² donde la IRM-20-5 eran 14); R con su franja de red, sus filtros y
sus interruptores anda por **200 × 150 (ESTIMADO)**; C, sin rectificador ni
toroide, **por debajo de 200 × 100 (ESTIMADO)**. Los ponen los `build_pcb.py`.

**El chasis** pierde el toroide (Ø93 × 46 en `chasis_toroide_x = 273,5`) y gana
una placa; y con D-F3 = A gana aberturas. Todo eso es del papel del case (§10).
Lo que este papel le exige: **las dos placas dentro del mismo recinto de
acero**, porque R lleva 230 V y C lleva los tres tabs contra la pared.

---

## 9. Las puertas

Principio II: un presupuesto es un guion con aserciones. Éstas son las de la
v4, y **cada una nace con la entrada que la junta dijo que le faltaba** —sin
eso nacen verdes por vacías (Principio VIII)—:

| Puerta | Estado | Qué pregunta, y con qué entrada |
|---|---|---|
| `check_absmax.py` | **se reescribe** | el sujeto ya no es VRAW = 20,54 V: es el **OVP máximo de `PS1`/`PS2` (20,25 V)** contra los 26 V de `U1`/`U2`, y el **OVP de `PS3`/`PS4` (16,2 V)** contra lo que el crowbar de rack deje pasar |
| `check_telemetria.py` | hereda, crece | direcciones, divisores (el nuevo de AIN3), shunts; `U13`/`U14` de D-F2 |
| `kicad/check_bom.py`, `check_netlist.py`, `check_pcb.py`, `check_fab.py`, `check_huellas.py` | **una por placa** | R y C; `check_huellas.py` estrena **seis huellas IRM de la p. 3** (§12.3); `check_netlist.py` de R asevera que **ningún retorno de IRM comparte pista** hasta ★ y que **`GNDD` no toca ★** |
| `check_netlist.py` de la bahía | **requisito** (§10) | **ningún casquillo de jack está en `GNDA`** |
| `check_red_chasis.py` | hereda, crece | IEC con su recorte (#130), un fusible, y `NT1`/`L_F` con rating ≥ la fila «AC CURRENT» sumada |
| `check_bringup.py` | **se reescribe** | §9.1 |
| `valle_budget.py` | **muere** | no hay valle |
| `margen_budget.py` | **nuevo** | tolerancia + tempco + rizado + `DCR` del LC contra el dropout de `U1`/`U2` a la corriente real |
| `fusible_budget.py` | **nuevo** | permanente con la fila «AC CURRENT»; I²t frío con `NT1` y **rearranque caliente**; contra el I²t de la hoja del fusible |
| `fuga_budget.py` | **nuevo** | seis fugas + Y2 contra la cifra de la norma |
| `calor_budget.py` | **nuevo** | **la cadena entera de §6**: sala 45 → `guarda_aire()` del case con los 120 W de fila y digital → recinto → módulo; curva de derating leída; devuelve **la columna «sostenido» de §1** |
| `rizado_budget.py` | **nuevo** | LC amortiguado × PSRR(`U1`) × PSRR(LT) a 65 kHz **y a 1–20 MHz**, contra la cota de ruido; y **declara que el modo común no lo cubre** |
| `secuencia_budget.py` | **nuevo** | umbrales del detector de ventana contra tolerancia + tempco de los IRM y el dropout de `U1`/`U2`; y que ningún estado deja un riel solo |
| `consumo_total_budget.py` (módulo 3) | **enmienda** | `RESERVA_INVITADOS` desaparece; el 650 con 30 % es del instrumento |
| `invitados_budget.py` | **nuevo** | placa vs. declarado vs. **sostenido** (de `calor_budget.py`) vs. censo de §4.3 |
| `power_budget.py` (módulo 2) | **enmienda** | `TECHO_W_PESIMISTA` = **sostenido de `PS6`**, de `calor_budget.py` |
| `ground_budget.py` (bus board) | **enmienda** | el desfase rack ↔ instrumento **I × R_retorno** con N patches como parámetro; y la aserción de que ese término **no entra** en la cadena de tono porque la bahía lo recibe en diferencial |
| `clearance_budget.py::guarda_aire()` (case) | **enmienda** | los 120 W del cajón que hoy no tiene |

Todos entran por `hardware/tools/gates.py` sin lista, y **cada uno se ve fallar
con su mutación antes de mergear**.

### 9.1 El bring-up, reescrito

Se escribe antes de que exista la placa, hereda la forma de la v3 (cada paso
predice un número, `medidas.csv` lo guarda, `check_bringup.py` juzga) y **no
pierde ninguno de sus pasos**: los 6 (telemetría contra multímetro), 7
(térmica con el recinto cerrado a carga de diseño) y 8 de la v3 siguen; la v1
de este papel los había dejado caer.

- **Paso 0** (desenchufado): aislamiento de los tres tabs contra la pared **se
  queda** (`U2` con el tab a −15 V, la pared a PE). Continuidad de tierra,
  igual. **Nuevo**: continuidad de cada borne de ★ de cada módulo con ★
  (miliohmios), y **aislamiento** —no «abierto»: > 1 MΩ— entre el borne de ★
  de un módulo y el de otro **con ★ desconectado**, medido entre los dos
  bornes que tocan ★ (para `PS2`/`PS4`, su positivo). Y **> 1 MΩ entre `GNDA` y
  `GNDD`**, como la v3.
- **Paso 1** (R sola, C y bus board desconectados): **cada IRM, uno por uno**,
  tensión en vacío y a su nominal con carga ficticia, **rizado a 20 MHz con el
  método de la nota 2 de la hoja** (par trenzado de 12", 0,1 µF ‖ 47 µF), y
  **la corriente de red rms** con pinza a esa carga, contra la fila de la hoja.
  **Inrush** con pinza de corriente en un arranque frío y en un rearranque a
  los 100 ms: contra `fusible_budget.py`.
- **Paso 2**: ±15 V con carga → rizado **después del LC**, a 20 MHz, y el
  mínimo de +15 V con carga contra los 14,1 V que `U1` necesita.
- **Paso 2b, el secuenciador**: quitar la red a `PS1` sola, con `PS2` viva:
  **los dos rieles de la cascada caen juntos**, y viceversa. Lo mismo en el
  rack. Es el paso que valida D-F4; sin él, D-F4 es una promesa.
- **Pasos 3–5**: la cascada, iguales a la v3 (setpoints, `J2` medido y no
  leído, ±12 V con carga).
- **El paso 4 de la v3 —el valle— muere**; su sustituto es el paso 2.
- **Paso 6**: telemetría contra multímetro, **más los ±15 V con carga**.
- **Paso 7**: térmica con el recinto en su configuración final (cerrado o
  ventilado, D-F3) **a la carga sostenida declarada**, TMP1075 y termopar sobre
  `PS3` y `PS6`: es la medida que valida `calor_budget.py`, y **la que decide
  si la columna «sostenido» de §1 es cierta**.
- **Nuevo, el desfase rack ↔ instrumento**: 2 A de carga ficticia en +12 V de
  rack y **milivoltios entre la masa del bus board de invitados y `GNDREF`
  de C**; contra `ground_budget.py`. Y con un CV de 1 V entrando por la bahía
  desde un jack cargado con esos 2 A, **el 1 V/oct del instrumento en cents**:
  es la medida de que el diferencial de la bahía funciona.
- **Nuevo, el crowbar de rack**: forzar el disparo con `PS3` cargada: **`PS3`
  entra en *hiccup*, `PS4` se apaga por el secuenciador**, nada humea.
- **El LNA (#58) es la puerta del riel ultra, y no basta**: además de su
  banda, **el riel de ±12 V se mira a 20 MHz de ancho de banda** con carga y
  los seis módulos encendidos, contra la cota de RF de `rizado_budget.py`.

---

## 10. Enmiendas a otros papeles

Para ejecutarlas en el plan de esta tanda, **no para que un documento prometa
lo que otro no hace** (#214, #206).

| Documento | Tipo | Qué |
|---|---|---|
| `hardware/01-power-supply/v3/README.md`, `docs/modules/01-power-supply.md` | Update | estado: la v3 no se pide; la v4 es la que se construye, y por qué; la regla «nunca con una v4» y qué la sustituye |
| `design-notes.md` v1 §13 | Patch | ★ es un nodo en R; `GNDD` no lo toca; el chasis es la masa del rack |
| `design-notes.md` v1 §18 | **Rewrite** | de 100 Hz a 65 kHz: seis módulos, LC amortiguado, ferritas, Y2 de modo común, enlace trenzado, **el LNA y la mirada a 20 MHz como puertas** |
| spec del chasis §3.1, §3.2, §3.3, §4 | Update / **Rewrite** de §3.2 | térmica → `calor_budget.py` con la cadena de §6; «conduce calor, nunca corriente» → «conduce la corriente del rack, nunca la del instrumento»; geometría sin toroide y con D-F3 |
| `case/clearance_budget.py::guarda_aire()` y el papel del case | Expand / Sync | los 120 W del cajón; D-F3; `chasis_toroide_*` desaparece; dos placas; distancia R ↔ C como parámetro y puerta; el IEC (#130) sigue pendiente |
| **Papel de la bahía** (#166 §5, #183) | **Requisito** | isla de masa del rack bajo los jacks; **recepción diferencial** de cada CV que cruza al instrumento; `check_netlist.py` con «ningún casquillo en `GNDA`» |
| `alimentacion-n657-design.md` §3.2 | Patch | el calor del LDO a máximo (4,57 W); D-R1 sigue abierto con los dos números |
| `psu-v2-goat-design.md` §7, §11.5 | Patch | la IRM-15-5 «fuera de la placa» → `PS6` en R |
| `consumo_total_budget.py` | Patch | sin `RESERVA_INVITADOS` |
| `power_budget.py` | Patch | techo = sostenido de `PS6`, de `calor_budget.py` |
| `ground_budget.py` | Expand | I × R_retorno con N; la aserción de que no entra en la cadena de tono |
| Spec del cerebro (módulo 2) | **Requisito** | el VBUS del host USB se regula en el módulo 2; la fuente entrega 4,875 V menos el cable |
| #169 | Update | rieles de §4.3, PTC por slot como requisito, secuenciador y crowbar aguas arriba |
| #151 | Update | dueño del techo: `calor_budget.py`; sigue abierto hasta que corra |
| #118 | Update | el crowbar vuelve **solo** en los rieles de rack, y por qué ahí sí cierra el lazo |
| #256 | Update | ya no bloquea el dimensionado del +5 V; bloquea el calor del 1,8 V |
| #58 | Update | puerta del riel ultra, y no basta sola (RF a 20 MHz) |
| #141, #280, #106, #56, #57 | Close (al adoptar la v4) | el sujeto desapareció con el toroide y el rectificador |

---

## 11. Lo que este papel NO decide

- **D-R1, el 1,8 V** (LDO o buck, y dónde vive). Aquí solo su calor en los dos
  extremos.
- **El bus board de invitados** (#169): peines, PTC (valor), sitio. Aquí sus
  rieles y sus requisitos.
- **La bahía**: aquí sus dos requisitos; el mecanismo del diferencial es suyo.
- **El valor del fusible**: 4 A T es hipótesis hasta `fusible_budget.py`.
- **Ninguna pieza que no esté en §3 con su hoja** (R-M3): LC, ferritas, Y2,
  detector de ventana, interruptores, SCR, conectores, `NT1` y `L_F` nuevos, se
  nombran en el plan con hoja en el árbol.
- **El tope de brillo de la cadena de LEDs**: se queda por diseño.

---

## 12. Verificaciones antes de sellar

1. **Las curvas de derating de las cuatro hojas, con los ojos** (p. 3): codo,
   pendiente y el 45 °C de las salidas de 5 V. Entrada de `calor_budget.py`.
2. **Las curvas de PSRR** de LM2941 (Fig. 9), LM2991 (Fig. 8), LT3045 y LT3094
   a 65 kHz y a 1–20 MHz, de las cuatro hojas ya en el árbol, con los ojos.
   Entrada de `rizado_budget.py`.
3. **Las seis huellas IRM** dibujadas de la p. 3 de cada hoja y pasadas por
   `check_huellas.py`: una huella equivocada pasa el ERC, el DRC y la netlist.
4. **«EMI testing of component power supplies»** de Mean Well
   (meanwell.com/Upload/PDF/EMI_statement_en.pdf): el mecanismo de modo común
   de D-F5, dicho por el fabricante.
5. **La cifra de fuga de IEC 62368-1** para Clase I enchufable, de la norma.
6. **La hoja de Ametherm SL22** (o la talla que salga): régimen ≥ 4 A, energía
   por arranque y capacidad máxima a 230 V contra ~205 µF.
7. **Si un IRM encapsulado puede conducir calor por su cara a la chapa**
   (pregunta a Mean Well, o medida en el paso 7): cambia cuánto vale A en D-F3.
8. **El I²t del fusible elegido**, de su hoja, para `fusible_budget.py`.
9. **Que ningún módulo del instrumento expone un jack** (#167, «el frente se
   unifica»): es la condición del invariante de §4.1. Si alguno lo hace, ese
   jack cumple la misma isla y el mismo diferencial.
10. **Stock real** de las seis referencias el día de mandar.

---

## 13. Riesgos

| # | Riesgo | Se cierra cuando |
|---|---|---|
| 1 | **El listón sostenido no existe en el recinto cerrado** (la junta lo estima en 17–52 % de placa) | D-F3 decidido; `calor_budget.py` con la cadena entera; paso 7 medido |
| 2 | La RF de los flancos (1–20 MHz) entra en los op-amps mientras el LNA da verde en su banda | ferritas + LC amortiguado; la mirada a 20 MHz del paso final de §9.1 |
| 3 | El modo común de seis conmutadores vuelve por ★ y por el espárrago | D-F5 (Y2 al chasis en cada módulo), §12.4 leído, medido con los seis encendidos |
| 4 | El retorno de un invitado desafina el instrumento | la isla y el diferencial de la bahía (requisitos de §10); `ground_budget.py` extendido; la medida en cents del bring-up |
| 5 | Un riel crudo solo, en cada encendido, apagado y microcorte | D-F4 (secuenciador), paso 2b |
| 6 | Un IRM de 12 V en OVP pone 16,2 V en una fila ajena | D-F6 (crowbar de rack), su prueba en el bring-up |
| 7 | El fusible se fatiga con los rearranques en caliente | `fusible_budget.py` con el término de rearranque; 4 A T como hipótesis |
| 8 | El calor del 1,8 V a máximo (4,57 W) cae dentro del recinto y nadie lo contó | §4.5 declarado; D-R1 decide con los dos números |
| 9 | El módulo 2 recibe 4,4 V por el cable y el host USB no arranca | conector y cable de §8; el VBUS regulado en el módulo 2 (requisito de §10) |
| 10 | Una huella IRM equivocada llega a fábrica | §12.3, `check_huellas.py` por placa |
| 11 | Tres proyectos KiCad donde había uno; las puertas se multiplican | heredan por placa (§9); lo que se paga es tiempo |
| 12 | El listón compró un máximo que no existe (fila de 104 HP a 3,8 A) y se paga en calor y chapa | es el precio del listón; lo que puede bajar es el **sostenido** declarado, y eso es D-F3, no un descubrimiento |

---

## 14. Lo que Samuel decidió (2026-09-03)

| | Decisión | Consecuencia inmediata |
|---|---|---|
| **D-F1** | el listón, como **corriente de placa** | §1; se **re-firma** en sostenida cuando corra `calor_budget.py` |
| **D-F3** | **A: ventilar** recinto y cajón, convección natural, **sin ventilador** | el papel del case rediseña techo y trasera; `guarda_aire()` con los 120 W; la franja de 230 V sigue cerrada |
| **D-F2** | telemetría de rack **poblada** (`U13`, `U14`) | +4 hilos en R ↔ C; 0x44 y 0x45 dejan de ser opcionales en `check_telemetria.py` |
| **D-F4** | **secuenciador** por ON/OFF, cascada y rack | detector de ventana ×2 en R; `secuencia_budget.py`; paso 2b del bring-up |
| **D-F5** | **Y2 de modo común** por módulo | seis Y2 al chasis en R; §12.4 por leer; entra en `fuga_budget.py` |
| **D-F6** | **crowbar** en los rieles de rack, y solo ahí | SCR por riel de rack; `check_absmax.py` contra los 16,2 V; su prueba en el bring-up |
| **D-F7** | `PS5` = **IRM-45-5** (era IRM-20-5); +5 V de rack **4,0 A declarados** sobre 8 de placa | `calor_budget.py` lo hizo nacer: con la IRM-20-5 el listón del +5 V no existía con ningún venteo (§3). Una referencia menos en R; 87 × 52 mm donde había 52 × 27 |

**La columna «sostenido» de §1 está rellena** (03-09, `calor_budget.py`, con
D-F3 = A y D-F7): 2,0 / 2,0 / 4,0 A de rack y 4,2 A digital con el venteo
mínimo de 20 600 mm². Es una **predicción de modelo**, pesimista a sabiendas
(§6); su testigo es el paso 7 del bring-up, y hasta esa medida el papel dice
«sostenido según modelo». Lo que ese número le exige a otros: el venteo
mínimo al case (#289) y el techo nuevo del digital a `power_budget.py`
(Tarea 5 del plan).

**Lo que sigue sin ser de este papel** (§11): D-R1 (el 1,8 V), el valor del
fusible hasta `fusible_budget.py`, los peines y el PTC de #169, y el mecanismo
del diferencial de la bahía.
