"""Carregamento e validação estrita do catálogo ``shared/processes.json``.

O JSON é a fonte única de verdade compartilhada entre frontend e backend. Aqui ele
é convertido em dataclasses imutáveis, validado no carregamento (falhas viram
``CatalogError``) e exposto ao público por :meth:`Catalog.to_public`.
"""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import process_not_found

VALID_MODES: tuple[str, ...] = ("gray", "rgb")
VALID_PARAM_TYPES: tuple[str, ...] = ("int", "float", "bool", "select")
VALID_CONSTRAINT_RULES: tuple[str, ...] = ("less_equal",)


class CatalogError(Exception):
    """Catálogo inválido: impede a inicialização do app com uma mensagem clara."""


@dataclass(frozen=True)
class ParamSpec:
    """Especificação de um parâmetro de processo (equivalente ao ParamSpec do JSON)."""

    id: str
    label: str
    type: str
    default: int | float | bool | str
    min: int | float | None = None
    max: int | float | None = None
    step: int | float | None = None
    odd: bool = False
    options: tuple[str, ...] = ()
    visible_if: dict[str, Any] | None = None
    help: str | None = None


@dataclass(frozen=True)
class ProcessSpec:
    """Especificação de um processo do catálogo."""

    id: str
    label: str
    category: str
    description: str
    modes: tuple[str, ...]
    params: tuple[ParamSpec, ...]
    constraints: tuple[dict[str, Any], ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)

    def param(self, param_id: str) -> ParamSpec | None:
        """Devolve o parâmetro com o id informado, ou ``None``."""
        for param in self.params:
            if param.id == param_id:
                return param
        return None


class Catalog:
    """Catálogo validado, com consulta por id e exportação no formato público."""

    def __init__(
        self,
        raw: dict[str, Any],
        categories: list[dict[str, Any]],
        processes: dict[str, ProcessSpec],
    ) -> None:
        self.raw = raw
        self.categories = categories
        self.processes = processes

    def get(self, process_id: str) -> ProcessSpec:
        """Devolve o processo ou levanta ``404 process_not_found``."""
        try:
            return self.processes[process_id]
        except KeyError:
            raise process_not_found(process_id) from None

    def to_public(self, implemented: dict[str, bool]) -> dict[str, Any]:
        """Devolve uma cópia do JSON original com ``implemented`` em cada processo.

        A cópia é profunda para que o ``raw`` do catálogo nunca seja alterado e a
        ordem dos campos e das listas do JSON seja preservada.
        """
        public = copy.deepcopy(self.raw)
        for process in public.get("processes", []):
            process_id = process.get("id", "")
            process["implemented"] = bool(implemented.get(process_id, False))
        return public


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------


def _fail(path: Path, message: str) -> CatalogError:
    return CatalogError(f"{path}: {message}")


