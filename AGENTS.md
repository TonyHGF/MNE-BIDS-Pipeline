# MNE-BIDS EEG Pipeline

## Goal

Set up the official MNE-BIDS-Pipeline for the in-house EEG data located at:

```text
/public/home/hugf2022/motor/in-house/20260616_hgf
```

The workflow should convert the BrainVision data to BIDS, run EEG quality control and preprocessing, and generate MNE reports.

## Requirements

1. Create an independent Conda environment for:

   * MNE-Python
   * MNE-BIDS
   * MNE-BIDS-Pipeline

2. Inspect the source data to determine:

   * recording files;
   * channels and channel types;
   * sampling frequency;
   * event markers;
   * montage information.

3. Keep the original data unchanged.

4. Use MNE-BIDS to convert the data into a valid BIDS dataset.

5. Configure and run the official MNE-BIDS-Pipeline. Do not reimplement its preprocessing, QC, caching, or report-generation logic.

6. Derive configuration values from the actual data. Document parameters that cannot be determined automatically.

7. Keep generated data and derivatives under `/public`.

## Deliverables

* `environment.yml`
* BIDS conversion script
* MNE-BIDS-Pipeline configuration
* simple run script
* concise `README.md`
* BIDS dataset
* preprocessing derivatives
* QC and HTML reports
