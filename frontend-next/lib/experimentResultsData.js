/**
 * CureGenix Experiment & Hardware Results Vault Manifest
 * 
 * Verified experiment records from actual runs:
 * - experiments/ibm_results/
 * 
 * Safety & Integrity Rules:
 * - No credentials, API tokens, or local environment paths are exposed.
 * - All values reflect verified on-disk experiment outputs.
 * - Hardware noise and divergence are explicitly reported; no quantum advantage is claimed.
 * - Intermediate diagnostic files are categorized separately from canonical results.
 */

export const SCIENTIFIC_DISCLOSURES = [
  {
    topic: "H2 Hardware Fixed VQE Divergence",
    disclosure:
      "Physical QPU evaluation on ibm_fez (Job dbho8401h92s73825deg, 1152 shots) evaluates fixed parameter angles derived from local simulation; it is not a closed-loop hardware-optimized VQE. The measured electronic energy (-1.6406 ± 0.0121 Ha) differs by +0.2167 Ha from the exact electronic reference (-1.8573 Ha) and by +0.1964 Ha from the local VQE solution. This divergence reflects physical transmon qubit noise, gate infidelities, and unmitigated decoherence on NISQ hardware, not energetic convergence.",
  },
  {
    topic: "Circuit Execution Diagnostics vs. Biological Binding",
    disclosure:
      "The VQC (Job dbhnetune4hc73bd8h70) and QGNN (Job dbhm4ntep8hs73amelf0) hardware runs on ibm_fez are circuit execution diagnostics comparing physical hardware bitstring sampling against statevector simulation. They verify circuit execution and sampling parity on physical qubits; they do not establish EGFR binding affinity, biological efficacy, or therapeutic validity.",
  },
  {
    topic: "Local Exact Ground Truth Reference",
    disclosure:
      "The H2 molecular Hamiltonian was generated locally using PySCF and Qiskit Nature with the STO-3G minimal basis and Jordan-Wigner fermion-to-qubit mapping (15 Pauli terms, bond length 0.735 Å). The exact diagonalized electronic eigenvalue is -1.857275 Ha (total energy -1.137306 Ha with 0.719969 Ha nuclear repulsion). Local SLSQP StatevectorEstimator VQE reached -1.836968 Ha (error 0.020307 Ha).",
  },
  {
    topic: "Retrospective Benchmarks & Scope",
    disclosure:
      "Benchmark metrics represent retrospective offline evaluations across 2,995 ChEMBL EGFR compounds using 5-split scaffold-disjoint splits and matched pilot tests. They serve as methodological comparisons against classical baselines (RBF-SVR, Random Forest) and do not imply clinical efficacy.",
  },
  {
    topic: "No Quantum Advantage Claimed",
    disclosure:
      "All quantum evaluations currently operate in an exploratory research regime on noisy intermediate-scale quantum (NISQ) systems. No quantum advantage or algorithmic superiority over optimized classical cheminformatics models is claimed.",
  },
];