def _require_mapping(path: Path, value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _fail(path, f"{where} must be a JSON object.")
    return value


def _require_str(path: Path, value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _fail(path, f"{where} must be a non-empty string.")
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_param(
    path: Path, process_id: str, raw: dict[str, Any], param_ids: set[str]
) -> tuple[ParamSpec, dict[str, Any]]:
    where = f"process '{process_id}'"
    param_id = _require_str(path, raw.get("id"), f"{where}: param id")
    label = _require_str(path, raw.get("label"), f"{where}: param '{param_id}' label")
    if param_id in param_ids:
        raise _fail(path, f"{where}: duplicated param id '{param_id}'.")
    param_ids.add(param_id)

    ptype = raw.get("type")
    if ptype not in VALID_PARAM_TYPES:
        raise _fail(
            path,
            f"{where}: param '{param_id}' has unknown type {ptype!r}; "
            f"expected one of {', '.join(VALID_PARAM_TYPES)}.",
        )
    if "default" not in raw:
        raise _fail(path, f"{where}: param '{param_id}' is missing 'default'.")
    default = raw["default"]

    min_value = raw.get("min")
    max_value = raw.get("max")
    step = raw.get("step")
    odd = raw.get("odd", False)
    options: tuple[str, ...] = ()
    visible_if = raw.get("visible_if")
    help_text = raw.get("help")

    if not isinstance(odd, bool):
        raise _fail(path, f"{where}: param '{param_id}' field 'odd' must be a boolean.")
    if help_text is not None and not isinstance(help_text, str):
        raise _fail(path, f"{where}: param '{param_id}' field 'help' must be a string.")
    if step is not None and not _is_number(step):
        raise _fail(path, f"{where}: param '{param_id}' field 'step' must be a number.")

    if ptype in ("int", "float"):
        if not _is_number(min_value) or not _is_number(max_value):
            raise _fail(
                path,
                f"{where}: param '{param_id}' of type {ptype} requires numeric 'min' and 'max'.",
            )
        if min_value > max_value:
            raise _fail(
                path,
                f"{where}: param '{param_id}' has min ({min_value}) greater than max "
                f"({max_value}).",
            )
        if ptype == "int":
            if not _is_int(min_value) or not _is_int(max_value):
                raise _fail(
                    path, f"{where}: param '{param_id}' of type int needs integer bounds."
                )
            if not _is_int(default):
                raise _fail(
                    path,
                    f"{where}: param '{param_id}' default must be an integer.",
                )
        else:
            if not _is_number(default) or not math.isfinite(float(default)):
                raise _fail(path, f"{where}: param '{param_id}' default must be a finite number.")
        if not (min_value <= default <= max_value):
            raise _fail(
                path,
                f"{where}: param '{param_id}' default ({default}) is outside "
                f"[{min_value}, {max_value}].",
            )
        if odd:
            if default % 2 == 0:
                raise _fail(
                    path, f"{where}: param '{param_id}' is odd-only but default is even."
                )
            if min_value % 2 == 0 or max_value % 2 == 0:
                raise _fail(
                    path,
                    f"{where}: param '{param_id}' is odd-only but min/max are even "
                    f"({min_value}, {max_value}).",
                )
    elif ptype == "bool":
        if not isinstance(default, bool):
            raise _fail(
                path, f"{where}: param '{param_id}' of type bool needs a boolean default."
            )
    elif ptype == "select":
        raw_options = raw.get("options")
        if not isinstance(raw_options, list) or not raw_options:
            raise _fail(
                path, f"{where}: param '{param_id}' of type select requires 'options'."
            )
        values: list[str] = []
        for option in raw_options:
            option = _require_mapping(path, option, f"{where}: param '{param_id}' option")
            values.append(_require_str(path, option.get("value"), "option value"))
            _require_str(path, option.get("label"), "option label")
        if len(set(values)) != len(values):
            raise _fail(path, f"{where}: param '{param_id}' has duplicated option values.")
        if not isinstance(default, str) or default not in values:
            raise _fail(
                path,
                f"{where}: param '{param_id}' default {default!r} is not one of "
                f"{values}.",
            )
        options = tuple(values)

    if visible_if is not None:
        if not isinstance(visible_if, dict):
            raise _fail(path, f"{where}: param '{param_id}' field 'visible_if' must be an object.")

    spec = ParamSpec(
        id=param_id,
        label=label,
        type=ptype,
        default=default,
        min=min_value,
        max=max_value,
        step=step,
        odd=odd,
        options=options,
        visible_if=dict(visible_if) if isinstance(visible_if, dict) else None,
        help=help_text,
    )
    return spec, raw


def _validate_visible_if(
    path: Path, process_id: str, spec: ParamSpec, raw_params: dict[str, dict[str, Any]]
) -> None:
    condition = spec.visible_if
    if condition is None:
        return
    where = f"process '{process_id}': param '{spec.id}'"
    target_id = condition.get("param")
    equals = condition.get("equals")
    if not isinstance(target_id, str) or target_id not in raw_params:
        raise _fail(
            path,
            f"{where}: visible_if references unknown param {target_id!r}.",
        )
    target = raw_params[target_id]
    if target.get("type") != "select":
        raise _fail(
            path,
            f"{where}: visible_if references param '{target_id}' which is not a select.",
        )
    valid_values = [option["value"] for option in target.get("options", [])]
    if equals not in valid_values:
        raise _fail(
            path,
            f"{where}: visible_if equals {equals!r} is not a valid option of "
            f"'{target_id}' ({valid_values}).",
        )


def _validate_constraints(
    path: Path, process_id: str, constraints: Any, param_ids: set[str]
) -> tuple[dict[str, Any], ...]:
    if constraints is None:
        return ()
    if not isinstance(constraints, list):
        raise _fail(path, f"process '{process_id}': 'constraints' must be a list.")
    validated: list[dict[str, Any]] = []
    for constraint in constraints:
        constraint = _require_mapping(path, constraint, f"process '{process_id}': constraint")
        rule = constraint.get("rule")
        if rule not in VALID_CONSTRAINT_RULES:
            raise _fail(
                path,
                f"process '{process_id}': unknown constraint rule {rule!r}; "
                f"expected one of {', '.join(VALID_CONSTRAINT_RULES)}.",
            )
        params = constraint.get("params")
        if not isinstance(params, list) or len(params) != 2:
            raise _fail(
                path,
                f"process '{process_id}': constraint '{rule}' requires exactly two params.",
            )
        for param_id in params:
            if not isinstance(param_id, str) or param_id not in param_ids:
                raise _fail(
                    path,
                    f"process '{process_id}': constraint references unknown param "
                    f"{param_id!r}.",
                )
        message = _require_str(
            path, constraint.get("message"), f"process '{process_id}': constraint message"
        )
        validated.append({"rule": rule, "params": list(params), "message": message})
    return tuple(validated)


def _build_process(path: Path, raw: dict[str, Any], category_ids: set[str]) -> ProcessSpec:
    process_id = _require_str(path, raw.get("id"), "process id")
    label = _require_str(path, raw.get("label"), f"process '{process_id}': label")
    category = _require_str(path, raw.get("category"), f"process '{process_id}': category")
    if category not in category_ids:
        raise _fail(
            path,
            f"process '{process_id}' references unknown category '{category}'.",
        )
    description = raw.get("description", "")
    if not isinstance(description, str):
        raise _fail(path, f"process '{process_id}': 'description' must be a string.")

    modes = raw.get("modes")
    if not isinstance(modes, list) or not modes:
        raise _fail(path, f"process '{process_id}': 'modes' must be a non-empty list.")
    for mode in modes:
        if mode not in VALID_MODES:
            raise _fail(
                path,
                f"process '{process_id}': invalid mode {mode!r}; "
                f"expected {', '.join(VALID_MODES)}.",
            )
    if len(set(modes)) != len(modes):
        raise _fail(path, f"process '{process_id}': duplicated modes.")

    raw_params = raw.get("params", [])
    if not isinstance(raw_params, list):
        raise _fail(path, f"process '{process_id}': 'params' must be a list.")

    param_ids: set[str] = set()
    raw_by_id: dict[str, dict[str, Any]] = {}
    specs: list[ParamSpec] = []
    for raw_param in raw_params:
        raw_param = _require_mapping(path, raw_param, f"process '{process_id}': param")
        spec, raw_param = _validate_param(path, process_id, raw_param, param_ids)
        specs.append(spec)
        raw_by_id[spec.id] = raw_param

    for spec in specs:
        _validate_visible_if(path, process_id, spec, raw_by_id)

    constraints = _validate_constraints(path, process_id, raw.get("constraints"), param_ids)

    return ProcessSpec(
        id=process_id,
        label=label,
        category=category,
        description=description,
        modes=tuple(modes),
        params=tuple(specs),
        constraints=constraints,
        raw=raw,
    )


def load_catalog(path: Path) -> Catalog:
    """Lê e valida o catálogo. Levanta ``CatalogError`` em qualquer inconsistência."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"{path}: cannot read catalog file: {exc}") from exc
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise _fail(path, f"invalid JSON: {exc}") from exc

    raw = _require_mapping(path, raw, "catalog")
    for key in ("version", "categories", "processes"):
        if key not in raw:
            raise _fail(path, f"missing required key '{key}'.")

    raw_categories = raw["categories"]
    if not isinstance(raw_categories, list):
        raise _fail(path, "'categories' must be a list.")
    category_ids: set[str] = set()
    categories: list[dict[str, Any]] = []
    for raw_category in raw_categories:
        raw_category = _require_mapping(path, raw_category, "category")
        category_id = _require_str(path, raw_category.get("id"), "category id")
        _require_str(path, raw_category.get("label"), f"category '{category_id}' label")
        if category_id in category_ids:
            raise _fail(path, f"duplicated category id '{category_id}'.")
        category_ids.add(category_id)
        categories.append(raw_category)

    raw_processes = raw["processes"]
    if not isinstance(raw_processes, list) or not raw_processes:
        raise _fail(path, "'processes' must be a non-empty list.")
    processes: dict[str, ProcessSpec] = {}
    for raw_process in raw_processes:
        raw_process = _require_mapping(path, raw_process, "process")
        process = _build_process(path, raw_process, category_ids)
        if process.id in processes:
            raise _fail(path, f"duplicated process id '{process.id}'.")
        processes[process.id] = process

    return Catalog(raw=raw, categories=categories, processes=processes)
