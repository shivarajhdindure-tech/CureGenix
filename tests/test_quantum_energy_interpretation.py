import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from quantum.chemistry.quantum_analysis import analyze_smiles
from quantum.wsl_worker import _run_molecular_analysis


class FakeOperator:
    num_qubits = 4

    def __len__(self):
        return 6


def fake_problem():
    hamiltonian = SimpleNamespace(constants={
        "ActiveSpaceTransformer": 0.4,
        "nuclear_repulsion_energy": 0.7,
    })
    return SimpleNamespace(
        orbital_energies=[-0.5, 0.25],
        num_spatial_orbitals=2,
        num_particles=(1, 1),
        hamiltonian=hamiltonian,
    )


class QuantumEnergyInterpretationTests(unittest.TestCase):
    def setup_quantum_mocks(self, stack):
        problem = fake_problem()
        active_problem = fake_problem()
        common = [
            patch("quantum.chemistry.molecule.build_molecular_problem", return_value=problem),
            patch("quantum.chemistry.quantum_analysis.build_molecular_problem", return_value=problem),
            patch("quantum.chemistry.active_space.reduce_to_active_space", return_value=active_problem),
            patch("quantum.chemistry.quantum_analysis.reduce_to_active_space", return_value=active_problem),
            patch("quantum.chemistry.hamiltonian.build_qubit_hamiltonian", return_value=FakeOperator()),
            patch("quantum.chemistry.quantum_analysis.build_qubit_hamiltonian", return_value=FakeOperator()),
            patch("quantum.algorithms.vqe.run_vqe", return_value={
                "electronic_energy": -1.2,
                "optimizer": "SLSQP",
                "ansatz": "n_local",
                "optimizer_success": True,
                "optimizer_message": "converged",
                "optimizer_status_available": True,
            }),
            patch("quantum.chemistry.quantum_analysis.run_vqe", return_value={
                "electronic_energy": -1.2,
                "optimizer": "SLSQP",
                "ansatz": "n_local",
                "optimizer_success": True,
                "optimizer_message": "converged",
                "optimizer_status_available": True,
            }),
        ]
        for item in common:
            stack.enter_context(item)
        return active_problem

    def test_local_smiles_path_reports_corrected_and_raw_energy(self):
        from contextlib import ExitStack

        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, {"pyscf": types.ModuleType("pyscf")}))
            stack.enter_context(patch("quantum.chemistry.quantum_analysis.smiles_to_geometry", return_value="H 0 0 0"))
            self.setup_quantum_mocks(stack)
            stack.enter_context(patch(
                "quantum.algorithms.exact_solver.run_exact_solver",
                return_value={"exact_energy_hartree": -1.3},
            ))
            result = analyze_smiles("O", benchmark=True)

        self.assertEqual(result["vqe"]["raw_active_space_energy_hartree"], -1.2)
        self.assertAlmostEqual(result["vqe"]["electronic_energy_hartree"], -0.8)
        self.assertAlmostEqual(result["vqe"]["total_molecular_energy_hartree"], -0.1)
        self.assertAlmostEqual(result["exact_reference"]["total_molecular_energy_hartree"], -0.2)
        self.assertAlmostEqual(result["benchmark"]["absolute_error_hartree"], 0.1)
        self.assertTrue(result["vqe"]["optimizer_success"])
        self.assertTrue(result["vqe"]["optimizer_status_available"])

    def test_wsl_worker_reports_same_corrected_energy_components(self):
        from contextlib import ExitStack

        with ExitStack() as stack:
            self.setup_quantum_mocks(stack)
            result = _run_molecular_analysis({
                "atom": "H 0 0 0; H 0 0 0.74",
                "basis": "sto3g",
                "maxiter": 10,
            })["result"]

        self.assertEqual(result["vqe"]["raw_active_space_energy_hartree"], -1.2)
        self.assertAlmostEqual(result["vqe"]["electronic_energy_hartree"], -0.8)
        self.assertAlmostEqual(result["vqe"]["total_molecular_energy_hartree"], -0.1)
        self.assertTrue(result["vqe"]["optimizer_success"])
        self.assertTrue(result["vqe"]["optimizer_status_available"])


if __name__ == "__main__":
    unittest.main()
