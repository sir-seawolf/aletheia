"""Punto de entrada para ejecutar Aletheia."""

import uvicorn
from config import MODEL


def main():
    print(f"🧠 Aletheia iniciando...")
    print(f"   Modelo: {MODEL}")
    print(f"   API: http://127.0.0.1:8000")
    print(f"   Docs: http://127.0.0.1:8000/docs")
    print()

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()

