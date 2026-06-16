"""Small shared helpers for report computations and plots."""

from __future__ import annotations

import mne
import numpy as np


def time_mask(times: np.ndarray, window: tuple[float, float]) -> np.ndarray:
    start, stop = window
    return (times >= start) & (times < stop)


def channel_index(epochs: mne.Epochs, channel: str) -> int:
    if channel not in epochs.ch_names:
        raise ValueError(f"Required channel not found: {channel}")
    return epochs.ch_names.index(channel)

