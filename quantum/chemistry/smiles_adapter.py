from rdkit import Chem
from rdkit.Chem import AllChem


def smiles_to_geometry(smiles: str, random_seed: int = 42) -> str:
    """
    Convert a SMILES string into a 3D molecular geometry
    compatible with Qiskit Nature / PySCF.

    Returns:
        Geometry string such as:
        C 0.0 0.0 0.0; H 0.0 0.0 1.0; ...
    """

    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    # Add explicit hydrogens
    mol = Chem.AddHs(mol)

    # Generate 3D coordinates
    status = AllChem.EmbedMolecule(
        mol,
        randomSeed=random_seed,
    )

    if status != 0:
        raise RuntimeError(
            f"RDKit failed to generate 3D coordinates for: {smiles}"
        )

    # Classical geometry optimization
    result = AllChem.MMFFOptimizeMolecule(mol)

    if result == -1:
        raise RuntimeError(
            f"MMFF optimization failed for: {smiles}"
        )

    conformer = mol.GetConformer()

    atoms = []

    for atom in mol.GetAtoms():
        idx = atom.GetIdx()
        position = conformer.GetAtomPosition(idx)

        atoms.append(
            f"{atom.GetSymbol()} "
            f"{position.x:.8f} "
            f"{position.y:.8f} "
            f"{position.z:.8f}"
        )

    return "; ".join(atoms)