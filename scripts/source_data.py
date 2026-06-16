"""Utilities for the in-house BrainVision EEG source data."""

from __future__ import annotations

import configparser
import re
from dataclasses import dataclass
from pathlib import Path

EEG_CHANNELS = (
    "Fp1",
    "Fz",
    "F3",
    "F4",
    "F7",
    "F8",
    "Cz",
    "C3",
    "C4",
    "T7",
    "T8",
    "Pz",
    "P3",
    "P4",
    "O1",
    "O2",
)
MISC_CHANNELS = ("x_dir", "y_dir", "z_dir")
DEFAULT_SOURCE_ROOT = Path("/public/home/hugf2022/motor/in-house/20260616_hgf")
DEFAULT_BIDS_ROOT = Path("/public/home/hugf2022/motor/in-house/20260616_hgf_bids")


@dataclass(frozen=True)
class BrainVisionRun:
    """A discovered BrainVision recording."""

    run: str
    vhdr_path: Path
    eeg_path: Path
    vmrk_path: Path
    vhdr_data_file: str
    vhdr_marker_file: str
    vmrk_data_file: str | None


def _read_ini(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    text = path.read_text(encoding="utf-8-sig")
    section_start = text.find("[")
    if section_start == -1:
        raise ValueError(f"No INI sections found in {path}")
    metadata = text[section_start:]
    comment_start = metadata.find("\n[Comment]")
    if comment_start != -1:
        metadata = metadata[:comment_start]
    parser.read_string(metadata, source=str(path))
    return parser


def _run_id(path: Path) -> str:
    match = re.search(r"trial_?(\d+)", path.parent.name)
    if match is None:
        raise ValueError(f"Cannot infer run number from {path}")
    return f"{int(match.group(1)):02d}"


def find_brainvision_runs(source_root: Path) -> list[BrainVisionRun]:
    """Discover BrainVision header files and their declared sidecars."""

    vhdr_paths = sorted(source_root.glob("trial_*/*.vhdr"), key=_run_id)
    if not vhdr_paths:
        raise FileNotFoundError(f"No BrainVision .vhdr files found under {source_root}")

    runs = []
    for vhdr_path in vhdr_paths:
        parser = _read_ini(vhdr_path)
        common = parser["Common Infos"]
        data_file = common["DataFile"]
        marker_file = common["MarkerFile"]
        vmrk_path = vhdr_path.with_name(marker_file)
        vmrk_data_file = None
        if vmrk_path.exists():
            vmrk_parser = _read_ini(vmrk_path)
            vmrk_data_file = vmrk_parser.get("Common Infos", "DataFile", fallback=None)
        runs.append(
            BrainVisionRun(
                run=_run_id(vhdr_path),
                vhdr_path=vhdr_path,
                eeg_path=vhdr_path.with_name(data_file),
                vmrk_path=vmrk_path,
                vhdr_data_file=data_file,
                vhdr_marker_file=marker_file,
                vmrk_data_file=vmrk_data_file,
            )
        )
    return runs


def channel_types(channel_names: list[str]) -> dict[str, str]:
    """Return MNE channel type mapping for the known EEG and motion channels."""

    mapping = {}
    for channel in channel_names:
        if channel in EEG_CHANNELS:
            mapping[channel] = "eeg"
        elif channel in MISC_CHANNELS:
            mapping[channel] = "misc"
    return mapping


def marker_descriptions(vmrk_path: Path) -> list[str]:
    """Read marker descriptions from a BrainVision marker file."""

    descriptions = []
    for line in vmrk_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.startswith("Mk"):
            continue
        _, value = line.split("=", 1)
        fields = value.split(",")
        if len(fields) >= 2:
            marker_type, description = fields[0], fields[1]
            descriptions.append(f"{marker_type}/{description}" if description else marker_type)
    return descriptions
