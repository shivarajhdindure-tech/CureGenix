"""Conservative size-based eligibility checks for isolated-molecule quantum jobs.

The STO-3G orbital count is an estimate from tabulated shell counts, not a
memory estimator. It is an operational guardrail motivated by observed WSL
OOMs at roughly 167-175 estimated functions, not a calibrated scientific limit.
"""

from __future__ import annotations

import os
import re


STO3G_AO_COUNTS = {
    "H": 1, "He": 1,
    "Li": 5, "Be": 5, "B": 5, "C": 5, "N": 5, "O": 5, "F": 5, "Ne": 5,
    "Na": 9, "Mg": 9, "Al": 9, "Si": 9, "P": 9, "S": 9, "Cl": 9, "Ar": 9,
}
ATOMIC_NUMBERS = {
    "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8,
    "F": 9, "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15,
    "S": 16, "Cl": 17, "Ar": 18,
}
DEFAULT_LIMITS = {
    "max_heavy_atoms": 20,
    "max_total_atoms": 80,
    "max_estimated_basis_functions": 100,
    "max_vqe_iterations": 100,
}
ENV_LIMITS = {
    "max_heavy_atoms": "CUREGENIX_QUANTUM_MAX_HEAVY_ATOMS",
    "max_total_atoms": "CUREGENIX_QUANTUM_MAX_ATOMS",
    "max_estimated_basis_functions": "CUREGENIX_QUANTUM_MAX_ESTIMATED_AO",
    "max_vqe_iterations": "CUREGENIX_QUANTUM_MAX_VQE_ITERATIONS",
}


def _limits_from_environment() -> dict:
    limits = dict(DEFAULT_LIMITS)
    for key, env_name in ENV_LIMITS.items():
        raw = os.getenv(env_name)
        if raw is not None:
            try:
                value = int(raw)
            except ValueError as exc:
                raise ValueError(f"{env_name} must be a positive integer.") from exc
            if value < 1:
                raise ValueError(f"{env_name} must be a positive integer.")
            limits[key] = value
    return limits


def _assessment(elements: list[str], basis: str, maxiter: int, charge: int, benchmark: bool) -> dict:
    limits = _limits_from_environment()
    normalized_basis = re.sub(r"[-_\s]", "", str(basis or "")).casefold()
    heavy_atoms = sum(element != "H" for element in elements)
    atom_count = len(elements)
    unknown_elements = sorted(set(elements) - set(ATOMIC_NUMBERS))
    ao_estimate = (
        sum(STO3G_AO_COUNTS[element] for element in elements)
        if normalized_basis == "sto3g" and not unknown_elements
        else None
    )
    electron_estimate = (
        sum(ATOMIC_NUMBERS[element] for element in elements) - charge
        if not unknown_elements else None
    )

    reasons = []
    if normalized_basis != "sto3g":
        reasons.append("The current resource estimate is only defined for STO-3G basis sets.")
    if unknown_elements:
        reasons.append("No supported lightweight resource estimate is available for element(s): " + ", ".join(unknown_elements) + ".")
    if heavy_atoms > limits["max_heavy_atoms"]:
        reasons.append(f"Heavy-atom count {heavy_atoms} exceeds configured limit {limits['max_heavy_atoms']}.")
    if atom_count > limits["max_total_atoms"]:
        reasons.append(f"Total atom count {atom_count} exceeds configured limit {limits['max_total_atoms']}.")
    if ao_estimate is not None and ao_estimate > limits["max_estimated_basis_functions"]:
        reasons.append(
            f"Estimated STO-3G basis-function count {ao_estimate} exceeds configured limit "
            f"{limits['max_estimated_basis_functions']}. This count is a rough size indicator, not an exact memory estimate."
        )
    if maxiter > limits["max_vqe_iterations"]:
        reasons.append(f"VQE iteration request {maxiter} exceeds configured limit {limits['max_vqe_iterations']}.")

    return {
        "status": "skipped_resource_limit" if reasons else "eligible",
        "eligible": not reasons,
        "reasons": reasons,
        "resource_metrics": {
            "heavy_atom_count": heavy_atoms,
            "total_atom_count": atom_count,
            "estimated_sto3g_basis_functions": ao_estimate,
            "estimated_electron_count": electron_estimate,
        },
        "calculation_parameters": {
            "basis": basis,
            "charge": charge,
            "max_vqe_iterations": maxiter,
            "benchmark_enabled": bool(benchmark),
        },
        "limits": limits,
        "estimation_method": (
            "Atom counts and tabulated STO-3G shell counts only; no memory prediction or PySCF integral estimate."
        ),
    }


def assess_smiles_resources(smiles: str, basis: str = "sto3g", maxiter: int = 50, charge: int = 0, benchmark: bool = False) -> dict:
    """Assess a SMILES before 3D embedding or quantum-chemistry setup."""
    from rdkit import Chem

    molecule = Chem.MolFromSmiles(smiles or "")
    if molecule is None:
        return {"status": "invalid_input", "eligible": False, "reasons": ["Invalid SMILES; molecular structure could not be estimated."]}
    explicit = Chem.AddHs(molecule)
    elements = [atom.GetSymbol() for atom in explicit.GetAtoms()]
    return _assessment(elements, basis, maxiter, charge, benchmark)


def assess_geometry_resources(atom_geometry: str, basis: str = "sto3g", maxiter: int = 50, charge: int = 0, benchmark: bool = False) -> dict:
    """Assess atom symbols from the adapter's `Element x y z; ...` geometry."""
    elements = []
    for fragment in str(atom_geometry or "").replace("\n", ";").split(";"):
        tokens = fragment.strip().split()
        if not tokens:
            continue
        symbol = tokens[0]
        if not re.fullmatch(r"[A-Z][a-z]?", symbol) or len(tokens) < 4:
            return {"status": "invalid_input", "eligible": False, "reasons": ["Geometry contains a malformed atom record; resource eligibility was not evaluated."]}
        try:
            for coordinate in tokens[1:4]:
                float(coordinate)
        except ValueError:
            return {"status": "invalid_input", "eligible": False, "reasons": ["Geometry contains nonnumeric coordinates; resource eligibility was not evaluated."]}
        elements.append(symbol)
    if not elements:
        return {"status": "invalid_input", "eligible": False, "reasons": ["Geometry has no atom records."]}
    return _assessment(elements, basis, maxiter, charge, benchmark)
