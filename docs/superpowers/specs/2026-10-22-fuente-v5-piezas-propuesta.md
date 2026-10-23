# Fuente v5: propuesta de piezas (convertidores, ladrillo, conector)

**Fecha**: 2026-10-22 · **Estado**: **PROPUESTA sin firmar.** No elige pieza, no cierra ningún HUECO de [v5 §9.2](2026-09-05-fuente-v5-ladrillo-design.md), no toca el [pliego](2026-09-08-pliego-ladrillo.md) y no autoriza fabricar ni comprar. Ordena lo que hay en hojas de datos para que una junta pueda firmar o descartar, pieza por pieza.

> **Nota de la revisión de #474:** donde este texto dice `TPS26630`, la BOM monta **`TPS26631PWPR`**: TI solo vende el TPS26630 en VQFN-24 (`tps2663.pdf`, orderables). RON, OVP e `I_OL` son los mismos en los dos (misma hoja); lo que cambia es la sobrecarga: el TPS26631 deja pasar hasta 2 × `I_OL` durante 25,5 ms antes de limitar, y su corte rápido está en 3 × `I_OL` (`tps2663.pdf` p. 7, 23; lo comprueba `recuperacion_budget.py`). Lo que se compra lo dice [`bom.csv`](../../../hardware/01-power-supply/v5/bom.csv), no esta propuesta.

**Decisión mía, revocable:** los convertidores se buscaron como **módulos hechos**, no como chips en placa propia. La razón es que la hoja del módulo garantiza ventana, UVLO y aislamiento, que son justo los datos que los HUECOS piden. Se vuelve a chips solo si un riel no tiene módulo.

**Cómo se hizo:** tres búsquedas independientes (convertidores, ladrillo, conector) contra las hojas, cada cifra con archivo y página. Luego comprobé a mano las cifras que deciden. Lo no comprobado por mí lleva la marca **[agente]**; lo que ninguna hoja dice, **NS** (no declarado).

---

## 1. En cristiano

