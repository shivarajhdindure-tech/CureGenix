"""Generate validated, provenance-carrying analogs for verified targets."""

from rdkit import Chem

from backend.agents.base_agent import BaseAgent
from backend.services.target_aware_generation import (
    candidate_provenance,
    get_target_references,
)


class MoleculeAgent(BaseAgent):
    def __init__(self, mcp_registry: dict):
        super().__init__("Molecule Agent", "Generates target-informed molecular analog hypotheses", mcp_registry)

    def run(self, context: dict) -> dict:
        info_result = self.mcp_call("memory", "retrieve", key="protein_info")
        protein_info = info_result.get("data", {}).get("value") or {}
        target_identity = protein_info.get("target_identity") or {}
        refs, reference_warning = get_target_references(target_identity)
        warnings = list(target_identity.get("warnings") or [])
        if reference_warning:
            warnings.append(reference_warning)
        warning = " ".join(dict.fromkeys(warnings)) or None

        candidates = []
        seen_smiles = set()
        generation_method = "RDKit rule-based analog enumeration"
        for reference in refs:
            analog_result = self.mcp_call(
                "molecule", "generate_analogs",
                parent_smiles=reference["smiles"],
                parent_name=reference["name"],
                modification_strategy="target_reference_analog",
                count=2,
            ).get("data", {})
            for analog in analog_result.get("analogs", []):
                mol = Chem.MolFromSmiles(analog.get("smiles") or "")
                if mol is None:
                    continue
                smiles = Chem.MolToSmiles(mol, canonical=True)
                if smiles in seen_smiles:
                    continue
                seen_smiles.add(smiles)
                props = self.mcp_call(
                    "molecule", "compute_molecular_properties", smiles=smiles
                ).get("data", {})
                provenance = candidate_provenance(
                    target_identity, reference, analog.get("modification", "")
                )
                candidates.append({
                    "name": analog.get("id", "Target-informed analog"),
                    "smiles": smiles,
                    "molecular_properties": props,
                    "source": f"MoleculeMCP analog of {reference['name']}",
                    "category": "novel",
                    "verification_status": "not_verified",
                    "target_association_verified": False,
                    "candidate_metadata": provenance,
                })

        if not refs:
            generation_method = (
                "disabled: no configured target references"
                if target_identity.get("candidate_generation_allowed") is True
                else "disabled: target identity is not accepted"
            )
        elif not candidates and not warning:
            warning = "Configured reference was available, but no valid unique analogs were generated."

        status = {
            "target_identity": target_identity,
            "generation_method": generation_method,
            "reference_compound_count": len(refs),
            "candidate_count": len(candidates),
            "warning": warning,
            "warnings": list(dict.fromkeys(warnings)),
            "claims": "Target-informed hypotheses only; no docking or binding-affinity prediction was performed.",
        }
        self.mcp_call("memory", "store", key="candidate_generation_status", value=status)
        self.mcp_call("memory", "store", key="molecules", value=candidates)
        return {
            "summary": f"Generated {len(candidates)} validated candidate hypotheses for {protein_info.get('protein_name', 'Unknown Target')}",
            "molecules": candidates,
            "candidate_generation": status,
        }