export const CANONICAL_EXPERIMENT_RESULTS = [
  {
    id: "h2_ibm_fixed_vqe",
    name: "H₂ Molecular Energy Estimation (Fixed VQE)",
    filename: "h2_ibm_fixed_vqe_energy.json",
    executionType: "IBM QPU execution",
    targetOrMolecule: "H₂ Molecule (STO-3G, 0.735 Å)",
    backend: "ibm_fez",
    jobId: "dbho8401h92s73825deg",
    timestampUtc: "2026-10-29T17:36:18.319715+00:00",
    status: "Completed (Noisy QPU Evaluation)",
    statusType: "hardware-noisy", // Amber/warning indication
    shots: 1152,
    qubits: 4,
    pauliTerms: 15,
    primaryMetricLabel: "Electronic Energy",
    primaryMetricValue: "-1.6406 Ha (Total: -0.9206 Ha)",
    referenceValue: "-1.8573 Ha (Exact Local Reference)",
    uncertaintyOrDelta: "±0.0121 Ha (SE) · Δ = +0.2167 Ha vs exact",
    scientificLimitations:
      "Fixed local VQE parameters evaluated on ibm_fez; not closed-loop hardware VQE. Energy difference demonstrates physical transmon noise and unmitigated decoherence.",
    summaryNotes:
      "Measured electronic energy of -1.6406 ± 0.0121 Ha on ibm_fez. Local reference is -1.8573 Ha. Difference of +0.2167 Ha illustrates NISQ hardware error rates across 15 Pauli terms.",
    rawData: {
      experiment: "H2 fixed-parameter energy estimation",
      created_utc: "2026-10-29T17:36:18.319715+00:00",
      molecule: "H2",
      bond_distance_angstrom: 0.735,
      basis: "STO-3G",
      mapping: "Jordan-Wigner",
      backend: "ibm_fez",
      num_qubits: 4,
      num_pauli_terms: 15,
      local_vqe_electronic_energy_hartree: -1.8369679413555875,
      exact_electronic_reference_hartree: -1.8572750302023775,
      nuclear_repulsion_energy_hartree: 0.7199689944489797,
      status: "completed",
      note: "Fixed local VQE parameters evaluated on hardware; not hardware-optimized VQE.",
      job_id: "dbho8401h92s73825deg",
      electronic_energy_hartree: -1.6406003241103697,
      electronic_energy_standard_error_hartree: 0.012084908926948218,
      total_energy_hartree: -0.92063132966139,
      total_energy_standard_error_hartree: 0.012084908926948218,
      difference_from_local_vqe_hartree: 0.19636761724521778,
      absolute_difference_from_exact_electronic_reference_hartree: 0.21667470609200778,
      result_metadata: {
        shots: 1152,
        target_precision: 0.03,
        num_randomizations: 18,
      },
    },
  },
  {
    id: "bell_state_verification",
    name: "Two-Qubit Bell State (|Φ⁺⟩) Verification",
    filename: "bell_dbhlhclep8hs73amdesg.json",
    executionType: "IBM QPU execution",
    targetOrMolecule: "2-Qubit Bell State (|00⟩ + |11⟩)/√2",
    backend: "ibm_fez",
    jobId: "dbhlhclep8hs73amdesg",
    timestampUtc: "2026-10-29T14:33:46.828893+00:00",
    status: "Completed (Entanglement Verified)",
    statusType: "hardware-done",
    shots: 256,
    qubits: 2,
    pauliTerms: null,
    primaryMetricLabel: "State Counts (|00⟩ / |11⟩)",
    primaryMetricValue: "110 / 126 (92.2% in Bell subspace)",
    referenceValue: "130 / 126 (100% ideal simulator)",
    uncertaintyOrDelta: "7.8% noise leakage (|10⟩: 16, |01⟩: 4)",
    scientificLimitations:
      "Hardware baseline demonstration of quantum entanglement; not an EGFR binding prediction or evidence of quantum advantage.",
    summaryNotes:
      "Physical execution of Hadamard and CNOT gates on ibm_fez. 236/256 shots occupied |00⟩ and |11⟩ states, with 20 shots leakage into non-entangled states due to readout and gate noise.",
    rawData: {
      experiment: "two_qubit_bell_state",
      timestamp_utc: "2026-10-29T14:33:46.828893+00:00",
      backend: "ibm_fez",
      job_id: "dbhlhclep8hs73amdesg",
      job_status: "DONE",
      shots: 256,
      logical_qubits: 2,
      transpiled_depth: 8,
      hardware_counts: {
        "11": 126,
        "00": 110,
        "10": 16,
        "01": 4,
      },
      simulator_counts: {
        "11": 126,
        "00": 130,
      },
      note: "Bell-state hardware demonstration; not an EGFR prediction or evidence of quantum advantage.",
    },
  },
  {
    id: "curegenix_qgnn_pqc_diagnostic",
    name: "Trained QGNN Quantum Component Diagnostic",
    filename: "curegenix_qgnn_dbhm4ntep8hs73amelf0.json",
    executionType: "Hardware circuit diagnostics",
    targetOrMolecule: "EGFR QGNN Message-Passing PQC",
    backend: "ibm_fez",
    jobId: "dbhm4ntep8hs73amelf0",
    timestampUtc: "2026-10-29T15:12:00.000000+00:00",
    status: "Completed (Diagnostic Sampled)",
    statusType: "diagnostic",
    shots: 256,
    qubits: 4,
    pauliTerms: null,
    primaryMetricLabel: "Measured P(q₀ = 1)",
    primaryMetricValue: "0.3984 (102 / 256 shots)",
    referenceValue: "0.4284 (Expected Local Statevector)",
    uncertaintyOrDelta: "Δ = 0.0300 vs statevector simulation",
    scientificLimitations:
      "Diagnostic hardware comparison of trained QGNN parameterized quantum circuit; not a molecular activity or affinity claim.",
    summaryNotes:
      "Bound trained QGNN model angles [0.1, 0.2, 0.3, 0.4] executed on ibm_fez. Measured marginal probability of qubit 0 being |1⟩ was 0.3984 vs local statevector 0.4284 (3.0% sampling deviation).",
    rawData: {
      model_id: "egfr-qgnn-message-passing-pqc-v1",
      circuit_type: "saved trained CureGenix QGNN quantum component",
      input_angles: [0.1, 0.2, 0.3, 0.4],
      expected_local_probability_qubit0_is_1: 0.42844793340541254,
      qubits: 4,
      shots_requested: 256,
      purpose: "diagnostic hardware-vs-statevector comparison; not a molecular prediction",
      ibm_job_id: "dbhm4ntep8hs73amelf0",
      backend: "ibm_fez",
      actual_shots: 256,
      hardware_counts: {
        "1000": 91,
        "1111": 17,
        "1011": 8,
        "0111": 59,
        "0000": 39,
        "0110": 15,
        "0001": 4,
        "0011": 3,
        "0010": 2,
        "1001": 10,
        "0101": 1,
        "1100": 3,
        "1110": 4,
      },
      measured_probability_qubit0_is_1: 0.3984375,
      absolute_difference_from_local: 0.03001043340541254,
      status: "DONE",
    },
  },
  {
    id: "curegenix_vqc_pqc_diagnostic",
    name: "Trained VQC ZZ-RealAmplitudes Diagnostic",
    filename: "curegenix_vqc_dbhnetune4hc73bd8h70.json",
    executionType: "Hardware circuit diagnostics",
    targetOrMolecule: "EGFR VQC Circuit (CCO Diagnostic)",
    backend: "ibm_fez",
    jobId: "dbhnetune4hc73bd8h70",
    timestampUtc: "2026-10-29T16:55:00.000000+00:00",
    status: "Completed (Diagnostic Sampled)",
    statusType: "diagnostic",
    shots: 256,
    qubits: 4,
    pauliTerms: null,
    primaryMetricLabel: "Hardware Class Probs [P(0), P(1)]",
    primaryMetricValue: "[0.6055, 0.3945] (155 vs 101 shots)",
    referenceValue: "[0.4927, 0.5073] (Exact Statevector)",
    uncertaintyOrDelta: "Δ = [0.1128, 0.1128] vs exact statevector",
    scientificLimitations:
      "Diagnostic comparison of trained VQC SamplerQNN circuit on ibm_fez; does not constitute evidence of molecular activity prediction or binding affinity.",
    summaryNotes:
      "Trained VQC (4 qubits, 8 parameters, ZZFeatureMap + RealAmplitudes) executed on ibm_fez with diagnostic molecule CCO angles. Parity interpretation yielded [0.6055, 0.3945] on hardware vs [0.4927, 0.5073] on statevector.",
    rawData: {
      model_id: "egfr-vqc-zz-real-amplitudes-v1",
      circuit_source: "trained model SamplerQNN circuit",
      diagnostic_smiles: "CCO",
      preprocessed_angles: [
        -0.26478612422943115,
        1.4844111204147339,
        1.5868207216262817,
        1.4113008975982666,
      ],
      qubits: 4,
      trainable_parameters: 8,
      shots_requested: 256,
      class_interpretation: "Qiskit VQC parity interpretation",
      local_sampler_probabilities: [0.45703125, 0.54296875],
      local_exact_probabilities: [
        0.4927137063464443,
        0.5072862936535554,
      ],
      purpose: "diagnostic hardware comparison; not a molecular activity claim",
      ibm_job_id: "dbhnetune4hc73bd8h70",
      backend: "ibm_fez",
      status: "DONE",
      actual_shots: 256,
      hardware_counts: {
        "0011": 5,
        "1101": 27,
        "1100": 40,
        "1111": 54,
        "1110": 13,
        "0101": 11,
        "1000": 12,
        "1010": 24,
        "0110": 11,
        "1011": 7,
        "1001": 7,
        "0010": 13,
        "0111": 19,
        "0100": 9,
        "0001": 1,
        "0000": 3,
      },
      hardware_class_counts: [155, 101],
      hardware_class_probabilities: [0.60546875, 0.39453125],
      absolute_difference_by_class: [
        0.11275504365355571,
        0.11275504365355538,
      ],
      comparison_reference: "exact statevector probabilities from the bound saved-model circuit",
    },
  },
  {
    id: "h2_local_exact_reference",
    name: "H₂ Exact Diagonalized Ground State Reference",
    filename: "h2_local_reference.json",
    executionType: "Local exact/statevector simulation",
    targetOrMolecule: "H₂ Molecule (STO-3G, 0.735 Å)",
    backend: "Local (PySCF 2.14 / NumPy Exact)",
    jobId: null,
    timestampUtc: "2026-10-29T17:26:00.000000+00:00",
    status: "Verified Exact Reference",
    statusType: "local-exact",
    shots: null,
    qubits: 4,
    pauliTerms: 15,
    primaryMetricLabel: "Exact Electronic Eigenvalue",
    primaryMetricValue: "-1.857275 Ha (Total: -1.137306 Ha)",
    referenceValue: "Full Hamiltonian Diagonalization Ground Truth",
    uncertaintyOrDelta: "0.0000 Ha (Exact matrix diagonalization)",
    scientificLimitations:
      "Numerical ground truth reference computed via PySCF and exact matrix diagonalization. Represents theoretical lower bound under STO-3G minimal basis.",
    summaryNotes:
      "Exact diagonalized electronic energy of -1.85727503 Ha with 0.719969 Ha nuclear repulsion, yielding total ground-state energy of -1.137306 Ha. Used as baseline for all VQE evaluations.",
    rawData: {
      molecule: "H2",
      bond_distance_angstrom: 0.735,
      basis: "STO-3G",
      mapping: "Jordan-Wigner",
      num_qubits: 4,
      num_particles: [1, 1],
      num_spatial_orbitals: 2,
      num_pauli_terms: 15,
      exact_qubit_hamiltonian_eigenvalue_hartree: -1.8572750302023775,
      nuclear_repulsion_energy_hartree: 0.7199689944489797,
      note: "Local exact reference; not a hardware result.",
    },
  },
  {
    id: "h2_local_vqe_simulation",
    name: "H₂ Local VQE Optimization (StatevectorEstimator)",
    filename: "h2_local_vqe.json",
    executionType: "Local variational quantum eigensolver",
    targetOrMolecule: "H₂ Molecule (STO-3G, 0.735 Å)",
    backend: "Local (StatevectorEstimator / SLSQP)",
    jobId: null,
    timestampUtc: "2026-10-29T17:29:00.000000+00:00",
    status: "Converged Locally (SLSQP)",
    statusType: "local-vqe",
    shots: null,
    qubits: 4,
    pauliTerms: 15,
    primaryMetricLabel: "VQE Electronic Eigenvalue",
    primaryMetricValue: "-1.836968 Ha (Total: -1.116999 Ha)",
    referenceValue: "-1.857275 Ha (Exact Diagonalization)",
    uncertaintyOrDelta: "Error: 0.020307 Ha (12 variational parameters)",
    scientificLimitations:
      "Local noiseless simulation using Qiskit StatevectorEstimator and SLSQP. Optimal parameters saved as baseline input for ibm_fez hardware evaluation.",
    summaryNotes:
      "Local VQE reached -1.836968 Ha electronic energy, within 0.0203 Ha of the exact STO-3G minimum. The 12 converged variational parameters were subsequently exported to hardware.",
    rawData: {
      molecule: "H2",
      bond_distance_angstrom: 0.735,
      basis: "STO-3G",
      mapping: "Jordan-Wigner",
      method: "VQE",
      simulator: "StatevectorEstimator",
      optimizer: "SLSQP",
      maxiter: 100,
      num_qubits: 4,
      vqe_eigenvalue_hartree: -1.8369679413555875,
      exact_reference_eigenvalue_hartree: -1.8572750302023775,
      absolute_energy_error_hartree: 0.02030708884679,
      optimal_parameters: {
        "θ[0]": -0.0005414282449277647,
        "θ[1]": -3.980479369120668,
        "θ[2]": -1.1977601898525885,
        "θ[3]": -0.0005560960149629218,
        "θ[4]": 3.1412319625332765,
        "θ[5]": 4.4401155537861055,
        "θ[6]": 1.6093760438336575,
        "θ[7]": 3.141085082358002,
        "θ[8]": 6.2837750124889595,
        "θ[9]": -5.168799603750725,
        "θ[10]": -5.401852372745225,
        "θ[11]": 3.1422201150908067,
      },
      note: "Local simulation only; not a hardware result.",
    },
  },
];

