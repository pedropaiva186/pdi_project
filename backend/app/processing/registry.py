"""Registro dos handlers: id do catálogo → função de processamento.

A ordem do dicionário acompanha ``shared/processes.json``. Na inicialização, o app
confere que os ids do catálogo e do registro são exatamente os mesmos (ver
``services/implemented.py``).
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from . import color, frequency, intensity, noise, spatial
from .types import ProcessResult

Handler = Callable[[np.ndarray, dict], ProcessResult]

PROCESS_HANDLERS: dict[str, Handler] = {
    "rgb_split": color.rgb_split,
    "hsv_split": color.hsv_split,
    "threshold": intensity.threshold,
    "log_transform": intensity.log_transform,
    "power_transform": intensity.power_transform,
    "histogram_equalization": intensity.histogram_equalization,
    "intensity_slicing": intensity.intensity_slicing,
    "gaussian_blur": spatial.gaussian_blur,
    "median_filter": spatial.median_filter,
    "min_filter": spatial.min_filter,
    "max_filter": spatial.max_filter,
    "unsharp_mask": spatial.unsharp_mask,
    "laplacian_sharpen": spatial.laplacian_sharpen,
    "sobel": spatial.sobel,
    "adaptive_median": spatial.adaptive_median,
    "gaussian_frequency_filter": frequency.gaussian_frequency_filter,
    "butterworth_filter": frequency.butterworth_filter,
    "gaussian_noise": noise.gaussian_noise,
    "salt_pepper_noise": noise.salt_pepper_noise,
}
