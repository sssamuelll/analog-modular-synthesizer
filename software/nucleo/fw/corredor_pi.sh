#!/usr/bin/env bash
# Corredor de corridas largas en la placa, para la Raspberry Pi (port de corredor.ps1,
# solo `-Fin resistencia`): lanza probe-rs, lo reengancha si se cae y para cuando
# aparece la fila de HORAS horas de resistencia_j2. Se lanza con systemd-run, asi no
# cuelga de la sesion ssh. Para pararlo a mano: crear el archivo PARAR en esta carpeta.
#
#   sudo systemd-run --unit=soak-NOMBRE --uid=$USER --gid=$USER \
#       ~/soak/corredor_pi.sh ELF NOMBRE HORAS [MAX_HORAS] [SILENCIO_MIN]
#   tail -f ~/soak/NOMBRE.corredor.log
#
# Un corte de luz lo mata (la placa no tiene flash: sin host no hay firmware), pero
# las filas ya impresas quedan en la tarjeta, una por hora.
set -u
export NO_COLOR=1 # sin escapes ANSI: la regex de las filas empieza en `[INFO ]`

if [ $# -lt 3 ]; then
    echo "uso: $0 ELF NOMBRE HORAS [MAX_HORAS] [SILENCIO_MIN]" >&2
    exit 2
fi
elf=$1 nombre=$2 horas=$3 max_horas=${4:-$(($3 + 4))} silencio_min=${5:-75}
dir=$(cd "$(dirname "$0")" && pwd)
bitacora="$dir/$nombre.corredor.log"
parar="$dir/PARAR"

anota() { printf '%s  %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" >>"$bitacora"; }

# Un solo corredor a la vez: la placa y la sonda son una.
exec 9>"$dir/.placa.lock"
if ! flock -n 9; then
    anota "corredor $$: ya hay otro vivo; no arranca"
    exit 1
fi
anota "corredor $$: inicio (resistencia, $horas h); elf $elf; tope $max_horas h"

# La mayor hora de resistencia vista en los logs de esta corrida, en `hora_max`.
# Anota cada fila nueva una vez. (Variable global y no `echo`: en un $(...) los
# vistos se perderian con el subshell.)
declare -A anotada
hora_max=-1
avance() {
    local linea h
    while IFS= read -r linea; do
        h=$(cut -d, -f6 <<<"$linea")
        [ "$h" -gt "$hora_max" ] && hora_max=$h
        if [ -z "${anotada[$h]:-}" ]; then
            anotada[$h]=1
            anota "fila: $linea"
        fi
    done < <(cat "$dir/${nombre}"_*.out 2>/dev/null |
        sed -n -E 's/^\[INFO \] ([0-9]+,SPI[0-9]+,[0-9]+,[a-z]+,[^,]*,[0-9]+,.*) \(resistencia[^)]*\)$/\1/p')
}

limite=$(($(date +%s) + max_horas * 3600))
modo=run
fallos=0
n=0
motivo=
ultimo_aviso=0
while :; do
    out=$(printf '%s/%s_%02d.out' "$dir" "$nombre" "$n")
    err=${out%.out}.err
    probe-rs "$modo" --chip STM32N657 "$elf" >"$out" 2>"$err" &
    pid=$!
    t0=$(date +%s)
    anota "intento $n: probe-rs $modo, pid $pid"
    while kill -0 "$pid" 2>/dev/null; do
        sleep 30
        if [ -e "$parar" ]; then motivo='archivo PARAR'; break; fi
        if [ "$(date +%s)" -gt "$limite" ]; then motivo='tope de horas'; break; fi
        avance
        if [ "$hora_max" -ge "$horas" ]; then
            sleep 60
            motivo='la corrida cumplio su condicion'
            break
        fi
        ahora=$(date +%s)
        mod=$(stat -c %Y "$out" 2>/dev/null || echo "$ahora")
        if [ $((ahora - mod)) -gt $((silencio_min * 60)) ] && [ $((ahora - ultimo_aviso)) -gt 900 ]; then
            ultimo_aviso=$ahora
            anota "SILENCIO: el log de este intento no crece desde $(date -d "@$mod" +%H:%M); probe-rs sigue vivo"
        fi
    done
    if [ -n "$motivo" ]; then
        kill "$pid" 2>/dev/null
        wait "$pid" 2>/dev/null
        anota "fin: $motivo"
        break
    fi
    wait "$pid"
    rc=$?
    dur=$(($(date +%s) - t0))
    anota "intento $n: probe-rs salio con $rc tras $dur s: $(tail -n 3 "$err" | tr '\n' '|')"
    if grep -q -E 'panicked|HardFault|Breakpoint' "$out" "$err"; then
        anota 'fin: el firmware se paro (panic, HardFault o bkpt); no se reengancha'
        break
    fi
    if [ "$dur" -lt 120 ]; then fallos=$((fallos + 1)); else fallos=0; fi
    if [ "$fallos" -ge 3 ]; then
        modo=run
        fallos=0
        anota 'tres reenganches seguidos fallaron: se vuelve a cargar el firmware (la corrida empieza de nuevo)'
    else
        modo=attach
    fi
    n=$((n + 1))
    sleep 15
done
anota "corredor $$: termina"
