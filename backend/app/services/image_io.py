"""Conversão entre bytes PNG e ``numpy.ndarray`` uint8.

Pillow é usado **apenas para I/O**: abrir/salvar o PNG e normalizar o modo do
arquivo. Nenhum processamento de imagem acontece aqui.
"""

from __future__ import annotations

import base64
import io
import warnings
from dataclasses import dataclass
from typing import Literal

import numpy as np
from PIL import Image, UnidentifiedImageError

from ..config import MAX_IMAGE_SIDE, MAX_UPLOAD_BYTES
from ..core.errors import image_too_large, invalid_image, unsupported_image

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
Mode = Literal["gray", "rgb"]

INVALID_PNG_MESSAGE = "O arquivo enviado não é um PNG válido."


@dataclass
class DecodedImage:
    """PNG decodificado e normalizado para o contrato interno do backend."""

    array: np.ndarray
    mode: Mode
    source_mode: str
    width: int
    height: int


def mode_of(array: np.ndarray) -> Mode:
    """Classifica o array como ``gray`` (H, W) ou ``rgb`` (H, W, 3)."""
    if array.ndim == 2:
        return "gray"
    if array.ndim == 3 and array.shape[2] == 3:
        return "rgb"
    raise ValueError(f"unsupported image shape: {array.shape}")


def _normalize(img: Image.Image) -> tuple[np.ndarray, Mode]:
    """Normaliza o modo do Pillow para ``(array uint8, gray|rgb)``."""
    if img.mode in ("P", "PA"):
        rgb = img.convert("RGBA").convert("RGB")
        array = np.asarray(rgb, dtype=np.uint8)
        # Paleta apenas de cinza: os três canais são idênticos em todo pixel.
        if np.array_equal(array[..., 0], array[..., 1]) and np.array_equal(
            array[..., 1], array[..., 2]
        ):
            array = array[..., 0]
        array = np.ascontiguousarray(array)
        return array, mode_of(array)

    if img.mode == "L":
        normalized = img
        mode: Mode = "gray"
    elif img.mode == "LA":
        normalized = img.getchannel("L")
        mode = "gray"
    elif img.mode == "1":
        normalized = img.convert("L")
        mode = "gray"
    elif img.mode == "RGB":
        normalized = img
        mode = "rgb"
    elif img.mode == "RGBA":
        normalized = img.convert("RGB")
        mode = "rgb"
    else:
        raise unsupported_image(
            f"Formato de PNG não suportado ({img.mode}). Use imagens em escala de cinza "
            "de 8 bits ou RGB de 24 bits."
        )

    array = np.ascontiguousarray(np.asarray(normalized, dtype=np.uint8))
    return array, mode


def decode_png(data: bytes) -> DecodedImage:
    """Decodifica bytes PNG e normaliza o modo, ou levanta ``AppError`` 400/413."""
    if not data.startswith(PNG_SIGNATURE):
        raise invalid_image(INVALID_PNG_MESSAGE)

    try:
        with warnings.catch_warnings():
            # O limite de lado abaixo já protege; não poluir o log com o aviso de
            # "decompression bomb" do Pillow para imagens grandes mas aceitáveis.
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(data))
    except Image.DecompressionBombError as exc:
        raise image_too_large(
            f"A imagem excede o limite de {MAX_IMAGE_SIDE} pixels por lado.",
            {"max_side": MAX_IMAGE_SIDE},
        ) from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise invalid_image(INVALID_PNG_MESSAGE) from exc

    if img.format != "PNG":
        raise invalid_image(INVALID_PNG_MESSAGE)

    width, height = img.size
    if width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE:
        raise image_too_large(
            f"A imagem excede o limite de {MAX_IMAGE_SIDE} pixels por lado ({width}×{height}).",
            {"width": width, "height": height, "max_side": MAX_IMAGE_SIDE},
        )

    source_mode = img.mode
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            img.load()
    except Exception as exc:  # qualquer falha do Pillow indica PNG corrompido
        raise invalid_image(INVALID_PNG_MESSAGE) from exc

    array, mode = _normalize(img)
    return DecodedImage(
        array=array,
        mode=mode,
        source_mode=source_mode,
        width=width,
        height=height,
    )


def encode_png_data_url(array: np.ndarray) -> str:
    """Codifica um array uint8 como ``data:image/png;base64,...``."""
    if array.ndim == 2:
        image = Image.fromarray(array)
    elif array.ndim == 3 and array.shape[2] == 3:
        image = Image.fromarray(array)
    else:
        raise ValueError(f"unsupported image shape: {array.shape}")

    buffer = io.BytesIO()
    # compress_level=1 prioriza a velocidade: as imagens são pequenas e vão em base64.
    image.save(buffer, format="PNG", compress_level=1)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def upload_limit_message() -> str:
    """Mensagem padrão para uploads acima do limite de bytes."""
    megabytes = MAX_UPLOAD_BYTES // (1024 * 1024)
    return f"O arquivo excede o limite de {megabytes} MB."
