#!/usr/bin/env python3
"""Reproducible small-active-space VQE vs CAQE benchmark for CureGenix.

Runs water and LiH on a classical simulator and writes CSV, JSON, and Markdown
reports to benchmark_reports/. It does not establish quantum advantage.
"""
import csv
import itertools
import json
import math
import random
import statistics
import time
from pathlib import Path

import numpy as np
from qiskit.circuit.library import n_local

from quantum.chemistry.smiles_adapter import smiles_to_geometry
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.vqe import run_vqe
from quantum.algorithms.caqe import run_caqe
from quantum.algorithms.exact_solver import run_exact_solver

TRIALS = 5
MAXITER = 50
CAQE_STARTS = 3
TOL_HA = 1e-8
OUT = Path("benchmark_reports")
MOLECULES = [
    {"name": "Water", "geometry": None, "smiles": "O", "seed_base": 2026,
     "description": "RDKit-generated geometry from SMILES O"},
    {"name": "LiH", "geometry": "Li 0.000000 0.000000 0.000000; H 0.000000 0.000000 1.600000",
     "smiles": None, "seed_base": 2030, "description": "Li-H distance 1.600 Angstrom"},
]


def mean_sd(values):
    return {"mean": float(statistics.mean(values)),
            "sd": float(statistics.stdev(values)) if len(values) > 1 else 0.0}


def build_case(spec):
    geometry = smiles_to_geometry(spec["smiles"]) if spec["smiles"] else spec["geometry"]
    problem = build_molecular_problem(atom=geometry, basis="sto3g", charge=0, spin=0)
    alpha, beta = problem.num_particles
    occupied = (alpha + beta) // 2
    active = reduce_to_active_space(problem, num_electrons=2, num_spatial_orbitals=2,
                                    active_orbitals=[occupied - 1, occupied])
    hamiltonian = build_qubit_hamiltonian(active)
    if active.num_particles != (1, 1) or hamiltonian.num_qubits != 4:
        raise ValueError(f"Unexpected active-space setup for {spec['name']}: "
                         f"particles={active.num_particles}, qubits={hamiltonian.num_qubits}")

    # Explicit (1 alpha, 1 beta) subspace. Assumes JW occupation-bit ordering:
    # alpha spin orbitals 0,1 and beta spin orbitals 2,3; verify convention before
    # using this as a scientific claim beyond this benchmark.
    matrix = hamiltonian.to_matrix()
    indices = []
    for a in itertools.combinations(range(2), 1):
        for b in itertools.combinations(range(2, 4), 1):
            indices.append(sum(1 << i for i in a + b))
    sector_matrix = matrix[np.ix_(indices, indices)]
    sector_energy = float(np.linalg.eigvalsh(sector_matrix)[0].real)
    unrestricted = float(run_exact_solver(hamiltonian)["exact_energy_hartree"])
    sector_delta = abs(unrestricted - sector_energy)
    if sector_delta > TOL_HA:
        raise RuntimeError(f"{spec['name']}: unrestricted reference and explicit sector differ "
                           f"by {sector_delta:.3e} Ha; stopping benchmark")

    ansatz = n_local(num_qubits=hamiltonian.num_qubits, rotation_blocks=["ry"],
                     entanglement_blocks=["cz"], entanglement="full", reps=2)
    correction = float(active.hamiltonian.constants.get("ActiveSpaceTransformer", 0.0))
    nuclear = float(active.hamiltonian.constants.get("nuclear_repulsion_energy", 0.0))
    return {"spec": spec, "problem": problem, "active": active, "hamiltonian": hamiltonian,
            "qubits": hamiltonian.num_qubits, "parameters": ansatz.num_parameters,
            "reference": sector_energy, "unrestricted": unrestricted,
            "sector_delta": sector_delta, "correction": correction, "nuclear": nuclear}


