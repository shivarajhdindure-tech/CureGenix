# VQC + molecular QGNN activity-proxy milestone — 2026-10-29

## Reusable training and inference

The earlier `vqc_same_day_final` directory contained predictions, metrics, and split audit records, but no fitted classifier or fitted feature transformations. A separate offline experiment now trains fresh deterministic VQC and QGNN models on the same saved EGFR scaffold-disjoint split and writes reusable model weights and training-only transformations to `benchmark_reports/egfr_regression/vqc_qgnn_same_day_v3/`. The script refuses to overwrite this directory. API requests only load these artifacts; they never train.

For a new valid SMILES, the shared API parses the molecule once with RDKit. The VQC path creates its 2048-bit Morgan fingerprint and applies its stored SVD and scalers. The QGNN path uses the same parsed molecule to form atom/bond features, perform one bond-weighted message-passing round and mean/max graph readout, and apply its stored graph representation SVD/scalers. The circuit consumes the resulting graph angles. Each model runs independently; missing artifacts return `not_trained`, inference exceptions return `failed`, and no substitute prediction is generated.

## QGNN definition and scope

This prototype is a small hybrid quantum graph classifier. Its graph operation aggregates neighboring atom features with bond weights, applies `tanh`, and pools node mean/max plus bond means. A four-qubit parameterized circuit encodes this graph vector, applies trainable RY/RZ rotations and entangling CNOT operations, and uses the measured first-qubit probability as the graph-level active-class score. COBYLA minimizes binary cross entropy. The circuit is simulated with Qiskit Statevector on a classical CPU. This is not a protein structure or binding model.

## Scaffold-held-out comparison

All models use the existing train/validation/test split, seed 42, and the same balanced training subset of 64 examples per class. There are 1,679 labeled training, 378 validation, and 311 test rows. Preprocessing is fit using labeled training rows only. VQC and classical RBF-SVM use the same Morgan/SVD/scaled features; QGNN uses molecular graph features with its own training-fitted graph projection, as required by the different model input. The final run artifacts are in `benchmark_reports/egfr_regression/vqc_qgnn_same_day_v3/`.

| Model | Test accuracy | Balanced accuracy | ROC-AUC |
|---|---:|---:|---:|
| VQC | 0.6431 | 0.6479 | 0.6605 |
| QGNN | 0.5563 | 0.5939 | 0.6145 |
| Classical RBF-SVM | 0.7781 | 0.8496 | 0.9112 |

The QGNN optimizer reached its configured 24 objective evaluations and did not report convergence. The model and predictions are retained with status `completed_max_evaluations`, not described as converged. The QGNN and VQC scores are uncalibrated. The classical baseline performed better on this single split; no quantum advantage is indicated.

The labels are retrospective threshold-derived biochemical activity proxies (`pIC50_min >= 7` active; `pIC50_max <= 6` inactive). Borderline/discordant and invalid rows are excluded. They are not measurements for new compounds and do not establish binding, efficacy, or safety.

## API and UI

- `GET /api/molecular-activity/egfr` returns saved evaluation metrics only.
- `POST /api/molecular-activity/predict` accepts `{ "smiles": "..." }` and returns canonical SMILES plus separate VQC, QGNN, and classical baseline model statuses and predictions. Inference currently runs VQC and QGNN; the classical baseline is shown for held-out evaluation, not new-molecule inference.
- The dashboard section displays saved comparison metrics and per-model prediction status, identifiers, uncalibrated scores, and runtime.

No dependency was installed. PyTorch/PyG were absent; the implementation uses installed RDKit, Qiskit, Qiskit Machine Learning, NumPy/SciPy, and scikit-learn.
