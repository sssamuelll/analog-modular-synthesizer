#!/usr/bin/env bash
# Puerta de la fase A del #250. SELLADA: el delegado no la toca.
#
# Dice verde cuando: los tests de `core` siguen enteros Y `fw/` enlaza de
# verdad para el STM32N657X0. No dice nada sobre arrancar en la placa: eso es
# la fase B, y necesita la Discovery del #231.
set -uo pipefail
cd "$(dirname "$0")"
fallo=0

echo "== 1/3  core: los tests del contrato (host) =="
salida=$(cargo test --manifest-path core/Cargo.toml 2>&1)
echo "$salida" | tail -5
verdes=$(echo "$salida" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | awk '{s+=$1} END {print s+0}')
verdes=${verdes:-0}
if ! echo "$salida" | grep -q "test result: ok"; then echo "ROJO: core no pasa"; fallo=1; fi
if [ "$verdes" -lt 232 ]; then echo "ROJO: $verdes tests verdes, se esperaban >= 232"; fallo=1; else echo "verde: $verdes tests"; fi

echo "== 2/3  fw: enlaza para thumbv8m.main-none-eabihf =="
# OJO: hay que ENTRAR en fw/. Cargo lee `.cargo/config.toml` desde el
# directorio de trabajo hacia arriba, NO desde el del manifiesto: con
# --manifest-path desde aqui el target sale el del host y la puerta miente.
if (cd fw && cargo build --release --locked 2>&1 | tail -15); then
  elf=fw/target/thumbv8m.main-none-eabihf/release/sam17-nucleo-fw
  if [ -f "$elf" ]; then echo "verde: ELF $(stat -c%s "$elf" 2>/dev/null || echo ?) bytes"; else echo "ROJO: no hay ELF"; fallo=1; fi
else
  echo "ROJO: fw no compila"; fallo=1
fi

echo "== 3/3  no queda RP2350 vivo en fw/ =="
# Solo codigo vivo: se quitan antes los comentarios de toml (#), de Rust (//)
# y de linker (*). Un comentario que cuenta de donde venimos no es un resto.
if grep -rn --include='*.rs' --include='*.toml' --include='*.x' -iE 'embassy[-_]rp|rp235|start_block|IMAGE_DEF' fw/Cargo.toml fw/.cargo/config.toml fw/memory.x fw/src fw/build.rs 2>/dev/null | grep -vE ':\s*(#|//|\*|/\*)' ; then
  echo "ROJO: quedan restos del RP2350 arriba"; fallo=1
else
  echo "verde: sin restos"
fi

[ $fallo -eq 0 ] && echo "== FASE A VERDE ==" || echo "== FASE A ROJA =="
exit $fallo
