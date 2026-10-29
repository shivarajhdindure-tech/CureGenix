"""
 Calculation of Lipinski parameters for molecules

"""
from __future__ import annotations
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import rdkit.Chem.rdchem
__all__: list[str] = ['Chem', 'HAcceptorSmarts', 'HDonorSmarts', 'HeavyAtomCount', 'HeteroatomSmarts', 'NHOHSmarts', 'NOCountSmarts', 'RotatableBondSmarts', 'nm', 'rdMolDescriptors', 'txt']
def HeavyAtomCount(mol):
    """
     Number of heavy atoms a molecule.
    """
HAcceptorSmarts: rdkit.Chem.rdchem.Mol
HDonorSmarts: rdkit.Chem.rdchem.Mol
HeteroatomSmarts: rdkit.Chem.rdchem.Mol
NHOHSmarts: rdkit.Chem.rdchem.Mol
NOCountSmarts: rdkit.Chem.rdchem.Mol
RotatableBondSmarts: rdkit.Chem.rdchem.Mol
_bulkConvert: tuple = ('CalcFractionCSP3', 'CalcNumAromaticRings', 'CalcNumSaturatedRings', 'CalcNumAromaticHeterocycles', 'CalcNumAromaticCarbocycles', 'CalcNumSaturatedHeterocycles', 'CalcNumSaturatedCarbocycles', 'CalcNumAliphaticRings', 'CalcNumAliphaticHeterocycles', 'CalcNumAliphaticCarbocycles', 'CalcNumHeterocycles', 'CalcNumBridgeheadAtoms', 'CalcNumAmideBonds', 'CalcNumAtomStereoCenters', 'CalcNumHeterocycles', 'CalcNumUnspecifiedAtomStereoCenters', 'CalcNumSpiroAtoms', 'CalcPhi')
nm: str = 'Phi'
txt: str = 'CalcPhi'
