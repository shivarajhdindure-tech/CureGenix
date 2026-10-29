
from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_nature.second_q.mappers import JordanWignerMapper
import itertools
import numpy as np

from quantum.chemistry.smiles_adapter import smiles_to_geometry
from quantum.chemistry.molecule import build_molecular_problem
from quantum.chemistry.active_space import reduce_to_active_space
from quantum.chemistry.hamiltonian import build_qubit_hamiltonian
from quantum.algorithms.exact_solver import run_exact_solver


def validate_molecule(name, geometry):
    print(f"\n{'=' * 60}")
    print(f"MOLECULE: {name}")
    print("=" * 60)

    problem = build_molecular_problem(
        atom=geometry,
        basis="sto3g",
        charge=0,
        spin=0,
    )

    alpha, beta = problem.num_particles
    occupied = (alpha + beta) // 2

    active_problem = reduce_to_active_space(
        problem,
        num_electrons=2,
        num_spatial_orbitals=2,
        active_orbitals=[occupied - 1, occupied],
    )

    hamiltonian = build_qubit_hamiltonian(active_problem)
        # Explicitly restrict the Hamiltonian to the
    # (N_alpha, N_beta) = (1, 1) sector.
    if active_problem.num_particles != (1, 1):
        raise ValueError(
            f"Expected active particles (1, 1), "
            f"got {active_problem.num_particles}"
        )

    if hamiltonian.num_qubits != 4:
        raise ValueError(
            f"Expected 4 qubits, got {hamiltonian.num_qubits}"
        )

    matrix = hamiltonian.to_matrix()

    # Jordan-Wigner occupation-basis ordering:
    # alpha orbitals 0, 1; beta orbitals 2, 3.
    sector_indices = []
    for alpha in itertools.combinations(range(2), 1):
        for beta in itertools.combinations(range(2, 4), 1):
            occupied = alpha + beta
            index = sum(1 << orbital for orbital in occupied)
            sector_indices.append(index)

    sector_matrix = matrix[
        np.ix_(sector_indices, sector_indices)
    ]

    sector_energy = float(
        np.linalg.eigvalsh(sector_matrix)[0].real
    )

    print(
        f"Explicit (1, 1) sector minimum: "
        f"{sector_energy:.12f} Ha"
    )
    full_reference = run_exact_solver(hamiltonian)

    # GroundStateEigensolver uses the molecular problem's
    # default filter criterion where supported.
    sector_solver = GroundStateEigensolver(
        JordanWignerMapper(),
        NumPyMinimumEigensolver(),
    )
    sector_result = sector_solver.solve(active_problem)

    full_energy = full_reference["exact_energy_hartree"]
    sector_energy = float(sector_result.eigenvalues[0].real)
    difference = abs(full_energy - sector_energy)

    print("Original alpha/beta electrons:", problem.num_particles)
    print("Active alpha/beta electrons:", active_problem.num_particles)
    print("Active spatial orbitals:", active_problem.num_spatial_orbitals)
    print("Qubits:", hamiltonian.num_qubits)
    print(f"Unrestricted minimum: {full_energy:.12f} Ha")
    print(f"Filtered ground-state eigenvalue: {sector_energy:.12f} Ha")
    print(f"Absolute difference: {difference:.3e} Ha")

    if difference < 1e-8:
        print("Result: energies agree within tolerance.")
    else:
        print("Result: energies differ; investigate before benchmarking.")

    print(
        "Note: confirm the installed Qiskit Nature version's filter "
        "criterion and returned state/auxiliary observables before "
        "treating this comparison alone as proof of sector membership."
    )


water_geometry = smiles_to_geometry("O")

lih_geometry = (
    "Li 0.000000 0.000000 0.000000; "
    "H 0.000000 0.000000 1.600000"
)

validate_molecule("Water", water_geometry)
validate_molecule("LiH", lih_geometry)