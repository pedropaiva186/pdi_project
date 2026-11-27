"""Fábrica do app FastAPI: catálogo, CORS, erros, rotas e frontend compilado."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.routing import Match, Route

from .api.routes import health, images, process, processes
from .config import CATALOG_PATH, CORS_ORIGINS, FRONTEND_DIST
from .core.catalog import load_catalog
from .core.errors import register_exception_handlers
from .logging_config import configure_logging
from .processing.registry import PROCESS_HANDLERS
from .services.implemented import check_handler_parity, detect_implemented

logger = logging.getLogger(__name__)

FRONTEND_MISSING_HTML = """<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Processador de Imagens — PDI</title></head>
<body style="font-family: system-ui, sans-serif; max-width: 40rem; margin: 4rem auto;">
  <h1>Frontend não compilado</h1>
  <p>Rode <code>npm run build</code> em <code>frontend/</code> ou use
     <code>python run.py</code>.</p>
  <p>A API está disponível em <a href="/docs">/docs</a>.</p>
</body>
</html>
"""

API_PREFIX = "/api"
API_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
API_ROUTERS: tuple[APIRouter, ...] = (
    health.router,
    processes.router,
    images.router,
    process.router,
)


def _api_route_table() -> list[Route]:
    """Rotas da API com o caminho completo (``/api/...``), para decidir 404 × 405.

    O ``include_router`` do FastAPI 0.165 não expõe o ``.path`` das rotas incluídas
    (são ``_IncludedRouter`` sem caminho), então a tabela é montada a partir dos
    routers de origem, aplicando o prefixo.
    """
    table: list[Route] = []
    for router in API_ROUTERS:
        for route in router.routes:
            if isinstance(route, APIRoute):
                table.append(
                    Route(
                        API_PREFIX + route.path,
                        route.endpoint,
                        methods=sorted(route.methods or ()),
                    )
                )
    return table


def create_app(
    catalog_path: Path = CATALOG_PATH,
    frontend_dist: Path = FRONTEND_DIST,
    handlers: dict[str, Any] | None = None,
) -> FastAPI:
    """Cria o app. ``handlers`` permite injetar handlers falsos nos testes."""
    configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        catalog = load_catalog(catalog_path)
        active_handlers = dict(PROCESS_HANDLERS if handlers is None else handlers)
        check_handler_parity(catalog, active_handlers)
        implemented = detect_implemented(catalog, active_handlers)
        app.state.catalog = catalog
        app.state.handlers = active_handlers
        app.state.implemented = implemented
        logger.info(
            "catalog loaded: %d processes, %d implemented",
            len(catalog.processes),
            sum(implemented.values()),
        )
        yield

    app = FastAPI(
        title="Processador de Imagens — PDI",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    for router in API_ROUTERS:
        app.include_router(router, prefix=API_PREFIX)

    api_table = _api_route_table()

    @app.api_route(
        f"{API_PREFIX}/{{path:path}}",
        methods=API_METHODS,
        include_in_schema=False,
    )
    def api_not_found(request: Request, path: str) -> None:
        """Garante JSON 404/405 em ``/api/*`` mesmo com o frontend montado em ``/``."""
        for route in api_table:
            match, _ = route.matches(request.scope)
            if match == Match.PARTIAL:
                raise HTTPException(status_code=405, detail="Método não permitido.")
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")

    frontend_index = Path(frontend_dist) / "index.html"
    if frontend_index.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(frontend_dist), html=True),
            name="frontend",
        )
    else:

        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        def frontend_missing() -> HTMLResponse:
            """Aviso quando o build do frontend ainda não existe."""
            return HTMLResponse(FRONTEND_MISSING_HTML)

    return app


app = create_app()
