"""Testes de validação/conversão de parâmetros."""

from __future__ import annotations

import pytest

from app.core.errors import AppError
from app.core.validation import parse_params


def _expect_error(process, raw: str | None, *, param: str | None = None) -> AppError:
    with pytest.raises(AppError) as excinfo:
        parse_params(process, raw)
    error = excinfo.value
    assert error.code == "invalid_params"
    assert error.status == 422
    if param is not None:
        assert error.details["param"] == param
    return error


def test_empty_and_null_params_use_defaults(catalog) -> None:
    process = catalog.get("threshold")
    assert parse_params(process, None) == {"k": 128}
    assert parse_params(process, "") == {"k": 128}
    assert parse_params(process, "   ") == {"k": 128}
    assert parse_params(process, "{}") == {"k": 128}
    assert parse_params(process, '{"k": null}') == {"k": 128}


def test_int_accepts_integral_float(catalog) -> None:
    assert parse_params(catalog.get("threshold"), '{"k": 5.0}') == {"k": 5}
    assert isinstance(parse_params(catalog.get("threshold"), '{"k": 5.0}')["k"], int)


@pytest.mark.parametrize("value", ["5.5", '"5"', "true", "[]"])
def test_int_rejects_non_integers(catalog, value: str) -> None:
    error = _expect_error(catalog.get("threshold"), '{"k": ' + value + "}", param="k")
    assert "número inteiro" in error.message


def test_int_range_is_enforced(catalog) -> None:
    low = _expect_error(catalog.get("threshold"), '{"k": -1}', param="k")
    assert low.details["min"] == 0
    assert low.details["max"] == 255
    high = _expect_error(catalog.get("threshold"), '{"k": 256}', param="k")
    assert "entre 0 e 255" in high.message


def test_odd_is_enforced(catalog) -> None:
    process = catalog.get("gaussian_blur")
    assert parse_params(process, '{"kernel_size": 5}')["kernel_size"] == 5
    error = _expect_error(process, '{"kernel_size": 4}', param="kernel_size")
    assert "ímpar" in error.message


def test_float_rejects_nan_and_bool(catalog) -> None:
    process = catalog.get("power_transform")
    error = _expect_error(process, '{"c": NaN}', param="c")
    assert "número" in error.message
    _expect_error(process, '{"c": true}', param="c")


def test_float_accepts_int_and_converts(catalog) -> None:
    process = catalog.get("power_transform")
    params = parse_params(process, '{"c": 5}')
    assert params["c"] == 5.0
    assert isinstance(params["c"], float)


def test_float_range_is_enforced(catalog) -> None:
    process = catalog.get("power_transform")
    error = _expect_error(process, '{"gamma": 0}', param="gamma")
    assert error.details["min"] == 0.01


def test_bool_only_accepts_booleans(catalog) -> None:
    process = catalog.get("intensity_slicing")
    assert parse_params(process, '{"preserve_background": false}')["preserve_background"] is False
    _expect_error(process, '{"preserve_background": 1}', param="preserve_background")


def test_select_rejects_unknown_option(catalog) -> None:
    process = catalog.get("gaussian_frequency_filter")
    error = _expect_error(process, '{"filter_type": "bandpass"}', param="filter_type")
    assert error.details["options"] == ["lowpass", "highpass"]
    assert parse_params(process, '{"filter_type": "highpass"}')["filter_type"] == "highpass"


def test_unknown_key_is_rejected(catalog) -> None:
    error = _expect_error(catalog.get("threshold"), '{"nope": 1}', param="nope")
    assert "desconhecido" in error.message


def test_malformed_json_is_rejected(catalog) -> None:
    error = _expect_error(catalog.get("threshold"), "{k: 1}")
    assert "JSON" in error.message


@pytest.mark.parametrize("raw", ["[]", '"texto"', "1"])
def test_non_object_json_is_rejected(catalog, raw: str) -> None:
    error = _expect_error(catalog.get("threshold"), raw)
    assert "objeto JSON" in error.message


def test_hidden_param_is_ignored(catalog) -> None:
    process = catalog.get("salt_pepper_noise")
    params = parse_params(
        process, '{"noise_type": "salt", "salt_probability": 0.3, "pepper_probability": 0.4}'
    )
    assert params == {"noise_type": "salt"}


def test_visible_param_receives_default(catalog) -> None:
    process = catalog.get("salt_pepper_noise")
    params = parse_params(process, '{"noise_type": "salt_and_pepper"}')
    assert params == {
        "noise_type": "salt_and_pepper",
        "salt_probability": 0.025,
        "pepper_probability": 0.025,
    }


def test_visible_param_sent_by_client_is_kept(catalog) -> None:
    process = catalog.get("salt_pepper_noise")
    params = parse_params(
        process, '{"noise_type": "salt_and_pepper", "salt_probability": 0.1}'
    )
    assert params["salt_probability"] == 0.1
    assert params["pepper_probability"] == 0.025


def test_constraint_less_equal_is_enforced(catalog) -> None:
    process = catalog.get("intensity_slicing")
    error = _expect_error(process, '{"a": 200, "b": 100}', param="b")
    assert error.details["params"] == ["a", "b"]
    assert "menor ou igual" in error.message
    assert parse_params(process, '{"a": 100, "b": 100}')["a"] == 100


def test_result_order_follows_catalog(catalog) -> None:
    process = catalog.get("intensity_slicing")
    params = parse_params(process, '{"b": 150, "a": 50}')
    assert list(params) == ["a", "b", "preserve_background"]
