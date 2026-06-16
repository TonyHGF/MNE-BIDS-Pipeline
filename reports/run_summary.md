# Run Summary

This file records the current run-specific outputs for the in-house EEG
workflow. It is generated documentation, separate from the stable project
README.

## Source Inspection

The source inspection found five BrainVision recordings, treated as one subject,
one session, and five BIDS runs:

```text
sub-01/ses-20260616/task-motor/run-01..05
```

The recordings contain 16 EEG channels and three motion channels:

```text
EEG:  Fp1 Fz F3 F4 F7 F8 Cz C3 C4 T7 T8 Pz P3 P4 O1 O2
Misc: x_dir y_dir z_dir
```

Sampling frequency is 250 Hz. Each run contains `Comment/11`; `trial_5` also
contains BrainVision `LostSamples` segment annotations. The marker files for
`trial_1` and `trial_4` declare stale `DataFile` values, while their headers
point to the correct EEG files. MNE reads through the header files, and the
original files are left unchanged.

Detailed source inspection:

```text
reports/source_inspection.json
```

## Latest Preprocessing Job

```text
job: 3677836
partition: bme_cpu
resources: 2 CPU, 12G memory
state: COMPLETED, exit code 0:0
elapsed: 00:01:12
```

The BIDS conversion expanded each run's single start marker into periodic trial
events. This produced 20 events per run and 100 events total:

```text
left_hand:  50 events
right_hand: 50 events
```

Final epoch counts from the latest pipeline run:

```text
task epochs before ICA/PTP cleaning: 100
ICA fitting epochs after PTP rejection: 99
ICA-reconstructed epochs before final PTP rejection: 100
final clean epochs: 99
```

The rejected epoch is a clear high-amplitude outlier. The automated ICA run did
not mark any ICA component as EOG-related:

```text
sub-01_ses-20260616_proc-ica_components.tsv: all 10 components are marked good
```

This means the workflow has run ICA and produced ICA-cleaning artifacts, but it
has not automatically removed an eye-movement component. This is expected to be
hard to validate because the recording has no dedicated EOG channel; `Fp1` is
only a proxy. The ICA component maps and EOG score plots should be manually
reviewed before marking components bad.

ICA review images:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/review
```

Important derivative files:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/sub-01/ses-20260616/eeg/sub-01_ses-20260616_proc-ica_ica.fif
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/sub-01/ses-20260616/eeg/sub-01_ses-20260616_proc-ica_components.tsv
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/sub-01/ses-20260616/eeg/sub-01_ses-20260616_task-motor_proc-clean_epo.fif
```

Official preprocessing / QC HTML reports:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/sub-01/ses-20260616/eeg/sub-01_ses-20260616_report.html
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/sub-average/ses-20260616/eeg/sub-average_ses-20260616_report.html
```

## Motor-Pattern Report

The exploratory motor-pattern report was generated from the clean epochs:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf_bids/derivatives/mne-bids-pipeline/motor-patterns/sub-01_ses-20260616_motor_patterns.html
```

The current single-subject result shows task-related spectral changes, but not a
clean, canonical contralateral C3/C4 mu/beta ERD pattern. Interpret it as a
quality-control and hypothesis-generation view rather than a validated motor
imagery biomarker.
