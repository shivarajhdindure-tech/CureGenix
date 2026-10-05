"""
Decision Agent — Final ranking and recommendation engine.

v2: LLM-POWERED. Combines deterministic screening scores and risk flags
    to produce the final output, then uses LLM to generate scientific
    reasoning for the top candidates.
    
    Deterministic: scoring, ranking, composite calculation
    LLM-powered: reasoning, justification, risk interpretation
"""

from backend.agents.base_agent import BaseAgent
from backend.services.llm_service import call_llm


class DecisionAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Decision Agent", "Produces final ranked drug recommendations with LLM-powered reasoning", mcp_registry)

    def run(self, context: dict) -> dict:
        # ── Retrieve all accumulated data from MemoryMCP ──────────────────
        scores_result = self.mcp_call("memory", "retrieve", key="screened_molecules")
        screening_scores = scores_result.get("data", {}).get("value") or []

        risk_result = self.mcp_call("memory", "retrieve", key="risk_flags")
        risk_flags = risk_result.get("data", {}).get("value") or []

        protein_result = self.mcp_call("memory", "retrieve", key="protein_info")
        protein_name = (protein_result.get("data", {}).get("value") or {}).get("protein_name", "Unknown Target")

        research_result = self.mcp_call("memory", "retrieve", key="research_result")
        llm_research = (research_result.get("data", {}).get("value") or {}).get("llm_analysis", "")

        # ── Build risk lookup ─────────────────────────────────────────────
        risk_lookup = {r["drug_name"]: r for r in risk_flags}

        # ── Calculate adjusted scores (DETERMINISTIC) ─────────────────────
        ranked = []
        for score_entry in screening_scores:
            drug_name = score_entry["drug_name"]
            composite = score_entry["composite_score"]
            risk = risk_lookup.get(drug_name, {})
            risk_level = risk.get("risk_level", "medium")
            risk_penalty = {"low": 0.0, "medium": 0.08, "high": 0.20}.get(risk_level, 0.1)
            adjusted = round(composite - risk_penalty, 3)

            if score_entry.get("category") == "approved":
                confidence = "high"
            elif score_entry.get("category") == "repurposed":
                confidence = "medium"
            else:
                confidence = "low"

            ranked.append({
                "drug_name": drug_name,
                "smiles": score_entry.get("smiles", ""),
                "category": score_entry.get("category", "novel"),
                "composite_score": composite,
                "risk_level": risk_level,
                "risk_penalty": risk_penalty,
                "adjusted_score": adjusted,
                "confidence": confidence,
                "reasoning": "",  # Will be filled by LLM
                "risk_flags": risk.get("flags", []),
                "screening_details": {
                    "drug_likeness": score_entry.get("drug_likeness", 0),
                    "bbb_permeability": score_entry.get("bbb_permeability", 0),
                    "potency_proxy": score_entry.get("potency_proxy", 0),
                    "toxicity_penalty": score_entry.get("toxicity_penalty", 0)
                }
            })

        # ── Sort by adjusted score (DETERMINISTIC) ────────────────────────
        ranked.sort(key=lambda x: x["adjusted_score"], reverse=True)

        for i, r in enumerate(ranked):
            r["rank"] = i + 1

        # ── LLM-Powered Reasoning for top candidates ──────────────────────
        # Build a single LLM call for efficiency
        candidates_text = ""
        for r in ranked[:5]:  # Top 5 candidates
            candidates_text += (
                f"\n- {r['drug_name']} (Category: {r['category']}, "
                f"Score: {r['adjusted_score']:.3f}, Risk: {r['risk_level']}, "
                f"Drug-likeness: {r['screening_details']['drug_likeness']}, "
                f"BBB: {r['screening_details']['bbb_permeability']}, "
                f"Risk flags: {', '.join(r['risk_flags']) if r['risk_flags'] else 'none'})"
            )

        prompt = f"""You are a drug discovery expert providing final recommendations.

Target Protein: {protein_name}

Research Context:
{llm_research[:500] if llm_research else 'No prior LLM research available.'}

Ranked Candidates (by composite score):
{candidates_text}

For each candidate above, provide a 2-3 sentence scientific justification covering:
1. Why this candidate is promising or concerning
2. Key strengths based on its screening profile
3. Any risks or uncertainties to highlight

Format your response as:
## [Candidate Name]
[Your reasoning]

Be concise and scientifically precise. Do NOT use markdown code blocks."""

        llm_reasoning = call_llm(prompt, temperature=0.6, max_tokens=1200)

        # Parse LLM reasoning back into individual candidates
        if llm_reasoning:
            for r in ranked:
                # Extract reasoning for this specific candidate
                r["reasoning"] = self._extract_candidate_reasoning(
                    llm_reasoning, r["drug_name"], r, protein_name
                )
        else:
            # Fallback to template reasoning if LLM fails
            for r in ranked:
                r["reasoning"] = self._build_template_reasoning(r, protein_name)

        # ── Highlights (DETERMINISTIC) ────────────────────────────────────
        best_approved = next((r for r in ranked if r["category"] == "approved"), None)
        best_repurposed = next((r for r in ranked if r["category"] == "repurposed"), None)
        best_novel = next((r for r in ranked if r["category"] == "novel"), None)

        highlights = {
            "best_known_drug": best_approved["drug_name"] if best_approved else "N/A",
            "best_repurposed": best_repurposed["drug_name"] if best_repurposed else "N/A",
            "best_novel_candidate": best_novel["drug_name"] if best_novel else "N/A"
        }

        # ── Store decisions in memory ─────────────────────────────────────
        self.mcp_call("memory", "store", key="final_decisions", value=ranked)
        self.mcp_call("memory", "store", key="highlights", value=highlights)

        summary = (f"Final ranking complete for {protein_name}. "
                   f"Top recommendation: {ranked[0]['drug_name'] if ranked else 'None'} ")

        return {
            "summary": summary,
            "recommendations": ranked,
            "highlights": highlights,
            "total_evaluated": len(ranked)
        }

    def _extract_candidate_reasoning(self, llm_text: str, drug_name: str, candidate: dict, protein_name: str) -> str:
        """Extract the LLM reasoning block for a specific candidate."""
        import re
        # Try to find a section headed with the drug name
        # Look for ## Drug Name or **Drug Name** patterns
        patterns = [
            rf"##\s*{re.escape(drug_name)}(.*?)(?=##|\Z)",
            rf"\*\*{re.escape(drug_name)}\*\*(.*?)(?=\*\*|\Z)",
            rf"{re.escape(drug_name)}[:\-](.*?)(?=\n\n|\Z)",
        ]
        for pattern in patterns:
            match = re.search(pattern, llm_text, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                if len(text) > 20:  # Meaningful reasoning
                    return text

        # If no specific match found, use template as fallback
        return self._build_template_reasoning(candidate, protein_name)

    def _build_template_reasoning(self, score: dict, protein_name: str) -> str:
        """Fallback: Generate template reasoning if LLM fails."""
        parts = [f"{score['drug_name']} was evaluated for {protein_name}."]

        cat = score.get("category", "unknown")
        if cat == "approved":
            parts.append("As an FDA-approved drug, it has established clinical evidence and safety data.")
        elif cat == "repurposed":
            parts.append("This is a repurposed drug originally approved for another indication, showing promising cross-disease activity.")
        elif cat == "novel":
            parts.append("This is a novel candidate generated through computational methods.")

        dl = score.get("screening_details", {}).get("drug_likeness", 0)
        if dl >= 0.75:
            parts.append(f"It shows excellent drug-likeness ({dl}).")
        elif dl >= 0.5:
            parts.append(f"It has acceptable drug-likeness ({dl}).")

        risk_level = score.get("risk_level", "medium")
        flags = score.get("risk_flags", [])
        if risk_level == "low":
            parts.append("Safety profile is favorable with low risk.")
        elif risk_level == "high":
            parts.append(f"Caution: elevated risk level. Key concerns: {', '.join(flags[:2])}.")
        else:
            parts.append(f"Moderate risk profile. Monitor for: {', '.join(flags[:2]) if flags else 'standard adverse effects'}.")

        return " ".join(parts)
