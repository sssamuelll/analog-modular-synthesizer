"""Junta 2026-09-11 - Halberg. Viabilidad en runtime del J2 sobre el SPI del N657."""
import math
SEP = "=" * 78
def h(t): print("\n" + SEP + "\n" + t + "\n" + SEP)

F_LAZO = 8_000.0
T_GIRO = 1.0 / F_LAZO
RANURAS = 6
F_PISO = 10e6
F_D8 = 34.5e6
T_WDG_MODULO = 50e-3
F_CPU = 800e6
T_REINICIO = 20e-6
ARMADOS_INSTR = F_LAZO * RANURAS
P_RANGO = {"peor del hilo p=2e-5": 2e-5, "900 s  p=2,2e-7": 2.2e-7, "120 min p=2,8e-8": 2.8e-8}
P_EVENTO_GIRO = {"normal 20 ev/s/ranura": 20/F_LAZO, "denso 50 ev/s/ranura": 50/F_LAZO}
F_AUDIBLE = 0.55

h("1. ERRATA 2.14.2 - hueco entre SPE=1 y CSTART contra 1 ciclo de SCK")
print("D2: SPE=1 -> EOTC(IFCR) -> EOTIE(IER) -> CSTART(CR1) = 3 escrituras APB")
print("espaciado minimo en el periferico: 2 ciclos de pclk por escritura APB")
for pclk in (100e6, 200e6, 400e6):
    gap = 6 / pclk
    v10 = "DENTRO de la errata" if gap < 1/F_PISO else "fuera"
    v345 = "DENTRO de la errata" if gap < 1/F_D8 else "fuera"
    print("  pclk %4.0f MHz: gap %5.1f ns | 1 SCK a 10 MHz = 100.0 ns -> %-20s | 1 SCK a 34,5 MHz = 29.0 ns -> %s"
          % (pclk/1e6, gap*1e9, v10, v345))
    print("        cuan pronto llega CSTART de mas: %.1fx a 10 MHz, %.1fx a 34,5 MHz"
          % ((1/F_PISO)/gap, (1/F_D8)/gap))
print("\nCoste de GARANTIZAR la solucion 2 (espera anclada tras read-back de CR1):")
for f_sck, nom_us in ((F_PISO, 20.0), (F_D8, 5.8)):
    t_sck = 1/f_sck
    print("  SCK %5.1f MHz: esperar %6.1f ns = %3d ciclos de CPU a 800 MHz; %5.2f %% del aire de la trama, %6.3f %% del giro, %5.3f %% de CPU por ranura"
          % (f_sck/1e6, t_sck*1e9, math.ceil(t_sck*F_CPU), t_sck/(nom_us*1e-6)*100, t_sck/T_GIRO*100, F_LAZO*t_sck*100))
print("  con embassy_time a 1 MHz de tick el grano minimo es 1 us = %.0fx el ciclo a 10 MHz y %.0fx a 34,5 MHz; con 2 us son %.1f %% de CPU por ranura"
      % (1e-6*F_PISO, 1e-6*F_D8, F_LAZO*2e-6*100))

h("2. LA TASA DEL HILO, NORMALIZADA POR ARMADO")
print("Montaje del hilo: 100 kHz, write(2B)+read(1B) = 2 armados por vuelta, con dos defmt por vuelta.")
for armados_s in (1_000, 5_000, 10_000):
    fila = "  a %6d armados/s:" % armados_s
    for intervalo, etq in ((10, "10 s"), (900, "900 s"), (1800, "30 min"), (7200, "120 min")):
        fila += "  p(%s)=%.2e" % (etq, 1.0/(armados_s*intervalo))
    print(fila)
print("\nNuestro montaje: %.0f armados/s en el instrumento (%.0f/s por ranura, una trama por giro)."
      % (ARMADOS_INSTR, F_LAZO))
for etq, p in P_RANGO.items():
    lam = p * ARMADOS_INSTR
    print("  %-22s: %8.4f cuelgues/s en el instrumento = uno cada %9.1f s = %6.1f min"
          % (etq, lam, 1/lam, 1/lam/60))

