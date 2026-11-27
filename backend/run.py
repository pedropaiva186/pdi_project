"""Servidor de desenvolvimento do backend (Uvicorn com ``--reload``).

Uso: ``python backend/run.py`` a partir da raiz do repositório.
"""

from __future__ import annotations

from pathlib import Path

import uvicorn


def main() -> None:
    """Sobe a API em ``http://127.0.0.1:8000`` recarregando ao salvar arquivos."""
    app_dir = Path(__file__).resolve().parent
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir=str(app_dir),
        reload_dirs=[str(app_dir)],
    )


if __name__ == "__main__":
    main()
