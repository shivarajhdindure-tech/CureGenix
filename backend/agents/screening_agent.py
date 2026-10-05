"""
Screening Agent — Scores all drug candidates using ComputeMCP.
Evaluates drug-likeness, BBB permeability, potency, and toxicity.
"""

from backend.agents.base_agent import BaseAgent


class ScreeningAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Screening Agent", "Screens and scores all drug candidates", mcp_registry)

    def run(self, context: dict) -> dict:
        # Get all candidates from memory
        mol_result = self.mcp_call("memory", "retrieve", key="molecules")
        candidates = mol_result.get("data", {}).get("value") or []

        screening_scores = []

        # Score novel candidates
        for candidate in candidates:
            smiles = candidate.get("smiles", "C")
            cat = candidate.get("category", "novel")
            dl_result = self.mcp_call("compute", "calculate_drug_likeness", smiles=smiles)
            bbb_result = self.mcp_call("compute", "calculate_bbb_score", smiles=smiles)
            tox_result = self.mcp_call("compute", "calculate_toxicity", smiles=smiles, drug_name=candidate["name"])

            dl_score = dl_result.get("data", {}).get("drug_likeness_score", 0.5)
            bbb_score = bbb_result.get("data", {}).get("bbb_score", 0.5)
            toxicity_penalty = tox_result.get("data", {}).get("toxicity_penalty", 0.1)
            toxicity_freedom = round(max(0.0, 1.0 - toxicity_penalty), 2)

            # Approved drugs get a potency proxy boost based on clinical evidence
            potency = 0.5
            if cat == "approved":
                potency = 0.85
            elif cat == "repurposed":
                potency = 0.70

            composite = self.mcp_call("compute", "calculate_composite_score", scores={
                "drug_likeness": dl_score,
                "bbb_permeability": bbb_score,
                "potency_proxy": potency,
                "toxicity_freedom": toxicity_freedom
            })

            screening_scores.append({
                "drug_name": candidate["name"],
                "smiles": smiles,
                "category": cat,
                "drug_likeness": round(dl_score, 2),
                "bbb_permeability": round(bbb_score, 2),
                "potency_proxy": potency,
                "toxicity_penalty": round(toxicity_penalty, 2),
                "toxicity_freedom": toxicity_freedom,
                "composite_score": round(composite.get("data", {}).get("composite_score", 0), 3)
            })

        # Sort by composite score
        screening_scores.sort(key=lambda x: x["composite_score"], reverse=True)

        self.mcp_call("memory", "store", key="screened_molecules", value=screening_scores)

        top = screening_scores[0] if screening_scores else {"drug_name": "N/A", "composite_score": 0}
        summary = f"Screened {len(screening_scores)} candidates. Top scorer: {top['drug_name']} ({top.get('composite_score',0):.3f})"

        return {
            "summary": summary,
            "screening_scores": screening_scores,
            "total_screened": len(screening_scores)
        }

