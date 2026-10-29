/**
 * Verified EGFR Benchmark & Validation Data
 *
 * Source artifacts:
 * - benchmark_reports/egfr_regression/scaffold_validation/results.json
 * - benchmark_reports/egfr_regression/scaffold_validation/report.md
 * - benchmark_reports/egfr_regression/classical_quantum_comparison_16d_pilot/comparison_results.json
 * - benchmark_reports/egfr_regression/classical_quantum_comparison_16d_pilot/comparison_report.md
 *
 * Metrics must never be fabricated or combined into misleading cross-split comparisons.
 */

export const STATIC_BENCHMARK_DATA = {
  status_indicators: {
    classical_validation: "Classical scaffold validation complete",
    quantum_validation: "Repeated scaffold-split quantum validation pending",
  },
  dataset: {
    name: "EGFR Biochemical IC50 / pIC50 (ChEMBL)",
    total_curated_rows: 2996,
    evaluated_compounds: 2995,
    unique_murcko_scaffolds: 1129,
    excluded_compounds: [
      {
        row_index: 0,
        reason: "Blank or invalid SMILES; RDKit cannot verify a Murcko scaffold.",
        canonical_smiles: "",
      },
    ],
    compound_identity: "Aggregated ChEMBL molecule IDs, canonical SMILES, median pIC50 target",
  },
  five_split_classical: {
    evaluation_scope: "Full-cohort repeated scaffold validation (2,995 compounds, 1,129 scaffolds)",
    protocol: {
      method: "Repeated nested GroupShuffleSplit by recomputed Murcko scaffold ID",
      seeds: [11, 23, 42, 87, 101],
      split_ratio: "~60% train / 20% validation / 20% test by scaffold groups",
      scaffold_overlap: "Zero scaffold overlap across partitions in every seed (verified)",
      selection_criterion: "Validation MAE only; held-out test labels never used for model selection or preprocessing",
      final_fitting: "Selected hyperparameter models refit on train+validation before test evaluation",
    },
    models: {
      rbf_svr: {
        name: "RBF-SVR",
        pipeline: "128-component TruncatedSVD + StandardScaler (fit on training only)",
        mae: {
          mean: 0.5607,
          sample_std: 0.0689,
          formatted: "0.5607 ± 0.0689",
          raw_mean: 0.560718,
          per_split: [0.4990, 0.6213, 0.5477, 0.4928, 0.6428],
        },
        rmse: {
          mean: 0.7609,
          sample_std: 0.0883,
          formatted: "0.7609 ± 0.0883",
          raw_mean: 0.760883,
          per_split: [0.6928, 0.8475, 0.7516, 0.6591, 0.8535],
        },
        r2: {
          mean: 0.6061,
          sample_std: 0.0496,
          formatted: "0.6061 ± 0.0496",
          raw_mean: 0.606132,
          per_split: [0.6496, 0.5919, 0.5956, 0.6578, 0.5358],
        },
      },
      random_forest: {
        name: "Random Forest",
        pipeline: "Original 2048 Morgan fingerprint bits; 200 trees, min_samples_leaf=2, max_features=0.7",
        mae: {
          mean: 0.5270,
          sample_std: 0.0672,
          formatted: "0.5270 ± 0.0672",
          raw_mean: 0.526999,
          per_split: [0.4555, 0.5873, 0.5079, 0.4771, 0.6073],
        },
        rmse: {
          mean: 0.7286,
          sample_std: 0.0758,
          formatted: "0.7286 ± 0.0758",
          raw_mean: 0.728605,
          per_split: [0.6459, 0.8080, 0.7138, 0.6690, 0.8064],
        },
        r2: {
          mean: 0.6386,
          sample_std: 0.0394,
          formatted: "0.6386 ± 0.0394",
          raw_mean: 0.638551,
          per_split: [0.6955, 0.6290, 0.6353, 0.6474, 0.5856],
        },
      },
    },
    per_seed_summary: [
      { seed: 11, train_n: 1641, val_n: 600, test_n: 754, svr_test_mae: 0.4990, rf_test_mae: 0.4555 },
      { seed: 23, train_n: 1771, val_n: 535, test_n: 689, svr_test_mae: 0.6213, rf_test_mae: 0.5873 },
      { seed: 42, train_n: 1922, val_n: 542, test_n: 531, svr_test_mae: 0.5477, rf_test_mae: 0.5079 },
      { seed: 87, train_n: 1770, val_n: 532, test_n: 693, svr_test_mae: 0.4928, rf_test_mae: 0.4771 },
      { seed: 101, train_n: 1873, val_n: 502, test_n: 620, svr_test_mae: 0.6428, rf_test_mae: 0.6073 },
    ],
  },
  single_split_pilot_comparison: {
    evaluation_scope: "Matched single scaffold-disjoint pilot split (seed 42, 384 compounds total)",
    split_composition: {
      train_samples: 256,
      validation_samples: 64,
      test_samples: 64,
      scaffold_overlap: "Zero scaffold overlap across partitions (163 train / 45 val / 46 test scaffolds)",
    },
    input_features: {
      dimensions: 16,
      source: "16-component TruncatedSVD + StandardScaler + MinMaxScaler to [0, pi] (fitted on pilot training split only)",
      variance_retained: "52.9% of reported fingerprint variance",
    },
    quantum_execution: {
      method: "16D ZZFeatureMap fidelity kernel, 4 Nyström landmarks, precomputed-kernel SVR (C=10.0, epsilon=0.2)",
      hardware: "Classical statevector simulator (Qiskit StatevectorSampler, 256 shots)",
      is_quantum_hardware: false,
      quantum_advantage_claimed: false,
      landmark_count_verified: 4,
    },
    models: {
      quantum_kernel_svr: {
        name: "Quantum-kernel SVR (4 landmarks)",
        execution: "Classical statevector simulator (not quantum hardware)",
        validation_mae: 1.1293,
        test_mae: 0.9435,
        test_rmse: 1.1234,
        test_r2: -0.0531,
      },
      classical_rbf_svr: {
        name: "Classical RBF-SVR (matched 16D)",
        execution: "Scikit-learn on identical 16D pilot features",
        validation_mae: 0.8919,
        test_mae: 0.6476,
        test_rmse: 0.9045,
        test_r2: 0.3172,
      },
      classical_random_forest: {
        name: "Classical Random Forest (matched 16D)",
        execution: "Scikit-learn on identical 16D pilot features (400 trees, min_leaf=2)",
        validation_mae: 0.8850,
        test_mae: 0.6166,
        test_rmse: 0.7839,
        test_r2: 0.4872,
      },
    },
    difference_quantum_minus_classical_rbf: {
      mae_diff: "+0.2959",
      rmse_diff: "+0.2188",
      r2_diff: "-0.3703",
      interpretation: "Positive MAE/RMSE difference indicates higher error for the quantum model. The matched classical RBF-SVR outperformed the quantum model on the same 16D representation.",
    },
  },
  scientific_integrity_notes: {
    split_separation_principle:
      "The five-split classical evaluation was conducted across 2,995 compounds and five independent scaffold splits. The quantum comparison was conducted on a single 64-compound pilot test split. These evaluations operate on different sample sizes and partitions and are intentionally separated to avoid misleading cross-split comparisons.",
    hardware_disclosure:
      "The quantum experiment was executed on a classical statevector simulator (Qiskit StatevectorSampler), not physical quantum hardware. No quantum advantage is claimed.",
    extrapolation_cost:
      "Quantum kernel construction took 19.5 minutes (1,168.6s) on the 384-compound pilot. Full-cohort 5-split quantum validation is estimated at ~12.5 hours on the simulator and is pending.",
  },
  reports: [
    {
      id: "scaffold_validation",
      title: "EGFR Scaffold-Aware Classical Validation Report",
      description: "Five-seed nested GroupShuffleSplit evaluation across 2,995 compounds and 1,129 scaffolds.",
      api_endpoint: "/api/benchmarks/egfr/reports/scaffold_validation",
    },
    {
      id: "pilot_comparison",
      title: "EGFR 16D Pilot Classical vs Quantum-Kernel Comparison Report",
      description: "Matched comparison on identical 256/64/64 compounds using saved 16D pilot representations.",
      api_endpoint: "/api/benchmarks/egfr/reports/pilot_comparison",
    },
  ],
};

export const METRIC_EXPLANATIONS = [
  {
    term: "MAE (Mean Absolute Error)",
    definition:
      "Average absolute difference between predicted and experimental pIC50 values. Lower is better. A difference of 1.0 pIC50 represents a 10-fold change in IC50 concentration.",
  },
  {
    term: "RMSE (Root Mean Squared Error)",
    definition:
      "Square root of the mean squared error. Penalizes larger prediction outliers more heavily than MAE. Lower is better.",
  },
  {
    term: "R² (Coefficient of Determination)",
    definition:
      "Proportion of target variance explained by the model. 1.0 indicates perfect prediction; 0.0 indicates performance equivalent to predicting the mean target; negative values indicate predictions worse than the mean.",
  },
  {
    term: "Scaffold-Disjoint Split",
    definition:
      "Compounds are grouped by their core Bemis-Murcko scaffold. All compounds with the same core structure are allocated strictly to either train, validation, or test. This prevents scaffold data leakage and tests realistic out-of-series generalization.",
  },
];
