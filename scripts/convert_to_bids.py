#!/usr/bin/env python
"""Convert the in-house BrainVision recordings to BIDS with MNE-BIDS."""

from __future__ import annotations

import argparse
from pathlib import Path

import mne
from mne_bids import BIDSPath, write_raw_bids

from source_data import DEFAULT_BIDS_ROOT, DEFAULT_SOURCE_ROOT, channel_types, find_brainvision_runs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--bids-root", type=Path, default=DEFAULT_BIDS_ROOT)
    parser.add_argument("--subject", default="01")
    parser.add_argument("--session", default="20260616")
    parser.add_argument("--task", default="motor")
    parser.add_argument("--first-hand", choices=("left", "right"), default="left")
    parser.add_argument("--n-cycles", type=int, default=10)
    parser.add_argument("--fixation-duration", type=float, default=2.0)
    parser.add_argument("--task-duration", type=float, default=4.0)
    parser.add_argument("--break-duration", type=float, default=8.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def read_raw(vhdr_path: Path) -> mne.io.BaseRaw:
    raw = mne.io.read_raw_brainvision(vhdr_path, preload=False, verbose="error")
    raw.set_channel_types(channel_types(raw.ch_names), verbose="error")
    raw.set_montage("standard_1020", match_case=False, on_missing="ignore", verbose="error")
    raw.info["line_freq"] = 50.0
    keep = raw.annotations.description == "Comment/11"
    raw.set_annotations(raw.annotations[keep])
    return raw


def add_periodic_trial_annotations(
    raw: mne.io.BaseRaw,
    *,
    first_hand: str,
    n_cycles: int,
    fixation_duration: float,
    task_duration: float,
    break_duration: float,
) -> None:
    """Replace the start marker with periodic left/right trial annotations."""

    starts = raw.annotations.onset[raw.annotations.description == "Comment/11"]
    if len(starts) != 1:
        raise ValueError(f"Expected exactly one Comment/11 marker, got {len(starts)}")

    epoch_duration = fixation_duration + task_duration
    trial_period = fixation_duration + task_duration + break_duration
    cycle_period = 2 * trial_period
    hands = (first_hand, "right" if first_hand == "left" else "left")

    onsets = []
    durations = []
    descriptions = []
    for cycle_idx in range(n_cycles):
        cycle_start = starts[0] + cycle_idx * cycle_period
        for hand_idx, hand in enumerate(hands):
            onset = cycle_start + hand_idx * trial_period
            if onset + epoch_duration > raw.times[-1]:
                print(
                    f"warning: skipping {hand}_hand cycle {cycle_idx + 1}; "
                    f"epoch end {onset + epoch_duration:.2f}s exceeds "
                    f"recording end {raw.times[-1]:.2f}s"
                )
                continue
            onsets.append(onset)
            durations.append(epoch_duration)
            descriptions.append(f"{hand}_hand")

    if not descriptions:
        raise RuntimeError("No periodic trial annotations could be generated")
    raw.set_annotations(
        mne.Annotations(onset=onsets, duration=durations, description=descriptions)
    )


def main() -> None:
    args = parse_args()
    runs = find_brainvision_runs(args.source_root)
    args.bids_root.mkdir(parents=True, exist_ok=True)

    for run in runs:
        if not run.eeg_path.exists() or not run.vmrk_path.exists():
            raise FileNotFoundError(f"Missing sidecar for {run.vhdr_path}")
        if run.vmrk_data_file != run.vhdr_data_file:
            print(
                f"warning: {run.vmrk_path} declares DataFile={run.vmrk_data_file}; "
                f"header declares DataFile={run.vhdr_data_file}. "
                "MNE reads via the header path, so the original files are left unchanged."
            )

        raw = read_raw(run.vhdr_path)
        add_periodic_trial_annotations(
            raw,
            first_hand=args.first_hand,
            n_cycles=args.n_cycles,
            fixation_duration=args.fixation_duration,
            task_duration=args.task_duration,
            break_duration=args.break_duration,
        )
        raw.drop_channels(
            [name for name in ("x_dir", "y_dir", "z_dir") if name in raw.ch_names]
        )
        bids_path = BIDSPath(
            subject=args.subject,
            session=args.session,
            task=args.task,
            run=run.run,
            datatype="eeg",
            suffix="eeg",
            root=args.bids_root,
        )
        write_raw_bids(
            raw,
            bids_path,
            event_id={"left_hand": 1, "right_hand": 2},
            overwrite=args.overwrite,
            allow_preload=False,
            format="BrainVision",
            verbose=True,
        )
        print(f"Wrote run-{run.run} to {bids_path.directory}")


if __name__ == "__main__":
    main()