h("3. QUE OYE EL MUSICO - el EVENTO es el unico canal sin red completa")
print("Red por mensaje (cabecera 3): TONO bloque completo >=1 kHz; SET/BAHIA refresco 1 Hz;")
print("EVENTO -> COMPUERTA a 200 Hz (R-E11) repara QUE suena, no CON QUE FUERZA: la nota")
print("reparada entra a FUERZA_REPARACION = u16::MAX y sin tono de arranque (evento, enmienda 02-09).")
print("'dispara' no tiene red ninguna: golpe perdido.")
for n in (1, 3):
    print("\n--- %d trama(s) perdida(s) por cuelgue (%s) ---"
          % (n, "tipico: el plazo de un EVENTO vence a 44 us y el reinicio cabe dentro del giro"
             if n == 1 else "peor caso de la spec 3: 490 us = 3 giros"))
    for etq_p, p in P_RANGO.items():
        lam = p * ARMADOS_INSTR
        for etq_d, pev in P_EVENTO_GIRO.items():
            mal = lam * n * pev * F_AUDIBLE
            print("  %-22s | %-22s -> artefacto audible cada %10.1f s = %8.1f min"
                  % (etq_p, etq_d, 1/mal, 1/mal/60))
print("\nA 100x la tasa del hilo (el caso que pide la junta):")
for etq_p, p in P_RANGO.items():
    lam = p * 100 * ARMADOS_INSTR
    por_ranura = p*100*F_LAZO
    giros_perdidos = por_ranura*3*T_GIRO
    mal = lam * 1 * P_EVENTO_GIRO["normal 20 ev/s/ranura"] * F_AUDIBLE
    print("  %-22s x100: %8.2f cuelgues/s instrumento; %6.2f %% de giros perdidos por ranura; CPU de reinicios %5.3f %%; artefacto audible cada %8.2f s"
          % (etq_p, lam, giros_perdidos*100, por_ranura*T_REINICIO*100, 1/mal))

h("4. EL MARGEN DE 102x: POR DONDE SE ROMPE DE VERDAD")
T_REC = 490e-6
print("Margen de la spec 3: %.0fx (%.0f ms / %.0f us)" % (T_WDG_MODULO/T_REC, T_WDG_MODULO*1e3, T_REC*1e6))
t_intento = 220e-6 + T_REINICIO
n_racha = math.ceil(T_WDG_MODULO / t_intento)
ventanas_h = ARMADOS_INSTR * 3600 / n_racha
p_rotura = math.exp(math.log(1/ventanas_h)/n_racha)
print("a) cuelgues INDEPENDIENTES: cada intento consume %.0f us -> %d intentos fallidos SEGUIDOS para que el modulo suelte"
      % (t_intento*1e6, n_racha))
print("   para UN disparo del watchdog del modulo por hora hace falta p = %.3f por armado" % p_rotura)
print("   -> el margen NO se rompe por tasa: aguanta hasta p = %.2f, %.0fx por encima del peor p del hilo"
      % (p_rotura, p_rotura/2e-5))
print("b) cuelgue de FASE BLOQUEADA: D4 termina en SPE=0 y el siguiente armado repite")
print("   SPE=1 -> EOTC -> EOTIE -> CSTART identico. Si la carrera es de fase y la fase esta")
print("   enganchada al arbol de reloj, p=1 durante T:")
print("     reinicios a %.0f/s = %.0f %% de un nucleo por ranura" % (F_LAZO, F_LAZO*T_REINICIO*100))
print("     'inestable' sube a los %.2f ms (10 plazos en 1 s) y D7.3 dice que NO es accion" % (10/F_LAZO*1e3))
print("     el modulo suelta a los %.0f ms; el sello de vitalidad de D5.4 se escribe AL ARMAR" % (T_WDG_MODULO*1e3))
print("     -> ranura muda permanente, IWDG alimentado para siempre, marca levantada y nadie la mira")
print("c) espera SIN COTA (riesgo 6): Drop del Transfer de GPDMA = bucle sin cota, sincrono,")
print("   dentro del InterruptExecutor que comparten las SEIS tareas -> un canal trabado congela")
print("   las seis ranuras -> los seis modulos sueltan a los %.0f ms -> el IWDG reinicia el chip." % (T_WDG_MODULO*1e3))
print("   Silencio: >%.0f ms (watchdog) + %.1f ms (refresco de la cabecera D5) + arranque del N657 = HUECO (S-10)"
      % (T_WDG_MODULO*1e3, 7.9))

