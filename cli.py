#!/usr/bin/env python3
"""
Aletheia CLI - python cli.py start [mode]
python cli.py status
python cli.py test
python cli.py reset
"""

import click
import os
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
    """Start Aletheia Kernel."""
    print(f"🧠 Starting Aletheia Kernel v1.0 in {mode} mode...")
    from core.bootstrap.system_init import init_system
    init_system(mode)
    print(f"API at http://{host}:{port}")
    print(f"Health: http://{host}:{port}/health")
    run(mode, host, port)

@cli.command()
def status():
    """System health status."""
    print("🧠 Aletheia Status:")
    print(system_health())

@cli.command()
def test():
    """Run system tests."""
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
def reset():
    """Reset memory database."""
    init_db()
    print("✅ Memory DB reset - tables recreated")

if __name__ == "__main__":
    cli()

