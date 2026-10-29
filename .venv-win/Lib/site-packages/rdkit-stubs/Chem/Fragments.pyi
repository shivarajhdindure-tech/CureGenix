"""
 functions to match a bunch of fragment descriptors from a file

No user-serviceable parts inside.  ;-)

"""
from __future__ import annotations
import os as os
from rdkit import Chem
from rdkit import RDConfig
__all__: list[str] = ['Chem', 'RDConfig', 'defaultPatternFileName', 'fn', 'fns', 'name', 'os']
def _CountMatches(mol, patt, unique = True):
    ...
def _LoadPatterns(fileName = None):
    ...
defaultPatternFileName: str = 'C:/rdkit/build/temp.win-amd64-cpython-312/Release/rdkit_install\\share/RDKit\\Data\\FragmentDescriptors.csv'
fn = None
fns: list
name: str = 'fr_HOCCN'
