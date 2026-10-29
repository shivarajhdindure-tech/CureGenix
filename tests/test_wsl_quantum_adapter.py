"""
Tests for WSL PySCF Quantum Integration

Covers:
1. PySCF smoke test (H2 and STO-3G verifying convergence and energy near -1.117 Hartree).
2. Valid molecular calculation through the Windows-to-WSL integration.
3. Missing and invalid input handling.
4. Calculation timeout handling and process cleanup.
5. Missing WSL environment or invalid distribution handling.
6. Error propagation to the quantum analysis agent.
7. Verification that existing endpoints (health, molecule 3D, benchmarks, mcp-tools) still work.
"""

import unittest
from backend.services.wsl_quantum_adapter import (
    WSLQuantumAdapter,
    WSLInputValidationError,
    WSLTimeoutError,
    WSLEnvironmentError,
    wsl_quantum_adapter,
)
from quantum.chemistry.quantum_analysis import analyze_smiles
from backend.mcp.memory_mcp import MemoryMCPServer
from backend.agents.quantum_analysis_agent import QuantumAnalysisAgent
from backend.main import app


class TestWSLQuantumIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Verify WSL environment is reachable before executing integration tests
        cls.is_available, cls.avail_msg = wsl_quantum_adapter.is_available()
        if not cls.is_available:
            print(f"WSL Not Available: {cls.avail_msg}")

    # -------------------------------------------------------------------------
    # 1. PySCF smoke test (H2, STO-3G)
    # -------------------------------------------------------------------------
    def test_01_pyscf_smoke_test(self):
        """Verify H2 Hartree-Fock calculation converges near -1.117 Hartree."""
        if not self.is_available:
            self.skipTest(f"WSL unavailable: {self.avail_msg}")

        result = wsl_quantum_adapter.run_smoke_test(basis="sto-3g", timeout=25)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("action"), "smoke_test")
        self.assertTrue(result.get("converged"), "SCF did not converge")

        scf_energy = result.get("scf_energy_hartree")
        self.assertIsInstance(scf_energy, float)
        # Expected H2 STO-3G ground state HF energy is approx -1.116759 Hartree
        self.assertAlmostEqual(scf_energy, -1.116759, places=3)

    # -------------------------------------------------------------------------
    # 2. Valid request through Windows-to-WSL integration
    # -------------------------------------------------------------------------
    def test_02_valid_molecular_quantum_request(self):
        """Test full VQE pipeline execution via analyze_smiles through WSL."""
        if not self.is_available:
            self.skipTest(f"WSL unavailable: {self.avail_msg}")

        # Analyze water (H2O, SMILES 'O')
        result = analyze_smiles("O", basis="sto3g", maxiter=20)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("method"), "VQE")
        self.assertIn("vqe", result)
        self.assertIn("electronic_energy_hartree", result["vqe"])
        self.assertIsInstance(result["vqe"]["electronic_energy_hartree"], float)

        # Orbital energies
        self.assertIn("homo", result)
        self.assertIn("lumo", result)
        self.assertIn("homo_lumo_gap_hartree", result)
        self.assertGreater(result["homo_lumo_gap_hartree"], 0.0)

        # Active space and Hamiltonian
        self.assertEqual(result["active_space"]["electrons"], 2)
        self.assertEqual(result["active_space"]["spatial_orbitals"], 2)
        self.assertEqual(result["hamiltonian"]["mapping"], "Jordan-Wigner")

    # -------------------------------------------------------------------------
    # 3. Missing or invalid input validation
    # -------------------------------------------------------------------------
    def test_03_invalid_input_handling(self):
        """Test that invalid inputs are rejected cleanly before running."""
        # Empty geometry string
        with self.assertRaises(WSLInputValidationError):
            wsl_quantum_adapter.analyze_geometry("")

        # Whitespace-only geometry string
        with self.assertRaises(WSLInputValidationError):
            wsl_quantum_adapter.analyze_geometry("   ")

        # Invalid maxiter (< 1 or > 1000)
        with self.assertRaises(WSLInputValidationError):
            wsl_quantum_adapter.analyze_geometry("H 0 0 0; H 0 0 0.74", maxiter=0)

        with self.assertRaises(WSLInputValidationError):
            wsl_quantum_adapter.analyze_geometry("H 0 0 0; H 0 0 0.74", maxiter=5000)

        # Invalid SMILES in analyze_smiles (handled on Windows by RDKit)
        with self.assertRaises(ValueError):
            analyze_smiles("")

        with self.assertRaises(ValueError):
            analyze_smiles("Invalid_Non_Existent_SMILES_12345")

    # -------------------------------------------------------------------------
    # 4. Calculation timeout handling
    # -------------------------------------------------------------------------
    def test_04_timeout_handling(self):
        """Test that a timeout triggers WSLTimeoutError and cleans up process."""
        if not self.is_available:
            self.skipTest(f"WSL unavailable: {self.avail_msg}")

        # Set an unrealistically short timeout (e.g., 0.001 seconds)
        adapter_short = WSLQuantumAdapter(timeout_seconds=0.001)
        with self.assertRaises(WSLTimeoutError):
            adapter_short.run_smoke_test(timeout=0.001)

    # -------------------------------------------------------------------------
    # 5. Missing WSL environment or distribution
    # -------------------------------------------------------------------------
    def test_05_missing_wsl_distribution(self):
        """Test error handling when distribution is nonexistent."""
        adapter_bad_distro = WSLQuantumAdapter(distro="CureGenixNonExistentDistro_9999")
        with self.assertRaises(WSLEnvironmentError):
            adapter_bad_distro.run_smoke_test(timeout=5)

    # -------------------------------------------------------------------------
    # 6. Correct error propagation to QuantumAnalysisAgent
    # -------------------------------------------------------------------------
    def test_06_agent_error_propagation(self):
        """Verify QuantumAnalysisAgent marks failed candidates gracefully."""
        memory = MemoryMCPServer()
        memory.init_pipeline("test_run", "TargetProtein")

        # Molecule with invalid SMILES that fails geometry generation
        test_molecules = [
            {
                "name": "MalformedCandidate",
                "smiles": ">>>INVALID<<<",
                "category": "novel",
            }
        ]
        memory._store("molecules", test_molecules)

        agent = QuantumAnalysisAgent({"memory": memory})
        run_res = agent.run({})

        self.assertEqual(run_res.get("failed"), 1)
        analyzed = memory._retrieve("molecules").get("value", [])
        self.assertEqual(len(analyzed), 1)
        self.assertEqual(analyzed[0]["quantum_analysis"]["status"], "failed")
        self.assertTrue(len(analyzed[0]["quantum_analysis"]["message"]) > 0)

    # -------------------------------------------------------------------------
    # 7. Confirmation that existing endpoints still work
    # -------------------------------------------------------------------------
    def test_07_existing_endpoints_integrity(self):
        """Verify existing FastAPI endpoints remain functional."""
        import asyncio

        async def check_endpoint(path: str, method: str = "GET", body: bytes = b""):
            response_body = []
            status_code = None

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            async def send(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                elif message["type"] == "http.response.body":
                    response_body.append(message.get("body", b""))

            scope = {
                "type": "http",
                "method": method,
                "path": path,
                "headers": [(b"content-type", b"application/json")] if body else [],
                "query_string": b"",
            }
            await app(scope, receive, send)
            import json
            raw_text = b"".join(response_body).decode("utf-8")
            data = json.loads(raw_text) if raw_text else {}
            return status_code, data

        # Check /api/health
        status, data = asyncio.run(check_endpoint("/api/health"))
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "healthy")

        # Check /api/benchmarks/egfr
        status, data = asyncio.run(check_endpoint("/api/benchmarks/egfr"))
        self.assertEqual(status, 200)
        self.assertIn("status_indicators", data)
        self.assertIn("five_split_classical", data)

        # Check /api/molecule/3d (RDKit 3D conformer generator)
        import json
        mol_payload = json.dumps({"smiles": "CCO"}).encode("utf-8")
        status, data = asyncio.run(check_endpoint("/api/molecule/3d", method="POST", body=mol_payload))
        self.assertEqual(status, 200)
        self.assertIn("mol_block", data)

        # Check /api/mcp-tools
        status, data = asyncio.run(check_endpoint("/api/mcp-tools"))
        self.assertEqual(status, 200)
        self.assertIn("mcp_servers", data)


if __name__ == "__main__":
    unittest.main()
