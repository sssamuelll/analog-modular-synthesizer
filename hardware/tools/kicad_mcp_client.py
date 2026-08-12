"""Cliente MCP stdio minimo para hablar con un KiCAD-MCP-Server local.

No requiere un agente de Claude corriendo: lanza el server
(``node dist/index.js``) como subproceso y le habla el protocolo MCP por
stdin/stdout directamente. Pensado para que los scripts de
``build_schematic.py`` de cada modulo sean ejecutables por cualquiera con el
server instalado, sin depender de una sesion de Claude Code.

Requiere:
  - https://github.com/mixelpixx/KiCAD-MCP-Server clonado y compilado
    (``npm install && npm run build``).
  - Un venv de Python creado DESDE el Python que trae KiCad
    (``<kicad>/bin/python.exe -m venv --system-site-packages .venv``) con
    ``pip install -r requirements.txt`` — asi hereda ``pcbnew`` y evita el
    conflicto con el Python del sistema.

Rutas configurables por variable de entorno (con defaults razonables para
Windows + KiCad 10):
  KICAD_MCP_SERVER_DIST   ruta a dist/index.js del server
  KICAD_MCP_SERVER_VENV   ruta al python.exe del venv del server
  KICAD_PYTHONPATH        site-packages de KiCad (para pcbnew)
"""
from __future__ import annotations

import json
import os
import subprocess

DEFAULT_ROOT = os.path.expanduser(r"~\.claude\mcp-servers\kicad-mcp-server")
DIST = os.environ.get("KICAD_MCP_SERVER_DIST", os.path.join(DEFAULT_ROOT, "dist", "index.js"))
VENV_PY = os.environ.get(
    "KICAD_MCP_SERVER_VENV", os.path.join(DEFAULT_ROOT, ".venv", "Scripts", "python.exe")
)
KICAD_SITE_PACKAGES = os.environ.get(
    "KICAD_PYTHONPATH", r"C:\Program Files\KiCad\10.0\bin\Lib\site-packages"
)


class Client:
    """Cliente JSON-RPC 2.0 sobre stdio para un KiCAD-MCP-Server."""

    def __init__(self, server_dist: str = DIST, venv_python: str = VENV_PY) -> None:
        env = {
            **os.environ,
            "PYTHONPATH": KICAD_SITE_PACKAGES,
            "KICAD_PYTHON": venv_python,
            "LOG_LEVEL": "warn",
            "KICAD_AUTO_LAUNCH": "false",
            "NODE_ENV": "production",
        }
        self.p = subprocess.Popen(
            ["node", server_dist],
            cwd=os.path.dirname(server_dist) or ".",
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._id = 0
        self.req("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "sam17-build-script", "version": "0"},
        })
        self.notify("notifications/initialized")

    def _send(self, obj: dict) -> None:
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def req(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method,
                    "params": params or {}})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("el server cerro stdout")
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue  # linea de log, no es un mensaje JSON-RPC
            if msg.get("id") == self._id:
                return msg

    def call(self, tool: str, args: dict):
        """Invoca una tool MCP y devuelve su resultado ya des-envuelto.

        Si la tool devuelve JSON lo parsea; si devuelve texto plano lo deja
        como string (varias tools del server responden asi).
        """
        r = self.req("tools/call", {"name": tool, "arguments": args})
        if "error" in r:
            return {"_rpc_error": r["error"]}
        content = r.get("result", {}).get("content", [])
        out = []
        for c in content:
            t = c.get("text", "")
            try:
                out.append(json.loads(t))
            except (json.JSONDecodeError, TypeError):
                out.append(t)
        return out[0] if len(out) == 1 else out

    def close(self) -> None:
        self.p.terminate()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