def run_case(case):
    spec = case["spec"]
    print("\n" + "=" * 68)
    print(f"{spec['name']} | STO-3G | {case['qubits']} qubits | {case['parameters']} ansatz parameters")
    print(f"Original alpha/beta electrons: {case['problem'].num_particles}")
    print(f"Active alpha/beta electrons: {case['active'].num_particles}")
    print(f"Unrestricted reference: {case['unrestricted']:.12f} Ha")
    print(f"Explicit (1,1) sector reference: {case['reference']:.12f} Ha")
    print(f"Sector difference: {case['sector_delta']:.3e} Ha — PASS")
    rows = []
    for trial in range(TRIALS):
        seed = spec["seed_base"] + trial
        rng = random.Random(seed)
        inits = [[rng.uniform(-math.pi, math.pi) for _ in range(case['parameters'])]
                 for _ in range(CAQE_STARTS)]
        shared = {"molecule": spec["name"], "trial": trial + 1, "seed": seed,
                  "reference_energy_hartree": case["reference"]}

        t0 = time.perf_counter()
        baseline = run_vqe(case["hamiltonian"], num_qubits=case["qubits"],
                           maxiter=MAXITER, initial_point=inits[0])
        baseline_wall = time.perf_counter() - t0
        b_energy = float(baseline["electronic_energy"])
        rows.append({**shared, "method": "Baseline VQE", "energy_hartree": b_energy,
                     "absolute_error_hartree": abs(b_energy-case["reference"]),
                     "wall_runtime_seconds": baseline_wall, "optimizer_runtime_seconds": None,
                     "evaluations": int(baseline.get("evaluations", 0)), "starts_completed": 1,
                     "active_space_correction_hartree": case["correction"],
                     "nuclear_repulsion_hartree": case["nuclear"],
                     "total_molecular_energy_hartree": b_energy+case["correction"]+case["nuclear"]})

        t0 = time.perf_counter()
        adaptive = run_caqe(case["hamiltonian"], maxiter=MAXITER, initializations=inits,
                            max_starts=CAQE_STARTS, stability_tolerance=None,
                            active_space_correction=case["correction"],
                            nuclear_repulsion_energy=case["nuclear"])
        caqe_wall = time.perf_counter() - t0
        best = adaptive["best_run"]
        c_energy = float(best["energy_hartree"])
        c_evals = sum(int(r.get("evaluations", 0)) for r in adaptive["runs"])
        rows.append({**shared, "method": "CAQE", "energy_hartree": c_energy,
                     "absolute_error_hartree": abs(c_energy-case["reference"]),
                     "wall_runtime_seconds": caqe_wall,
                     "optimizer_runtime_seconds": float(adaptive.get("total_vqe_runtime_seconds", 0.0)),
                     "evaluations": c_evals,
                     "starts_completed": int(adaptive.get("starts_completed", len(adaptive["runs"]))),
                     "active_space_correction_hartree": case["correction"],
                     "nuclear_repulsion_hartree": case["nuclear"],
                     "total_molecular_energy_hartree": best.get("total_molecular_energy_hartree")})
        print(f"Trial {trial+1}/{TRIALS} seed={seed}: baseline error="
              f"{rows[-2]['absolute_error_hartree']:.3e} Ha ({baseline_wall:.2f}s); CAQE error="
              f"{rows[-1]['absolute_error_hartree']:.3e} Ha ({caqe_wall:.2f}s, {c_evals} evals)")

    b = [r for r in rows if r["method"] == "Baseline VQE"]
    c = [r for r in rows if r["method"] == "CAQE"]
    bm = statistics.mean(r["absolute_error_hartree"] for r in b)
    cm = statistics.mean(r["absolute_error_hartree"] for r in c)
    summary = {
        "molecule": spec["name"], "description": spec["description"], "basis": "STO-3G",
        "original_alpha_beta_electrons": list(case["problem"].num_particles),
        "active_alpha_beta_electrons": list(case["active"].num_particles),
        "active_spatial_orbitals": int(case["active"].num_spatial_orbitals),
        "qubits": case["qubits"], "ansatz_parameters": case["parameters"],
        "trials": TRIALS, "maxiter": MAXITER, "caqe_starts_per_trial": CAQE_STARTS,
        "seed_base": spec["seed_base"], "reference_energy_hartree": case["reference"],
        "unrestricted_reference_hartree": case["unrestricted"],
        "sector_reference_difference_hartree": case["sector_delta"],
        "sector_reference_check_passed": True,
        "baseline": {"absolute_error_hartree": mean_sd([r["absolute_error_hartree"] for r in b]),
                     "wall_runtime_seconds": mean_sd([r["wall_runtime_seconds"] for r in b]),
                     "evaluations": mean_sd([r["evaluations"] for r in b])},
        "caqe": {"absolute_error_hartree": mean_sd([r["absolute_error_hartree"] for r in c]),
                 "wall_runtime_seconds": mean_sd([r["wall_runtime_seconds"] for r in c]),
                 "optimizer_runtime_seconds": mean_sd([r["optimizer_runtime_seconds"] for r in c]),
                 "evaluations": mean_sd([r["evaluations"] for r in c]),
                 "starts_completed": mean_sd([r["starts_completed"] for r in c])},
        "caqe_lower_error_trials": sum(x["absolute_error_hartree"] < y["absolute_error_hartree"] for x,y in zip(c,b)),
        "equal_error_trials": sum(x["absolute_error_hartree"] == y["absolute_error_hartree"] for x,y in zip(c,b)),
        "mean_error_reduction_percent": ((bm-cm)/bm*100) if bm > 0 else None,
        "limitations": ["Small active-space classical simulator; no quantum hardware execution.",
                        "No quantum advantage is established.",
                        "Only two molecules and five paired trials per molecule are tested.",
                        "CAQE uses up to three starts; baseline uses one, so resource budgets differ.",
                        "Sector check assumes the stated Jordan-Wigner alpha/beta occupation-bit ordering.",
                        "LiH is a two-electron, two-spatial-orbital active-space model, not a full six-electron calculation.",
                        "Wall-clock timings depend on machine load and software environment."]}
    print(f"{spec['name']} mean error: baseline {bm:.6e} Ha; CAQE {cm:.6e} Ha; "
          f"CAQE lower-error trials {summary['caqe_lower_error_trials']}/{TRIALS}")
    return rows, summary


