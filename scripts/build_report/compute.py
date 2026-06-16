"""Numerical computations for motor-imagery report sections."""

from __future__ import annotations

import mne
import numpy as np

from .utils import channel_index, time_mask


def compute_band_erd(
    epochs: mne.Epochs,
    *,
    fmin: float,
    fmax: float,
    baseline: tuple[float, float],
    conditions: tuple[str, ...],
) -> dict[str, np.ndarray]:
    """Return per-condition ERD/ERS time courses in percent change."""

    band_epochs = epochs.copy().filter(
        fmin,
        fmax,
        method="fir",
        phase="zero-double",
        verbose="error",
    )
    band_epochs.apply_hilbert(envelope=True, verbose="error")

    erd_by_condition = {}
    baseline_mask = time_mask(band_epochs.times, baseline)
    eps = np.finfo(float).eps

    for condition in conditions:
        power = band_epochs[condition].get_data(copy=True) ** 2
        baseline_power = power[:, :, baseline_mask].mean(axis=2, keepdims=True)
        erd_by_condition[condition] = 100.0 * (
            power / np.maximum(baseline_power, eps) - 1.0
        )

    return erd_by_condition


def task_average(
    erd: np.ndarray,
    times: np.ndarray,
    task: tuple[float, float],
) -> np.ndarray:
    return erd[:, :, time_mask(times, task)].mean(axis=(0, 2))


def make_summary_rows(
    epochs: mne.Epochs,
    *,
    band_name: str,
    erd_by_condition: dict[str, np.ndarray],
    task: tuple[float, float],
    conditions: tuple[str, ...],
    roi_channels: tuple[str, ...],
) -> list[dict[str, str]]:
    task_mask = time_mask(epochs.times, task)
    rows = []
    for condition in conditions:
        for channel in roi_channels:
            ch_idx = channel_index(epochs, channel)
            values = erd_by_condition[condition][:, ch_idx, :][:, task_mask].mean(axis=1)
            rows.append(
                {
                    "band": band_name,
                    "condition": condition,
                    "channel": channel,
                    "mean": f"{values.mean():.2f}",
                    "sem": f"{(values.std(ddof=1) / np.sqrt(len(values))):.2f}",
                    "n": str(len(values)),
                }
            )
    return rows

