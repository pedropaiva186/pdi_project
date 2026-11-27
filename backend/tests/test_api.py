"""Testes dos endpoints HTTP (contrato de ``API.md``)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.processing.types import OutputImage, ProcessResult

SIZE = (16, 12)


def _error(response, status: int, code: str) -> dict:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error) == {"code", "message", "details"}
    assert error["code"] == code
    assert isinstance(error["message"], str) and error["message"]
    assert isinstance(error["details"], dict)
    return error


def _png(make_png, mode: str = "L", **kwargs) -> dict:
    return {"file": ("test.png", make_png(mode, SIZE, **kwargs), "image/png")}


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_processes_lists_all_stubs_as_not_implemented(client: TestClient) -> None:
    response = client.get("/api/processes")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert [category["id"] for category in body["categories"]] == [
        "color",
        "intensity",
        "spatial",
        "frequency",
        "noise",
    ]
    assert len(body["processes"]) == 19
    assert all(process["implemented"] is False for process in body["processes"])
    threshold = next(p for p in body["processes"] if p["id"] == "threshold")
    assert threshold["label"] == "Limiarização"
    assert threshold["params"][0]["id"] == "k"


def test_inspect_gray(client: TestClient, make_png) -> None:
    response = client.post("/api/images/inspect", files=_png(make_png))
    assert response.status_code == 200
    assert response.json() == {
        "mode": "gray",
        "width": SIZE[0],
        "height": SIZE[1],
        "source_mode": "L",
        "filename": "test.png",
    }


def test_inspect_rgb(client: TestClient, make_png) -> None:
    response = client.post(
        "/api/images/inspect", files=_png(make_png, "RGB", color=(1, 2, 3))
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "rgb"
    assert response.json()["source_mode"] == "RGB"


def test_inspect_without_file_is_400(client: TestClient) -> None:
    error = _error(client.post("/api/images/inspect"), 400, "invalid_image")
    assert error["message"] == "Nenhum arquivo foi enviado."


def test_inspect_non_png_is_400(client: TestClient, make_png) -> None:
    files = {"file": ("test.png", make_png("RGB", SIZE, fmt="JPEG"), "image/png")}
    error = _error(client.post("/api/images/inspect", files=files), 400, "invalid_image")
    assert "PNG" in error["message"]


def test_inspect_unsupported_png_is_400(client: TestClient, make_png) -> None:
    files = {"file": ("test.png", make_png("I;16", SIZE, 10), "image/png")}
    _error(client.post("/api/images/inspect", files=files), 400, "unsupported_image")


def test_process_unknown_id_is_404(client: TestClient, make_png) -> None:
    response = client.post("/api/process/does_not_exist", files=_png(make_png))
    _error(response, 404, "process_not_found")


def test_process_unsupported_mode_is_422(client: TestClient, make_png) -> None:
    files = _png(make_png, "RGB", color=(1, 2, 3))
    error = _error(
        client.post("/api/process/histogram_equalization", files=files),
        422,
        "unsupported_mode",
    )
    assert error["details"] == {"mode": "rgb", "allowed_modes": ["gray"]}


def test_process_invalid_params_is_422(client: TestClient, make_png) -> None:
    response = client.post(
        "/api/process/threshold",
        files=_png(make_png),
        data={"params": '{"k": 999}'},
    )
    error = _error(response, 422, "invalid_params")
    assert error["details"]["param"] == "k"


def test_process_malformed_params_is_422(client: TestClient, make_png) -> None:
    response = client.post(
        "/api/process/threshold",
        files=_png(make_png),
        data={"params": "{oops"},
    )
    _error(response, 422, "invalid_params")


def test_process_stub_is_501(client: TestClient, make_png) -> None:
    response = client.post(
        "/api/process/threshold",
        files=_png(make_png),
        data={"params": '{"k": 100}'},
    )
    error = _error(response, 501, "not_implemented")
    assert "Limiarização" in error["message"]


def test_process_without_file_is_400(client: TestClient) -> None:
    _error(client.post("/api/process/threshold"), 400, "invalid_image")


def test_process_with_oversized_upload_is_413(
    client: TestClient, make_png, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.uploads.MAX_UPLOAD_BYTES", 10)
    _error(
        client.post("/api/process/threshold", files=_png(make_png)),
        413,
        "image_too_large",
    )


def test_unknown_process_without_file_is_404_not_400(client: TestClient) -> None:
    # Ordem do §9: o processo é validado antes do arquivo.
    _error(client.post("/api/process/does_not_exist"), 404, "process_not_found")


def test_unknown_api_route_is_json_404(client: TestClient) -> None:
    error = _error(client.get("/api/xyz"), 404, "not_found")
    assert error["message"] == "Recurso não encontrado."


def test_wrong_method_on_api_route_is_405(client: TestClient) -> None:
    _error(client.post("/api/health"), 405, "method_not_allowed")


def test_frontend_missing_returns_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Frontend não compilado" in response.text


def test_frontend_dist_is_served(dist_dir: Path) -> None:
    with TestClient(create_app(frontend_dist=dist_dir)) as test_client:
        response = test_client.get("/")
        assert response.status_code == 200
        assert "frontend-fake" in response.text
        # /api continua devolvendo JSON, não o index.html.
        _error(test_client.get("/api/xyz"), 404, "not_found")


def test_openapi_is_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    assert "/api/processes" in paths
    assert "/api/images/inspect" in paths
    assert "/api/process/{process_id}" in paths


def test_process_success_with_fake_handler(fake_client: TestClient, make_png) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        return ProcessResult(
            outputs=[
                OutputImage(id="result", label="Imagem limiarizada", data=image),
                OutputImage(
                    id="extra", label="Auxiliar", data=image, role="aux"
                ),
            ],
            metrics=[],
        )

    test_client = fake_client(threshold=handler)
    files = _png(make_png)
    response = test_client.post(
        "/api/process/threshold", files=files, data={"params": '{"k": 42}'}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["process_id"] == "threshold"
    assert body["params"] == {"k": 42}
    assert body["input"] == {"mode": "gray", "width": SIZE[0], "height": SIZE[1]}
    assert [output["role"] for output in body["outputs"]] == ["main", "aux"]
    assert body["outputs"][0]["image"].startswith("data:image/png;base64,")
    assert body["metrics"][-1]["label"] == "Tempo de processamento"
    assert body["metrics"][-1]["unit"] == "ms"
    assert isinstance(body["elapsed_ms"], float)


def test_fake_handler_marks_process_as_implemented(
    fake_client: TestClient, make_png
) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        return ProcessResult(outputs=[OutputImage(id="result", label="R", data=image)])

    test_client = fake_client(threshold=handler)
    body = test_client.get("/api/processes").json()
    implemented = {process["id"]: process["implemented"] for process in body["processes"]}
    assert implemented["threshold"] is True
    assert sum(implemented.values()) == 1


def test_invalid_output_is_500_with_helpful_message(
    fake_client: TestClient, make_png
) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        return ProcessResult(
            outputs=[
                OutputImage(id="result", label="R", data=image.astype(np.float64))
            ]
        )

    test_client = fake_client(threshold=handler)
    error = _error(
        test_client.post("/api/process/threshold", files=_png(make_png)),
        500,
        "invalid_output",
    )
    assert "uint8" in error["message"]


def test_processing_error_is_500(fake_client: TestClient, make_png) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        raise ValueError("falhou de propósito")

    test_client = fake_client(threshold=handler)
    error = _error(
        test_client.post("/api/process/threshold", files=_png(make_png)),
        500,
        "processing_error",
    )
    assert "ValueError" in error["message"]


def test_request_validation_error_uses_single_format() -> None:
    from fastapi import FastAPI

    from app.core.errors import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/needs-int")
    def needs_int(value: int) -> dict:
        return {"value": value}

    with TestClient(app) as test_client:
        error = _error(
            test_client.get("/needs-int", params={"value": "abc"}),
            422,
            "invalid_params",
        )
    assert error["message"] == "Requisição inválida."
    assert error["details"]["errors"][0]["loc"] == ["query", "value"]
