"""Validação e conversão dos parâmetros enviados pelo cliente.

O cliente manda um JSON livre (``params`` do multipart). Aqui ele é confrontado com
o ``ProcessSpec`` do catálogo: tipos, faixas, ``odd``, ``select``, visibilidade
condicional (``visible_if``) e restrições entre parâmetros (``less_equal``).

O resultado é o dicionário que vai para o handler e para o campo ``params`` da
resposta, sempre na ordem do catálogo e com os defaults preenchidos.
"""

from __future__ import annotations

import json
import math
from typing import Any

from .catalog import ParamSpec, ProcessSpec
from .errors import invalid_params

ParamValue = int | float | bool | str


def _safe_value(value: Any) -> Any:
    """Converte valores não finitos em texto para que o ``details`` seja JSON válido."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _error(message: str, param: ParamSpec, value: Any, **details: Any) -> Exception:
    return invalid_params(
        message,
        param=param.id,
        value=_safe_value(value),
        **details,
    )


def _convert_int(param: ParamSpec, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(f"'{param.label}' deve ser um número inteiro.", param, value)
    if isinstance(value, float):
        if not value.is_integer():
            raise _error(f"'{param.label}' deve ser um número inteiro.", param, value)
        number = int(value)
    else:
        number = int(value)
    if param.min is not None and number < param.min:
        raise _error(
            f"'{param.label}' deve estar entre {param.min} e {param.max}.",
            param,
            value,
            min=param.min,
            max=param.max,
        )
    if param.max is not None and number > param.max:
        raise _error(
            f"'{param.label}' deve estar entre {param.min} e {param.max}.",
            param,
            value,
            min=param.min,
            max=param.max,
        )
    if param.odd and number % 2 == 0:
        raise _error(f"'{param.label}' deve ser um número ímpar.", param, value)
    return number


def _convert_float(param: ParamSpec, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(f"'{param.label}' deve ser um número.", param, value)
    number = float(value)
    if not math.isfinite(number):
        raise _error(f"'{param.label}' deve ser um número.", param, value)
    if param.min is not None and number < param.min:
        raise _error(
            f"'{param.label}' deve estar entre {param.min} e {param.max}.",
            param,
            value,
            min=param.min,
            max=param.max,
        )
    if param.max is not None and number > param.max:
        raise _error(
            f"'{param.label}' deve estar entre {param.min} e {param.max}.",
            param,
            value,
            min=param.min,
            max=param.max,
        )
    return number


def _convert_bool(param: ParamSpec, value: Any) -> bool:
    if not isinstance(value, bool):
        raise _error(f"'{param.label}' deve ser verdadeiro ou falso.", param, value)
    return value


def _convert_select(param: ParamSpec, value: Any) -> str:
    if not isinstance(value, str) or value not in param.options:
        options = ", ".join(param.options)
        raise _error(
            f"'{param.label}' deve ser uma das opções: {options}.",
            param,
            value,
            options=list(param.options),
        )
    return value


_CONVERTERS = {
    "int": _convert_int,
    "float": _convert_float,
    "bool": _convert_bool,
    "select": _convert_select,
}


def parse_params(process: ProcessSpec, raw: str | None) -> dict[str, ParamValue]:
    """Valida ``raw`` (string JSON) contra ``process`` e devolve os parâmetros resolvidos.

    Levanta ``AppError`` (422 ``invalid_params``) no primeiro problema encontrado.
    """
    if raw is None or not raw.strip():
        payload: dict[str, Any] = {}
    else:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise invalid_params("Os parâmetros não estão em JSON válido.") from None
        if not isinstance(payload, dict):
            raise invalid_params("Os parâmetros devem ser um objeto JSON.")

    known = {param.id for param in process.params}
    for key in payload:
        if key not in known:
            raise invalid_params(f"Parâmetro desconhecido: '{key}'.", param=key)

    resolved: dict[str, ParamValue] = {}
    for param in process.params:
        value = payload.get(param.id)
        if value is None:
            value = param.default
        resolved[param.id] = _CONVERTERS[param.type](param, value)

    visible: dict[str, ParamValue] = {}
    for param in process.params:
        condition = param.visible_if
        if condition is not None:
            target = condition.get("param")
            expected = condition.get("equals")
            if resolved.get(target) != expected:
                continue
        visible[param.id] = resolved[param.id]

    for constraint in process.constraints:
        first, second = constraint["params"]
        if first in visible and second in visible and visible[first] > visible[second]:
            raise invalid_params(
                constraint["message"], param=second, params=[first, second]
            )

    return visible
