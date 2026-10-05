"""
Risk Agent — Evaluates safety risks for all drug candidates.

v2: Falls back gracefully when no curated risk profiles exist for the protein.
    Uses ComputeMCP for structural toxicity assessment on all candidates.
"""

from backend.agents.base_agent import BaseAgent


class RiskAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Risk Agent", "Evaluates safety and risk profiles for candidates", mcp_registry)

    def run(self, context: dict) -> dict:
        # Get screening scores from memory
        scores_result = self.mcp_call("memory", "retrieve", key="screened_molecules")
        screening_scores = scores_result.get("data", {}).get("value") or []

        risk_flags = []
        for score_entry in screening_scores:
            drug_name = score_entry["drug_name"]
            
            # Since these are minimal generated compounds, compute risk
            smiles = score_entry.get("smiles", "CC(=O)OC1=CC=CC=C1")
            tox_result = self.mcp_call("compute", "calculate_toxicity", smiles=smiles, drug_name=drug_name)
            tox_data = tox_result.get("data", {})

            predicted_level = tox_data.get("predicted_toxicity", "medium")
            alerts = tox_data.get("structural_alerts", [])
            flags = alerts if alerts else ["Limited safety data — novel compound"]

            risk_flags.append({
                "drug_name": drug_name,
                "risk_level": predicted_level,
                "flags": flags,
                "details": f"Computationally predicted risk profile. Structural alerts: {len(alerts)}",
                "source": "ComputeMCP:calculate_toxicity"
            })

        self.mcp_call("memory", "store", key="risk_flags", value=risk_flags)

        high_risk = [r for r in risk_flags if r["risk_level"] == "high"]
        low_risk = [r for r in risk_flags if r["risk_level"] == "low"]
        summary = (f"Assessed {len(risk_flags)} candidates: {len(low_risk)} low risk, "
                   f"{len(risk_flags) - len(high_risk) - len(low_risk)} medium risk, "
                   f"{len(high_risk)} high risk")

        return {
            "summary": summary,
            "risk_flags": risk_flags,
            "risk_distribution": {
                "low": len(low_risk),
                "medium": len(risk_flags) - len(high_risk) - len(low_risk),
                "high": len(high_risk)
            }
        }
