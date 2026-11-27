"""Testes do runner: validação da saída e formato completo da resposta."""

from __future__ import annotations

import numpy as np
import pytest

from app.core.errors import AppError
from app.processing.types import Histogram, Metric, OutputImage, ProcessResult
from app.services.runner import run_process

SIZE = (4, 3)


def test_success_builds_full_payload(catalog, make_handlers, make_png) -> None:
    captured: dict[str, object] = {}

    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        captured["params"] = params
        captured["shape"] = image.shape
        return ProcessResult(
            outputs=[
                OutputImage(
                    id="result",
                    label="Principal",
                    data=np.zeros(image.shape, dtype=np.uint8),
                ),
                OutputImage(
                    id="laplacian",
                    label="Auxiliar",
                    data=np.full(image.shape, 7, dtype=np.uint8),
                    role="aux",
                ),
            ],
            histograms=[Histogram(id="h", label="Histograma", values=[1] * 256)],
            metrics=[Metric(label="Média", value=1.5, unit="nível")],
        )

    handlers = make_handlers(threshold=handler)
    payload = run_process(
        catalog, handlers, "threshold", make_png("L", SIZE, 10), '{"k": 100}'
    )

    assert payload["process_id"] == "threshold"
    assert payload["params"] == {"k": 100}
    assert payload["input"] == {"mode": "gray", "width": SIZE[0], "height": SIZE[1]}
    assert [output["id"] for output in payload["outputs"]] == ["result", "laplacian"]
    assert [output["role"] for output in payload["outputs"]] == ["main", "aux"]
    assert payload["outputs"][0]["mode"] == "gray"
    assert payload["outputs"][0]["width"] == SIZE[0]
    assert payload["outputs"][0]["height"] == SIZE[1]
    assert payload["outputs"][0]["image"].startswith("data:image/png;base64,")
    assert payload["histograms"][0]["values"] == [1] * 256
    assert payload["histograms"][0]["channel"] == "gray"
    assert payload["metrics"][0] == {"label": "Média", "value": 1.5, "unit": "nível"}
    assert payload["metrics"][-1]["label"] == "Tempo de processamento"
    assert payload["metrics"][-1]["unit"] == "ms"
    assert isinstance(payload["metrics"][-1]["value"], float)
    assert payload["elapsed_ms"] == payload["metrics"][-1]["value"]
    assert captured["params"] == {"k": 100}
    assert captured["shape"] == (SIZE[1], SIZE[0])


def test_main_outputs_come_before_aux(catalog, make_handlers, make_png) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        return ProcessResult(
            outputs=[
                OutputImage(id="aux1", label="Aux", data=image, role="aux"),
                OutputImage(id="main1", label="Main", data=image),
                OutputImage(id="aux2", label="Aux 2", data=image, role="aux"),
                OutputImage(id="main2", label="Main 2", data=image),
            ]
        )

    payload = run_process(
        catalog,
        make_handlers(threshold=handler),
        "threshold",
        make_png("L", SIZE, 0),
        None,
    )
    assert [output["id"] for output in payload["outputs"]] == [
        "main1",
        "main2",
        "aux1",
        "aux2",
    ]


def test_numpy_scalars_are_converted(catalog, make_handlers, make_png) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        return ProcessResult(
            outputs=[OutputImage(id="result", label="R", data=image)],
            histograms=[
                Histogram(
                    id="h",
                    label="H",
                    values=np.zeros(256, dtype=np.int64).tolist(),
                )
            ],
            metrics=[Metric(label="Máximo", value=np.float64(255.0))],
        )

    payload = run_process(
        catalog, make_handlers(threshold=handler), "threshold", make_png("L", SIZE, 0), None
    )
    assert isinstance(payload["metrics"][0]["value"], float)
    assert all(isinstance(value, int) for value in payload["histograms"][0]["values"])


