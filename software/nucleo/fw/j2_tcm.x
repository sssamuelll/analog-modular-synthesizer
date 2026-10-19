/* El texto del J2 en ITCM y sus statics en DTCM (feature `j2-tcm`, solo banco).

   Lo pasa `build.rs` ANTES de `link.x`: sus sentencias de SECTIONS quedan delante de
   `.text` en el orden del guion y se llevan las secciones de entrada que nombran. Las
   dos TCM son las del STM32N657 en su alias seguro (el nucleo corre en seguro, desde
   0x341A0000): ITCM 0x10000000 y DTCM 0x30000000, con los tamanos que deja la ROM
   (CM55TCMCR = 0x87: 64 KB y 128 KB; ITCMCR y DTCMCR con EN = 1). Las extensiones de
   FLEXRAM no se tocan.

   El depurador no escribe en las TCM (el AP da SwdApFault), asi que la imagen de las dos
   va en IMG, un tramo libre de la AXISRAM2 por debajo de FLASH, y `j2_tcm::copiar` (pre_init) la
   copia a su sitio al arrancar. */
MEMORY
{
  ITCM : ORIGIN = 0x10000000, LENGTH = 64K
  DTCM : ORIGIN = 0x30000000, LENGTH = 128K
  IMG  : ORIGIN = 0x34100000, LENGTH = 256K
}

SECTIONS
{
  .itcm : ALIGN(4)
  {
    __sitcm = .;
    *(.text.TIM7 .text.DMA2D .text.JPEG)
    *(.text._ZN15sam17_nucleo_fw6j2_tic*)
    *(.text._ZN15sam17_nucleo_fw6j2_spi*)
    *(.text._ZN15sam17_nucleo_fw8j2_banco*)
    *(.text._ZN15sam17_nucleo_fw11j2_ejecutor*)
    *(.text._ZN17sam17_nucleo_core*)
    *(.text._ZN13embassy_stm323rcc*)
    *(.text.memcmp .text.__aeabi_uldivmod .text.__aeabi_memclr4 .text.__aeabi_memmove8)
    . = ALIGN(4);
    __eitcm = .;
  } > ITCM AT> IMG
  __siitcm = LOADADDR(.itcm);

  .dtcm : ALIGN(4)
  {
    __sdtcm = .;
    *(.dtcm .dtcm.*)
    . = ALIGN(4);
    __edtcm = .;
  } > DTCM AT> IMG
  __sidtcm = LOADADDR(.dtcm);
}
