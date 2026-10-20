# CureGenix VQE vs CAQE Benchmark Report

- Trials per molecule: 5
- Optimizer max iterations: 50
- CAQE starts per trial: 3
- Basis: STO-3G
- Execution: classical simulator; no quantum hardware

## Accuracy results

| Molecule | Reference (Ha) | Baseline mean ± SD error (Ha) | CAQE mean ± SD error (Ha) | CAQE wins | Mean error reduction |
|---|---:|---:|---:|---:|---:|
| Water | -1.663224164388 | 1.001469e-03 ± 5.596334e-04 | 4.771207e-04 ± 6.437575e-04 | 3/5 | 52.36% |
| LiH | -1.058116535137 | 2.654583e-04 ± 1.275075e-05 | 1.712122e-04 ± 1.164183e-04 | 4/5 | 35.50% |

## Runtime and evaluation results

| Molecule | Method | Wall runtime mean ± SD (s) | Evaluations mean ± SD |
|---|---|---:|---:|
| Water | Baseline VQE | 1.443 ± 0.731 | 364.2 ± 180.0 |
| Water | CAQE | 4.330 ± 1.206 | 1134.0 ± 257.7 |
| LiH | Baseline VQE | 2.207 ± 0.264 | 529.0 ± 63.8 |
| LiH | CAQE | 5.703 ± 0.567 | 1353.6 ± 133.5 |

## Method

Each trial uses a deterministic seed to generate three random initial parameter vectors. Baseline VQE uses the first vector; CAQE receives the same first vector plus two additional starts. The reference is the minimum of an explicitly constructed (1 alpha, 1 beta) sector, and the runner stops if this differs from the unrestricted four-qubit minimum beyond tolerance.

## Limitations

- Small active-space classical simulator experiments; no quantum hardware execution.
- CAQE uses up to three starts while baseline uses one, so resource budgets differ.
- Only two molecules and five trials per molecule are included; results are preliminary.
- The sector check assumes the stated Jordan-Wigner alpha/beta occupation-bit ordering; verify before making external scientific claims.
- LiH is a reduced two-electron, two-spatial-orbital model, not a full six-electron calculation.
- No quantum advantage, drug efficacy, or clinical claim is established.

## Files

- `benchmark_trials.csv`: per-trial data.
- `benchmark_summary.json`: machine-readable summary.
- `benchmark_report.md`: this report.
