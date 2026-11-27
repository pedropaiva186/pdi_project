#!/usr/bin/env python3
"""Execução em um comando para a apresentação: build do frontend + Uvicorn.

Uso::

    python run.py [--host 127.0.0.1] [--port 8000] [--dev] [--rebuild]
                  [--no-build] [--no-browser]

O script usa apenas a biblioteca padrão (mais o Uvicorn, já instalado com o
backend): confere a versão do Python e as dependências, compila ``frontend/dist``
quando necessário e sobe o servidor servindo a API e o frontend no mesmo endereço.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
DIST_INDEX = FRONTEND_DIR / "dist" / "index.html"
MIN_PYTHON = (3, 11)

#: módulo importável -> nome do pacote no ``requirements.txt``
REQUIRED_MODULES: dict[str, str] = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "numpy": "numpy",
    "PIL": "Pillow",
    "multipart": "python-multipart",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Lê os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Compila o frontend (se preciso) e sobe o Processador de Imagens."
    )
    parser.add_argument("--host", default="127.0.0.1", help="endereço do servidor")
    parser.add_argument("--port", type=int, default=8000, help="porta do servidor")
    parser.add_argument("--dev", action="store_true", help="Uvicorn com --reload")
    parser.add_argument(
        "--rebuild", action="store_true", help="força o rebuild do frontend"
    )
    parser.add_argument(
        "--no-build", action="store_true", help="não compila o frontend"
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="não abre o navegador"
    )
    return parser.parse_args(argv)


def check_python() -> bool:
    """Confere se a versão do interpretador é compatível."""
    if sys.version_info >= MIN_PYTHON:
        return True
    wanted = ".".join(str(part) for part in MIN_PYTHON)
    print(
        f"Erro: Python {wanted}+ é necessário (versão atual: "
        f"{sys.version_info.major}.{sys.version_info.minor}).",
        file=sys.stderr,
    )
    return False


def missing_dependencies() -> list[str]:
    """Devolve os pacotes obrigatórios que não podem ser importados."""
    missing: list[str] = []
    for module, package in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    return missing


def build_frontend(rebuild: bool) -> None:
    """Compila ``frontend/dist`` quando necessário, sem impedir a subida da API."""
    if not FRONTEND_DIR.exists() or not (FRONTEND_DIR / "package.json").exists():
        print("Aviso: frontend/ não encontrado; subindo só a API.")
        return
    if DIST_INDEX.exists() and not rebuild:
        return

    npm = shutil.which("npm")
    if npm is None:
        print("Aviso: npm não encontrado; subindo só a API.")
        return

    try:
        if not (FRONTEND_DIR / "node_modules").exists():
            print("Instalando dependências do frontend (npm install)...")
            subprocess.run([npm, "install"], cwd=FRONTEND_DIR, check=True)
        print("Compilando o frontend (npm run build)...")
        subprocess.run([npm, "run", "build"], cwd=FRONTEND_DIR, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Aviso: falha ao compilar o frontend ({exc}); subindo só a API.")


def open_browser_later(url: str, delay: float = 1.5) -> None:
    """Abre o navegador numa thread com atraso, depois de o servidor subir."""
    timer = threading.Timer(delay, webbrowser.open, args=(url,))
    timer.daemon = True
    timer.start()


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada do script."""
    args = parse_args(argv)

    if not check_python():
        return 1

    missing = missing_dependencies()
    if missing:
        print(
            "Erro: dependências ausentes: " + ", ".join(missing) + ".",
            file=sys.stderr,
        )
        print("Instale com: pip install -r backend/requirements.txt", file=sys.stderr)
        return 1

    if not args.no_build:
        build_frontend(rebuild=args.rebuild)

    url = f"http://{args.host}:{args.port}"
    print(f"Servidor em {url}")
    if not args.no_browser:
        open_browser_later(url)

    import uvicorn

    uvicorn.run(
        "app.main:app",
        app_dir=str(BACKEND_DIR),
        host=args.host,
        port=args.port,
        reload=args.dev,
        # Sem isto o reloader observa a raiz inteira (inclui frontend/node_modules).
        reload_dirs=[str(BACKEND_DIR)] if args.dev else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
