"""Punto de entrada para ejecutar Aletheia."""

import uvicorn
from config import MODEL


"""
Entry point - now uses CLI.
python run.py → python cli.py start
"""

from cli import cli
if __name__ == "__main__":
    cli()


