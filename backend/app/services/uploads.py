"""Leitura do ``UploadFile`` do FastAPI com limite de tamanho."""

from __future__ import annotations

from fastapi import UploadFile

from ..config import MAX_UPLOAD_BYTES
from ..core.errors import image_too_large, invalid_image
from .image_io import INVALID_PNG_MESSAGE, upload_limit_message


def read_upload(file: UploadFile | None) -> bytes:
    """Lê o arquivo enviado, recusando ausência, vazio e excesso de tamanho."""
    if file is None or not file.filename:
        raise invalid_image("Nenhum arquivo foi enviado.")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise image_too_large(upload_limit_message(), {"max_bytes": MAX_UPLOAD_BYTES})
    if not data:
        raise invalid_image(INVALID_PNG_MESSAGE)
    return data
