/* Fase A: el STM32N657 no tiene flash interna; codigo y datos viven en
 * AXISRAM2, habilitada por la ROM. FLASH es el nombre que espera cortex-m-rt
 * para el codigo, no una memoria no volatil. El arranque firmado desde XSPI
 * queda pendiente de FSBL y de la validacion en placa.
 *
 * Direcciones y tamanos copiados de examples/stm32n6/memory.x de embassy (rev dc6b716):
 * alias seguro de AXISRAM2, banco de 1024 KiB en 0x34100000. Asi no se usa
 * AXISRAM1, que requiere habilitacion explicita y esta apagada al reset.
 * Codigo: 0x341A0000..0x341E0000; datos/pila: 0x341E0000..0x34200000.
 * Quedan 640 KiB antes del codigo, por resta de direcciones. El comentario
 * del ejemplo dice 768 KiB libres: no coincide con sus regiones; se conserva
 * el mapa y se deja la discrepancia anotada en EN-PLACA.md.
 */
MEMORY
{
    FLASH : ORIGIN = 0x341A0000, LENGTH = 256K
    RAM   : ORIGIN = 0x341E0000, LENGTH = 128K
}
