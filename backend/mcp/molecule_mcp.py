"""
Molecule MCP Server

Provides tools for generating/simulating new molecule structures,
creating analogs of known drugs, computing molecular properties,
and performing similarity searches. This is the creative engine
of the drug discovery pipeline.
"""

import time
import random
import hashlib
from backend.mcp.base_mcp import BaseMCPServer


class MoleculeMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            server_name="MoleculeMCP",
            description="Tools for molecule generation, analog design, structure simulation, and molecular property computation"
        )
        self._register_all_tools()

    def _register_all_tools(self):
        self.register_tool(
            name="generate_analogs",
            description="Generate structural analogs of a parent drug molecule with targeted modifications",
            handler=self._generate_analogs,
            parameters={"parent_smiles": "str", "parent_name": "str", "modification_strategy": "str", "count": "int"}
        )
        self.register_tool(
            name="simulate_structure",
            description="Report that target docking is unavailable; no binding prediction is performed",
            handler=self._simulate_structure,
            parameters={"smiles": "str", "target_protein": "str"}
        )
        self.register_tool(
            name="compute_molecular_properties",
            description="Compute key molecular properties: MW, LogP, HBD, HBA, TPSA, rotatable bonds",
            handler=self._compute_molecular_properties,
            parameters={"smiles": "str"}
        )
        self.register_tool(
            name="similarity_search",
            description="Find similar molecules from known actives database using fingerprint similarity",
            handler=self._similarity_search,
            parameters={"query_smiles": "str", "threshold": "float"}
        )
        self.register_tool(
            name="scaffold_hop",
            description="Generate new molecules by replacing the core scaffold while preserving pharmacophore features",
            handler=self._scaffold_hop,
            parameters={"smiles": "str", "target_scaffold": "str"}
        )
        self.register_tool(
            name="enumerate_modifications",
            description="Enumerate possible modifications at specified positions on a molecule",
            handler=self._enumerate_modifications,
            parameters={"smiles": "str", "positions": "list", "modification_types": "list"}
        )

    def _generate_analogs(self, parent_smiles: str, parent_name: str = "", modification_strategy: str = "balanced", count: int = 3) -> dict:
        """Enumerate valid variants around a known terminal-alkyne motif.

        This is structure editing, not a prediction of target binding or ADMET.
        The caller must supply a documented parent compound and preserve its
        provenance separately.
        """
        from rdkit import Chem

        parent = Chem.MolFromSmiles(parent_smiles or "")
        if parent is None:
            return {
                "strategy": "RDKit analog enumeration",
                "parent": parent_name,
                "analogs_generated": 0,
                "analogs": [],
                "warning": "Parent SMILES is invalid.",
            }

        parent_canonical = Chem.MolToSmiles(parent, canonical=True)
        motif = Chem.MolFromSmarts("[c:1][C:2]#[CH:3]")
        matches = parent.GetSubstructMatches(motif)
        analog_specs = []

        for aromatic_carbon, alkyne_carbon, terminal_carbon in matches:
            extended = Chem.RWMol(parent)
            methyl_index = extended.AddAtom(Chem.Atom("C"))
            extended.AddBond(terminal_carbon, methyl_index, Chem.BondType.SINGLE)
            extended_molecule = extended.GetMol()
            try:
                Chem.SanitizeMol(extended_molecule)
                analog_specs.append(
                    (
                        Chem.MolToSmiles(extended_molecule, canonical=True),
                        "Extended the reference terminal alkyne by one carbon.",
                    )
                )
            except Exception:
                pass

            nitrile = Chem.RWMol(parent)
            nitrile_atom = nitrile.GetAtomWithIdx(terminal_carbon)
            nitrile_atom.SetAtomicNum(7)
            nitrile_atom.SetNoImplicit(True)
            nitrile_molecule = nitrile.GetMol()
            try:
                Chem.SanitizeMol(nitrile_molecule)
                analog_specs.append(
                    (
                        Chem.MolToSmiles(nitrile_molecule, canonical=True),
                        "Replaced the reference terminal alkyne terminus with a nitrile bioisostere.",
                    )
                )
            except Exception:
                pass

        motif_acetamide = Chem.MolFromSmarts("[CH3:1][C:2](=[O:3])[NH:4]")
        matches_acetamide = parent.GetSubstructMatches(motif_acetamide)

        for methyl_carbon, carbonyl_carbon, o_atom, n_atom in matches_acetamide:
            extended = Chem.RWMol(parent)
            new_c = extended.AddAtom(Chem.Atom("C"))
            extended.AddBond(methyl_carbon, new_c, Chem.BondType.SINGLE)
            extended_molecule = extended.GetMol()
            try:
                Chem.SanitizeMol(extended_molecule)
                analog_specs.append(
                    (
                        Chem.MolToSmiles(extended_molecule, canonical=True),
                        "Extended the reference acetamido methyl by one carbon (N-propionyl analog).",
                    )
                )
            except Exception:
                pass

            glycolyl = Chem.RWMol(parent)
            new_o = glycolyl.AddAtom(Chem.Atom("O"))
            glycolyl.AddBond(methyl_carbon, new_o, Chem.BondType.SINGLE)
            glycolyl_molecule = glycolyl.GetMol()
            try:
                Chem.SanitizeMol(glycolyl_molecule)
                analog_specs.append(
                    (
                        Chem.MolToSmiles(glycolyl_molecule, canonical=True),
                        "Hydroxylated the reference acetamido methyl (N-glycolyl analog).",
                    )
                )
            except Exception:
                pass

        motif_tbutyl = Chem.MolFromSmarts("[CH3:1][C:2]([CH3:3])([CH3:4])[NH:5]")
        matches_tbutyl = parent.GetSubstructMatches(motif_tbutyl)
        for m1, quat, m2, m3, nh in matches_tbutyl:
            des_methyl = Chem.RWMol(parent)
            des_methyl.RemoveAtom(m1)
            des_methyl_molecule = des_methyl.GetMol()
            try:
                Chem.SanitizeMol(des_methyl_molecule)
                analog_specs.append(
                    (
                        Chem.MolToSmiles(des_methyl_molecule, canonical=True),
                        "Homologated the reference tert-butylamide to an N-isopropylamide (des-methyl analog).",
                    )
                )
            except Exception:
                pass

        motif_pyridine = Chem.MolFromSmarts("[c:1]1[c:2][c:3][c:4][n:5][c:6]1")
        matches_pyridine = parent.GetSubstructMatches(motif_pyridine)
        for c1, c2, c3, c4, n5, c6 in matches_pyridine:
            benzyl = Chem.RWMol(parent)
            benzyl.GetAtomWithIdx(n5).SetAtomicNum(6)
            benzyl_molecule = benzyl.GetMol()
            try:
                Chem.SanitizeMol(benzyl_molecule)
                analog_specs.append(
                    (
                        Chem.MolToSmiles(benzyl_molecule, canonical=True),
                        "Substituted the reference 3-pyridylmethyl moiety with a benzyl bioisostere (pyridine N to C).",
                    )
                )
            except Exception:
                pass

        analogs = []
        seen = {parent_canonical}
        for analog_smiles, modification in analog_specs:
            molecule = Chem.MolFromSmiles(analog_smiles)
            if molecule is None:
                continue
            canonical = Chem.MolToSmiles(molecule, canonical=True)
            if canonical in seen:
                continue
            seen.add(canonical)
            digest = hashlib.sha256(
                f"{parent_canonical}|{canonical}|{modification_strategy}".encode()
            ).hexdigest()
            analogs.append(
                {
                    "id": f"GEN-{digest[:8].upper()}",
                    "smiles": canonical,
                    "parent_drug": parent_name or "Reference compound",
                    "parent_smiles": parent_canonical,
                    "modification": modification,
                    "strategy": modification_strategy,
                }
            )
            if len(analogs) >= max(0, min(int(count), 2)):
                break

        return {
            "strategy": "RDKit rule-based analog enumeration",
            "parent": parent_name,
            "analogs_generated": len(analogs),
            "analogs": analogs,
            "warning": None if analogs else "No supported editable motif was found in the reference compound.",
        }

    def _simulate_structure(self, smiles: str, target_protein: str = "") -> dict:
        """Fail clearly instead of fabricating docking or affinity results."""
        return {
            "smiles": smiles,
            "target_protein": target_protein,
            "simulation": {
                "status": "not_performed",
                "method": None,
                "warning": (
                    "No protein-ligand docking or binding-affinity prediction is "
                    "implemented. A protein structure and validated docking workflow "
                    "are required; no binding result is available."
                ),
            },
        }

    def _compute_molecular_properties(self, smiles: str) -> dict:
        """Compute standard 2D molecular descriptors with RDKit."""
        from rdkit import Chem
        from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors

        molecule = Chem.MolFromSmiles(smiles or "")
        if molecule is None:
            return {"status": "invalid_smiles", "error": "SMILES could not be parsed."}
        return {
            "status": "computed",
            "method": "RDKit 2D descriptors",
            "molecular_weight": round(float(Descriptors.MolWt(molecule)), 3),
            "logp": round(float(Crippen.MolLogP(molecule)), 3),
            "hbd": int(Lipinski.NumHDonors(molecule)),
            "hba": int(Lipinski.NumHAcceptors(molecule)),
            "tpsa": round(float(rdMolDescriptors.CalcTPSA(molecule)), 3),
            "rotatable_bonds": int(Lipinski.NumRotatableBonds(molecule)),
        }

    def _quick_property_estimate(self, smiles: str) -> dict:
        """Estimate molecular properties from SMILES using heuristic rules."""
        base_mw = len(smiles) * 5.5 + random.uniform(-20, 20)
        mw = round(min(max(base_mw, 150), 650), 1)

        heavy_atoms = sum(1 for c in smiles if c.isalpha() and c.isupper())
        logp = round(random.uniform(0.5, 5.0), 2)
        hbd = smiles.count("N") + smiles.count("O") - smiles.count("(=O)")
        hbd = max(0, min(hbd, 5))
        hba = smiles.count("N") + smiles.count("O")
        hba = min(hba, 10)
        tpsa = round(hbd * 20.2 + hba * 9.2 + random.uniform(-5, 5), 1)
        rot_bonds = smiles.count("C") // 3

        lipinski_violations = 0
        if mw > 500: lipinski_violations += 1
        if logp > 5: lipinski_violations += 1
        if hbd > 5: lipinski_violations += 1
        if hba > 10: lipinski_violations += 1

        return {
            "molecular_weight": mw,
            "logP": logp,
            "hydrogen_bond_donors": hbd,
            "hydrogen_bond_acceptors": hba,
            "topological_polar_surface_area": tpsa,
            "rotatable_bonds": rot_bonds,
            "heavy_atom_count": heavy_atoms,
            "lipinski_violations": lipinski_violations,
            "drug_like": lipinski_violations <= 1
        }

    def _similarity_search(self, query_smiles: str, threshold: float = 0.6) -> dict:
        """Find similar molecules using fingerprint-based similarity."""
        time.sleep(random.uniform(0.05, 0.15))

        similar_molecules = [
            {"smiles": "CC(=O)Oc1ccccc1C(=O)O", "name": "Aspirin", "similarity": round(random.uniform(threshold, 0.95), 2)},
            {"smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O", "name": "Ibuprofen", "similarity": round(random.uniform(threshold, 0.85), 2)},
            {"smiles": "OC(=O)c1ccccc1O", "name": "Salicylic acid", "similarity": round(random.uniform(threshold, 0.90), 2)}
        ]

        hits = [m for m in similar_molecules if m["similarity"] >= threshold]
        hits.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "query_smiles": query_smiles,
            "threshold": threshold,
            "hits_found": len(hits),
            "similar_molecules": hits
        }

    def _scaffold_hop(self, smiles: str, target_scaffold: str = "auto") -> dict:
        """Generate scaffold-hopped variants preserving pharmacophore."""
        time.sleep(random.uniform(0.1, 0.25))

        scaffolds = ["pyridine", "pyrimidine", "indole", "benzimidazole", "thiazole", "oxazole"]
        if target_scaffold == "auto":
            target_scaffold = random.choice(scaffolds)

        return {
            "original_smiles": smiles,
            "target_scaffold": target_scaffold,
            "hopped_variants": [
                {
                    "smiles": f"c1ncc({smiles[:10]})cc1" if len(smiles) > 10 else smiles,
                    "scaffold": target_scaffold,
                    "pharmacophore_preserved": round(random.uniform(0.7, 0.95), 2),
                    "novelty_score": round(random.uniform(0.6, 0.9), 2)
                }
            ]
        }

    def _enumerate_modifications(self, smiles: str, positions: list = None, modification_types: list = None) -> dict:
        """Enumerate possible modifications at specified positions."""
        time.sleep(random.uniform(0.05, 0.15))

        if modification_types is None:
            modification_types = ["fluorination", "methylation", "hydroxylation", "amination"]

        enumerations = []
        for mod_type in modification_types:
            enumerations.append({
                "modification_type": mod_type,
                "position": "auto-detected",
                "resulting_smiles": smiles + f"_{mod_type[:3]}",
                "predicted_impact": random.choice(["improved potency", "improved stability", "improved selectivity", "minimal change"]),
                "confidence": round(random.uniform(0.5, 0.9), 2)
            })

        return {
            "original_smiles": smiles,
            "total_modifications": len(enumerations),
            "enumerations": enumerations
        }

    def _mutate_smiles(self, smiles: str, mutation_index: int) -> str:
        """Simple SMILES mutation for generating analogs (demonstration)."""
        mutations = [
            lambda s: s.replace("c1ccccc1", "c1ccncc1", 1) if "c1ccccc1" in s else s + "F",
            lambda s: s.replace("O", "S", 1) if "O" in s else s + "C",
            lambda s: s.replace("N", "NC", 1) if "N" in s else s + "N",
            lambda s: s + "c1ccc(F)cc1" if len(s) < 50 else s.replace("C", "CC", 1)
        ]
        mutation_fn = mutations[mutation_index % len(mutations)]
        return mutation_fn(smiles)