h("5. CORRUPCION: lo DETECTADO pesa mas que lo no detectado")
lam_c = 2.0/60 * RANURAS
print("Tasa del hilo: 2/min por enlace -> %.3f tramas corruptas/s en el instrumento" % lam_c)
for etq_d, pev in P_EVENTO_GIRO.items():
    mal = lam_c * pev * F_AUDIBLE
    print("  DETECTADA (CRC la caza, R-C2 la rechaza entera) | %-22s -> artefacto audible cada %8.1f s = %6.1f min"
          % (etq_d, 1/mal, 1/mal/60))
p_no_det = 2.0**-16
print("  NO DETECTADA: CRC-16/CCITT-FALSE, P(pasar) <= 2^-16 = %.2e (cota floja: el modo del hilo" % p_no_det)
print("    desplaza bits y acorta la trama, y R-C1 la rechaza por cuenta de bytes ANTES del CRC)")
print("    -> %.2e tramas malas aceptadas/s = una cada %.0f h de instrumento encendido" % (lam_c*p_no_det, 1/(lam_c*p_no_det)/3600))

h("6. EL ESCLAVO: 6 de los 12 extremos de SPI no tienen recuperacion")
print("Los dos extremos del J2 son N657 (spec 2). El papel firmado cubre el MAESTRO (sujeto, 0).")
print("La limpieza del esclavo es una fila 'pendiente' del mapa de enmiendas (10).")
for etq, p in P_RANGO.items():
    lam_inst = p * F_LAZO
    print("  %-22s: un cuelgue por instancia esclava cada %9.1f s = %7.1f min -> una voz muerta hasta el reset"
          % (etq, 1/lam_inst, 1/lam_inst/60))

h("7. EL SOAK: potencia estadistica en LAS DOS UNIDADES")
print("Regla de tres (Poisson, cero eventos): lambda_max(C) = -ln(1-C)/T\n")
print("a) hipotesis POR TIEMPO (deriva, PLL, periodo de minutos a horas):")
print("%9s | %12s %12s | %s" % ("soak (h)", "lam<_95%", "lam<_99%", "P(ver >=1) si la verdad es 1/h"))
for T in (1, 3, 4.6, 12, 24, 72, 168):
    print("%9.1f | %8.3f /h %8.3f /h | %29.6f %%" % (T, 3.0/T, 4.605/T, (1-math.exp(-T))*100))
print("\nb) hipotesis POR ARMADO (la carrera de la errata vive en CSTART):")
objetivo_s = 1/(10*3600.0)
pev = P_EVENTO_GIRO["normal 20 ev/s/ranura"]
p_acept = objetivo_s / (ARMADOS_INSTR * 1 * pev * F_AUDIBLE)
print("   umbral derivado del bloque 3 (<=1 artefacto audible por 10 h de toque, pasaje normal,")
print("   1 trama perdida por cuelgue): p_aceptable = %.2e por armado = un cuelgue cada %.0f s en el instrumento"
      % (p_acept, 1/(p_acept*ARMADOS_INSTR)))
print("%10s %8s %14s | %10s %s" % ("soak", "ranuras", "armados", "p<_95%", "contra el umbral"))
for T_s, etq in ((60, "1 min"), (446, "7,4 min"), (2679, "45 min"), (3600, "1 h"), (3*3600, "3 h"), (24*3600, "24 h")):
    for nr in (1, 6):
        N = T_s * F_LAZO * nr
        p95 = 3.0/N
        v = "PASA" if p95 <= p_acept else ("corto %.0fx" % (p95/p_acept))
        print("%10s %8d %14.0f | %10.2e %s" % (etq, nr, N, p95, v))
print("\n   para probar p <= %.1e al 95 %%: %.0f armados = %.0f min en UNA ranura, %.1f min en seis"
      % (p_acept, 3/p_acept, 3/p_acept/F_LAZO/60, 3/p_acept/ARMADOS_INSTR/60))
print("   el soak de 24 h de R-MJ8 en una ranura son %.3g armados: p < %.1e al 95 %%, %.0fx por debajo del umbral"
      % (24*3600*F_LAZO, 3/(24*3600*F_LAZO), p_acept/(3/(24*3600*F_LAZO))))

h("8. CONTROL POSITIVO: potencia de reproducir el bug CONOCIDO")
print("Sin reproducir el cuelgue en la config mala, un soak verde no distingue 'no nos afecta'")
print("de 'el arnes no lo detecta' ni de 'el firmware no corria'.")
for T_h in (0.25, 0.5, 1, 2, 4):
    fila = "  control de %4.2f h:" % T_h
    for intervalo, etq in ((900, "900 s"), (7200, "120 min")):
        fila += "  P(ver >=1 | %s) = %6.2f %%" % (etq, (1-math.exp(-T_h*3600/intervalo))*100)
    print(fila)

