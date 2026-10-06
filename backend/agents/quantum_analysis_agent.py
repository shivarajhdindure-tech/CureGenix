import os
import gc
from backend.agents.base_agent import BaseAgent


class QuantumAnalysisAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__(
            "Quantum Analysis Agent",
            "Performs quantum-assisted molecular analysis using RDKit, PySCF and VQE",
            mcp_registry,
        )

    def run(self, context: dict) -> dict:
        molecules_result = self.mcp_call(
            "memory",
            "retrieve",
            key="molecules",
        )

        molecules = molecules_result.get("data", {}).get("value") or []

        if not molecules:
            return {
                "status": "error",
                "message": "No molecules found for quantum analysis",
            }

        # ---------------------------------------------------------
        # Deployment mode
        #
        # full  -> real PySCF + Qiskit + VQE
        # light -> Render Free safe RDKit-only analysis
        # ---------------------------------------------------------
        mode = os.getenv("CUREGENIX_QUANTUM_MODE", "full").lower()

        if mode == "light":
            return self._run_lightweight_analysis(molecules)

        return self._run_full_quantum_analysis(molecules)

    # =============================================================
    # FULL QUANTUM MODE
    # =============================================================

    def _run_full_quantum_analysis(self, molecules: list) -> dict:
        # IMPORTANT:
        # Import the heavy quantum stack ONLY when full mode is used.
        from quantum.chemistry.quantum_analysis import analyze_smiles

        analyzed = []
        quantum_candidates = 0
        successful = 0
        failed = 0

        for candidate in molecules:
            candidate = dict(candidate)

            category = candidate.get("category", "novel")
            smiles = candidate.get("smiles", "")

            # Quantum analysis is applied only to generated candidates.
            if category != "novel":
                candidate["quantum_analysis"] = {
                    "status": "skipped",
                    "message": (
                        "Quantum analysis limited to novel "
                        "generated candidates"
                    ),
                }
                analyzed.append(candidate)
                continue

            quantum_candidates += 1

            if not smiles:
                candidate["quantum_analysis"] = {
                    "status": "failed",
                    "message": "No SMILES available",
                }
                failed += 1
                analyzed.append(candidate)
                continue

            try:
                result = analyze_smiles(
                    smiles=smiles,
                    basis="sto3g",
                    maxiter=50,
                )

                candidate["quantum_analysis"] = result
                successful += 1

            except Exception as exc:
                candidate["quantum_analysis"] = {
                    "status": "failed",
                    "message": str(exc),
                }
                failed += 1

            finally:
                # Release temporary quantum-chemistry objects
                # before processing the next candidate.
                gc.collect()

            analyzed.append(candidate)

        self.mcp_call(
            "memory",
            "store",
            key="molecules",
            value=analyzed,
        )

        skipped = len(analyzed) - quantum_candidates

        return {
            "summary": (
                f"Quantum analysis completed for "
                f"{successful}/{quantum_candidates} novel candidates"
            ),
            "total_candidates": len(analyzed),
            "quantum_candidates": quantum_candidates,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "molecules": analyzed,
        }

    # =============================================================
    # LIGHTWEIGHT MODE
    # =============================================================

    def _run_lightweight_analysis(self, molecules: list) -> dict:
        """
        Render Free safe mode.

        Uses RDKit only.
        Does NOT load PySCF, Qiskit or run VQE.

        This keeps the public demo within the 512 MB Render limit.
        The real quantum implementation remains available in full mode.
        """

        from rdkit import Chem
        from rdkit.Chem import Descriptors, Lipinski, Crippen, rdMolDescriptors

        analyzed = []
        quantum_candidates = 0
        successful = 0
        failed = 0

        for candidate in molecules:
            candidate = dict(candidate)

            category = candidate.get("category", "novel")
            smiles = candidate.get("smiles", "")

            if category != "novel":
                candidate["quantum_analysis"] = {
                    "status": "skipped",
                    "message": (
                        "Quantum analysis limited to novel "
                        "generated candidates"
                    ),
                }

                analyzed.append(candidate)
                continue

            quantum_candidates += 1

            if not smiles:
                candidate["quantum_analysis"] = {
                    "status": "failed",
                    "message": "No SMILES available",
                }

                failed += 1
                analyzed.append(candidate)
                continue

            try:
                molecule = Chem.MolFromSmiles(smiles)

                if molecule is None:
                    raise ValueError("Invalid SMILES")

                molecular_weight = float(
                    Descriptors.MolWt(molecule)
                )

                logp = float(
                    Crippen.MolLogP(molecule)
                )

                tpsa = float(
                    rdMolDescriptors.CalcTPSA(molecule)
                )

                hbd = int(
                    Lipinski.NumHDonors(molecule)
                )

                hba = int(
                    Lipinski.NumHAcceptors(molecule)
                )

                rotatable_bonds = int(
                    Lipinski.NumRotatableBonds(molecule)
                )

                heavy_atoms = int(
                    Lipinski.HeavyAtomCount(molecule)
                )

                formal_charge = int(
                    Chem.GetFormalCharge(molecule)
                )

                # This is deliberately NOT presented as a VQE result.
                candidate["quantum_analysis"] = {
                    "status": "success",
                    "mode": "lightweight",
                    "method": "RDKit molecular descriptor analysis",

                    "message": (
                        "Lightweight cloud mode enabled. "
                        "Full PySCF + Jordan-Wigner + VQE analysis "
                        "is available in the full quantum mode."
                    ),

                    "molecular_descriptors": {
                        "molecular_weight": molecular_weight,
                        "logp": logp,
                        "tpsa": tpsa,
                        "hbd": hbd,
                        "hba": hba,
                        "rotatable_bonds": rotatable_bonds,
                        "heavy_atoms": heavy_atoms,
                        "formal_charge": formal_charge,
                    },

                    # Explicitly mark quantum computation as skipped.
                    "vqe": {
                        "status": "not_run",
                        "reason": "Render Free memory-safe mode",
                    },

                    "hamiltonian": {
                        "status": "not_built",
                        "reason": "Render Free memory-safe mode",
                    },

                    "active_space": {
                        "status": "not_computed",
                        "reason": "Render Free memory-safe mode",
                    },
                }

                successful += 1

            except Exception as exc:
                candidate["quantum_analysis"] = {
                    "status": "failed",
                    "mode": "lightweight",
                    "message": str(exc),
                }

                failed += 1

            analyzed.append(candidate)

        self.mcp_call(
            "memory",
            "store",
            key="molecules",
            value=analyzed,
        )

        skipped = len(analyzed) - quantum_candidates

        return {
            "summary": (
                f"Lightweight molecular analysis completed for "
                f"{successful}/{quantum_candidates} novel candidates"
            ),
            "total_candidates": len(analyzed),
            "quantum_candidates": quantum_candidates,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "mode": "lightweight",
            "molecules": analyzed,
        }