"""Plotting components for the motor-imagery report."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import mne
import numpy as np

from .utils import channel_index, time_mask


def save_topomaps(
    epochs: mne.Epochs,
    *,
    band_name: str,
    task_maps: dict[str, np.ndarray],
    conditions: tuple[str, ...],
    figure_dir: Path,
) -> Path:
    if len(conditions) != 2:
        raise ValueError("Topomap summary expects exactly two conditions")

    first, second = conditions
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    maps = [
        (first.replace("_", " ").title(), task_maps[first]),
        (second.replace("_", " ").title(), task_maps[second]),
        (f"{first} - {second}", task_maps[first] - task_maps[second]),
    ]
    vmax = max(float(np.nanmax(np.abs(data))) for _, data in maps)
    vmax = max(vmax, 1.0)

    for ax, (title, data) in zip(axes, maps):
        im, _ = mne.viz.plot_topomap(
            data,
            epochs.info,
            axes=ax,
            show=False,
            cmap="RdBu_r",
            vlim=(-vmax, vmax),
            contours=6,
        )
        ax.set_title(title)
    cbar = fig.colorbar(im, ax=axes, shrink=0.8)
    cbar.set_label("ERD/ERS (% task vs baseline)")
    fig.suptitle(f"{band_name} task-period topography")

    path = figure_dir / f"{band_name}_topomaps.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def save_roi_timecourses(
    epochs: mne.Epochs,
    *,
    band_name: str,
    erd_by_condition: dict[str, np.ndarray],
    conditions: tuple[str, ...],
    roi_channels: tuple[str, ...],
    figure_dir: Path,
    task: tuple[float, float],
) -> Path:
    fig, axes = plt.subplots(
        1,
        len(roi_channels),
        figsize=(4.5 * len(roi_channels), 3.8),
        sharey=True,
        constrained_layout=True,
    )
    axes = np.atleast_1d(axes)
    colors = ("#1f77b4", "#d62728", "#2ca02c", "#9467bd")

    for ax, channel in zip(axes, roi_channels):
        ch_idx = channel_index(epochs, channel)
        for condition, color in zip(conditions, colors):
            trace = erd_by_condition[condition][:, ch_idx, :].mean(axis=0)
            ax.plot(epochs.times, trace, label=condition, color=color, linewidth=1.8)
        ax.axvspan(0.0, task[0], color="#d9d9d9", alpha=0.35)
        ax.axvspan(task[0], task[1], color="#e6f2ff", alpha=0.35)
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.axvline(task[0], color="black", linewidth=0.8, linestyle="--")
        ax.set_title(channel)
        ax.set_xlabel("Time (s)")
    axes[0].set_ylabel("ERD/ERS (% baseline)")
    axes[-1].legend(loc="best", frameon=False)
    fig.suptitle(f"{band_name} ERD/ERS time courses")

    path = figure_dir / f"{band_name}_roi_timecourses.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def save_roi_bars(
    epochs: mne.Epochs,
    *,
    band_name: str,
    erd_by_condition: dict[str, np.ndarray],
    conditions: tuple[str, ...],
    roi_channels: tuple[str, ...],
    figure_dir: Path,
    task: tuple[float, float],
) -> Path:
    task_mask = time_mask(epochs.times, task)
    x = np.arange(len(roi_channels))
    width = min(0.8 / len(conditions), 0.36)
    offsets = (np.arange(len(conditions)) - (len(conditions) - 1) / 2.0) * width
    colors = ("#1f77b4", "#d62728", "#2ca02c", "#9467bd")

    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    for offset, condition, color in zip(offsets, conditions, colors):
        values = []
        for channel in roi_channels:
            ch_idx = channel_index(epochs, channel)
            values.append(erd_by_condition[condition][:, ch_idx, :][:, task_mask].mean())
        ax.bar(x + offset, values, width=width, label=condition, color=color)

    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(x, roi_channels)
    ax.set_ylabel("Mean task ERD/ERS (%)")
    ax.set_title(f"{band_name} task-period central-channel summary")
    ax.legend(frameon=False)

    path = figure_dir / f"{band_name}_roi_bars.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def save_tfr_maps(
    epochs: mne.Epochs,
    *,
    conditions: tuple[str, ...],
    tfr_channels: tuple[str, ...],
    figure_dir: Path,
    baseline: tuple[float, float],
    task: tuple[float, float],
) -> Path:
    freqs = np.arange(6.0, 36.0, 1.0)
    n_cycles = freqs / 2.0
    fig, axes = plt.subplots(
        len(tfr_channels),
        len(conditions),
        figsize=(5.5 * len(conditions), 3.25 * len(tfr_channels)),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )
    axes = np.atleast_2d(axes)
    images = []
    tfr_data = {}

    for condition in conditions:
        power = epochs[condition].compute_tfr(
            method="morlet",
            freqs=freqs,
            average=True,
            output="power",
            return_itc=False,
            n_cycles=n_cycles,
            use_fft=True,
            verbose="error",
        )
        baseline_mask = time_mask(power.times, baseline)
        base = power.data[:, :, baseline_mask].mean(axis=2, keepdims=True)
        tfr_data[condition] = 100.0 * (
            power.data / np.maximum(base, np.finfo(float).eps) - 1.0
        )

    vmax = max(float(np.nanpercentile(np.abs(data), 98)) for data in tfr_data.values())
    vmax = max(vmax, 1.0)

    for row, channel in enumerate(tfr_channels):
        ch_idx = channel_index(epochs, channel)
        for col, condition in enumerate(conditions):
            ax = axes[row, col]
            image = ax.imshow(
                tfr_data[condition][ch_idx],
                aspect="auto",
                origin="lower",
                extent=[epochs.times[0], epochs.times[-1], freqs[0], freqs[-1]],
                cmap="RdBu_r",
                vmin=-vmax,
                vmax=vmax,
            )
            images.append(image)
            ax.axvspan(0.0, task[0], color="black", alpha=0.08)
            ax.axvline(task[0], color="black", linewidth=0.8, linestyle="--")
            ax.set_title(f"{condition} {channel}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Frequency (Hz)")

    cbar = fig.colorbar(images[-1], ax=axes, shrink=0.82)
    cbar.set_label("ERD/ERS (% baseline)")
    fig.suptitle("C3/C4 time-frequency ERD/ERS")

    path = figure_dir / "c3_c4_tfr.png"
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path