h("9. BARRIDO DE LA ERRATA: cuanto cuesta dirimir la hipotesis del brief 3.2")
print("Variable: retardo D entre SPE=1 (anclado con read-back de CR1) y CSTART, en ciclos de SCK.")
print("Puntos: D en {0, 1/4, 1/2, 1, 2, 4, 8} x T_SCK, en la config mala (100 kHz, TSIZE=0, CS por GPIO)")
print("y en la nuestra (10 MHz y 34,5 MHz, TSIZE>0, NSS hw, DMA). 7 puntos x 3 relojes = 21 celdas.")
for p_malo in (2e-5, 2.2e-7):
    N_punto = 3/p_malo
    N_fijo = 3/(p_malo/10)
    print("  si p(D=0) = %.1e: %.0f armados por celda para 3 cuelgues esperados = %.1f s a 8 kHz;"
          % (p_malo, N_punto, N_punto/F_LAZO))
    print("     y %.0f armados en el brazo con retardo para acreditar una mejora de 10x al 95 %% = %.1f min"
          % (N_fijo, N_fijo/F_LAZO/60))
print("  coste total del barrido con el p suave: %.1f h de DK; con el p malo: %.1f min"
      % (21*(3/(2.2e-8))/F_LAZO/3600, 21*(3/2e-5)/F_LAZO/60))

assert 6/200e6 < 1/F_PISO
assert abs(T_WDG_MODULO/T_REC - 102) < 2
assert 3/p_acept/ARMADOS_INSTR < 3600
print("\n[autocomprobaciones OK]")

h("10. LA BIFURCACION DEL RM: p.3492 contra p.3490, cuantificada")
print("Lectura A (p.3492 literal: 'EOT is set ... when SPI is re-enabled'):")
print("   el evento EOT lo levanta el propio SPE=1 de D2 -> CSTART llega 3 escrituras APB despues")
print("   = 15-60 ns. Ventana de la errata a 10 MHz = 100 ns -> DENTRO en cada armado, siempre.")
print("Lectura B (el EOT solo lo levanta la terminacion de TSIZE datos):")
print("   el ultimo EOT fue al final de la trama del giro anterior. Con el SPI apagado en medio,")
t_prev_eot = T_GIRO - 20e-6
print("   el hueco entre ese EOT y el CSTART siguiente es ~%.0f us = %.0fx la ventana a 10 MHz y %.0fx a 34,5 MHz"
      % (t_prev_eot*1e6, t_prev_eot/(1/F_PISO), t_prev_eot/(1/F_D8)))
print("   -> bajo la lectura B el diseno firmado cumple la solucion 2 con %.0fx de holgura sin tocar nada."
      % (t_prev_eot/(1/F_PISO)))
print("La medida que dirime: armar NADA, escribir SPE=1, leer SR.EOT. Un acceso de lectura.")
print("   EOT=1 -> la hipotesis del brief 3.2 esta viva y TODO armado cae dentro de la ventana al piso.")
print("   EOT=0 -> la errata 2.14.2 no es el mecanismo de #5607 en nuestra config, y D2 ya la cubre.")

h("11. POTENCIA DE LOS CRITERIOS DE CIERRE QUE LA SPEC YA FIRMO")
for N, etq, fuente in ((1e5, "cien mil transferencias", "spec 9, riesgo 5"),
                       (24*3600*F_LAZO, "24 h a 8 kHz en un enlace", "spec 9 riesgo 1 / R-MJ8")):
    p95 = 3.0/N
    peor = 2e-5
    print("  %-26s (%s): %.3g armados -> p < %.1e al 95 %%" % (etq, fuente, N, p95))
    print("     %s el peor p del hilo (%.1e): %s" %
          ("excluye" if p95 < peor else "NO excluye ni", peor,
           "criterio con poder" if p95 < peor else "criterio sin poder discriminante"))
    print("     contra el umbral audible %.1e: %s" % (4.21e-7, "PASA" if p95 <= 4.21e-7 else "corto %.0fx" % (p95/4.21e-7)))
print("  tiempo de los cien mil armados a 8 kHz: %.1f s" % (1e5/F_LAZO))
