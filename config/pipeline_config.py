"""MNE-BIDS-Pipeline configuration for the in-house EEG dataset."""

from pathlib import Path

bids_root = Path("/public/home/hugf2022/motor/in-house/20260616_hgf_bids")
deriv_root = bids_root / "derivatives" / "mne-bids-pipeline"

subjects = ["01"]
sessions = ["20260616"]
runs = ["01", "02", "03", "04", "05"]
task = "motor"
data_type = "eeg"
ch_types = ["eeg"]

interactive = False
n_jobs = 1
parallel_backend = "loky"

eeg_reference = "average"
eeg_template_montage = "standard_1020"
eog_channels = ["Fp1"]

l_freq = 1.0
h_freq = 40.0
notch_freq = 50.0
raw_resample_sfreq = None

conditions = ["left_hand", "right_hand"]
epochs_tmin = 0.0
epochs_tmax = 6.0
baseline = (0.0, 2.0)
reject = {"eeg": 500e-6}

spatial_filter = "ica"
ica_reject = {"eeg": 500e-6}
ica_algorithm = "picard"
ica_n_components = 10
ica_decim = 2
ica_use_ecg_detection = False
ica_use_eog_detection = True
ica_use_icalabel = False
run_source_estimation = False
find_flat_channels_meg = False
find_noisy_channels_meg = False

on_error = "abort"
report_add_epochs_image_kwargs = None
