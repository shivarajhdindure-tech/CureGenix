from backend.agents.base_agent import BaseAgent


class QuantumAnalysisAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__(
            "Quantum Analysis Agent",
            "Performs quantum-assisted molecular analysis using RDKit, PySCF and VQE",
            mcp_registry,
        )

    def run(self, context: dict) -> dict:
        from quantum.chemistry.quantum_analysis import analyze_smiles

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

        analyzed = []
        quantum_candidates = 0
        successful = 0
        failed = 0

        for candidate in molecules:
            candidate = dict(candidate)
            category = candidate.get("category", "novel")
            smiles = candidate.get("smiles", "")

            # For the hackathon MVP, quantum analysis is applied
            # only to newly generated candidates.
            if category != "novel":
                candidate["quantum_analysis"] = {
                    "status": "skipped",
                    "message": "Quantum analysis limited to novel generated candidates",
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