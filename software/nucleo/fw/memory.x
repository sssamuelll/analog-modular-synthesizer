/* El mapa del STM32N657. El chip NO TIENE FLASH INTERNA: arranca desde XSPI
   con un FSBL y un binario firmado (hub sec.8, riesgo 2), o se carga en RAM
   por el USB serial de la ROM, que es el camino de los primeros dias.

   Este mapa es el segundo: FLASH y RAM son dos tramos de la MISMA AXISRAM2, y
   el binario se carga ahi. El arranque firmado desde XSPI es del bring-up con
   placa (#231) y trae su propio mapa.

   Copiado del `examples/stm32n6/memory.x` de embassy (rama `n6-usb`, que es
   `main` mas #6939), con su razon intacta:

     FLEXRAM  0x34000000   400 KB
     AXISRAM1 0x34064000   624 KB   (pide RCC.memenr.axisram1en = 1; apagada al reset)
     AXISRAM2 0x34100000  1024 KB   (la enciende la ROM -- siempre segura)
     AXISRAM3 0x34200000   448 KB
     AXISRAM4 0x34270000   448 KB
     AXISRAM5 0x342E0000   448 KB
     AXISRAM6 0x34350000   448 KB
     NPURAM   0x343C0000   256 KB
     VENCRAM  0x34400000   128 KB

   FLASH y RAM se compactan ARRIBA de AXISRAM2 para que lo de abajo quede
   contiguo. El comentario del ejemplo de embassy dice que abajo quedan 768 KB
   y ESO ES FALSO -- lo desmienten sus propias direcciones, y lo heredamos:

     0x341A0000 - 0x34100000 = 0xA0000 = 640 KiB
     1024 KiB - 256 (FLASH) - 128 (RAM) = 640 KiB

   Y un framebuffer de 800x480 RGB565 son 768 000 B = 750 KiB, que en 640 KiB
   NO CABE. O sea que la razon con la que este mapa se justifica no se cumple
   como esta escrita: la contiguidad si se consigue, el framebuffer no.

   Donde vive el framebuffer es decision abierta y no de este archivo: es del
   #296 y de `2026-08-26-pantalla-motor-design.md` sec.1. Las direcciones se
   dejan EXACTAS como estan -- corregir la cuenta no es mover el mapa. */
MEMORY
{
  FLASH : ORIGIN = 0x341A0000, LENGTH = 256K
  RAM   : ORIGIN = 0x341E0000, LENGTH = 128K
}
