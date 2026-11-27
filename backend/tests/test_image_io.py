"""Testes do I/O de PNG (normalização de modos e codificação em data URL)."""

from __future__ import annotations

import base64
import io

import numpy as np
import pytest
from PIL import Image

from app.core.errors import AppError
from app.services.image_io import decode_png, encode_png_data_url, mode_of

SIZE = (16, 12)

GRAY_PALETTE: list[int] = []
COLOR_PALETTE: list[int] = []
for index in range(256):
    GRAY_PALETTE.extend([index, index, index])
    COLOR_PALETTE.extend([index, (index * 3) % 256, (index * 7) % 256])

PIXEL_DATA = [index % 256 for index in range(SIZE[0] * SIZE[1])]


def _expect(error_cls: type[AppError] | None, code: str, data: bytes) -> AppError:
    with pytest.raises(AppError) as excinfo:
        decode_png(data)
    error = excinfo.value
    assert error.code == code
    return error


def test_decode_gray(make_png) -> None:
    image = decode_png(make_png("L", SIZE, 42))
    assert image.mode == "gray"
    assert image.source_mode == "L"
    assert image.array.shape == (SIZE[1], SIZE[0])
    assert image.array.dtype == np.uint8
    assert image.array.flags["C_CONTIGUOUS"]
    assert (image.array == 42).all()
    assert (image.width, image.height) == SIZE


def test_decode_la_discards_alpha(make_png) -> None:
    image = decode_png(make_png("LA", SIZE, (50, 200)))
    assert image.mode == "gray"
    assert image.source_mode == "LA"
    assert (image.array == 50).all()


def test_decode_rgb(make_png) -> None:
    image = decode_png(make_png("RGB", SIZE, (10, 20, 30)))
    assert image.mode == "rgb"
    assert image.array.shape == (SIZE[1], SIZE[0], 3)
    assert (image.array[..., 0] == 10).all()


def test_decode_rgba_discards_alpha_without_compositing(make_png) -> None:
    image = decode_png(make_png("RGBA", SIZE, (10, 20, 30, 0)))
    assert image.mode == "rgb"
    assert image.source_mode == "RGBA"
    assert image.array.shape == (SIZE[1], SIZE[0], 3)
    assert (image.array == np.array([10, 20, 30], dtype=np.uint8)).all()


def test_decode_palette_color_is_rgb(make_png) -> None:
    data = make_png("P", SIZE, palette=COLOR_PALETTE, data=PIXEL_DATA)
    image = decode_png(data)
    assert image.mode == "rgb"
    assert image.source_mode == "P"
    assert image.array.shape == (SIZE[1], SIZE[0], 3)


def test_decode_palette_gray_is_gray(make_png) -> None:
    data = make_png("P", SIZE, palette=GRAY_PALETTE, data=PIXEL_DATA)
    image = decode_png(data)
    assert image.mode == "gray"
    assert image.source_mode == "P"
    assert image.array.shape == (SIZE[1], SIZE[0])


def test_decode_binary_is_gray_with_0_and_255(make_png) -> None:
    image = decode_png(make_png("1", SIZE, 1))
    assert image.mode == "gray"
    assert set(np.unique(image.array)).issubset({0, 255})


def test_decode_16bit_is_unsupported(make_png) -> None:
    error = _expect(AppError, "unsupported_image", make_png("I;16", SIZE, 1000))
    assert "I;16" in error.message
    assert error.status == 400


def test_decode_non_png_is_invalid(make_png) -> None:
    jpeg = make_png("RGB", SIZE, (1, 2, 3), fmt="JPEG")
    _expect(AppError, "invalid_image", jpeg)


def test_decode_truncated_png_is_invalid(make_png) -> None:
    png = make_png("L", SIZE, 10)
    # Metade do arquivo: os dados da imagem ficam incompletos e o Pillow falha.
    _expect(AppError, "invalid_image", png[: len(png) // 2])


def test_decode_png_cut_only_before_iend_is_accepted(make_png) -> None:
    # Documenta o comportamento do Pillow: sem o chunk IEND (12 bytes), mas com
    # todos os dados de imagem, o PNG ainda é decodificado.
    png = make_png("L", SIZE, 10)
    image = decode_png(png[:-12])
    assert (image.width, image.height) == SIZE


def test_decode_empty_bytes_is_invalid() -> None:
    _expect(AppError, "invalid_image", b"")


def test_decode_too_large_side_is_413(make_png, monkeypatch) -> None:
    monkeypatch.setattr("app.services.image_io.MAX_IMAGE_SIDE", 4)
    error = _expect(AppError, "image_too_large", make_png("L", (5, 5), 0))
    assert error.status == 413
    assert error.details["width"] == 5
    assert error.details["height"] == 5
    assert error.details["max_side"] == 4


def test_encode_data_url_prefix() -> None:
    array = np.zeros((4, 5), dtype=np.uint8)
    url = encode_png_data_url(array)
    assert url.startswith("data:image/png;base64,")
    base64.b64decode(url.split(",", 1)[1])


def test_encode_roundtrip_gray() -> None:
    rng = np.random.default_rng(0)
    array = rng.integers(0, 256, size=(9, 13), dtype=np.uint8)
    decoded = decode_png(base64.b64decode(encode_png_data_url(array).split(",", 1)[1]))
    assert decoded.mode == "gray"
    np.testing.assert_array_equal(decoded.array, array)


def test_encode_roundtrip_rgb() -> None:
    rng = np.random.default_rng(1)
    array = rng.integers(0, 256, size=(7, 11, 3), dtype=np.uint8)
    decoded = decode_png(base64.b64decode(encode_png_data_url(array).split(",", 1)[1]))
    assert decoded.mode == "rgb"
    np.testing.assert_array_equal(decoded.array, array)


def test_mode_of() -> None:
    assert mode_of(np.zeros((3, 4), dtype=np.uint8)) == "gray"
    assert mode_of(np.zeros((3, 4, 3), dtype=np.uint8)) == "rgb"
    with pytest.raises(ValueError):
        mode_of(np.zeros((3, 4, 4), dtype=np.uint8))


def test_png_signature_is_checked_before_pillow() -> None:
    buffer = io.BytesIO()
    Image.new("L", (2, 2)).save(buffer, format="PNG")
    data = buffer.getvalue()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