def write_reports(rows, summaries):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "benchmark_trials.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    payload = {"benchmark_name": "CureGenix VQE vs CAQE small active-space benchmark",
               "configuration": {"trials_per_molecule": TRIALS, "maxiter": MAXITER,
                                 "caqe_starts_per_trial": CAQE_STARTS, "basis": "STO-3G",
                                 "execution": "classical simulator; no quantum hardware"},
               "molecules": summaries,
               "overall_caveats": ["Preliminary results for two small active-space models only.",
                                   "No quantum advantage, drug efficacy, or clinical claim is established."]}
    (OUT / "benchmark_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# CureGenix VQE vs CAQE Benchmark Report", "",
             f"- Trials per molecule: {TRIALS}", f"- Optimizer max iterations: {MAXITER}",
             f"- CAQE starts per trial: {CAQE_STARTS}", "- Basis: STO-3G",
             "- Execution: classical simulator; no quantum hardware", "",
             "## Accuracy results", "",
             "| Molecule | Reference (Ha) | Baseline mean ± SD error (Ha) | CAQE mean ± SD error (Ha) | CAQE wins | Mean error reduction |",
             "|---|---:|---:|---:|---:|---:|"]
    for s in summaries:
        b, c = s["baseline"]["absolute_error_hartree"], s["caqe"]["absolute_error_hartree"]
        change = s["mean_error_reduction_percent"]
        change_text = "n/a" if change is None else f"{change:.2f}%"
        lines.append(f"| {s['molecule']} | {s['reference_energy_hartree']:.12f} | "
                     f"{b['mean']:.6e} ± {b['sd']:.6e} | {c['mean']:.6e} ± {c['sd']:.6e} | "
                     f"{s['caqe_lower_error_trials']}/{TRIALS} | {change_text} |")
    lines += ["", "## Runtime and evaluation results", "",
              "| Molecule | Method | Wall runtime mean ± SD (s) | Evaluations mean ± SD |",
              "|---|---|---:|---:|"]
    for s in summaries:
        for key, label in [("baseline", "Baseline VQE"), ("caqe", "CAQE")]:
            rt, ev = s[key]["wall_runtime_seconds"], s[key]["evaluations"]
            lines.append(f"| {s['molecule']} | {label} | {rt['mean']:.3f} ± {rt['sd']:.3f} | {ev['mean']:.1f} ± {ev['sd']:.1f} |")
    lines += ["", "## Method", "",
              "Each trial uses a deterministic seed to generate three random initial parameter vectors. "
              "Baseline VQE uses the first vector; CAQE receives the same first vector plus two additional starts. "
              "The reference is the minimum of an explicitly constructed (1 alpha, 1 beta) sector, and the runner "
              "stops if this differs from the unrestricted four-qubit minimum beyond tolerance.", "",
              "## Limitations", "",
              "- Small active-space classical simulator experiments; no quantum hardware execution.",
              "- CAQE uses up to three starts while baseline uses one, so resource budgets differ.",
              "- Only two molecules and five trials per molecule are included; results are preliminary.",
              "- The sector check assumes the stated Jordan-Wigner alpha/beta occupation-bit ordering; verify before making external scientific claims.",
              "- LiH is a reduced two-electron, two-spatial-orbital model, not a full six-electron calculation.",
              "- No quantum advantage, drug efficacy, or clinical claim is established.", "",
              "## Files", "", "- `benchmark_trials.csv`: per-trial data.",
              "- `benchmark_summary.json`: machine-readable summary.", "- `benchmark_report.md`: this report.", ""]
    (OUT / "benchmark_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nReports written to benchmark_reports/: benchmark_trials.csv, benchmark_summary.json, benchmark_report.md")


def main():
    all_rows, summaries = [], []
    for spec in MOLECULES:
        rows, summary = run_case(build_case(spec))
        all_rows.extend(rows); summaries.append(summary)
    write_reports(all_rows, summaries)

if __name__ == "__main__":
    main()