def _invalid_cases():
    image = np.zeros((3, 4), dtype=np.uint8)
    return {
        "not-a-process-result": lambda: "nope",
        "empty-outputs": lambda: ProcessResult(outputs=[]),
        "no-main": lambda: ProcessResult(
            outputs=[OutputImage(id="aux", label="Aux", data=image, role="aux")]
        ),
        "duplicated-ids": lambda: ProcessResult(
            outputs=[
                OutputImage(id="result", label="A", data=image),
                OutputImage(id="result", label="B", data=image),
            ]
        ),
        "invalid-role": lambda: ProcessResult(
            outputs=[OutputImage(id="result", label="A", data=image, role="other")]
        ),
        "not-an-array": lambda: ProcessResult(
            outputs=[OutputImage(id="result", label="A", data=[[0]])]
        ),
        "float64": lambda: ProcessResult(
            outputs=[
                OutputImage(id="result", label="A", data=image.astype(np.float64))
            ]
        ),
        "four-channels": lambda: ProcessResult(
            outputs=[
                OutputImage(id="result", label="A", data=np.zeros((3, 4, 4), np.uint8))
            ]
        ),
        "one-dimensional": lambda: ProcessResult(
            outputs=[OutputImage(id="result", label="A", data=np.zeros(4, np.uint8))]
        ),
        "histogram-255-values": lambda: ProcessResult(
            outputs=[OutputImage(id="result", label="A", data=image)],
            histograms=[Histogram(id="h", label="H", values=[0] * 255)],
        ),
        "histogram-negative": lambda: ProcessResult(
            outputs=[OutputImage(id="result", label="A", data=image)],
            histograms=[Histogram(id="h", label="H", values=[-1] + [0] * 255)],
        ),
        "histogram-bad-channel": lambda: ProcessResult(
            outputs=[OutputImage(id="result", label="A", data=image)],
            histograms=[
                Histogram(id="h", label="H", values=[0] * 256, channel="alpha")
            ],
        ),
        "metric-bad-type": lambda: ProcessResult(
            outputs=[OutputImage(id="result", label="A", data=image)],
            metrics=[Metric(label="M", value=[1, 2])],
        ),
    }


@pytest.mark.parametrize(
    "build",
    list(_invalid_cases().values()),
    ids=list(_invalid_cases().keys()),
)
def test_invalid_output_is_500(catalog, make_handlers, make_png, build) -> None:
    def handler(image: np.ndarray, params: dict):
        return build()

    with pytest.raises(AppError) as excinfo:
        run_process(
            catalog,
            make_handlers(threshold=handler),
            "threshold",
            make_png("L", SIZE, 0),
            None,
        )
    assert excinfo.value.code == "invalid_output"
    assert excinfo.value.status == 500


def test_processing_error_is_500(catalog, make_handlers, make_png) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        raise ValueError("boom")

    with pytest.raises(AppError) as excinfo:
        run_process(
            catalog,
            make_handlers(threshold=handler),
            "threshold",
            make_png("L", SIZE, 0),
            None,
        )
    error = excinfo.value
    assert error.code == "processing_error"
    assert error.status == 500
    assert "ValueError" in error.message
    assert "boom" in error.message


def test_not_implemented_is_501(catalog, make_handlers, make_png) -> None:
    def handler(image: np.ndarray, params: dict) -> ProcessResult:
        raise NotImplementedError

    with pytest.raises(AppError) as excinfo:
        run_process(
            catalog,
            make_handlers(threshold=handler),
            "threshold",
            make_png("L", SIZE, 0),
            None,
        )
    error = excinfo.value
    assert error.code == "not_implemented"
    assert error.status == 501
    assert "Limiarização" in error.message


def test_unknown_process_is_404(catalog, make_handlers, make_png) -> None:
    with pytest.raises(AppError) as excinfo:
        run_process(
            catalog,
            make_handlers(),
            "does_not_exist",
            make_png("L", SIZE, 0),
            None,
        )
    assert excinfo.value.code == "process_not_found"
    assert excinfo.value.status == 404


def test_unsupported_mode_is_422(catalog, make_handlers, make_png) -> None:
    with pytest.raises(AppError) as excinfo:
        run_process(
            catalog,
            make_handlers(),
            "histogram_equalization",
            make_png("RGB", SIZE, (1, 2, 3)),
            None,
        )
    error = excinfo.value
    assert error.code == "unsupported_mode"
    assert error.status == 422
    assert error.details == {"mode": "rgb", "allowed_modes": ["gray"]}


def test_invalid_params_are_422(catalog, make_handlers, make_png) -> None:
    with pytest.raises(AppError) as excinfo:
        run_process(
            catalog,
            make_handlers(),
            "threshold",
            make_png("L", SIZE, 0),
            '{"k": 999}',
        )
    error = excinfo.value
    assert error.code == "invalid_params"
    assert error.details["param"] == "k"


def test_invalid_image_is_400(catalog, make_handlers) -> None:
    with pytest.raises(AppError) as excinfo:
        run_process(catalog, make_handlers(), "threshold", b"not a png", None)
    assert excinfo.value.code == "invalid_image"
    assert excinfo.value.status == 400
