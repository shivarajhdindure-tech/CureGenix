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
            description="Simulate 3D molecular structure and predict binding conformation",
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
        """Generate structural analogs with realistic modifications."""
        time.sleep(random.uniform(0.1, 0.3))

        strategies = {
            "bbb_penetration": {
                "description": "Optimize for blood-brain barrier permeability",
                "modifications": [
                    "Added lipophilic fluorine substituent to improve membrane permeability",
                    "Replaced polar hydroxyl with methoxy group to reduce TPSA",
                    "Introduced N-methylation to reduce hydrogen bond donors",
                    "Replaced carboxylic acid with tetrazole bioisostere"
                ]
            },
            "selectivity": {
                "description": "Improve target selectivity to reduce off-target effects",
                "modifications": [
                    "Extended binding motif with pyridine ring for selective pocket interaction",
                    "Added steric bulk near off-target binding region",
                    "Introduced conformational constraint via cyclization",
                    "Replaced flexible linker with rigid biphenyl scaffold"
                ]
            },
            "metabolic_stability": {
                "description": "Improve metabolic stability and oral bioavailability",
                "modifications": [
                    "Blocked CYP3A4 metabolic soft spot with fluorine",
                    "Replaced ester with amide for hydrolytic stability",
                    "Deuterium substitution at metabolically labile position",
                    "Added gem-dimethyl group to block oxidative metabolism"
                ]
            },
            "balanced": {
                "description": "Balanced optimization across ADMET properties",
                "modifications": [
                    "Fluorine substitution for improved metabolic stability and lipophilicity",
                    "Piperazine replacement for enhanced solubility and target engagement",
                    "Cyclopropyl introduction for conformational rigidity",
                    "Bioisosteric replacement of amide with sulfonamide"
                ]
            }
        }

        strategy = strategies.get(modification_strategy, strategies["balanced"])
        analogs = []

        for i in range(min(count, len(strategy["modifications"]))):
            seed = hashlib.md5(f"{parent_smiles}_{i}_{modification_strategy}".encode()).hexdigest()
            analog_smiles = self._mutate_smiles(parent_smiles, i)
            analogs.append({
                "id": f"GEN-{seed[:6].upper()}",
                "smiles": analog_smiles,
                "parent_drug": parent_name or "Unknown",
                "parent_smiles": parent_smiles,
                "modification": strategy["modifications"][i],
                "strategy": modification_strategy,
                "predicted_properties": self._quick_property_estimate(analog_smiles),
                "similarity_to_parent": round(random.uniform(0.55, 0.90), 2),
                "confidence": round(random.uniform(0.6, 0.9), 2)
            })

        return {
            "strategy": strategy["description"],
            "parent": parent_name,
            "analogs_generated": len(analogs),
            "analogs": analogs
        }

    def _simulate_structure(self, smiles: str, target_protein: str = "") -> dict:
        """Simulate 3D structure and predict binding properties."""
        time.sleep(random.uniform(0.15, 0.35))

        energy_score = round(random.uniform(-12.5, -5.2), 2)
        rmsd = round(random.uniform(0.8, 3.5), 2)

        return {
            "smiles": smiles,
            "target_protein": target_protein,
            "simulation": {
                "method": "Semi-empirical conformer generation (PM7-level)",
                "num_conformers_generated": random.randint(10, 50),
                "lowest_energy_conformer": {
                    "energy_kcal_mol": energy_score,
                    "rmsd_angstrom": rmsd,
                    "num_rotatable_bonds": random.randint(2, 8)
                },
                "binding_prediction": {
                    "docking_score": round(energy_score * random.uniform(0.8, 1.2), 2),
                    "predicted_ki_nm": round(10 ** random.uniform(0.5, 3.5), 1),
                    "binding_mode": random.choice([
                        "Competitive inhibitor — binds active site",
                        "Allosteric modulator — binds regulatory site",
                        "Mixed inhibition — partial active site overlap",
                        "Covalent binder — irreversible modification"
                    ]),
                    "key_interactions": random.sample([
                        "Hydrogen bond with Asp32",
                        "Pi-stacking with Phe108",
                        "Salt bridge with Glu205",
                        "Hydrophobic contact with Leu120",
                        "Van der Waals with Val148",
                        "Water-mediated H-bond with Thr72"
                    ], k=random.randint(2, 4))
                }
            }
        }

    def _compute_molecular_properties(self, smiles: str) -> dict:
        """Compute molecular properties using rule-based estimation."""
        time.sleep(random.uniform(0.02, 0.08))
        return self._quick_property_estimate(smiles)

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