export const SUPPORTING_DIAGNOSTIC_ARTIFACTS = [
  {
    id: "curegenix_qgnn_diagnostic_input",
    name: "QGNN Hardware Diagnostic Input Specification",
    filename: "curegenix_qgnn_diagnostic.json",
    category: "Intermediate Diagnostic Specification",
    qubits: 4,
    shotsRequested: 256,
    description:
      "Pre-run parameter and expectation specification for QGNN circuit diagnostic before submission to ibm_fez.",
    rawData: {
      model_id: "egfr-qgnn-message-passing-pqc-v1",
      circuit_type: "saved trained CureGenix QGNN quantum component",
      input_angles: [0.1, 0.2, 0.3, 0.4],
      expected_local_probability_qubit0_is_1: 0.42844793340541254,
      qubits: 4,
      shots_requested: 256,
      purpose: "diagnostic hardware-vs-statevector comparison; not a molecular prediction",
    },
  },
  {
    id: "curegenix_vqc_ethanol_diagnostic",
    name: "VQC Feature Preprocessing Specification (CCO)",
    filename: "curegenix_vqc_ethanol.json",
    category: "Intermediate Diagnostic Specification",
    qubits: 4,
    shotsRequested: 256,
    description:
      "Pre-run feature angles and local simulator expectation for diagnostic CCO molecule before QPU execution.",
    rawData: {
      model_id: "egfr-vqc-zz-real-amplitudes-v1",
      circuit_type: "saved trained CureGenix VQC",
      diagnostic_smiles: "CCO",
      preprocessed_feature_angles: [
        -0.26478612422943115,
        1.4844111204147339,
        1.5868207216262817,
        1.4113008975982666,
      ],
      qubits: 4,
      trainable_parameter_count: 8,
      shots_requested: 256,
      class_interpretation: "parity of measured four-bit output; even parity is class 0, odd parity is class 1",
      local_exact_class_probabilities: [
        0.6259772481182152,
        0.37402275188178435,
      ],
      purpose: "hardware-versus-simulator diagnostic; not evidence of molecular activity",
    },
  },
  {
    id: "curegenix_vqc_model_circuit_spec",
    name: "VQC Bound Model Circuit Specification",
    filename: "curegenix_vqc_ethanol_model_circuit.json",
    category: "Intermediate Diagnostic Specification",
    qubits: 4,
    shotsRequested: 256,
    description:
      "SamplerQNN bound circuit specification with local sampler (45.7% / 54.3%) and statevector (49.3% / 50.7%) references.",
    rawData: {
      model_id: "egfr-vqc-zz-real-amplitudes-v1",
      circuit_source: "trained model SamplerQNN circuit",
      diagnostic_smiles: "CCO",
      preprocessed_angles: [
        -0.26478612422943115,
        1.4844111204147339,
        1.5868207216262817,
        1.4113008975982666,
      ],
      qubits: 4,
      trainable_parameters: 8,
      shots_requested: 256,
      class_interpretation: "Qiskit VQC parity interpretation",
      local_sampler_probabilities: [0.45703125, 0.54296875],
      local_exact_probabilities: [
        0.4927137063464443,
        0.5072862936535554,
      ],
      purpose: "diagnostic hardware comparison; not a molecular activity claim",
    },
  },
  {
    id: "h2_hamiltonian_export_spec",
    name: "H₂ 15-Term Pauli Hamiltonian Operator Export",
    filename: "h2_hamiltonian_export.json",
    category: "Hamiltonian Operator Decomposition",
    qubits: 4,
    pauliTerms: 15,
    description:
      "Full Pauli tensor product expansion for H2 (STO-3G, Jordan-Wigner) generated by PySCF and Qiskit Nature.",
    rawData: {
      molecule: "H2",
      bond_distance_angstrom: 0.735,
      basis: "STO-3G",
      mapping: "Jordan-Wigner",
      num_qubits: 4,
      num_pauli_terms: 15,
      nuclear_repulsion_energy_hartree: 0.7199689944489797,
      terms_count: 15,
      pauli_terms_summary: "IIII, IIIZ, IIZI, IIZZ, IZII, IZIZ, ZIII, ZIIZ, YYYY, XXYY, YYXX, XXXX, IZZI, ZIZI, ZZII",
      note: "Hamiltonian generated locally with PySCF and Qiskit Nature.",
    },
  },
];

