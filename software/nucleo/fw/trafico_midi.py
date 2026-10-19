"""Tráfico MIDI hacia el cerebro por USB, para medir lo que el USB le impone al tic (#443).

    python trafico_midi.py [mensajes_por_s] [segundos] [nombre]

Espera a que Windows enumere el puerto MIDI cuyo nombre contiene `nombre` (por defecto «SAM17»)
y le manda notas encendidas y apagadas al ritmo pedido, con la API MIDI de Windows (`winmm`),
sin nada que instalar. Al acabar dice cuántos mensajes mandó y a qué ritmo de verdad. Se corre
mientras `carga_j2 --features con-usb` mide.
"""
import ctypes
import sys
import time
from ctypes import wintypes

winmm = ctypes.WinDLL("winmm")


class MIDIOUTCAPSW(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * 32),
        ("wTechnology", wintypes.WORD),
        ("wVoices", wintypes.WORD),
        ("wNotes", wintypes.WORD),
        ("wChannelMask", wintypes.WORD),
        ("dwSupport", wintypes.DWORD),
    ]


def busca(nombre, espera_s):
    fin = time.time() + espera_s
    while time.time() < fin:
        for i in range(winmm.midiOutGetNumDevs()):
            caps = MIDIOUTCAPSW()
            winmm.midiOutGetDevCapsW(ctypes.c_size_t(i), ctypes.byref(caps), ctypes.sizeof(caps))
            if nombre.lower() in caps.szPname.lower():
                return i, caps.szPname
        time.sleep(0.25)
    return None, None


def main():
    por_s = float(sys.argv[1]) if len(sys.argv) > 1 else 1000.0
    segundos = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    nombre = sys.argv[3] if len(sys.argv) > 3 else "SAM17"
    i, puerto = busca(nombre, 120)
    if i is None:
        print(f"trafico_midi: ningún puerto MIDI con «{nombre}» en 120 s")
        return 1
    h = wintypes.HANDLE()
    r = winmm.midiOutOpen(ctypes.byref(h), wintypes.UINT(i), 0, 0, 0)
    if r != 0:
        print(f"trafico_midi: midiOutOpen({puerto}) dio {r}")
        return 1
    print(f"trafico_midi: {puerto}, {por_s:.0f} mensajes/s durante {segundos:.0f} s", flush=True)
    paso = 1.0 / por_s
    t0 = time.perf_counter()
    siguiente, n, fallos, aviso = t0, 0, 0, t0 + 5
    while time.perf_counter() - t0 < segundos:
        # Cuando el banco acaba, el USB deja de contestar y `midiOutShortMsg` se queda colgado:
        # la cuenta sale cada 5 s para que quede aunque nunca se llegue al final.
        if time.perf_counter() >= aviso:
            print(f"trafico_midi: {n} mensajes en {aviso - t0:.0f} s, {fallos} fallidos", flush=True)
            aviso += 5
        nota = 36 + (n // 2) % 48
        msg = (0x90 if n % 2 == 0 else 0x80) | (nota << 8) | (100 << 16)
        if winmm.midiOutShortMsg(h, wintypes.DWORD(msg)) != 0:
            fallos += 1
        n += 1
        siguiente += paso
        while time.perf_counter() < siguiente:
            pass
    dur = time.perf_counter() - t0
    winmm.midiOutReset(h)
    winmm.midiOutClose(h)
    print(f"trafico_midi: {n} mensajes en {dur:.1f} s ({n / dur:.0f}/s), {fallos} fallidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
