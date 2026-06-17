from __future__ import annotations

import json
from pathlib import Path

import joblib
import mne
import numpy as np
from mne.decoding import CSP
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedShuffleSplit, cross_val_score
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parent
RANDOM_STATE = 42
TEST_SIZE = 0.2


def main() -> None:
    x_path = ROOT / "preprocessed_me_epochs.npy"
    y_path = ROOT / "preprocessed_attention_me_labels.npy"
    if not x_path.exists() or not y_path.exists():
        raise FileNotFoundError(
            "Preprocessed files are missing. Run preprocess_attention_me_mne.py first."
        )

    X = np.load(x_path).astype(np.float64, copy=False)
    y = np.load(y_path)
    if X.ndim != 3:
        raise ValueError(f"Expected X to be 3D n_epochs x n_channels x n_times, got {X.shape}")
    if len(X) != len(y):
        raise ValueError(f"X and y length mismatch: {len(X)} vs {len(y)}")

    splitter = StratifiedShuffleSplit(
        n_splits=1,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    train_idx, test_idx = next(splitter.split(X, y))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    clf = Pipeline(
        steps=[
            (
                "csp",
                CSP(
                    n_components=6,
                    reg="ledoit_wolf",
                    log=True,
                    norm_trace=False,
                    component_order="mutual_info",
                ),
            ),
            ("lda", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
        ]
    )

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    y_score = clf.predict_proba(X_test)

    cv = StratifiedShuffleSplit(
        n_splits=20,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    cv_scores = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")

    label_names = ["left_hand", "right_hand"]
    report = classification_report(
        y_test,
        y_pred,
        target_names=label_names,
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    accuracy = accuracy_score(y_test, y_pred)

    out_dir = ROOT / "csp_classification_results"
    out_dir.mkdir(exist_ok=True)
    joblib.dump(clf, out_dir / "csp_lda_model.joblib")
    np.save(out_dir / "test_indices.npy", test_idx)
    np.save(out_dir / "test_labels.npy", y_test)
    np.save(out_dir / "test_predictions.npy", y_pred)
    np.save(out_dir / "test_probabilities.npy", y_score)

    result = {
        "description": "CSP + LDA classification for left/right motor execution.",
        "input_epochs": "preprocessed_me_epochs.npy",
        "input_labels": "preprocessed_attention_me_labels.npy",
        "label_map": {"0": "left_hand", "1": "right_hand"},
        "data_shape": list(X.shape),
        "train_test_split": {
            "method": "StratifiedShuffleSplit",
            "train_ratio": 0.8,
            "test_ratio": 0.2,
            "random_state": RANDOM_STATE,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "train_counts": {
                "left_hand": int(np.sum(y_train == 0)),
                "right_hand": int(np.sum(y_train == 1)),
            },
            "test_counts": {
                "left_hand": int(np.sum(y_test == 0)),
                "right_hand": int(np.sum(y_test == 1)),
            },
        },
        "model": {
            "pipeline": "MNE CSP + sklearn LinearDiscriminantAnalysis",
            "csp": {
                "n_components": 6,
                "reg": "ledoit_wolf",
                "log": True,
                "norm_trace": False,
                "component_order": "mutual_info",
            },
            "lda": {"solver": "lsqr", "shrinkage": "auto"},
        },
        "held_out_test": {
            "accuracy": float(accuracy),
            "confusion_matrix_rows_true_cols_pred": cm.tolist(),
            "classification_report": report,
            "test_indices": test_idx.tolist(),
            "y_true": y_test.tolist(),
            "y_pred": y_pred.tolist(),
            "probabilities": y_score.tolist(),
        },
        "repeated_stratified_shuffle_cv": {
            "n_splits": 20,
            "test_ratio": TEST_SIZE,
            "accuracy_scores": cv_scores.tolist(),
            "mean_accuracy": float(cv_scores.mean()),
            "std_accuracy": float(cv_scores.std(ddof=1)),
        },
        "outputs": {
            "model": "csp_classification_results/csp_lda_model.joblib",
            "test_indices": "csp_classification_results/test_indices.npy",
            "test_labels": "csp_classification_results/test_labels.npy",
            "test_predictions": "csp_classification_results/test_predictions.npy",
            "test_probabilities": "csp_classification_results/test_probabilities.npy",
            "summary": "csp_classification_results/csp_classification_summary.json",
        },
        "versions": {
            "mne": mne.__version__,
        },
    }
    (out_dir / "csp_classification_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Saved results to {out_dir}")
    print(f"Held-out accuracy: {accuracy:.3f}")
    print(f"Confusion matrix [[left,left/right], [right,left/right]]: {cm.tolist()}")
    print(f"Repeated split CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std(ddof=1):.3f}")


if __name__ == "__main__":
    main()
