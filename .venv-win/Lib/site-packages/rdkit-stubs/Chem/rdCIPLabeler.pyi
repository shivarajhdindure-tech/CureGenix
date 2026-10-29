"""
Module containing a function to assign stereochemical labels based on an accurate CIP rules implementation. This algoritm is a port of https://github.com/SiMolecule/centres, which was originally written by John Mayfield. The original algorithm is described in:

Hanson, R. M., Musacchio, S., Mayfield, J. W., Vainio, M. J., Yerin, A., Redkin, D.
Algorithmic Analysis of Cahn--Ingold--Prelog Rules of Stereochemistry:
Proposals for Revised Rules and a Guide for Machine Implementation.
J. Chem. Inf. Model. 2018, 58, 1755-1765.
"""
from __future__ import annotations
import typing
__all__: list[str] = ['AssignCIPLabels']
def AssignCIPLabels(mol: Mol, atomsToLabel: typing.Any = None, bondsToLabel: typing.Any = None, maxRecursiveIterations: int = 0) -> None:
    """
        New implementation of Stereo assignment using a true CIP ranking.
        On return:  The molecule to contains CIP flags
        Errors:  when maxRecursiveIterations is exceeded, throws a MaxIterationsExceeded error
        ARGUMENTS:
        
         - mol: the molecule
         - atomsToLabel: (optional) list of atoms to label
         - bondsToLabel: (optional) list of bonds to label
         - maxRecursiveIterations: (optional) protects against pseudo-infinite
        recursion for highly symmetrical structures. The limit is shared by the preliminary and full labeling passes.
         A value of 1,250,000 takes about 1 second. Most structures require fewer than 10,000 recursive comparisons.
         A peptide with MW~3000 took about 100 comparisons, and a 20,000 MW protein took about 600 comparisons
        (0 = default - no limit)
        
    
        C++ signature :
            void AssignCIPLabels(class RDKit::ROMol {lvalue} [,class boost::python::api::object=None [,class boost::python::api::object=None [,unsigned int=0]]])
    """
