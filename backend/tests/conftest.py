"""Fixtures compartilhadas: cliente de teste, PNGs em memória e handlers falsos."""

from __future__ import annotations

import io
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.catalog import Catalog, load_catalog
from app.config import CATALOG_PATH
from app.main import create_app
from app.processing.registry import PROCESS_HANDLERS
from app.processing.types import OutputImage, ProcessResult

PngFactory = Callable[..., bytes]
ClientFactory = Callable[..., TestClient]


def _save(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _save_as(image: Image.Image, fmt: str) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture(scope="session")
def catalog() -> Catalog:
    """Catálogo real (``shared/processes.json``)."""
    return load_catalog(CATALOG_PATH)


@pytest.fixture
def make_png() -> PngFactory:
    """Fábrica de PNGs em memória.

    ``make_png(mode, size, color)`` cobre os modos simples. Para ``P``, use
    ``palette`` (768 inteiros) e ``data`` (índices dos pixels).
    """

    def _make_png(
        mode: str = "L",
        size: tuple[int, int] = (16, 12),
        color: Any = None,
        palette: list[int] | None = None,
        data: list[int] | None = None,
        fmt: str = "PNG",
    ) -> bytes:
        if mode == "P":
            image = Image.new("P", size, 0)
            if palette is not None:
                image.putpalette(palette)
            if data is not None:
                image.putdata(data)
        else:
            image = Image.new(mode, size, color)
        return _save(image) if fmt == "PNG" else _save_as(image, fmt)

    return _make_png


@pytest.fixture
def make_handlers() -> Callable[..., dict[str, Any]]:
    """Devolve o registro real com handlers sobrescritos para o teste."""

    def _make_handlers(**overrides: Callable[..., ProcessResult]) -> dict[str, Any]:
        handlers = dict(PROCESS_HANDLERS)
        handlers.update(overrides)
        return handlers

    return _make_handlers


@pytest.fixture
def no_frontend_dist(tmp_path: Path) -> Path:
    """Caminho de ``frontend/dist`` inexistente, para o app não servir a interface real."""
    return tmp_path / "nao_existe"


@pytest.fixture
def client(no_frontend_dist: Path) -> Iterator[TestClient]:
    """Cliente com o app real (stubs), sem frontend, e o lifespan executado."""
    with TestClient(create_app(frontend_dist=no_frontend_dist)) as test_client:
        yield test_client


@pytest.fixture
def fake_client(no_frontend_dist: Path) -> Iterator[ClientFactory]:
    """Fábrica de clientes com handlers falsos injetados no app (sem frontend)."""
    clients: list[TestClient] = []

    def _factory(**overrides: Callable[..., ProcessResult]) -> TestClient:
        handlers = dict(PROCESS_HANDLERS)
        handlers.update(overrides)
        test_client = TestClient(
            create_app(frontend_dist=no_frontend_dist, handlers=handlers)
        )
        test_client.__enter__()
        clients.append(test_client)
        return test_client

    yield _factory
    for test_client in clients:
        test_client.__exit__(None, None, None)


@pytest.fixture
def make_result() -> Callable[..., ProcessResult]:
    """Fábrica de ``ProcessResult`` válido para os testes do runner."""

    def _make_result(
        data: np.ndarray | None = None,
        *,
        outputs: list[OutputImage] | None = None,
        histograms: list[Any] | None = None,
        metrics: list[Any] | None = None,
    ) -> ProcessResult:
        if outputs is None:
            array = np.zeros((8, 8), dtype=np.uint8) if data is None else data
            outputs = [OutputImage(id="result", label="Resultado", data=array)]
        return ProcessResult(
            outputs=outputs,
            histograms=histograms or [],
            metrics=metrics or [],
        )

    return _make_result


@pytest.fixture
def dist_dir(tmp_path: Path) -> Path:
    """Diretório de build falso do frontend."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        "<!doctype html><html><body><div id=\"root\">frontend-fake</div></body></html>",
        encoding="utf-8",
    )
    return dist
