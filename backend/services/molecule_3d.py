from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/molecule", tags=["Molecular Explorer"])


class MoleculeRequest(BaseModel):
    smiles: str = Field(min_length=1, max_length=1000)


@router.post("/3d")
def generate_3d_structure(request: MoleculeRequest):
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem

        smiles = request.smiles.strip()
        molecule = Chem.MolFromSmiles(smiles)

        if molecule is None:
            raise HTTPException(status_code=422, detail="Invalid SMILES string.")

        if molecule.GetNumAtoms() > 150:
            raise HTTPException(
                status_code=422,
                detail="Molecule is too large for interactive conformer generation."
            )

        molecule = Chem.AddHs(molecule)
        params = AllChem.ETKDGv3()
        params.randomSeed = 42

        status = AllChem.EmbedMolecule(molecule, params)
        if status != 0:
            raise HTTPException(
                status_code=422,
                detail="RDKit could not generate a 3D conformer for this molecule."
            )

        optimization_status = AllChem.MMFFOptimizeMolecule(
            molecule, maxIters=200
        )
        optimization = (
            "converged" if optimization_status == 0
            else "iteration_limit_or_not_converged"
        )

        return {
            "mol_block": Chem.MolToMolBlock(molecule),
            "canonical_smiles": Chem.MolToSmiles(Chem.RemoveHs(molecule)),
            "atom_count": molecule.GetNumAtoms(),
            "heavy_atom_count": molecule.GetNumHeavyAtoms(),
            "geometry_optimization": optimization,
            "structure_status": "generated_computational_conformer",
            "method": "RDKit ETKDGv3 + MMFF",
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Molecular conformer generation failed."
        )
