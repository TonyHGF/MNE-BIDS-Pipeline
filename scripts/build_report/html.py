"""HTML rendering for report outputs."""

from __future__ import annotations

import html
from pathlib import Path

import mne


def write_motor_html(
    output: Path,
    *,
    epochs_path: Path,
    epochs: mne.Epochs,
    conditions: tuple[str, ...],
    baseline: tuple[float, float],
    task: tuple[float, float],
    figures: list[Path],
    rows: list[dict[str, str]],
) -> None:
    rel_figures = [path.relative_to(output.parent) for path in figures]
    table_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['band'])}</td>"
        f"<td>{html.escape(row['condition'])}</td>"
        f"<td>{html.escape(row['channel'])}</td>"
        f"<td>{row['mean']}</td>"
        f"<td>{row['sem']}</td>"
        f"<td>{row['n']}</td>"
        "</tr>"
        for row in rows
    )
    figure_blocks = "\n".join(
        f'<figure><img src="{html.escape(str(path))}" alt="{html.escape(path.stem)}">'
        f"<figcaption>{html.escape(path.stem.replace('_', ' '))}</figcaption></figure>"
        for path in rel_figures
    )
    condition_counts = ", ".join(
        f"{name}: {len(epochs[name])}" for name in conditions if name in epochs.event_id
    )

    output.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Motor Imagery Pattern Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #222; }}
    h1, h2 {{ margin-bottom: 0.35rem; }}
    code {{ background: #f2f2f2; padding: 2px 4px; border-radius: 3px; }}
    .note {{ max-width: 980px; line-height: 1.45; }}
    figure {{ margin: 28px 0; }}
    img {{ max-width: 1120px; width: 100%; border: 1px solid #ddd; }}
    figcaption {{ margin-top: 6px; color: #555; }}
    table {{ border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: right; }}
    th:nth-child(-n+3), td:nth-child(-n+3) {{ text-align: left; }}
    th {{ background: #eee; }}
  </style>
</head>
<body>
  <h1>Motor Imagery Pattern Report</h1>
  <p class="note">
    Source epochs: <code>{html.escape(str(epochs_path))}</code><br>
    Epochs: {len(epochs)} clean epochs ({html.escape(condition_counts)}).<br>
    Baseline window: {baseline[0]:.1f}-{baseline[1]:.1f} s fixation.
    Task window: {task[0]:.1f}-{task[1]:.1f} s motor imagery.
  </p>
  <p class="note">
    ERD/ERS is computed as <code>100 * (band power / baseline power - 1)</code>
    after band-pass filtering and Hilbert-envelope power estimation. Negative
    values indicate event-related desynchronization (ERD), which is the expected
    motor-imagery pattern in mu and beta rhythms over sensorimotor channels.
  </p>

  <h2>Figures</h2>
  {figure_blocks}

  <h2>Central-Channel Summary</h2>
  <table>
    <thead>
      <tr>
        <th>Band</th><th>Condition</th><th>Channel</th>
        <th>Mean task ERD/ERS (%)</th><th>SEM</th><th>N epochs</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )

