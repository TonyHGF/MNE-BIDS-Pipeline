"""Default settings for the motor-pattern report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from source_data import DEFAULT_BIDS_ROOT


DERIV_ROOT = DEFAULT_BIDS_ROOT / "derivatives" / "mne-bids-pipeline"
DEFAULT_EPOCHS = (
    DERIV_ROOT
    / "sub-01"
    / "ses-20260616"
    / "eeg"
    / "sub-01_ses-20260616_task-motor_proc-clean_epo.fif"
)
DEFAULT_OUTPUT = DERIV_ROOT / "motor-patterns" / "sub-01_ses-20260616_motor_patterns.html"


@dataclass(frozen=True)
class MotorReportConfig:
    """Parameters needed to build the motor-imagery report."""

    epochs_path: Path = DEFAULT_EPOCHS
    output_path: Path = DEFAULT_OUTPUT
    baseline: tuple[float, float] = (0.0, 2.0)
    task: tuple[float, float] = (2.0, 6.0)
    bands: dict[str, tuple[float, float]] | None = None
    conditions: tuple[str, ...] = ("left_hand", "right_hand")
    roi_channels: tuple[str, ...] = ("C3", "C4", "Cz")
    tfr_channels: tuple[str, ...] = ("C3", "C4")

    def band_definitions(self) -> dict[str, tuple[float, float]]:
        if self.bands is not None:
            return self.bands
        return {
            "mu": (8.0, 13.0),
            "beta": (13.0, 30.0),
        }

