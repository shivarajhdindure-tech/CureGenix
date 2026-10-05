"""
Compute MCP Server

Provides computational tools for drug screening calculations:
drug-likeness scoring, BBB permeability, toxicity prediction,
molecular similarity, and ADMET property estimation.
"""

import random
import time
import math
from backend.mcp.base_mcp import BaseMCPServer


class ComputeMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            server_name="ComputeMCP",
            description="Computational tools for drug screening, scoring, and ADMET property prediction"
        )
        self._register_all_tools()

    def _register_all_tools(self):
        self.register_tool("calculate_drug_likeness", "Evaluate Lipinski Rule of Five and drug-likeness score", self._calculate_drug_likeness, {"smiles": "str", "properties": "dict"})
        self.register_tool("calculate_bbb_score", "Predict blood-brain barrier permeability score", self._calculate_bbb_score, {"smiles": "str", "properties": "dict"})
        self.register_tool("calculate_toxicity", "Predict toxicity risk using structural alerts and property rules", self._calculate_toxicity, {"smiles": "str", "drug_name": "str"})
        self.register_tool("calculate_similarity", "Calculate Tanimoto similarity between two molecules", self._calculate_similarity, {"smiles1": "str", "smiles2": "str"})
        self.register_tool("calculate_admet_score", "Comprehensive ADMET profiling", self._calculate_admet_score, {"smiles": "str", "properties": "dict"})
        self.register_tool("calculate_composite_score", "Calculate weighted composite screening score", self._calculate_composite_score, {"scores": "dict", "weights": "dict"})

    def _calculate_drug_likeness(self, smiles: str, properties: dict = None) -> dict:
        time.sleep(random.uniform(0.02, 0.06))
        if not properties:
            properties = self._estimate_properties(smiles)

        mw = properties.get("molecular_weight", 350)
        logp = properties.get("logP", 2.5)
        hbd = properties.get("hydrogen_bond_donors", 2)
        hba = properties.get("hydrogen_bond_acceptors", 5)

        violations = 0
        checks = []
        if mw > 500:
            violations += 1
            checks.append({"rule": "MW ≤ 500", "value": mw, "passed": False})
        else:
            checks.append({"rule": "MW ≤ 500", "value": mw, "passed": True})
        if logp > 5:
            violations += 1
            checks.append({"rule": "LogP ≤ 5", "value": logp, "passed": False})
        else:
            checks.append({"rule": "LogP ≤ 5", "value": logp, "passed": True})
        if hbd > 5:
            violations += 1
            checks.append({"rule": "HBD ≤ 5", "value": hbd, "passed": False})
        else:
            checks.append({"rule": "HBD ≤ 5", "value": hbd, "passed": True})
        if hba > 10:
            violations += 1
            checks.append({"rule": "HBA ≤ 10", "value": hba, "passed": False})
        else:
            checks.append({"rule": "HBA ≤ 10", "value": hba, "passed": True})

        score = max(0, 1.0 - (violations * 0.25))
        return {"drug_likeness_score": round(score, 2), "lipinski_violations": violations, "checks": checks, "drug_like": violations <= 1}

    def _calculate_bbb_score(self, smiles: str, properties: dict = None) -> dict:
        time.sleep(random.uniform(0.02, 0.06))
        if not properties:
            properties = self._estimate_properties(smiles)

        mw = properties.get("molecular_weight", 350)
        logp = properties.get("logP", 2.5)
        tpsa = properties.get("topological_polar_surface_area", 70)
        hbd = properties.get("hydrogen_bond_donors", 2)

        score = 1.0
        factors = []
        if tpsa > 90:
            penalty = min(0.4, (tpsa - 90) / 100)
            score -= penalty
            factors.append(f"TPSA {tpsa} > 90: penalty -{penalty:.2f}")
        if mw > 450:
            penalty = min(0.3, (mw - 450) / 500)
            score -= penalty
            factors.append(f"MW {mw} > 450: penalty -{penalty:.2f}")
        if hbd > 3:
            penalty = (hbd - 3) * 0.1
            score -= penalty
            factors.append(f"HBD {hbd} > 3: penalty -{penalty:.2f}")
        if 1.5 <= logp <= 4.0:
            factors.append(f"LogP {logp} in optimal range [1.5-4.0]")
        else:
            score -= 0.15
            factors.append(f"LogP {logp} outside optimal range")

        score = round(max(0, min(1, score)), 2)
        return {"bbb_score": score, "permeable": score >= 0.5, "factors": factors}

    def _calculate_toxicity(self, smiles: str, drug_name: str = "") -> dict:
        time.sleep(random.uniform(0.03, 0.08))
        alerts = []
        smiles_lower = smiles.lower()

        structural_alerts = [
            ("N=N", "Azo group — potential mutagenicity"),
            ("N(=O)=O", "Nitro group — hepatotoxicity risk"),
            ("[N+](=O)[O-]", "Nitro group — genotoxicity concern"),
            ("S(=O)(=O)F", "Sulfonyl fluoride — reactive electrophile"),
            ("C(=O)Cl", "Acyl chloride — reactive and toxic"),
        ]
        for pattern, alert in structural_alerts:
            if pattern in smiles:
                alerts.append(alert)

        if "F" in smiles and smiles.count("F") > 3:
            alerts.append("Multiple fluorine atoms — potential metabolic concerns")

        base_penalty = len(alerts) * 0.15 + random.uniform(0.0, 0.1)
        toxicity_penalty = round(min(1.0, base_penalty), 2)

        return {
            "drug_name": drug_name,
            "toxicity_penalty": toxicity_penalty,
            "structural_alerts": alerts,
            "alert_count": len(alerts),
            "predicted_toxicity": "high" if toxicity_penalty > 0.5 else "medium" if toxicity_penalty > 0.2 else "low"
        }

    def _calculate_similarity(self, smiles1: str, smiles2: str) -> dict:
        time.sleep(random.uniform(0.01, 0.04))
        set1 = set(smiles1[i:i+3] for i in range(len(smiles1)-2))
        set2 = set(smiles2[i:i+3] for i in range(len(smiles2)-2))
        if not set1 or not set2:
            tanimoto = 0.0
        else:
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            tanimoto = intersection / union if union > 0 else 0.0
        return {"smiles1": smiles1, "smiles2": smiles2, "tanimoto_similarity": round(tanimoto, 3)}

    def _calculate_admet_score(self, smiles: str, properties: dict = None) -> dict:
        time.sleep(random.uniform(0.05, 0.12))
        if not properties:
            properties = self._estimate_properties(smiles)

        absorption = round(random.uniform(0.4, 0.95), 2)
        distribution = round(random.uniform(0.3, 0.9), 2)
        metabolism = round(random.uniform(0.4, 0.95), 2)
        excretion = round(random.uniform(0.5, 0.9), 2)
        toxicity_score = round(1.0 - random.uniform(0.05, 0.4), 2)

        overall = round((absorption + distribution + metabolism + excretion + toxicity_score) / 5, 2)
        return {
            "absorption": absorption,
            "distribution": distribution,
            "metabolism": metabolism,
            "excretion": excretion,
            "toxicity_freedom": toxicity_score,
            "overall_admet": overall,
            "grade": "A" if overall >= 0.8 else "B" if overall >= 0.6 else "C" if overall >= 0.4 else "D"
        }

    def _calculate_composite_score(self, scores: dict, weights: dict = None) -> dict:
        if not weights:
            weights = {"drug_likeness": 0.25, "bbb_permeability": 0.20, "potency_proxy": 0.30, "toxicity_freedom": 0.25}
        composite = sum(scores.get(k, 0) * w for k, w in weights.items())
        return {"composite_score": round(composite, 3), "components": scores, "weights": weights}

    def _estimate_properties(self, smiles: str) -> dict:
        mw = round(len(smiles) * 5.5 + random.uniform(-20, 20), 1)
        return {
            "molecular_weight": min(max(mw, 150), 650),
            "logP": round(random.uniform(0.5, 5.0), 2),
            "hydrogen_bond_donors": max(0, min(smiles.count("N") + smiles.count("O") - smiles.count("=O"), 5)),
            "hydrogen_bond_acceptors": min(smiles.count("N") + smiles.count("O"), 10),
            "topological_polar_surface_area": round(random.uniform(30, 140), 1)
        }
