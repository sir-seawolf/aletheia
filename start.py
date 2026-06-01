"""
Aletheia — single-command launcher.

Usage:
  python start.py              # web mode, auto-detect everything
  python start.py --voice      # terminal voice session
  python start.py --demo       # mock LLM (no Ollama needed)
  python start.py --reset      # wipe DB and restart fresh
  python start.py --status     # show system status, don't start
  python start.py --stop       # kill all Aletheia processes

All flags can be combined:  python start.py --demo --reset
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Windows cp1252 terminals can't print box-drawing chars; force utf-8 output.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).parent
os.chdir(ROOT)

# ── helpers ────────────────────────────────────────────────────────────────

def _c(text: str, code: str) -> str:
    """ANSI color."""
    codes = {"green": "32", "red": "31", "yellow": "33", "cyan": "36", "bold": "1", "dim": "2"}
    return f"\033[{codes.get(code,'0')}m{text}\033[0m"


def _print(icon: str, msg: str, color: str = ""):
    print(f"  {icon}  {_c(msg, color) if color else msg}")


def _ok(msg):   _print("✓", msg, "green")
def _warn(msg): _print("!", msg, "yellow")
def _err(msg):  _print("✗", msg, "red")
def _info(msg): _print("·", msg, "dim")


def _check_ollama() -> bool:
    try:
        import requests
        return requests.get("http://localhost:11434", timeout=1).status_code == 200
    except Exception:
        return False


def _kill_ports(*ports: int):
    for port in ports:
        try:
            result = subprocess.run(
                f'netstat -aon | findstr ":{port} "',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if parts:
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) > 4:
                        subprocess.run(f"taskkill /f /pid {pid}", shell=True,
                                       capture_output=True)
        except Exception:
            pass


def _find_free_port(start: int, max_attempts: int = 10) -> int:
    import socket
    for port in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No hay puertos libres entre {start} y {start + max_attempts - 1}")


_PORTS_FILE = ROOT / ".running-ports"


def _save_ports(api_port: int, ui_port: int) -> None:
    _PORTS_FILE.write_text(f"{api_port}\n{ui_port}")


def _load_ports() -> tuple[int, int]:
    try:
        if _PORTS_FILE.exists():
            parts = _PORTS_FILE.read_text().strip().splitlines()
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return 8000, 3000


def _get_installed_packages() -> set:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=freeze"],
        capture_output=True, text=True
    )
    return {line.split("==")[0].lower() for line in result.stdout.splitlines()}


# ── steps ──────────────────────────────────────────────────────────────────

def step_deps():
    marker = ROOT / ".deps-ok"
    req    = ROOT / "requirements.txt"
    if not req.exists():
        _warn("requirements.txt no encontrado, saltando instalación")
        return

    # Only reinstall if requirements.txt is newer than the marker
    if marker.exists() and marker.stat().st_mtime >= req.stat().st_mtime:
        _ok("Dependencias OK (sin cambios)")
        return

    _info("Instalando dependencias Python…")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req), "-q"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        _err(f"pip install falló:\n{r.stderr[-400:]}")
        sys.exit(1)
    marker.touch()
    _ok("Dependencias instaladas")


def step_db(reset: bool):
    if reset:
        _info("Reiniciando base de datos…")
        subprocess.run([sys.executable, "cli.py", "reset"], capture_output=True)
        _ok("Base de datos reiniciada")
    else:
        _ok("Base de datos OK")


def step_ollama(demo: bool) -> str:
    if demo:
        _warn("Modo DEMO — usando LLM mock (respuestas simuladas)")
        return "DEV"
    if _check_ollama():
        _ok("Ollama respondiendo")
        return "PROD"
    else:
        _warn("Ollama no responde — arrancando en modo mock")
        _info("Para LLM real: abre otra terminal y ejecuta 'ollama serve'")
        return "DEV"


def _write_env_local(api_port: int) -> None:
    """Write REACT_APP_API_URL to aletheia-ui/.env.local so CRA picks it up."""
    env_local = ROOT / "aletheia-ui" / ".env.local"
    env_local.write_text(
        f"REACT_APP_API_URL=http://127.0.0.1:{api_port}\n"
        f"BROWSER=none\n"
    )
    _ok(f"UI apuntará a API en puerto {api_port}")


def step_ui_deps():
    node_modules = ROOT / "aletheia-ui" / "node_modules"
    if node_modules.exists():
        _ok("Node modules OK")
        return
    _info("Instalando dependencias npm (primera vez, ~1 min)…")
    r = subprocess.run(
        ["npm", "install"],
        cwd=ROOT / "aletheia-ui",
        capture_output=True, text=True, shell=True
    )
    if r.returncode != 0:
        _err("npm install falló. ¿Tienes Node.js instalado?")
        _info(r.stderr[-300:])
    else:
        _ok("Node modules instalados")


def start_web(mode: str):
    _info("Liberando puertos previos…")
    prev_api, prev_ui = _load_ports()
    _kill_ports(prev_api, prev_ui)
    time.sleep(0.5)

    try:
        api_port = _find_free_port(8000)
        ui_port  = _find_free_port(3000)
    except RuntimeError as e:
        _err(str(e))
        sys.exit(1)

    _save_ports(api_port, ui_port)
    _write_env_local(api_port)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["ALETHEIA_MODE"]    = mode

    # API server
    _info(f"Arrancando servidor API en puerto {api_port}…")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn",
         "core.bootstrap.runtime:app",
         "--host", "127.0.0.1",
         "--port", str(api_port),
         "--log-level", "warning"],
        env=env, creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )

    # UI dev server — PORT tells CRA which port to bind; .env sets BROWSER=none
    _info(f"Arrancando UI React en puerto {ui_port}…")
    subprocess.Popen(
        "npm start",
        cwd=ROOT / "aletheia-ui",
        shell=True,
        env={**env, "PORT": str(ui_port)},
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )

    # Wait for API
    _info("Esperando que el servidor API arranque…")
    for attempt in range(20):
        time.sleep(1)
        try:
            import requests
            r = requests.get(f"http://127.0.0.1:{api_port}/health", timeout=1)
            if r.status_code == 200:
                _ok(f"API lista en http://127.0.0.1:{api_port}")
                break
        except Exception:
            pass
        if attempt == 19:
            _warn("API tardando — puede que aún esté arrancando")

    # Wait for UI to be ready (React compile takes 15-30s)
    _info("Esperando que la UI compile…")
    import socket as _socket
    for attempt in range(45):
        time.sleep(2)
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            s.settimeout(1)
            ready = s.connect_ex(("127.0.0.1", ui_port)) == 0
            s.close()
            if ready:
                _ok(f"UI lista en http://localhost:{ui_port}")
                break
        except Exception:
            pass
        if attempt % 5 == 4:
            _info(f"UI aún compilando… ({(attempt + 1) * 2}s)")
    else:
        _warn("UI tardando más de lo esperado, abriendo de todas formas")

    _info("Abriendo navegador…")
    import webbrowser
    webbrowser.open(f"http://localhost:{ui_port}")

    print()
    print(_c("  Aletheia en marcha", "bold"))
    print(_c(f"  UI  → http://localhost:{ui_port}", "cyan"))
    print(_c(f"  API → http://127.0.0.1:{api_port}/docs", "dim"))
    print()
    _info("Cierra esta ventana para detener los servidores (o usa Ctrl+C)")
    print()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        _info("Deteniendo…")
        _kill_ports(api_port, ui_port)
        _PORTS_FILE.unlink(missing_ok=True)
        _ok("Servidores detenidos")


def start_telegram():
    config = ROOT / "PALACE" / "config" / "telegram.json"
    if not config.exists():
        _err("No se encontró PALACE/config/telegram.json")
        _info(
            'Crea el archivo con tu token de @BotFather:\n'
            '  {\n'
            '    "token": "TU_TOKEN",\n'
            '    "allowed_user_ids": [],\n'
            '    "admin_user_id": null\n'
            '  }'
        )
        return None
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    _info("Arrancando bot de Telegram en background…")
    proc = subprocess.Popen(
        [sys.executable, "tools/telegram_bot.py"],
        env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )
    _ok("Bot de Telegram arrancado")
    return proc


def start_voice(mode: str, always_on: bool = False):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["ALETHEIA_MODE"]    = mode
    print()
    if always_on:
        _ok("Iniciando sesión siempre-activa — di 'Aletheia' para activar (Ctrl+C para salir)")
    else:
        _ok("Iniciando sesión de voz (push-to-talk, Ctrl+C para salir)")
    print()
    cmd = [sys.executable, "cli.py", "voice"]
    if always_on:
        cmd.append("--always-on")
    subprocess.run(cmd, env=env)


def show_status():
    print()
    print(_c("  Estado del sistema", "bold"))
    print()

    # Python
    _ok(f"Python {sys.version.split()[0]}")

    # Ollama
    if _check_ollama():
        _ok("Ollama respondiendo en localhost:11434")
    else:
        _warn("Ollama no responde (ejecuta 'ollama serve')")

    # DB
    from memory.storage import MEMORY_DB_PATH
    if Path(MEMORY_DB_PATH).exists():
        size = Path(MEMORY_DB_PATH).stat().st_size // 1024
        _ok(f"Base de datos: {MEMORY_DB_PATH} ({size} KB)")
    else:
        _warn("Base de datos no inicializada")

    # Artifact store
    try:
        from core.docs.artifact_store import stats
        s = stats()
        _ok(f"Artefactos: {s['total_artifacts']} documentos almacenados")
    except Exception as e:
        _warn(f"Artifact store: {e}")

    # LLM provider
    try:
        from core.config.preferences import load as load_prefs
        prefs = load_prefs()
        provider = prefs["llm"]["provider"]
        has_key  = bool(prefs["llm"].get("api_key"))
        _ok(f"LLM provider: {provider}" + (" (API key configurada)" if has_key else ""))
    except Exception:
        pass

    # Gmail
    try:
        from core.docs.gmail import is_available, _TOKEN_PATH
        if is_available():
            token = "token OK" if _TOKEN_PATH.exists() else "pendiente autorizar"
            _ok(f"Gmail: credenciales configuradas ({token})")
        else:
            _warn("Gmail: sin credenciales")
    except Exception:
        pass

    # ── Cognitive layer (Aletheia 3.0) ──────────────────────────────────────
    print()
    print(_c("  Capa cognitiva 3.0", "bold"))
    print()

    try:
        import sqlite3 as _sq
        from memory.storage import MEMORY_DB_PATH
        with _sq.connect(MEMORY_DB_PATH) as _c2:
            n_traces = _c2.execute("SELECT COUNT(*) FROM cognitive_traces").fetchone()[0]
            n_shadow = _c2.execute(
                "SELECT COUNT(*) FROM cognitive_traces WHERE source='shadow_3.0'"
            ).fetchone()[0]
            n_degraded = _c2.execute(
                "SELECT COUNT(*) FROM strategy_degradation WHERE penalty_score >= 0.7"
            ).fetchone()[0]
            n_div = _c2.execute("SELECT COUNT(*) FROM trace_divergences").fetchone()[0]
            n_replay = _c2.execute("SELECT COUNT(*) FROM cognitive_replays").fetchone()[0]
        _ok(f"Trazas totales:     {n_traces}  (shadow: {n_shadow})")
        _ok(f"Divergencias:       {n_div}")
        _ok(f"Replays:            {n_replay}")
        if n_degraded > 0:
            _warn(f"Modos degradados:   {n_degraded}")
        else:
            _ok("Modos degradados:   0")
    except Exception as e:
        _warn(f"Tablas cognitivas no inicializadas ({e})")
        _info("Ejecuta el servidor una vez para crear las tablas automáticamente")

    try:
        from core.cognition.trace_learner import trace_learner
        modes, providers = trace_learner.compute_insights(force=True)
        qualified = sum(1 for m in modes if m.qualifies())
        _ok(f"Modos con insights: {len(modes)} ({qualified} calificados, mín. 5 muestras)")
        if providers:
            top = max(providers, key=lambda p: p.efficiency_score)
            _ok(f"Provider top:       {top.provider} (eff={top.efficiency_score:.2f})")
    except Exception:
        _info("TraceLearner sin datos aún (normal en primer arranque)")

    shadow_on = Path(ROOT / "PALACE" / "config" / "preferences.json").exists()
    try:
        import json as _json
        prefs = _json.loads((ROOT / "PALACE" / "config" / "preferences.json").read_text())
        shadow_on = prefs.get("shadow_mode", False)
    except Exception:
        shadow_on = False

    if shadow_on:
        _ok("Shadow mode:        ACTIVO (Aletheia 3.0 en paralelo)")
    else:
        _info("Shadow mode:        inactivo — actívalo con shadow_mode:true en preferences.json")

    print()


# ── entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Aletheia launcher",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--voice",     action="store_true", help="Sesión de voz en terminal")
    parser.add_argument("--always-on", action="store_true", dest="always_on",
                        help="Escucha continua — di 'Aletheia' para activar (requiere --voice)")
    parser.add_argument("--demo",      action="store_true", help="Modo demo (LLM mock, sin Ollama)")
    parser.add_argument("--reset",     action="store_true", help="Reiniciar base de datos")
    parser.add_argument("--status",    action="store_true", help="Mostrar estado y salir")
    parser.add_argument("--stop",      action="store_true", help="Matar servidores en puertos 8000/3000")
    parser.add_argument("--telegram",        action="store_true", help="Arrancar bot de Telegram junto al servidor web")
    parser.add_argument("--train-wake-word", action="store_true", dest="train_wake_word",
                        help="Entrenar modelo personalizado de wake word 'Aletheia' (openWakeWord)")
    args = parser.parse_args()

    print()
    print(_c("  ╔══════════════════════════════╗", "bold"))
    print(_c("  ║       ALETHEIA  v3.0         ║", "bold"))
    print(_c("  ╚══════════════════════════════╝", "bold"))
    print()

    if args.stop:
        _info("Deteniendo servidores…")
        api_port, ui_port = _load_ports()
        _kill_ports(api_port, ui_port)
        _PORTS_FILE.unlink(missing_ok=True)
        _ok(f"Puertos {api_port} y {ui_port} liberados")
        return

    if args.status:
        show_status()
        return

    if args.train_wake_word:
        _info("Entrenando wake word personalizado…")
        try:
            from core.voice.wake_trainer import train
            success = train(verbose=True)
            if not success:
                _warn("El modelo no se generó automáticamente (ver instrucciones arriba).")
        except Exception as exc:
            _err(f"Error durante el entrenamiento: {exc}")
        return

    # Standard startup sequence
    step_deps()
    step_db(args.reset)
    mode = step_ollama(args.demo)

    if args.voice:
        start_voice(mode, always_on=args.always_on)
    else:
        step_ui_deps()
        if args.telegram:
            start_telegram()
        start_web(mode)


if __name__ == "__main__":
    main()