/**
 * Trigger clean client-side Blob download and ensure URL revocation.
 */
export function triggerBlobDownload(blob, filename) {
  if (typeof window === "undefined") return;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/**
 * Download a single experiment record as an individual JSON file.
 */
export function downloadSingleRecordJson(record) {
  const exportPayload = {
    schema_version: "1.0.0",
    exported_at_utc: new Date().toISOString(),
    record_id: record.id,
    record_name: record.name,
    execution_type: record.executionType,
    target_or_molecule: record.targetOrMolecule,
    backend: record.backend,
    job_id: record.jobId,
    status: record.status,
    scientific_limitations: record.scientificLimitations,
    verified_data: record.rawData,
  };

  const jsonString = JSON.stringify(exportPayload, null, 2);
  const blob = new Blob([jsonString], { type: "application/json;charset=utf-8" });
  triggerBlobDownload(blob, record.filename || `${record.id}.json`);
}

/**
 * Download a supporting diagnostic artifact as an individual JSON file.
 */
export function downloadSupportingArtifactJson(artifact) {
  const exportPayload = {
    schema_version: "1.0.0",
    exported_at_utc: new Date().toISOString(),
    artifact_id: artifact.id,
    artifact_name: artifact.name,
    category: artifact.category,
    description: artifact.description,
    verified_data: artifact.rawData,
  };

  const jsonString = JSON.stringify(exportPayload, null, 2);
  const blob = new Blob([jsonString], { type: "application/json;charset=utf-8" });
  triggerBlobDownload(blob, artifact.filename || `${artifact.id}.json`);
}

/**
 * Download consolidated results JSON containing all allowlisted canonical records,
 * supporting diagnostic artifacts, and scientific disclosures.
 */
export function downloadConsolidatedResultsJson() {
  const consolidatedPayload = {
    schema_version: "1.0.0",
    generated_at_utc: new Date().toISOString(),
    vault_name: "CureGenix Quantum Experiment & Hardware Results Vault",
    environment: {
      host: "Windows 11 x86_64 / FastAPI Backend",
      quantum_adapter: "Ubuntu 22.04 WSL 2 (PySCF 2.14.0)",
      quantum_sdk: "Qiskit 2.5.2 & Qiskit Nature",
      qpu_hardware: "ibm_fez (IBM Quantum Heron Processor)",
    },
    canonical_experiment_count: CANONICAL_EXPERIMENT_RESULTS.length,
    supporting_artifact_count: SUPPORTING_DIAGNOSTIC_ARTIFACTS.length,
    scientific_disclosures: SCIENTIFIC_DISCLOSURES,
    canonical_results: CANONICAL_EXPERIMENT_RESULTS.map((r) => ({
      id: r.id,
      name: r.name,
      filename: r.filename,
      execution_type: r.executionType,
      target_or_molecule: r.targetOrMolecule,
      backend: r.backend,
      job_id: r.jobId,
      timestamp_utc: r.timestampUtc,
      status: r.status,
      shots: r.shots,
      qubits: r.qubits,
      pauli_terms: r.pauliTerms,
      primary_metric: {
        label: r.primaryMetricLabel,
        value: r.primaryMetricValue,
        reference_value: r.referenceValue,
        uncertainty_or_delta: r.uncertaintyOrDelta,
      },
      scientific_limitations: r.scientificLimitations,
      verified_data: r.rawData,
    })),
    supporting_artifacts: SUPPORTING_DIAGNOSTIC_ARTIFACTS.map((a) => ({
      id: a.id,
      name: a.name,
      filename: a.filename,
      category: a.category,
      description: a.description,
      verified_data: a.rawData,
    })),
  };

  const jsonString = JSON.stringify(consolidatedPayload, null, 2);
  const blob = new Blob([jsonString], { type: "application/json;charset=utf-8" });
  triggerBlobDownload(blob, "curegenix_consolidated_experiment_results.json");
}

/**
 * Download experiment summary table as properly formatted CSV with UTF-8 BOM.
 */
export function downloadExperimentSummaryCsv() {
  const headers = [
    "Experiment ID",
    "Experiment Name",
    "Filename",
    "Execution Type",
    "Target / Molecule",
    "Backend",
    "Job ID",
    "Status",
    "Timestamp (UTC)",
    "Shots",
    "Qubits",
    "Primary Metric",
    "Metric Value",
    "Reference Value",
    "Uncertainty / Delta",
    "Scientific Limitations",
  ];

  function escapeCsvCell(val) {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  }

  const rows = CANONICAL_EXPERIMENT_RESULTS.map((r) => [
    escapeCsvCell(r.id),
    escapeCsvCell(r.name),
    escapeCsvCell(r.filename),
    escapeCsvCell(r.executionType),
    escapeCsvCell(r.targetOrMolecule),
    escapeCsvCell(r.backend),
    escapeCsvCell(r.jobId || "N/A"),
    escapeCsvCell(r.status),
    escapeCsvCell(r.timestampUtc),
    escapeCsvCell(r.shots !== null ? r.shots : "N/A"),
    escapeCsvCell(r.qubits),
    escapeCsvCell(r.primaryMetricLabel),
    escapeCsvCell(r.primaryMetricValue),
    escapeCsvCell(r.referenceValue),
    escapeCsvCell(r.uncertaintyOrDelta),
    escapeCsvCell(r.scientificLimitations),
  ]);

  // Append supporting diagnostic artifacts as separate rows with clear classification
  SUPPORTING_DIAGNOSTIC_ARTIFACTS.forEach((a) => {
    rows.push([
      escapeCsvCell(a.id),
      escapeCsvCell(a.name),
      escapeCsvCell(a.filename),
      escapeCsvCell(a.category),
      escapeCsvCell("Intermediate Diagnostic Artifact"),
      escapeCsvCell("Pre-run Specification / Local"),
      escapeCsvCell("N/A"),
      escapeCsvCell("Supporting Artifact"),
      escapeCsvCell("N/A"),
      escapeCsvCell(a.shotsRequested || "N/A"),
      escapeCsvCell(a.qubits || "N/A"),
      escapeCsvCell("Artifact Purpose"),
      escapeCsvCell(a.description),
      escapeCsvCell("Intermediate File (Not Canonical Evaluation)"),
      escapeCsvCell("N/A"),
      escapeCsvCell("Supporting diagnostic artifact. Not a canonical experiment evaluation."),
    ]);
  });

  const csvContent =
    "\uFEFF" +
    headers.join(",") +
    "\r\n" +
    rows.map((row) => row.join(",")).join("\r\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
  triggerBlobDownload(blob, "curegenix_experiment_summary.csv");
}
