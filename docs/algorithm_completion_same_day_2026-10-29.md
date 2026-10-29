# Same-day algorithm completion status — 2026-10-29

## VQE energy interpretation

The molecular workflow keeps the raw active-space eigenvalue distinct from the corrected electronic energy. It adds the active-space transformer constant to obtain the electronic energy, then adds nuclear repulsion for the total molecular energy. Convergence is reported only when the installed optimizer exposes a usable status; otherwise status availability is explicit. Energy-interpretation unit tests cover both local and WSL worker response paths.

The current Windows session cannot start/verify WSL: `Wsl/Service/E_ACCESSDENIED` (process return code `4294967295`). The adapter test suite consequently skipped the live H2 and VQE tests. No fresh H2/STO-3G calculation was claimed in this run. Previously recorded H2 values are not represented as a new verification.

## VQC experiment

`benchmark_egfr_vqc.py` trains a genuine Qiskit Machine Learning `VQC`: a trainable RealAmplitudes ansatz, ZZ feature map, cross-entropy objective, COBYLA optimizer, and local statevector sampler. It uses the existing curated EGFR biochemical IC50 cohort and the already saved Murcko scaffold-disjoint split. Active labels require `pIC50_min >= 7`; inactive labels require `pIC50_max <= 6`; borderline/discordant and invalid rows are excluded. Training-only SVD and scaling are used. A deterministic 64-per-class subset of training rows is used for the VQC and the RBF-SVM baseline; validation and test labels are held out.

Run details and per-row split/prediction records are in `benchmark_reports/egfr_regression/vqc_same_day_final/`. On the 311-row held-out test set:

| Model | Accuracy | Balanced accuracy | ROC-AUC | Runtime |
|---|---:|---:|---:|---:|
| VQC | 0.6431 | 0.6479 | 0.6605 | 5.73 s |
| RBF-SVM | 0.7781 | 0.8496 | 0.9112 | 0.0025 s |

This is one small prototype split with a small balanced training subset. The classical model performs better; no quantum advantage is indicated. The labels are retrospective threshold-derived biochemical activity proxies, not evidence of efficacy, target engagement, or binding.

The read-only endpoint `/api/vqc/egfr` serves the saved result; it does not start training. The dashboard shows VQC results separately from the quantum-kernel SVM/SVR demo.

## Other algorithms

| Algorithm | Status |
|---|---|
| VQE | Implemented; energy-component mocks pass. Fresh WSL/PySCF H2 validation blocked by `E_ACCESSDENIED`. |
| VQC | Implemented, trained, and tested on the existing EGFR cohort; classical RBF-SVM is better on the held-out split. |
| QGNN | Incomplete. No existing graph-learning implementation was found and PyTorch/PyG are absent from the current environment. No ordinary GNN or unrelated quantum model is labeled QGNN. |
| Quantum-kernel SVM/SVR | Existing separate demo/pilot remains accurately labeled and unchanged. Its historical benchmark results were not modified. |
| Classical baselines | Existing scaffold regression results remain unchanged; the added classification baseline is the matched RBF-SVM in the VQC report. |

## Verification performed

- `.venv-win\\Scripts\\python.exe benchmark_egfr_vqc.py` — completed and saved a new result directory.
- `.venv-win\\Scripts\\python.exe -m unittest tests.test_vqc tests.test_vqc_api tests.test_quantum_energy_interpretation tests.test_wsl_quantum_adapter tests.test_wsl_quantum_adapter_failures tests.test_quantum_resource_policy tests.test_target_aware_generation tests.test_target_identity_policy_evaluation tests.test_target_identity_policy_m6 tests.test_egfr_classical_quantum_comparison tests.test_egfr_scaffold_validation tests.test_benchmark_api -v` — 82 tests passed, 3 live WSL tests skipped due to `Wsl/Service/E_ACCESSDENIED`.

The VQC experiment is a simulator-based prototype. The available results do not establish quantum advantage, and no protein-binding or clinical claims are made.
