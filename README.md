# MNE-BIDS EEG Pipeline

This repository contains a lightweight wrapper around the official
MNE-BIDS and MNE-BIDS-Pipeline tools for the in-house BrainVision EEG data.

## Data Layout

Raw source data is kept unchanged at:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf
```

Generated BIDS data and derivatives are stored under `/public`:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf_bids
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline
```

Run-specific inspection results are written under `reports/` and should be
treated as generated records, not source code.

## Environment

Create the dedicated Conda environment:

```bash
conda env create -f environment.yml
conda activate eeg-preprocessing
```

On the cluster, `mamba` is usually faster for this scientific environment:

```bash
mamba env create -f environment.yml
conda activate eeg-preprocessing
```

If the environment already exists, update it with:

```bash
conda env update -n eeg-preprocessing -f environment.yml
```

## Inspect Source Data

Run a local metadata inspection / source-data QC:

```bash
bash run_pipeline.sh inspect local
```

`qc` is kept as an alias for the same source inspection:

```bash
bash run_pipeline.sh qc local
```

This writes:

```text
reports/source_inspection.json
```

The inspection reads the BrainVision headers with MNE and reports recording
paths, channel names and types, sampling frequency, annotations, event marker
counts, and sidecar filename mismatches. It does not modify source data.

## Convert To BIDS

Run BIDS conversion locally:

```bash
bash run_pipeline.sh convert local
```

Or submit it to Slurm CPU resources:

```bash
bash run_pipeline.sh convert server
```

The conversion uses `mne_bids.write_raw_bids`, applies the standard 10-20
montage to matching EEG channels, keeps `x_dir`, `y_dir`, and `z_dir` in the
MNE raw object as misc channels, and excludes those auxiliary motion channels
from BIDS writing because the official EEG BIDS dataset should contain the EEG
recording channels used by MNE-BIDS-Pipeline.

By default, the conversion avoids overwriting existing BIDS files. To force an
overwrite, run the Python script directly:

```bash
python scripts/convert_to_bids.py --overwrite
```

## Run MNE-BIDS-Pipeline

Run the official MNE-BIDS-Pipeline after conversion:

```bash
bash run_pipeline.sh pipeline server
```

For a full workflow:

```bash
bash run_pipeline.sh all server
```

The pipeline configuration is:

```text
config/pipeline_config.py
```

Slurm logs are written to:

```text
logs/%x_%j.out
logs/%x_%j.err
```

## Preprocessing Configuration

The BIDS conversion expands each run's single start marker into periodic trial
events using the recorded task structure:

```text
2 s fixation + 4 s task + 8 s break
left and right hand once per cycle
10 cycles per run
```

Epochs are segmented as fixation plus task:

```text
epochs_tmin = 0.0
epochs_tmax = 6.0
baseline = (0.0, 2.0)
```

The current pipeline applies:

```text
average EEG reference
standard_1020 montage
1-40 Hz band-pass filter
50 Hz notch filter
ICA fitting with 10 Picard components
Fp1 as a proxy EOG channel
500 uV EEG peak-to-peak rejection for ICA fitting and final cleaned epochs
```

Run-specific epoch counts, job IDs, and QC interpretations belong in generated
run summaries, for example:

```text
reports/run_summary.md
```

Official MNE-BIDS-Pipeline HTML reports are written under the derivatives tree:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline
```

## Motor-Pattern Report

An additional exploratory motor-imagery report can be generated from the clean
epochs:

```bash
conda activate eeg-preprocessing
python scripts/motor_report.py
```

The report builder is split into reusable pieces under `scripts/build_report/`:

```text
config.py   default paths and report parameters
compute.py  ERD/ERS and summary-table computations
plots.py    topomap, ROI time-course, bar, and time-frequency figures
html.py     HTML rendering
builder.py  composition of the report sections
```

The report is written to:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/motor-patterns/sub-01_ses-20260616_motor_patterns.html
```

It contains:

```text
mu-band (8-13 Hz) ERD/ERS topomaps and C3/C4/Cz time courses
beta-band (13-30 Hz) ERD/ERS topomaps and C3/C4/Cz time courses
C3/C4 6-35 Hz time-frequency ERD/ERS maps
central-channel summary table for left_hand and right_hand
```

ERD/ERS is computed as:

```text
100 * (task-period band power / fixation-baseline band power - 1)
```

Negative values indicate ERD. This report is exploratory and should be treated
as a quality-control and hypothesis-generation view rather than a validated
motor imagery biomarker.

## Notes And Assumptions

- The five `trial_*` folders are mapped to BIDS runs `01` through `05`.
- Subject is set to `01`; session is set to `20260616`.
- Task name is set to `motor`.
- Trial events are generated from the periodic design because each recording
  only contains the run start marker.
- EEG montage is set to `standard_1020`.
- No dedicated EOG channel was found. `Fp1` is configured as a proxy for
  automated ICA EOG detection, and any component rejection should be reviewed
  manually in the HTML report and component TSV.
- Full preprocessing, QC, and report generation are handled by the official
  `mne_bids_pipeline` command.
