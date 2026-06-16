#!/usr/bin/env python
"""Inspect the in-house BrainVision source data without modifying it."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import mne

from source_data import DEFAULT_SOURCE_ROOT, channel_types, find_brainvision_runs, marker_descriptions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/source_inspection.json"),
        help="Path for the JSON inspection summary.",
    )
    return parser.parse_args()


def inspect_run(vhdr_path: Path, vmrk_path: Path) -> dict:
    raw = mne.io.read_raw_brainvision(vhdr_path, preload=False, verbose="error")
    raw.set_channel_types(channel_types(raw.ch_names), verbose="error")

    annotations = list(raw.annotations.description)
    marker_counts = Counter(marker_descriptions(vmrk_path))
    mapped_types = channel_types(raw.ch_names)
    eeg_channels = [name for name in raw.ch_names if mapped_types.get(name) == "eeg"]
    misc_channels = [name for name in raw.ch_names if mapped_types.get(name) == "misc"]

    montage_status = "standard_1020_names_match" if set(eeg_channels) else "unknown"
    return {
        "sfreq": raw.info["sfreq"],
        "n_channels": len(raw.ch_names),
        "duration_sec": raw.n_times / raw.info["sfreq"],
        "channels": raw.ch_names,
        "eeg_channels": eeg_channels,
        "misc_channels": misc_channels,
        "annotations": annotations,
        "marker_counts": dict(sorted(marker_counts.items())),
        "montage_status": montage_status,
    }


def main() -> None:
    args = parse_args()
    runs = find_brainvision_runs(args.source_root)
    summary = {
        "source_root": str(args.source_root),
        "n_runs": len(runs),
        "runs": [],
        "notes": [
            "Original BrainVision files are read-only inputs for this workflow.",
            "EEG channel names match standard 10-20 labels used by MNE's standard_1020 montage.",
            "x_dir, y_dir, and z_dir are treated as misc channels.",
        ],
    }

    for run in runs:
        missing = [
            str(path)
            for path in (run.vhdr_path, run.eeg_path, run.vmrk_path)
            if not path.exists()
        ]
        info = inspect_run(run.vhdr_path, run.vmrk_path)
        summary["runs"].append(
            {
                "run": run.run,
                "vhdr": str(run.vhdr_path),
                "eeg": str(run.eeg_path),
                "vmrk": str(run.vmrk_path),
                "vhdr_data_file": run.vhdr_data_file,
                "vhdr_marker_file": run.vhdr_marker_file,
                "vmrk_data_file": run.vmrk_data_file,
                "vmrk_data_file_matches_vhdr": run.vmrk_data_file == run.vhdr_data_file,
                "missing_sidecars": missing,
                **info,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote source inspection summary to {args.output}")
    for run in summary["runs"]:
        print(
            f"run-{run['run']}: {run['n_channels']} channels, "
            f"{run['sfreq']} Hz, annotations={run['annotations']}"
        )
        if not run["vmrk_data_file_matches_vhdr"]:
            print(
                f"  warning: marker DataFile={run['vmrk_data_file']} "
                f"but header DataFile={run['vhdr_data_file']}"
            )


if __name__ == "__main__":
    main()
