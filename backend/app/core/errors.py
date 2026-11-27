"""Erros da aplicação e handlers que garantem o formato único de resposta.

Todo erro devolvido pela API tem o formato::

    {"error": {"code": "...", "message": "...", "details": {...}}}

As mensagens voltadas ao usuário são em português do Brasil; os logs, em inglês.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

#: Tamanho máximo do arquivo, em MB, usado nas mensagens de erro.
MAX_UPLOAD_MB = 20

MODE_DESCRIPTIONS: dict[str, str] = {
    "gray": "em escala de cinza",
    "rgb": "coloridas (RGB)",
}


class AppError(Exception):
    """Erro de aplicação já pronto para virar uma resposta HTTP no formato único."""

    def __init__(
        self,
        code: str,
        message: str,
        status: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details: dict[str, Any] = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serializa o erro no formato público de ``API.md``."""
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


# ---------------------------------------------------------------------------
# Fábricas: uma por código de erro do contrato.
# ---------------------------------------------------------------------------


def invalid_image(message: str = "O arquivo enviado não é um PNG válido.") -> AppError:
    """400 ``invalid_image``: arquivo ausente, corrompido ou que não é PNG."""
    return AppError("invalid_image", message, 400)


def unsupported_image(message: str) -> AppError:
    """400 ``unsupported_image``: PNG com profundidade ou modo não suportado."""
    return AppError("unsupported_image", message, 400)


def image_too_large(message: str, details: dict[str, Any] | None = None) -> AppError:
    """413 ``image_too_large``: arquivo acima do limite de bytes ou de lado."""
    return AppError("image_too_large", message, 413, details)


def process_not_found(process_id: str) -> AppError:
    """404 ``process_not_found``: id fora do catálogo."""
    return AppError(
        "process_not_found",
        f"Processo '{process_id}' não encontrado.",
        404,
        {"process_id": process_id},
    )


def invalid_params(
    message: str, param: str | None = None, **details: Any
) -> AppError:
    """422 ``invalid_params``: JSON inválido, tipo/faixa/opção/restrição violados."""
    payload: dict[str, Any] = dict(details)
    if param is not None:
        payload["param"] = param
    return AppError("invalid_params", message, 422, payload)


def unsupported_mode(process_label: str, mode: str, allowed: tuple[str, ...] | list[str]) -> AppError:
    """422 ``unsupported_mode``: o processo não aceita o modo da imagem enviada."""
    description = MODE_DESCRIPTIONS.get(mode, mode)
    return AppError(
        "unsupported_mode",
        f"O processo '{process_label}' não está disponível para imagens {description}.",
        422,
        {"mode": mode, "allowed_modes": list(allowed)},
    )


def not_implemented(process_label: str) -> AppError:
    """501 ``not_implemented``: o handler ainda lança ``NotImplementedError``."""
    return AppError(
        "not_implemented",
        f"O processo '{process_label}' ainda não foi implementado.",
        501,
        {"process_label": process_label},
    )


def invalid_output(message: str) -> AppError:
    """500 ``invalid_output``: o handler devolveu dados fora do contrato."""
    return AppError("invalid_output", message, 500)


def processing_error(exc: BaseException) -> AppError:
    """500 ``processing_error``: exceção inesperada dentro do handler."""
    message = f"Erro ao executar o processo: {type(exc).__name__}: {exc}"
    return AppError("processing_error", message, 500)


# ---------------------------------------------------------------------------
# Registro dos handlers no FastAPI
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers que normalizam todas as respostas de erro."""

    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        if exc.status >= 500:
            logger.error("%s %s -> %d %s", request.method, request.url.path, exc.status, exc.code)
        return JSONResponse(status_code=exc.status, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"loc": [str(part) for part in error.get("loc", ())], "msg": error.get("msg", "")}
            for error in exc.errors()
        ]
        error = invalid_params("Requisição inválida.", errors=errors)
        return JSONResponse(status_code=error.status, content=error.to_dict())

    @app.exception_handler(StarletteHTTPException)
    async def _http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        status = exc.status_code
        if status == 404:
            code, message = "not_found", "Recurso não encontrado."
        elif status == 405:
            code, message = "method_not_allowed", "Método não permitido."
        else:
            code = "http_error"
            message = exc.detail if isinstance(exc.detail, str) else f"Erro HTTP {status}."
        error = AppError(code, message, status)
        return JSONResponse(status_code=status, content=error.to_dict())

    @app.exception_handler(Exception)
    async def _unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        error = AppError("internal_error", "Erro interno do servidor.", 500)
        return JSONResponse(status_code=500, content=error.to_dict())
