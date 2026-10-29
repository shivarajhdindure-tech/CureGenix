"""
Module containing functions to generate hashes for molecules
"""
from __future__ import annotations
import typing
__all__: list[str] = ['HashFunction', 'MolHash', 'excludeFromTautomerismProp']
class HashFunction(Boost.Python.enum):
    AnonymousGraph: typing.ClassVar[HashFunction]
    ArthorSubstructureOrder: typing.ClassVar[HashFunction]
    AtomBondCounts: typing.ClassVar[HashFunction]
    CanonicalSmiles: typing.ClassVar[HashFunction]
    DegreeVector: typing.ClassVar[HashFunction]
    ElementGraph: typing.ClassVar[HashFunction]
    ExtendedMurcko: typing.ClassVar[HashFunction]
    HetAtomProtomer: typing.ClassVar[HashFunction]
    HetAtomProtomerv2: typing.ClassVar[HashFunction]
    HetAtomTautomer: typing.ClassVar[HashFunction]
    HetAtomTautomerv2: typing.ClassVar[HashFunction]
    Mesomer: typing.ClassVar[HashFunction]
    MolFormula: typing.ClassVar[HashFunction]
    MurckoScaffold: typing.ClassVar[HashFunction]
    NetCharge: typing.ClassVar[HashFunction]
    RedoxPair: typing.ClassVar[HashFunction]
    Regioisomer: typing.ClassVar[HashFunction]
    SmallWorldIndexBR: typing.ClassVar[HashFunction]
    SmallWorldIndexBRL: typing.ClassVar[HashFunction]
    __slots__: typing.ClassVar[tuple] = tuple()
    names: typing.ClassVar[dict]
    values: typing.ClassVar[dict]
def MolHash(mol: Mol, func: HashFunction, useCxSmiles: bool = False, cxFlagsToSkip: int = 0) -> str:
    """
        Generate a hash for a molecule. The func argument determines which hash is generated.
    
        C++ signature :
            class std::basic_string<char,struct std::char_traits<char>,class std::allocator<char> > MolHash(class RDKit::ROMol,enum RDKit::MolHash::HashFunction [,bool=False [,unsigned int=0]])
    """
excludeFromTautomerismProp: str = '_MolHashExcludeFromTautomerism'
