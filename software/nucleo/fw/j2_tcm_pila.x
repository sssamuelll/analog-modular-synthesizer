/* La pila principal (MSP) en el tope de la DTCM (feature `j2-tcm-pila`, solo banco).
   Va antes de `link.x`, que solo ofrece `_stack_start` con PROVIDE: este valor manda.
   Es la pila de las excepciones: el tic, el planificador y la recuperacion apilan su marco
   y sus locales aqui, y con la D-cache desalojada eso eran fallos hacia la AXISRAM. */
_stack_start = ORIGIN(DTCM) + LENGTH(DTCM);
/* El fondo de la pila queda 8 KB por encima del origen de la DTCM: debajo estan los statics
   de `.dtcm` (unos 4,3 KB). `cortex-m-rt` exige el fondo por debajo del tope. */
_stack_end = ORIGIN(DTCM) + 8K;
