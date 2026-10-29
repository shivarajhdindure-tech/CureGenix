from __future__ import annotations
import logging as logging
from rdkit import Chem
from rdkit.Chem import inchi
import re as re
__all__: list[str] = ['Chem', 'InchiInfo', 'UPD_APP', 'all_stereo_re', 'console', 'defined_stereo_re', 'fixed_h_re', 'h_layer_re', 'inchi', 'isotope_re', 'logging', 'mobile_h_atoms_re', 'mobile_h_group_re', 're', 'reconnected_re', 'stereo_all_re', 'stereo_re', 'undef_stereo_re', 'version_re']
class InchiInfo:
    def __init__(self, inchi_str):
        ...
    def get_mobile_h(self):
        """
         retrieve mobile H (tautomer) information
                return a 2-item tuple containing
                1) Number of mobile hydrogen groups detected. If 0, next item = '' 
                2) List of groups   
                
        """
    def get_sp3_stereo(self):
        """
         retrieve sp3 stereo information
                return a 4-item tuple containing
                1) Number of stereocenters detected. If 0, the remaining items of the tuple = None
                2) Number of undefined stereocenters. Must be smaller or equal to above
                3) True if the molecule is a meso form (with chiral centers and a plane of symmetry)
                4) Comma-separated list of internal atom numbers with sp3 stereochemistry
                
        """
def _is_achiral_by_symmetry(INCHI):
    ...
UPD_APP: logging.Logger
all_stereo_re: re.Pattern
console: logging.StreamHandler
defined_stereo_re: re.Pattern
fixed_h_re: re.Pattern
h_layer_re: re.Pattern
isotope_re: re.Pattern
mobile_h_atoms_re: re.Pattern
mobile_h_group_re: re.Pattern
reconnected_re: re.Pattern
stereo_all_re: re.Pattern
stereo_re: re.Pattern
undef_stereo_re: re.Pattern
version_re: re.Pattern
