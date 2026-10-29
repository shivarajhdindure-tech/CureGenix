"""Curated, fail-closed target reference data for candidate generation.

References are analog parents only. Their target evidence does not transfer to
generated analogs, and no binding or affinity prediction is performed here.
"""

from __future__ import annotations

from copy import deepcopy


SUPPORTED_TARGETS = {
    "P00533": {
        "target_name": "Epidermal growth factor receptor",
        "organism": "Homo sapiens",
        "references": [
            {
                "name": "Erlotinib",
                "chembl_id": "CHEMBL553",
                "smiles": "COCCOc1cc2ncnc(Nc3cccc(c3)C#C)c2cc1OCCOC",
                "scaffold_name": "4-anilinoquinazoline",
                "rationale": (
                    "Erlotinib has published EGFR inhibitory activity and is used "
                    "only as a documented medicinal-chemistry analog parent. "
                    "This does not establish activity for generated analogs."
                ),
                "sources": [
                    {
                        "name": "UniProt P00533: human EGFR target record",
                        "url": "https://www.uniprot.org/uniprotkb/P00533/entry",
                    },
                    {
                        "name": "ChEMBL compound CHEMBL553",
                        "url": "https://www.ebi.ac.uk/chembl/explore/compound/CHEMBL553",
                    },
                    {
                        "name": "IUPHAR/BPS erlotinib ligand activity record (includes EGFR assay and ChEMBL link)",
                        "url": "https://www.guidetopharmacology.org/GRAC/LigandActivityRangeVisForward?ligandId=4920",
                    },
                    {
                        "name": "ChEBI erlotinib structure record",
                        "url": "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=114785",
                    },
                ],
            }
        ],
    }
}


def get_target_references(target_identity: dict | None) -> tuple[list[dict], str | None]:
    """Return references only for an exact, resolved UniProt target identity."""
    identity = target_identity or {}
    accession = str(identity.get("uniprot_id") or "").upper()
    status = identity.get("identity_state")

    if status not in {
        "structure_linked_sequence_validated",
        "structure_linked_partial_sequence_support",
    } or identity.get("candidate_generation_allowed") is not True or not accession:
        return [], (
            "No target-informed candidates were generated because target identity "
            "does not have accepted sequence support for a DBREF-linked target on the "
            "selected PDB chain. Select a chain or use a structure with a usable DBREF."
        )

    target = SUPPORTED_TARGETS.get(accession)
    if target is None:
        return [], (
            f"Target {accession} is verified, but CureGenix has no configured "
            "target-linked reference compounds for it. No analogs were generated."
        )

    return deepcopy(target["references"]), None


def candidate_provenance(
    target_identity: dict, reference: dict, modification: str
) -> dict:
    """Build candidate metadata that distinguishes parent evidence from hypothesis."""
    return {
        "target": {
            "name": target_identity.get("protein_name"),
            "uniprot_id": target_identity.get("uniprot_id"),
            "identity_state": target_identity.get("identity_state"),
            "identity_status": target_identity.get("identity_state"),
            "structure_link_status": target_identity.get("structure_link_status"),
            "selected_chain_id": target_identity.get("selected_chain_id"),
            "identity_source": target_identity.get("identity_source"),
            "warnings": target_identity.get("warnings", []),
                "generation_authorization": target_identity.get("generation_authorization", {}),
                "independent_structure_evidence": target_identity.get("independent_structure_evidence", {}),
            "evidence": {
                "dbref_records": target_identity.get("dbref_records", []),
                "chain_accessions": target_identity.get("chain_accessions", {}),
                "uniprot_lookup": target_identity.get("uniprot_lookup", {}),
                "sequence_validation": target_identity.get("sequence_validation", {}),
            },
        },
        "scaffold_provenance": {
            "scaffold_name": reference["scaffold_name"],
            "reference_compound": reference["name"],
            "reference_chembl_id": reference["chembl_id"],
            "rationale": reference["rationale"],
            "sources": reference["sources"],
        },
        "generation_method": {
            "name": "RDKit rule-based analog enumeration",
            "modification": modification,
            "scope": "target-informed hypothesis; not an experimentally validated target binder",
            "protein_ligand_docking_performed": False,
            "binding_affinity_predicted": False,
        },
    }
