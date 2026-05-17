#!/usr/bin/env python3
"""
Aletheia CLI entry point.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: core.bootstrap.*, memory.storage, click
Last stable version: v1.1

Commands: start [mode], status, test, reset
"""

import click
import subprocess
from core.bootstrap.runtime import run
from core.bootstrap.healthcheck import system_health
from memory.storage import init_db

@click.group()
def cli():
    """Aletheia Kernel v1.0 CLI."""
    pass

@cli.command()
@click.option('--mode', default='DEV', help='Execution mode: DEV/TEST/PROD')
@click.option('--host', default='127.0.0.1')
@click.option('--port', default=8000, type=int)
def start(mode, host, port):
    """
    Start Aletheia Kernel server.

    Args:
        mode (str): Execution mode: DEV/TEST/PROD. Default: DEV
        host (str): Bind address. Default: 127.0.0.1
        port (int): Port number. Default: 8000

    Returns:
        None

    Raises:
        Exception: If system init fails
    """
    print(f"🧠 Starting Aletheia Kernel v1.0 in {mode} mode...")
    from core.bootstrap.system_init import init_system
    init_system(mode)
    print(f"API at http://{host}:{port}")
    print(f"Health: http://{host}:{port}/health")
    run(mode, host, port)

@cli.command()
def status():
    """
    Display current system health status.

    Args:
        None

    Returns:
        None

    Raises:
        None
    """
    print("🧠 Aletheia Status:")
    print(system_health())

@cli.command()
def test():
    """
    Run system integration tests.

    Args:
        None

    Returns:
        None

    Raises:
        click.ClickException: If pytest fails
    """
    result = subprocess.run(["python", "-m", "pytest", "tests/system/", "-v"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("✅ All system tests PASSED")
    else:
        print("❌ Some tests FAILED")
        print(result.stderr)
        raise click.ClickException("Tests failed")

@cli.command()
@click.option("--always-on", "always_on", is_flag=True, default=False,
              help="Continuous listening: say 'Aletheia' to activate (no ENTER needed)")
def voice(always_on: bool):
    """Start Aletheia voice session (offline, no internet needed)."""
    if always_on:
        from core.voice.session import run_voice_session_always_on
        run_voice_session_always_on()
    else:
        from core.voice.session import run_voice_session
        run_voice_session()


@cli.command()
def voices():
    """List available TTS voices on this system."""
    from core.voice.speaker import list_voices as _list
    available = _list()
    if not available:
        print("No se encontraron voces pyttsx3.")
    for name in available:
        print(f"  • {name}")


@cli.command()
def reset():
    """
    Reset and recreate memory database tables.

    Args:
        None

    Returns:
        None

    Raises:
        Exception: If DB init fails
    """

    init_db()
    print("✅ Memory DB reset - tables recreated")

if __name__ == "__main__":
    cli()

