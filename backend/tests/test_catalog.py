"""Testes do carregamento e da validação estrita do catálogo."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from app.config import CATALOG_PATH
from app.core.catalog import CatalogError, load_catalog
from app.core.errors import AppError
from app.processing.registry import PROCESS_HANDLERS

BASE: dict[str, Any] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
Mutator = Callable[[dict[str, Any]], None]


def _process(data: dict[str, Any], process_id: str) -> dict[str, Any]:
    for process in data["processes"]:
        if process["id"] == process_id:
            return process
    raise AssertionError(f"process {process_id} not found in fixture")


def _param(data: dict[str, Any], process_id: str, param_id: str) -> dict[str, Any]:
    for param in _process(data, process_id)["params"]:
        if param["id"] == param_id:
            return param
    raise AssertionError(f"param {param_id} not found in fixture")


def _duplicated_category(data: dict[str, Any]) -> None:
    data["categories"].append(copy.deepcopy(data["categories"][0]))


def _duplicated_process(data: dict[str, Any]) -> None:
    data["processes"].append(copy.deepcopy(data["processes"][0]))


def _unknown_category(data: dict[str, Any]) -> None:
    _process(data, "rgb_split")["category"] = "inexistente"


def _empty_modes(data: dict[str, Any]) -> None:
    _process(data, "rgb_split")["modes"] = []


def _invalid_mode(data: dict[str, Any]) -> None:
    _process(data, "rgb_split")["modes"] = ["cmyk"]


def _duplicated_modes(data: dict[str, Any]) -> None:
    _process(data, "threshold")["modes"] = ["gray", "gray"]


def _unknown_param_type(data: dict[str, Any]) -> None:
    _param(data, "threshold", "k")["type"] = "range"


def _duplicated_param(data: dict[str, Any]) -> None:
    process = _process(data, "threshold")
    process["params"].append(copy.deepcopy(process["params"][0]))


def _int_without_min(data: dict[str, Any]) -> None:
    del _param(data, "threshold", "k")["min"]


def _min_greater_than_max(data: dict[str, Any]) -> None:
    param = _param(data, "threshold", "k")
    param["min"], param["max"] = 200, 100


def _default_out_of_range(data: dict[str, Any]) -> None:
    _param(data, "threshold", "k")["default"] = 300


def _int_default_not_int(data: dict[str, Any]) -> None:
    _param(data, "threshold", "k")["default"] = "128"


def _odd_with_even_default(data: dict[str, Any]) -> None:
    _param(data, "gaussian_blur", "kernel_size")["default"] = 4


def _odd_with_even_min(data: dict[str, Any]) -> None:
    _param(data, "gaussian_blur", "kernel_size")["min"] = 4


def _select_without_options(data: dict[str, Any]) -> None:
    del _param(data, "gaussian_frequency_filter", "filter_type")["options"]


def _select_default_not_option(data: dict[str, Any]) -> None:
    _param(data, "gaussian_frequency_filter", "filter_type")["default"] = "bandpass"


def _bool_default_not_bool(data: dict[str, Any]) -> None:
    _param(data, "intensity_slicing", "preserve_background")["default"] = "sim"


def _visible_if_unknown_param(data: dict[str, Any]) -> None:
    _param(data, "salt_pepper_noise", "salt_probability")["visible_if"]["param"] = "nope"


def _visible_if_invalid_equals(data: dict[str, Any]) -> None:
    _param(data, "salt_pepper_noise", "salt_probability")["visible_if"]["equals"] = "x"


def _constraint_unknown_rule(data: dict[str, Any]) -> None:
    _process(data, "intensity_slicing")["constraints"][0]["rule"] = "less"


def _constraint_unknown_param(data: dict[str, Any]) -> None:
    _process(data, "intensity_slicing")["constraints"][0]["params"] = ["a", "zzz"]


def _missing_processes(data: dict[str, Any]) -> None:
    del data["processes"]


INVALID_CASES: list[tuple[str, Mutator]] = [
    ("missing-version", lambda data: data.pop("version")),
    ("missing-processes", _missing_processes),
    ("duplicated-category", _duplicated_category),
    ("duplicated-process", _duplicated_process),
    ("unknown-category", _unknown_category),
    ("empty-modes", _empty_modes),
    ("invalid-mode", _invalid_mode),
    ("duplicated-modes", _duplicated_modes),
    ("unknown-param-type", _unknown_param_type),
    ("duplicated-param", _duplicated_param),
    ("int-without-min", _int_without_min),
    ("min-greater-than-max", _min_greater_than_max),
    ("default-out-of-range", _default_out_of_range),
    ("int-default-not-int", _int_default_not_int),
    ("odd-with-even-default", _odd_with_even_default),
    ("odd-with-even-min", _odd_with_even_min),
    ("select-without-options", _select_without_options),
    ("select-default-not-option", _select_default_not_option),
    ("bool-default-not-bool", _bool_default_not_bool),
    ("visible-if-unknown-param", _visible_if_unknown_param),
    ("visible-if-invalid-equals", _visible_if_invalid_equals),
    ("constraint-unknown-rule", _constraint_unknown_rule),
    ("constraint-unknown-param", _constraint_unknown_param),
]


@pytest.fixture
def catalog_path_for(tmp_path: Path) -> Callable[[dict[str, Any]], Path]:
    def _write(data: dict[str, Any]) -> Path:
        path = tmp_path / "processes.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    return _write


def test_real_catalog_loads_with_all_processes(catalog) -> None:
    assert len(catalog.processes) == 19
    assert list(catalog.processes) == list(PROCESS_HANDLERS)
    assert set(catalog.processes) == set(PROCESS_HANDLERS)


def test_real_catalog_has_expected_categories(catalog) -> None:
    ids = [category["id"] for category in catalog.categories]
    assert ids == ["color", "intensity", "spatial", "frequency", "noise"]


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "processes.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


@pytest.mark.parametrize("mutate", [case[1] for case in INVALID_CASES], ids=[case[0] for case in INVALID_CASES])
def test_invalid_catalog_is_rejected(catalog_path_for, mutate: Mutator) -> None:
    data = copy.deepcopy(BASE)
    mutate(data)
    with pytest.raises(CatalogError):
        load_catalog(catalog_path_for(data))


def test_missing_catalog_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(CatalogError):
        load_catalog(tmp_path / "does-not-exist.json")


def test_to_public_preserves_fields_and_order(catalog) -> None:
    public = catalog.to_public({"threshold": True})
    assert list(public) == list(BASE)
    assert public["version"] == BASE["version"]
    assert [category["id"] for category in public["categories"]] == [
        category["id"] for category in BASE["categories"]
    ]
    assert [process["id"] for process in public["processes"]] == [
        process["id"] for process in BASE["processes"]
    ]
    for original, exported in zip(BASE["processes"], public["processes"]):
        assert list(exported) == list(original) + ["implemented"]
        assert exported["implemented"] == (original["id"] == "threshold")
        assert exported["params"] == original["params"]
        assert exported["modes"] == original["modes"]


def test_to_public_does_not_mutate_raw(catalog) -> None:
    catalog.to_public({"threshold": True})
    assert all("implemented" not in process for process in catalog.raw["processes"])


def test_to_public_defaults_to_false(catalog) -> None:
    public = catalog.to_public({})
    assert all(process["implemented"] is False for process in public["processes"])


def test_get_unknown_process_raises_app_error(catalog) -> None:
    with pytest.raises(AppError) as excinfo:
        catalog.get("does_not_exist")
    error = excinfo.value
    assert error.code == "process_not_found"
    assert error.status == 404
    assert "does_not_exist" in error.message


def test_get_known_process(catalog) -> None:
    process = catalog.get("threshold")
    assert process.id == "threshold"
    assert process.label == "Limiarização"
    assert process.modes == ("gray", "rgb")
    assert process.param("k").default == 128
