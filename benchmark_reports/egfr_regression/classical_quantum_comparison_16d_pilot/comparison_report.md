# EGFR 16D Pilot: Classical vs Quantum-Kernel Comparison

## Design and alignment

- Same exact pilot compounds and targets: 256 train, 64 validation, 64 test.
- SMILES, pIC50 targets, scaffold labels, sample order, and seeded source row selection were checked against the original dataset before fitting.
- Classical preprocessing is reused from the saved pilot feature file. Its SVD, standardization, and angle scaling were fitted on training rows only; classical estimators were also fitted on those 256 rows only.
- No quantum simulation was rerun. Quantum test and validation metrics come from the saved pilot JSON.
- Both classical models use the same 16-dimensional saved pilot representation as the quantum feature map.

## Results

| Model | Validation MAE | Test MAE | Test RMSE | Test R² |
|---|---:|---:|---:|---:|
| Saved quantum Nyström SVR (4 landmarks) | 1.1293 | 0.9435 | 1.1234 | -0.0531 |
| Classical RBF-SVR on same saved 16D features | 0.8919 | 0.6476 | 0.9045 | 0.3172 |
| Classical random forest on same saved 16D features | 0.8850 | 0.6166 | 0.7839 | 0.4872 |

Quantum minus matched classical RBF-SVR test MAE: **+0.2959 pIC50**. Positive values mean higher error for the quantum-kernel model.

The matched classical RBF-SVR has lower test MAE and RMSE and higher test R² than the saved quantum-kernel pilot. **These results do not support a quantum advantage.**

## Landmark metadata correction

The pilot script and `quantum_kernel.landmarks` result field both specify **4 landmarks**. A limitations string in the saved pilot result incorrectly says 8; this comparison uses the verified count of 4 and records the source inconsistency rather than editing the original artifact.

The baseline metrics embedded in the pilot JSON are omitted from this comparison because they were calculated on the full 408-compound test split, not this 64-compound pilot test split.

## Limitations

- The quantum model’s per-compound predictions and kernel matrices were not saved, so its comparison is at split-metric level only.
- The 16D reduction retains 52.9% of the reported fingerprint variance; the model sees a compressed representation.
- The quantum kernel uses a classical statevector simulator, four landmarks, and fixed SVR settings. It was not run on quantum hardware.
- Classical settings were fixed in advance and not tuned. No test-set tuning or model selection was done.
- The assay cohort is heuristically curated; this pilot does not establish drug efficacy or clinical performance.

## Artifacts

- `comparison_results.json`: metrics, configuration, and alignment audit.
- `test_predictions_classical.csv`: exact test-compound identities, targets, and classical predictions.
- `benchmark_egfr_classical_quantum_comparison_16d_pilot.py`: reproducible comparison script.
