"""High-level composition for the motor-imagery report."""

from __future__ import annotations

from pathlib import Path

import mne

from .compute import compute_band_erd, make_summary_rows, task_average
from .config import MotorReportConfig
from .html import write_motor_html
from .plots import save_roi_bars, save_roi_timecourses, save_tfr_maps, save_topomaps


def build_motor_report(config: MotorReportConfig) -> Path:
    """Build the motor-imagery ERD/ERS HTML report and return its path."""

    output = config.output_path
    figure_dir = output.parent / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    epochs = mne.read_epochs(config.epochs_path, preload=True, verbose="error")
    epochs.pick("eeg")

    figures = []
    rows = []
    for band_name, (fmin, fmax) in config.band_definitions().items():
        erd_by_condition = compute_band_erd(
            epochs,
            fmin=fmin,
            fmax=fmax,
            baseline=config.baseline,
            conditions=config.conditions,
        )
        task_maps = {
            condition: task_average(erd, epochs.times, config.task)
            for condition, erd in erd_by_condition.items()
        }
        figures.extend(
            [
                save_topomaps(
                    epochs,
                    band_name=band_name,
                    task_maps=task_maps,
                    conditions=config.conditions,
                    figure_dir=figure_dir,
                ),
                save_roi_timecourses(
                    epochs,
                    band_name=band_name,
                    erd_by_condition=erd_by_condition,
                    conditions=config.conditions,
                    roi_channels=config.roi_channels,
                    figure_dir=figure_dir,
                    task=config.task,
                ),
                save_roi_bars(
                    epochs,
                    band_name=band_name,
                    erd_by_condition=erd_by_condition,
                    conditions=config.conditions,
                    roi_channels=config.roi_channels,
                    figure_dir=figure_dir,
                    task=config.task,
                ),
            ]
        )
        rows.extend(
            make_summary_rows(
                epochs,
                band_name=band_name,
                erd_by_condition=erd_by_condition,
                task=config.task,
                conditions=config.conditions,
                roi_channels=config.roi_channels,
            )
        )

    figures.append(
        save_tfr_maps(
            epochs,
            conditions=config.conditions,
            tfr_channels=config.tfr_channels,
            figure_dir=figure_dir,
            baseline=config.baseline,
            task=config.task,
        )
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    write_motor_html(
        output,
        epochs_path=config.epochs_path,
        epochs=epochs,
        conditions=config.conditions,
        baseline=config.baseline,
        task=config.task,
        figures=figures,
        rows=rows,
    )
    return output

