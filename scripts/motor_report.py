#!/usr/bin/env python
"""Create a motor-imagery ERD/ERS HTML report from clean epochs."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_report.builder import build_motor_report
from build_report.config import DEFAULT_EPOCHS, DEFAULT_OUTPUT, MotorReportConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=Path, default=DEFAULT_EPOCHS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--baseline", type=float, nargs=2, default=(0.0, 2.0))
    parser.add_argument("--task", type=float, nargs=2, default=(2.0, 6.0))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = build_motor_report(
        MotorReportConfig(
            epochs_path=args.epochs,
            output_path=args.output,
            baseline=tuple(args.baseline),
            task=tuple(args.task),
        )
    )
    print(f"Wrote motor-pattern report to {output}")


if __name__ == "__main__":
    main()