- **Convertidores:** cuatro módulos TRACO de la serie **THN ...WI** (los cuatro con la misma entrada 4:1, el mismo mando de encendido y la misma caja) y un quinto, no aislado, para el +5 V del rack. El digital queda aislado (M1) sin diseñar la barrera: el módulo ya la trae.
- **Ladrillo:** el único candidato cuyas protecciones se recuperan todas solas es el **AE/SL Power TE90** (hiccup en sobrecarga, sobretensión y corto; sobretemperatura se recupera sola). Es también el de menos margen de potencia. Los Mean Well GST120A / GSM120A y el TDK DTM110 **se enclavan** en sobretensión y sobretemperatura: hay que quitar la red para rearmarlos.
- **Conector:** **LEMO serie 1B** (12 A, 3,6 mΩ, 5000 ciclos) o **Switchcraft EN3 de 2 polos** (13 A, 300 ciclos). El conector de los Mean Well (mini-DIN de 4 polos, «R7B») queda como el peor: lo acepta cualquier fuente de 12–48 V y se come 161 mV del cordón.
- **Lo que ninguna hoja contesta, de ninguna de las tres piezas:** qué pasa al enchufar con la salida viva, qué pasa si el módulo falla con la entrada puenteada a la salida (#334), y el valor y sitio del condensador Y del ladrillo. Eso no se resuelve eligiendo: se pregunta al fabricante (§6) y se ensaya.

## 2. Convertidores

Cargas del [guion](../../../hardware/01-power-supply/v5/ladrillo_budget.py) (declarado / censo): +12 V 1,050 / 0,850 A · −12 V 0,500 / 0,300 A · +5 V rack 0,500 / 0,300 A · +5 V digital 2,895 / 0,965 A · cada crudo 0,650 / 0,334 A. Aire del case: techo de diseño 65 °C (sala de 45 °C del `calor_budget.py:138` más 20 K del v5 §6) **[comprobado]**.

| Riel | Candidato 1 | Qué cubre | Lo que lo descartaría |
|---|---|---|---|
| ±12 V rack | **TRACO THN 30-2422WI**, ±12 V a ±1,25 A | 18,6 W declarados de 30 W | Regulación cruzada 5 % máx. **solo entre 25 y 100 % de carga asimétrica**: el −12 V declarado (40 %) cabe, el del censo (24 %) queda justo fuera |
| +5 V digital, aislado (M1) | **Mornsun URB2405YMD-20WR3** (5 V a 4 A, **88 % mín. / 90 % típ.**, `mornsun_urb_ymd20wr3.pdf` p. 1) o **TRACO THN 20-2411WI** (5 V a 4 A, 89 % típ.) | 14,47 W de 20 W (72 %) | El URB2405YMD-20WR3 publica eficiencia mínima garantizada (88 % mín., p. 1) y UVLO (5,5 V mín. / 6,5 V típ., arranque 9,0 V máx., p. 2); el THN 20-2411WI da solo eficiencia típica (89 %) |
| Crudos ±15,5 V (D-V3) | **2 × THN 20-2413WI** (15 V, 1,33 A), uno cableado invertido, cada uno recortado +3,3 % | 10 W de 20 W cada uno | La exactitud **tras recortar** no se declara; el modelo del margen supone ±2,5 % (`ladrillo_budget.py:109`) |
| +5 V rack | Un módulo no aislado: **RECOM RPMB5.0-2.0** (88 % típ., p. 2) o **Mornsun K7805T-1000R3** (85 % típ. a Vin máx. / 93 % a Vin mín., p. 1) | 2,5 W | RPMB sin UVLO declarado y sin certificado; K78 sin máximo absoluto de entrada publicado (rango operativo 8–36 VDC, derating 100 % hasta 60 °C para Vin ≤ 26 V, p. 1, 3), «no apto para hot-swap», sin protección de polaridad |

**Por qué los crudos van de a dos módulos y no uno doble:** el recorte de la serie THN está escrito «(single output models only)» **[comprobado, p. 2]**, así que un ±15 V doble no llega a 15,5 V.

**Lo que da la familia THN WI** (comprobado en `traco_thn20wi.pdf` y `traco_thn30wi.pdf`, p. 1–4): entrada 4:1 para 24 V nominales, UVLO 7,5 / 8 / 8,8 V (mín/típ/máx), sobretensión admitida 50 VDC durante 1 s, IEC/EN/UL 62368-1, aislamiento entrada-salida 1600 VDC durante 60 s con capacidad de **1500 pF máx.**, mando «Remote» referido a −Vin (un vigilante del lado de 24 V lo puede manejar), protección de corto continua con recuperación automática, exactitud de ajuste ±1 % máx. en las salidas simples.

**Efecto sobre la ventana (pliego §2):** con un ladrillo de ±5 % (22,8 a 25,2 V) y 0,5 V de caídas, la entrada del módulo no baja de ~22 V y no sube de 25,2 V, contra un arranque de 9 V y un tope de 36 V. Holgura de más de 13 V abajo. Con los módulos 2:1 de 18 V la holgura baja a ~4 V y la elección del ladrillo pasaría a mandar. **El 4:1 desacopla el H-V2-ENTRADA de la elección del ladrillo.** Esto es cuenta mía con tolerancia genérica; falta la del ladrillo elegido.

**Lo que no cierra:**

1. **Eficiencia: H-CENSO-ETA-DIGITAL.** El **Mornsun URB2405YMD-20WR3** publica **88 % mín. / 90 % típ.** a plena carga en hoja (`mornsun_urb_ymd20wr3.pdf` p. 1) **[comprobado]**; la familia THN da **89 % típico** sin columna mínima (`traco_thn20wi.pdf` p. 1, `traco_thn30wi.pdf` p. 1).
2. **Reintentos con abandono.** Todos los candidatos reintentan solos y sin tope ante un corto. **El pin Remote no sirve como actuador del abandono** **[comprobado, thn20wi/thn30wi p. 3]**: es «passive = on» (abierto o 3–15 V = encendido; 0–1,2 V o cortocircuito = apagado), así que un mando muerto o un hilo roto deshace el abandono, y apagado el módulo sigue conectado a la entrada (corriente de reposo 2 mA). Un puente entrada-salida (#334) seguiría alimentado. Solo un elemento en serie delante de los convertidores corta a todos. (Corrección del 2026-10-22: la primera redacción de este punto decía lo contrario.)
3. **#334.** Ninguna hoja dice qué pasa si un módulo falla con la entrada puenteada a la salida. Los THN aíslan 1600 VDC, lo que cambia el camino de fallo pero no demuestra nada. El tope delante de `U1` (M3) se resuelve con `TPS26630` + `SMBJ16A` (§9.1).
4. **Hot-plug.** Mornsun lo prohíbe en hoja («Hot Plug: Unavailable», `mornsun_urb_ymd20wr3.pdf` p. 1). TRACO y RECOM no lo declaran. Hay que preguntar.
5. **Ruido.** Las hojas dan rizado pico a pico a 20 MHz de ancho de banda y sin espectro (`THN 20WI`: 75 mVp-p típ. / 100 mVp-p máx. a 330 kHz; `URB2405YMD-20WR3`: 50 mVp-p típ. / 100 mVp-p máx. a 300 kHz). El LC y el rechazo de los LDO (`LT1963A` + `LT3045` y `LT3015` + `LT3094`) atenúan esa banda por debajo de los 0,30 µVrms presupuestados para rizado dentro de los 0,8 µVrms de la cascada.
6. **GNDD.** La capacidad de aislamiento (hasta 1500 pF en THN, 2000 pF típ. en URB2405YMD-20WR3 p. 3) acopla en AC GNDD con el retorno de 24 V mientras conserva ≥ 1000 MΩ en DC (> 1 MΩ exigidos en la fuente). Pesa sobre H-V5-PE.
7. **Dimensionado de los crudos:** 0,65 A declarado o 0,334 A del censo (HUECO 5) decide si bastan módulos de 10 W.
8. **Precios y stock:** solo Octopart, sin definir; THN 20-2411 con stock visto en Mouser, Farnell, RS y TME. Mornsun aparece bajo marca Hi-Link en Octopart: revisar marca antes de comprar.

## 3. Ladrillo

Piso de cribado usado: ≥ 80 W continuos a 45 °C. **No es requisito**: el real sale de H-PL-ENTREGA con el presupuesto corregido por M1.

| | **AE/SL Power TE90A2403F01** | Mean Well GST120A24-R7B | Mean Well GSM120A24-R7B | TDK-Lambda DTM110PW240C8 |
|---|---|---|---|---|
| Potencia a 45 °C | **82,5 W** (90 W hasta 40 °C, −1,5 W/°C hasta 45 W a 70 °C) **[comprobado, p. 3]** | **120 W a 230 VAC** / **108 W (90 %) a 100 VAC** **[comprobado, p. 3]** | **108 W (90 %)** (100 % hasta 40 °C, 80 % a 50 °C) **[comprobado, p. 3]** | 96,25 W (regla lineal) |
| Sobrecarga / corto | hiccup, automático **[comprobado]** | hiccup, automático **[comprobado]** | hiccup **[comprobado]** | hiccup (corto), automático |
| Sobretensión | hiccup **[comprobado]** | **enclava** «re-power on to recover» **[comprobado]** | **enclava** **[comprobado]** | enclava |
| Sobretemperatura | automático **[comprobado]** | **enclava** **[comprobado]** | **enclava** **[comprobado]** | NS |
| Salida vs PE (L14) | por variante: «A» flotante, «B» unida a tierra (nota 3, p. 5) | −V unido a FG **[comprobado, p. 3]** | −V **no** unido a FG, carcasa a FG **[comprobado, p. 3]** | NS |
| Fuga | <500 µA entrada–tierra y <4 mA salida–tierra **[comprobado, p. 2]** | 0,75 mA a 240 V **[comprobado]** | <115 µA tierra, <100 µA contacto **[comprobado, p. 2]** | <100 µA contacto |
| Certificación | EN 62368-1 (`ae-TE90-DEMKO-EN62368.pdf`) y CB IEC 60950-1 (`ae-TE90-CB-cert.pdf`, Tma = 40 °C en p. 11) **[comprobado]** | EN 62368-1 declarada en hoja (`meanwell-GST120A-spec.pdf` p. 2) | IEC/EN 60601-1 2×MOPP (`meanwell-GSM120A-spec.pdf` p. 2) | 60601-1, 62368-1, CE |
| Clase | I (C14) o II (C8) | I (C14) | I (C14) | II (C8) |

**Lectura:** el pliego §4.1 deja al ladrillo la mitad de «reintentos con abandono». Un enclavamiento que pide quitar la red no es un reintento de la cadena. Por eso el TE90 va primero, aunque su margen es el más delgado (la hoja dice en p. 2: *«All specifications are typical at nominal input, full load, at 25°C ambient unless noted»* **[comprobado]** y el informe CB p. 11 fija `Tma = 40 °C` a plena carga de 90 W **[comprobado]**). Si H-PL-ENTREGA sube de ~80 W, o AE no garantiza la curva a 45 °C, entra el GST120A24-R7B (120 W a 45 °C con 230 VAC, −V unido a FG) o el GSM120A24-R7B (108 W a 45 °C, −V flotante respecto a FG).

**Condensador Y:** **ningún fabricante publica valor ni sitio.** Es la pregunta decisiva de L14 (pliego §7, Q6) y no se puede aceptar ninguno sin respuesta. Descartados con motivo: Cosel CXLA100F-24 (enclava), SDM120-24-U (0–40 °C), Phihong AA120U-240B-R (relación con PE sin declarar), Cincon TRH100A240 (fuga 1,3 mA, L14 sin declarar), XP Power AHM100PS24 (sobretensión por reciclar entrada; 45 °C contradictorio entre documentos). **FSP no se revisó.**

## 4. Conector y cordón

| | **LEMO 1B** (FGG.1B.303.CYCD62Z / EGG.1B.303.CLL) | Switchcraft EN3 2P #16 (EN3C2F16 / EN3P2M16) | binder 680 M16 | Kycon KPPX-4P + KPJX-PM-4S (= «R7B») |
|---|---|---|---|---|
| Corriente por contacto | 12 A **[comprobado]**, sin temperatura | 13 A, plano sin texto | 7 A, hoja de revendedor | **7,5 A a 48 VDC** **[comprobado, `kycon_KPJX-PM-4S.pdf` y `kycon_KPPX-4P.pdf`]** |
| R de contacto máx. | 3,6 mΩ **[comprobado]** | 5 mΩ | 5 mΩ | **30 mΩ máx.** **[comprobado]** |
| Bucle de contactos a 2,68 A | 19 mV | 27 mV | 27 mV | **80 mV con 2 pines en paralelo por polo** (161 mV con 1 pin por polo) |
| Ciclos | 5000 **[comprobado]** | 300 mín. (drawing) | >500 | NS |
| Cable | ≤ 18 AWG en el plug de crimpar **[comprobado]** | 16 AWG | NS | 18 AWG × 4C (1,2 m en GST120A/GSM120A p. 2) **[comprobado]** |
| Se confunde con otros | cualquier LEMO 1B.303 con llave G | cualquier EN3 de 2 polos | cualquier M16 de 3 polos | fuentes Mean Well / AE de 12–48 V |
| Retención | push-pull, fuerza NS | bayoneta, fuerza NS | rosca, fuerza NS | snap-and-lock, fuerza NS **[comprobado]** |

Enchufe con salida viva, rebote de contacto y corriente de corto de corta duración: **NS en todas.** H-V5-CALIENTE, -RECONEXION y -CORTO solo se cierran ensayando la pareja. El único fabricante que lo dice es Neutrik (speakON: «NOT FOR INTERRUPTING CURRENT»), y por eso está fuera.

**Rechazadas:** Neutrik XLR-4 (cualquier XLR-4 la acepta y el SAM17 ya tiene entradas XLR/TRS), speakON (prohibido como conector de alimentación en hoja), M12 T de Phoenix (>100 ciclos), jacks de barril (CUI, Switchcraft 760K).

**Cordón** (rangos, no elección): dos conductores de 16–18 AWG (o 4 conductores 18 AWG en paralelo 2+2 en el cable R7B nativo de 1,2 m, `meanwell-GST120A-spec.pdf` p. 2), ≤ 2 m, funda de goma o PUR para manejo frecuente, alivio de tracción en ambos extremos. Ampacidad de la tabla Lapp (DIN VDE 0298-4) para 1,0 mm² a 30 °C: 10 A; a 45 °C el factor 0,79 da ~7,9 A. **Manda la caída de tensión, no el calor.**

**El nudo que ningún agente cerró, y que es mío:** el ladrillo trae **su propio cable fijo con su propio enchufe** (barril 2,5 × 5,5, o mini-DIN KPPX/KPP-4P; el TE90 ofrece también la opción 45, barril con rosca). Para usar un LEMO o un EN3 en el chasis hay tres caminos, y la decisión es de Samuel:

1. **Aceptar el enchufe del ladrillo** (el más barato, y el que cualquier fuente de 12–48 V puede ocupar: pierde el sentido del contrato exclusivo).
2. **Pedir al fabricante del ladrillo un enchufe a medida** (la hoja del GST90A de Mean Well lo ofrece «a petición del cliente», con pedido mínimo; AE: sin consultar).
3. **Un cordón intermedio nuestro** entre el enchufe nativo y el conector del chasis (añade una pareja de contactos y su caída a H-V5-CALIBRE, y es un segundo cordón por el que preguntar H-V5-CORTO).

Cortar el cable certificado del ladrillo y soldarle otro enchufe rompe lo que L10 y L16 piden acreditar; no se propone.

> **DECIDIDO 2026-10-22 (Samuel, en la conversación): camino 1, se acepta el enchufe nativo del ladrillo.** Lo que arrastra (consecuencias mías; ninguna la contradice una hoja):
>
> - La pareja del chasis ya no se escoge entre LEMO y EN3: es el receptáculo **Kycon KPJX-PM-4S** (`kycon_KPJX-PM-4S.pdf`) que acopla con la clavija de 4 polos (`KPPX-4P` / `R7B`) del ladrillo. La tabla de arriba queda como respaldo por si se vuelve al camino 2.
> - El contrato exclusivo (v5 §9.3, H-V5-INCOMPATIBLE) pasa a descansar solo en declararlo: ese enchufe lo aceptan fuentes ajenas. El bloqueo de polaridad nuestro (H-V5-INVERSION, `LM74502` en `lm74502.pdf`) deja de ser un seguro y pasa a ser la única defensa.
> - Los fabricantes cablean distinto el mismo mini-DIN de 4 polos (`TE90` opción 49 en `ae-TE90-datasheet.pdf` p. 6: pines 1, 3 = +V y 2, 4 = −V; Mean Well `R7B` en `meanwell-GST120A-spec.pdf` p. 2: pines 1, 4 = +V y 2, 3 = −V) **[comprobado]**: que un enchufe encaje no dice que la polaridad sea la buena.
> - Con la opción de 4 polos, tanto el receptáculo **Kycon KPJX-PM-4S** como la clavija **Kycon KPPX-4P** están especificados a **48 VDC y 7,5 A por pin** **[comprobado]**.

## 5. Cómo encajan las tres piezas

- **Ventana (pliego §2):** con módulos 4:1, holgura holgada. Con el cordón de 141 mV (16 AWG, 2 m) y el peor bucle de contactos (161 mV del Kycon con 1 pin por polo, 80 mV con 2 pines en paralelo), las caídas siguen siendo décimas de voltio contra una holgura de >13 V.
- **Lazo de retorno (inferencia mía, no de una hoja):** M2 une chasis y retorno DC, y el cordón no lleva PE. Con el TE90 en variante «A» o el GSM120A24-R7B (salida sin unir a tierra) el chasis quedaría sin camino DC a PE; con la «B» o con un GST120A24-R7B (−V a FG) el retorno DC, y con él el chasis, quedan atados a tierra desde el ladrillo, con el lazo de masa que eso trae hacia otros equipos con tierra. Es H-V5-PE y no se resuelve aquí.
- **Reintentos:** ladrillo con hiccup + un elemento en serie en la entrada (el vigilante M5, `TPS26630` + `MSP430FR2111`) que corta a todos los convertidores a la vez; el pin Remote de los THN queda como mando secundario, no como actuador del abandono. El ladrillo sigue enviando pulsos a un corto del cordón aguas arriba del vigilante: H-PL-ABANDONO-FUENTE sigue sin dueño.
## 6. Qué se pregunta a quién

- **Ladrillo (todos):** Q2, Q6 (valor y sitio del Y), Q9, Q10, Q11, Q13, Q14, Q15, Q16, Q17, Q18, Q19 del pliego §7. **AE:** además Q1 (variante A/B, opción 45 o 49, calibre), Q2 (el informe CB completo; el publicado son 7 páginas de un informe de 17 de IEC 60950-1), Q5 («<4 mA salida–tierra»), Q7–Q8 (curva garantizada). **Mean Well:** Q3, Q4 (¿el −V a FG es protector o funcional?), Q12.
- **TRACO:** UVLO de encendido contra apagado e histéresis; exactitud tras recortar; enchufe en caliente; comportamiento ante entrada puenteada a salida; eficiencia **garantizada** a 25–100 % de carga.
- **Conectores:** LEMO (llave, 2B y calibre 16, conmutación bajo carga), Switchcraft (ciclos: dibujo 300 contra web 600).

## 7. Qué comprobé yo y qué no

- **Comprobé** en los PDFs versionados en `docs/reference/datasheets/`: protecciones, curva de derating a 45 °C (82,5 W), fuga y pinout opción 49 del TE90 (`ae-TE90-datasheet.pdf`, `ae-TE90-CB-cert.pdf`, `ae-TE90-DEMKO-EN62368.pdf`); enclavamientos, curvas de derating a 45 °C (120 W / 108 W), pinout R7B y relación −V/FG de GST120A y GSM120A (`meanwell-GST120A-spec.pdf`, `meanwell-GSM120A-spec.pdf`); UVLO, sobretensión, 62368-1, 1600 VDC, 1500 pF, «single output models only», regulación cruzada 5 %, eficiencia típica y listado de modelos de THN 20/30 WI (`traco_thn20wi.pdf`, `traco_thn30wi.pdf`); eficiencia mínima garantizada (88 % mín. / 90 % típ.) y aislamiento 1500 VDC del Mornsun `URB2405YMD-20WR3` (`mornsun_urb_ymd20wr3.pdf`); `RPMB5.0-2.0` (`recom_rpmb20.pdf`) y `K7805T-1000R3` (`mornsun_k78_t1000r3.pdf`); Kycon 7,5 A a 48 V y 30 mΩ (`kycon_KPJX-PM-4S.pdf`, `kycon_KPPX-4P.pdf`); `TPS26630` RON máx. 53 mΩ y corte OVP 8,5–14 µs (`tps2663.pdf`); `LM74502` (`lm74502.pdf`); `SMBJ16A`/`SMBJ26A` (`bourns_smbj.pdf`); `SF-1206F` (`bourns_sf1206f.pdf`); `TL431BI` (`tl431.pdf`); `MSP430FR2111` (`msp430fr2111.pdf`); `BT151-500R` (`nxp-bt151-500r.pdf`); y `LM393B` (`ti-lm393b.pdf`).
- **No comprobé:** TDK DTM110 (copia de terceros); los dibujos EN3 (PDF sin texto); la hoja de binder (de revendedor); precios; el máximo absoluto de entrada en régimen permanente de la serie THN fuera del transitorio de 50 VDC / 1 s (NS).
- **Hojas versionadas en `docs/reference/datasheets/`** y registradas en [`docs/references.md`](../../references.md): las veinte hojas de convertidores, ladrillos, conectores y protecciones citadas arriba.
- **Hojas que faltan:** TDK DTM110 oficial (403, solo copia); Cincon TRH100A y LEMO 2B / EGG.1B.302 / catálogo de llaves (403); Hirose HR10, Molex PS-45750, Wago 890, Lumberg 0270 y las hojas propias de binder.
- **No se revisaron** Murata, TDK-Lambda, Cosel, Artesyn y Cincon para convertidores, ni FSP para ladrillo.

## 8. Lo que hay que decidir, en este orden

1. ~~El camino del enchufe~~ **Decidido el 2026-10-22: camino 1, enchufe nativo del ladrillo** (§4). La pareja sale de la referencia de ladrillo.
2. **Si el piso de 80 W aguanta** o se vuelve a mirar el presupuesto con las eficiencias de hoja antes de elegir ladrillo.
3. **Si los crudos se dimensionan por 0,65 A o por el censo** (HUECO 5).
4. **Junta** sobre esta propuesta, antes de pedir nada a los fabricantes ni pedir muestras; luego firma.

---

## 9. #334 y reintentos con abandono: dos propuestas independientes, y cómo encajan

Dos agentes sin contacto entre sí, 2026-10-22. Cada uno escribió lo que necesitaba del otro como «interfaz supuesta». Ninguno elige pieza. Todas las cifras de hoja de abajo están **[comprobadas]** en los PDFs versionados en `docs/reference/datasheets/`.

### 9.1 #334 (H-V2-CORTO-DCDC): qué protege a `U1`

**El riesgo es real, pero casi no viene del fallo que nombra el issue.** El THN es un flyback aislado; el corto de barrera es el camino menos probable (aislamiento «Functional», 1600 VDC, p. 3). Dos fallos corrientes ya llegan al límite de `U1` (±20 V, `check_absmax.py:209`):

- **El OVP propio del módulo** se dispara entre el 112 y el 164 % del nominal **[comprobado, thn20wi p. 2]**: para el de 15 V, de **16,8 a 24,6 V**. La hoja no dice qué hace después (enclava, hiccup o recorta), así que «el módulo se apagará» no tiene página.
- **Trim a −Vout** ≈ 19,9 V (fórmula de la nota de la serie 20 **sin WI**, usada fuera de su rango recortable). Sin tiempo permitido en `U1`.
- Si la barrera sí se pone en corto, nada lo corta: con M2 el chasis va al retorno de 24 V, `U1` solo gasta 0,71 A y ni el límite del ladrillo ni el fusible de entrada del módulo actúan. El pico en `U1` por el filtro LC sale en ~27 V a los ~40 µs hasta 20 V (con parásitos ESTIMADO y una fuente supuesta de 0,05 Ω).

**Recomendación (para junta):**
1. **Riel positivo:** un eFuse con OVP, **TI TPS26630** (`tps2663.pdf`), **en serie en el riel crudo positivo, entre el módulo y el filtro LC, sensando del lado del módulo**, más clamp **Bourns SMBJ16A** (`bourns_smbj.pdf` p. 2, `V_WM` = 16,0 V, `V_BR` = 17,8–19,7 V) en la entrada de `U1`. Corte por OVP en 8,5–14 µs **[comprobado, tps2663 p. 8]**; entrada hasta 60 V (67 V absmax, p. 5), `V(OVPR)` = 1,176–1,224 V, modo latch o reintento por pin MODE **[comprobado, p. 1, 6]**. Cuesta 40,8 mV de los +811 mV de `U1` (`RON` máx. 53 mΩ en −40..125 °C a 0,77 A **[comprobado, tps2663 p. 7]**).
2. **Plan B:** crowbar SCR (`NXP BT151-500R`, `nxp-bt151-500r.pdf`) + fusible (`Bourns SF-1206F`, `bourns_sf1206f.pdf`); solo sirve si M5 enclava la entrada.
3. **Riel negativo:** `U2` (`LT3015`, `lt3015-rev-b.pdf` p. 2) soporta **±33 V** de `IN Pin Voltage`, por lo que aguanta el OVP propio del módulo (−24,6 V) sin superar su máximo absoluto; un diodo Schottky en inversa entre `U2 IN` y `GND` sujeta cualquier excursión positiva dentro del límite `OUT to IN Differential Voltage ≥ −0,3 V` (p. 2, Nota 10).

**Ventana de disparo, estrecha por los dos lados.** El máximo sano en `U1` es 16,19 V (modelo del repo con ±2,5 % supuesto para el THN recortado, que la hoja no declara). El modelo ejecutable (`check_absmax.py` en `v5/`) **corre y sus mutaciones se ponen en rojo**, probando ambos lados:

- **Lado alto (real):** con el disparo en su borde alto (16,92 V) y una falla de 36 V, el pico en `U1` sale **18,08 V < 20,0 V**. Si el disparo sube o el retardo pasa de 43 µs, el pico supera 20 V. Con sensado después del LC, **22,21 V > 20,0 V**: falla.
- **Lado bajo (por construcción, no es margen):** el disparo nominal deja el borde bajo justo encima del máximo sano (16,19 V) con divisores de 0,1 %.

### 9.2 Reintentos con abandono (H-V2-RECUPERACION)

**El pin Remote del THN no sirve como actuador del abandono** (ver §2 punto 2, **[comprobado]**). Realización comprobada contra hojas (`recuperacion_budget.py` en `v5/`):

- **Corte:** un eFuse **TI TPS26630** (`tps2663.pdf`) en serie en los 24 V de entrada, en modo latch, más el controlador de bloqueo de polaridad **TI LM74502** (`lm74502.pdf`). Añade ≤ 53 mΩ (`tps2663.pdf` p. 7) ≈ 0,145 V a 2,74 A (no afecta al margen de la cascada, que va detrás del THN).
- **Decisor:** un microcontrolador pequeño con FRAM, **TI MSP430FR2111** (`msp430fr2111.pdf`: 3,75 KB FRAM en p. 7, $10^{15}$ ciclos de escritura en p. 35, SVS en 1,71–1,99 V en p. 20), alimentado desde el lado de 24 V, que guarda la cuenta y la bandera de «abandonado». No depende de los N657. Un pull-down mantiene el eFuse apagado (`V(SHUTF)` = 0,8 V, p. 7) mientras el MCU no esté vivo; con la FRAM corrupta (CRC inválido) arranca como «abandonado».
- **Un abandono no se borra apagando:** se suelta con un botón dedicado ≥ 2 s con entrada válida, nunca por el cerebro digital.
- **Alternativas descartadas o por detrás:** lógica discreta con relé de enclavamiento (un golpe puede «setearlo»), y el secuenciador UCD9090A (cuenta bien pero su reinicio de cuenta a 1 s deja ciclar un fallo de ~3 s para siempre y no recuerda el abandono).

**Parámetros verificados en `recuperacion_budget.py`:** 3 reintentos (4 intentos en total); espera fija de 1,0 s; filtro de rebote de 100 ms; cuenta a cero tras 60 s sin fallo; ventana de entrada 20 V arranca / 18 V apaga / 30 V sobretensión; límite de corriente 4,5 A nominal con `R_ILIM = 4,02 kΩ` (banda 4,185–4,815 A con ±7 % en `tps2663.pdf` p. 7, ec. 5 p. 22).

**Causas distintas, tratamiento distinto.** Gastan intento: corto o sobrecarga en el bus interior, sobrecarga de un riel, colapso del ladrillo por nuestra carga. No lo gastan: subtensión o apagón de red, desconexión, rebote, polaridad inversa (el FET de bloqueo lo hace por construcción). **Sobretensión de riel: abandono inmediato, sin reintentos.** El rearme del cupo al corregir polaridad sigue siendo la obligación abierta sin dueño de v5 §9.3.

**El hueco de arriba del vigilante (H-PL-ABANDONO-FUENTE) sigue abierto.** Un corto en el cordón del propio ladrillo no pasa por nuestro interruptor. El TE90 no declara temporización del hiccup. Cotas: ≤ 2,4 W con un corto franco (6,75 A × 52,6 mΩ de bucle), pero ~117 W continuos en un corto parcial justo por debajo del umbral de sobrecarga (4,875 A), que nunca dispara el hiccup. Opciones: pedir a AE tiempo de hiccup, pico, umbral garantizado a 45 °C y variante con enclavamiento; otro ladrillo; aceptarlo y documentar (el cordón certificado se protege con la seguridad del ladrillo); o un elemento en el extremo del ladrillo, que exige un cordón intermedio y por tanto el camino 3 que Samuel descartó.

### 9.3 Cómo encajan las dos

Se cierran sin contradecirse:

- **Un eFuse de entrada** (`TPS26630`, latch, ~4,5 A) + MCU/FRAM (`MSP430FR2111`) decide y corta todo.
- **Un eFuse OVP por riel crudo positivo** (`TPS26630`, módulo → OVP → LC → `U1`); su bandera de falla (`FLT`) **baja directamente el `SHDN` del de entrada** y la anota el MCU.
- Son **dos eFuses de la misma clase con trabajos distintos**: el de entrada no ve un corto de barrera (`U1` solo gasta 0,77 A con `Iq` máx.), y el de riel no puede cortar una falla aguas arriba de él.
- Piezas que añade esto sobre la v5 de papel: eFuse de entrada (`TPS26630`), bloqueo de polaridad (`LM74502` + MOSFET), MCU+FRAM (`MSP430FR2111`) con su alimentación, botón de rearme, un eFuse para el riel crudo positivo (`TPS26630`), clamp Schottky en el negativo y TVS (`SMBJ16A`, `SMBJ26A`).

### 9.4 Qué falta, en orden de coste

1. **Gratis:** preguntar a TRACO por escrito (a) qué hace el OVP del módulo al dispararse y si es independiente del lazo de regulación, (b) la constante de trim de la serie WI, (c) arranque contra capacidad y enchufe en caliente, (d) cómo falla la barrera. Preguntar a AE por la temporización del hiccup y una variante con enclavamiento.
2. **Barato:** en 3 muestras de THN 20-2413WI, llevar el trim a −Vout y registrar la tensión, si el OVP dispara y qué hace en 10 min. Resuelve F1 y F2 del árbol.
3. **Diseño pendiente:** si el lazo de retorno realmente se cierra en la v5 (M2 + J5, H-CENSO-MAPA); y las preguntas de fabricante del §6.
4. **Ensayos que pueden fallar:** la tabla de inyección de reintentos (4 pulsos exactos, espera de 1,0 s, sin pulso tras reconectar, el rebote no gasta intentos) y la de #334 (inyección en el nodo de salida del módulo con control sin protección: debe aparecer el rizado de ~27 V, o el banco no reproduce la falla y cualquier «pasa» no vale; ruido A/B contra los 0,8 µVrms).

**Comprobado en hojas versionadas (`docs/reference/datasheets/`):** `TPS26630` RON máx. 53 mΩ (`tps2663.pdf` p. 7), `MSP430FR2111` (`msp430fr2111.pdf`), `LM74502` (`lm74502.pdf`), `SMBJ16A` (`bourns_smbj.pdf`), `TL431BI` (`tl431.pdf`), `BT151-500R` (`nxp-bt151-500r.pdf`), `LM393B` (`ti-lm393b.pdf`).
