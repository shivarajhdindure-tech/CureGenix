"""
Module containing RGroupDecomposition classes and functions.
"""
from __future__ import annotations
import typing
__all__: list[str] = ['AtomIndexLabels', 'AtomMap', 'AtomMapLabels', 'AutoDetect', 'DummyAtomLabels', 'Exhaustive', 'FingerprintVariance', 'GA', 'Greedy', 'GreedyChunks', 'Isotope', 'IsotopeLabels', 'MCS', 'MDLRGroup', 'MDLRGroupLabels', 'MOL_SPTR_VECT', 'Match', 'NoAlignment', 'NoSymmetrization', 'None', 'RGroupCoreAlignment', 'RGroupDecompose', 'RGroupDecomposition', 'RGroupDecompositionParameters', 'RGroupLabelling', 'RGroupLabels', 'RGroupMatching', 'RGroupScore', 'RelabelDuplicateLabels', 'RelabelMappedDummies']
class MOL_SPTR_VECT(Boost.Python.instance):
    __instance_size__: typing.ClassVar[int] = 48
    @staticmethod
    def __reduce__(*args, **kwargs):
        ...
    def __contains__(self, item: typing.Any) -> bool:
        """
            C++ signature :
                bool __contains__(class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > {lvalue},struct _object * __ptr64)
        """
    def __delitem__(self, item: typing.Any) -> None:
        """
            C++ signature :
                void __delitem__(class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > {lvalue},struct _object * __ptr64)
        """
    def __getitem__(self, item: typing.Any) -> typing.Any:
        """
            C++ signature :
                class boost::python::api::object __getitem__(struct boost::python::back_reference<class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > & __ptr64>,struct _object * __ptr64)
        """
    def __init__(self) -> None:
        """
            C++ signature :
                void __init__(struct _object * __ptr64)
        """
    def __iter__(self) -> typing.Any:
        """
            C++ signature :
                struct boost::python::objects::iterator_range<struct boost::python::return_value_policy<struct boost::python::return_by_value,struct boost::python::default_call_policies>,class std::_Vector_iterator<class std::_Vector_val<struct std::_Simple_types<class boost::shared_ptr<class RDKit::ROMol> > > > > __iter__(struct boost::python::back_reference<class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > & __ptr64>)
        """
    def __len__(self) -> int:
        """
            C++ signature :
                unsigned __int64 __len__(class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > {lvalue})
        """
    def __setitem__(self, item: typing.Any, value: typing.Any) -> None:
        """
            C++ signature :
                void __setitem__(class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > {lvalue},struct _object * __ptr64,struct _object * __ptr64)
        """
    def append(self, item: typing.Any) -> None:
        """
            C++ signature :
                void append(class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > {lvalue},class boost::python::api::object)
        """
    def extend(self, other: typing.Any) -> None:
        """
            C++ signature :
                void extend(class std::vector<class boost::shared_ptr<class RDKit::ROMol>,class std::allocator<class boost::shared_ptr<class RDKit::ROMol> > > {lvalue},class boost::python::api::object)
        """
class RGroupLabels(Boost.Python.enum):
    AtomIndexLabels: typing.ClassVar[RGroupLabels]
    AtomMapLabels: typing.ClassVar[RGroupLabels]
    AutoDetect: typing.ClassVar[RGroupLabels]
    DummyAtomLabels: typing.ClassVar[RGroupLabels]
    IsotopeLabels: typing.ClassVar[RGroupLabels]
    MDLRGroupLabels: typing.ClassVar[RGroupLabels]
    RelabelDuplicateLabels: typing.ClassVar[RGroupLabels]
    __slots__: typing.ClassVar[tuple] = tuple()
    names: typing.ClassVar[dict]
    values: typing.ClassVar[dict]
class RGroupMatching(Boost.Python.enum):
    Exhaustive: typing.ClassVar[RGroupMatching]
    GA: typing.ClassVar[RGroupMatching]
    Greedy: typing.ClassVar[RGroupMatching]
    GreedyChunks: typing.ClassVar[RGroupMatching]
    NoSymmetrization: typing.ClassVar[RGroupMatching]
    __slots__: typing.ClassVar[tuple] = tuple()
    names: typing.ClassVar[dict]
    values: typing.ClassVar[dict]
class RGroupLabelling(Boost.Python.enum):
    AtomMap: typing.ClassVar[RGroupLabelling]
    Isotope: typing.ClassVar[RGroupLabelling]
    MDLRGroup: typing.ClassVar[RGroupLabelling]
    __slots__: typing.ClassVar[tuple] = tuple()
    names: typing.ClassVar[dict]
    values: typing.ClassVar[dict]
class RGroupCoreAlignment(Boost.Python.enum):
    MCS: typing.ClassVar[RGroupCoreAlignment]
    NoAlignment: typing.ClassVar[RGroupCoreAlignment]
    None: typing.ClassVar[RGroupCoreAlignment]
    __slots__: typing.ClassVar[tuple] = tuple()
    names: typing.ClassVar[dict]
    values: typing.ClassVar[dict]
class RGroupScore(Boost.Python.enum):
    FingerprintVariance: typing.ClassVar[RGroupScore]
    Match: typing.ClassVar[RGroupScore]
    __slots__: typing.ClassVar[tuple] = tuple()
    names: typing.ClassVar[dict]
    values: typing.ClassVar[dict]
class RGroupDecompositionParameters(Boost.Python.instance):
    """
    RGroupDecompositionParameters controls how the RGroupDecomposition sets labelling and matches structures
      OPTIONS:
        - RGroupCoreAlignment: can be one of RGroupCoreAlignment.None_ or RGroupCoreAlignment.MCS
                               If set to MCS, cores labels are mapped to each other using their
                               Maximum common substructure overlap.
        - RGroupLabels: optionally set where the rgroup labels to use are encoded.
                         RGroupLabels.IsotopeLabels - labels are stored on isotopes
                         RGroupLabels.AtomMapLabels - labels are stored on atommaps
                         RGroupLabels.MDLRGroupLabels - labels are stored on MDL R-groups
                         RGroupLabels.DummyAtomLabels - labels are stored on dummy atoms
                         RGroupLabels.AtomIndexLabels - use the atom index as the label
                         RGroupLabels.RelabelDuplicateLabels - fix any duplicate labels
                         RGroupLabels.AutoDetect - auto detect the label [default]
           Note: in all cases, any rgroups found on unlabelled atoms will be automatically
                  labelled.
        - RGroupLabelling: choose where the rlabels are stored on the decomposition
                            RGroupLabelling.AtomMap - store rgroups as atom maps (for smiles)
                            RGroupLabelling.Isotope - store rgroups on the isotope
                            RGroupLabelling.MDLRGroup - store rgroups as mdl rgroups (for molblocks)
                           default: AtomMap | MDLRGroup
        - onlyMatchAtRGroups: only allow rgroup decomposition at the specified rgroups
        - removeAllHydrogenRGroups: remove all user-defined rgroups that only have hydrogens
        - removeAllHydrogenRGroupsAndLabels: remove all user-defined rgroups that only have hydrogens, and also remove the corresponding labels from the core
        - removeHydrogensPostMatch: remove all hydrogens from the output molecules
        - allowNonTerminalRGroups: allow labelled Rgroups of degree 2 or more
        - doTautomers: match all tautomers of a core against each input structure
        - doEnumeration: expand input cores into enumerated mol bundles
        - allowMultipleRGroupsOnUnlabelled: permit more than one rgroup to be attached to an unlabelled core atom
        - allowMultipleCoresInSameMol: permit a core to match more than once in the same molecule if the sets of matched atoms are not equal (default=False)
    """
    __instance_size__: typing.ClassVar[int] = 384
    @staticmethod
    def __reduce__(*args, **kwargs):
        ...
    @staticmethod
    def __setattr__(arg1: typing.Any, arg2: str, arg3: typing.Any) -> None:
        """
            C++ signature :
                void __setattr__(class boost::python::api::object,class std::basic_string<char,struct std::char_traits<char>,class std::allocator<char> >,class boost::python::api::object)
        """
    def __init__(self) -> None:
        """
            Constructor, takes no arguments
        
            C++ signature :
                void __init__(struct _object * __ptr64)
        """
    @property
    def alignment(*args, **kwargs):
        ...
    @alignment.setter
    def alignment(*args, **kwargs):
        ...
    @property
    def allowMultipleCoresInSameMol(*args, **kwargs):
        ...
    @allowMultipleCoresInSameMol.setter
    def allowMultipleCoresInSameMol(*args, **kwargs):
        ...
    @property
    def allowMultipleRGroupsOnUnlabelled(*args, **kwargs):
        ...
    @allowMultipleRGroupsOnUnlabelled.setter
    def allowMultipleRGroupsOnUnlabelled(*args, **kwargs):
        ...
    @property
    def allowNonTerminalRGroups(*args, **kwargs):
        ...
    @allowNonTerminalRGroups.setter
    def allowNonTerminalRGroups(*args, **kwargs):
        ...
    @property
    def chunkSize(*args, **kwargs):
        ...
    @chunkSize.setter
    def chunkSize(*args, **kwargs):
        ...
    @property
    def doEnumeration(*args, **kwargs):
        ...
    @doEnumeration.setter
    def doEnumeration(*args, **kwargs):
        ...
    @property
    def doTautomers(*args, **kwargs):
        ...
    @doTautomers.setter
    def doTautomers(*args, **kwargs):
        ...
    @property
    def gaMaximumOperations(*args, **kwargs):
        ...
    @gaMaximumOperations.setter
    def gaMaximumOperations(*args, **kwargs):
        ...
    @property
    def gaNumberOperationsWithoutImprovement(*args, **kwargs):
        ...
    @gaNumberOperationsWithoutImprovement.setter
    def gaNumberOperationsWithoutImprovement(*args, **kwargs):
        ...
    @property
    def gaNumberRuns(*args, **kwargs):
        ...
    @gaNumberRuns.setter
    def gaNumberRuns(*args, **kwargs):
        ...
    @property
    def gaParallelRuns(*args, **kwargs):
        ...
    @gaParallelRuns.setter
    def gaParallelRuns(*args, **kwargs):
        ...
    @property
    def gaPopulationSize(*args, **kwargs):
        ...
    @gaPopulationSize.setter
    def gaPopulationSize(*args, **kwargs):
        ...
    @property
    def gaRandomSeed(*args, **kwargs):
        ...
    @gaRandomSeed.setter
    def gaRandomSeed(*args, **kwargs):
        ...
    @property
    def includeTargetMolInResults(*args, **kwargs):
        ...
    @includeTargetMolInResults.setter
    def includeTargetMolInResults(*args, **kwargs):
        ...
    @property
    def labels(*args, **kwargs):
        ...
    @labels.setter
    def labels(*args, **kwargs):
        ...
    @property
    def matchingStrategy(*args, **kwargs):
        ...
    @matchingStrategy.setter
    def matchingStrategy(*args, **kwargs):
        ...
    @property
    def onlyMatchAtRGroups(*args, **kwargs):
        ...
    @onlyMatchAtRGroups.setter
    def onlyMatchAtRGroups(*args, **kwargs):
        ...
    @property
    def removeAllHydrogenRGroups(*args, **kwargs):
        ...
    @removeAllHydrogenRGroups.setter
    def removeAllHydrogenRGroups(*args, **kwargs):
        ...
    @property
    def removeAllHydrogenRGroupsAndLabels(*args, **kwargs):
        ...
    @removeAllHydrogenRGroupsAndLabels.setter
    def removeAllHydrogenRGroupsAndLabels(*args, **kwargs):
        ...
    @property
    def removeHydrogensPostMatch(*args, **kwargs):
        ...
    @removeHydrogensPostMatch.setter
    def removeHydrogensPostMatch(*args, **kwargs):
        ...
    @property
    def rgroupLabelling(*args, **kwargs):
        ...
    @rgroupLabelling.setter
    def rgroupLabelling(*args, **kwargs):
        ...
    @property
    def scoreMethod(*args, **kwargs):
        ...
    @scoreMethod.setter
    def scoreMethod(*args, **kwargs):
        ...
    @property
    def substructMatchParams(*args, **kwargs):
        ...
    @property
    def timeout(*args, **kwargs):
        ...
    @timeout.setter
    def timeout(*args, **kwargs):
        ...
class RGroupDecomposition(Boost.Python.instance):
    __instance_size__: typing.ClassVar[int] = 32
    @staticmethod
    def __reduce__(*args, **kwargs):
        ...
    def Add(self, mol: Mol) -> int:
        """
            C++ signature :
                int Add(class RDKit::RGroupDecompositionHelper {lvalue},class RDKit::ROMol)
        """
    def GetMatchingCoreIdx(self, mol: Mol, matches: typing.Any = None) -> int:
        """
            C++ signature :
                int GetMatchingCoreIdx(class RDKit::RGroupDecompositionHelper {lvalue},class RDKit::ROMol [,class boost::python::api::object {lvalue}=None])
        """
    def GetRGroupLabels(self) -> list:
        """
            Return the current list of found rgroups.
            Note, Process() should be called first
        
            C++ signature :
                class boost::python::list GetRGroupLabels(class RDKit::RGroupDecompositionHelper {lvalue})
        """
    def GetRGroupsAsColumns(self, asSmiles: bool = False) -> dict:
        """
            Return the rgroups as columns (note: can be fed directly into a pandas datatable)
              ARGUMENTS:
               - asSmiles: if True return smiles strings, otherwise return molecules [default: False]
                Column structure:
                   columns[rgroup_label] = [ mols_or_smiles ]
            
        
            C++ signature :
                class boost::python::dict GetRGroupsAsColumns(class RDKit::RGroupDecompositionHelper {lvalue} [,bool=False])
        """
    def GetRGroupsAsRows(self, asSmiles: bool = False) -> list:
        """
            Return the rgroups as rows (note: can be fed directly into a pandas datatable)
              ARGUMENTS:
               - asSmiles: if True return smiles strings, otherwise return molecules [default: False]
                Row structure:
                   rows[idx] = {rgroup_label: molecule_or_smiles}
            
        
            C++ signature :
                class boost::python::list GetRGroupsAsRows(class RDKit::RGroupDecompositionHelper {lvalue} [,bool=False])
        """
    def Process(self) -> bool:
        """
            Process the rgroups (must be done prior to GetRGroupsAsRows/Columns and GetRGroupLabels)
        
            C++ signature :
                bool Process(class RDKit::RGroupDecompositionHelper {lvalue})
        """
    def ProcessAndScore(self) -> tuple:
        """
            Process the rgroups and returns the score (must be done prior to GetRGroupsAsRows/Columns and GetRGroupLabels)
        
            C++ signature :
                class boost::python::tuple ProcessAndScore(class RDKit::RGroupDecompositionHelper {lvalue})
        """
    @typing.overload
    def __init__(self, cores: typing.Any) -> None:
        """
            Construct from a molecule or sequence of molecules
        
            C++ signature :
                void __init__(struct _object * __ptr64,class boost::python::api::object)
        """
    @typing.overload
    def __init__(self, cores: typing.Any, params: RGroupDecompositionParameters) -> None:
        """
            Construct from a molecule or sequence of molecules and a parameters object
        
            C++ signature :
                void __init__(struct _object * __ptr64,class boost::python::api::object,struct RDKit::RGroupDecompositionParameters)
        """
def RGroupDecompose(cores: typing.Any, mols: typing.Any, asSmiles: bool = False, asRows: bool = True, options: RGroupDecompositionParameters = ...) -> typing.Any:
    """
        Decompose a collection of molecules into their Rgroups
          ARGUMENTS:
            - cores: a set of cores from most to least specific.
                     See RGroupDecompositionParameters for more details
                     on how the cores can be labelled
            - mols: the molecules to be decomposed
            - asSmiles: if True return smiles strings, otherwise return molecules [default: False]
            - asRows: return the results as rows (default) otherwise return columns
            - options: RGroupDecompositionParameters object that defines the parameters for the decomposition.
                     See RGroupDecompositionParameters for defaults
        
          RETURNS: row_or_column_results, unmatched
        
            Row structure:
               rows[idx] = {rgroup_label: molecule_or_smiles}
            Column structure:
               columns[rgroup_label] = [ mols_or_smiles ]
        
            unmatched is a vector of indices in the input mols that were not matched.
        
    
        C++ signature :
            class boost::python::api::object RGroupDecompose(class boost::python::api::object,class boost::python::api::object [,bool=False [,bool=True [,struct RDKit::RGroupDecompositionParameters=<rdkit.Chem.rdRGroupDecomposition.RGroupDecompositionParameters object at 0x00000266D24FFDE0>]]])
    """
def RelabelMappedDummies(mol: Mol, inputLabels: int = ..., outputLabels: int = ...) -> None:
    """
        Relabel dummy atoms bearing an R-group mapping (as
        atom map number, isotope or MDLRGroup label) such that
        they will be displayed by the rendering code as R# rather
        than #*, *:#, #*:#, etc. By default, only the MDLRGroup label
        is retained on output; this may be configured through the
        outputLabels parameter.
        In case there are multiple potential R-group mappings,
        the priority on input is Atom map number > Isotope > MDLRGroup.
        The inputLabels parameter allows to configure which mappings
        are taken into consideration.
        
    
        C++ signature :
            void RelabelMappedDummies(class RDKit::ROMol {lvalue} [,unsigned int=rdkit.Chem.rdRGroupDecomposition.RGroupLabelling(7) [,unsigned int=rdkit.Chem.rdRGroupDecomposition.RGroupLabelling.MDLRGroup]])
    """
AtomIndexLabels: RGroupLabels
AtomMap: RGroupLabelling
AtomMapLabels: RGroupLabels
AutoDetect: RGroupLabels
DummyAtomLabels: RGroupLabels
Exhaustive: RGroupMatching
FingerprintVariance: RGroupScore
GA: RGroupMatching
Greedy: RGroupMatching
GreedyChunks: RGroupMatching
Isotope: RGroupLabelling
IsotopeLabels: RGroupLabels
MCS: RGroupCoreAlignment
MDLRGroup: RGroupLabelling
MDLRGroupLabels: RGroupLabels
Match: RGroupScore
NoAlignment: RGroupCoreAlignment
NoSymmetrization: RGroupMatching
None: RGroupCoreAlignment
RelabelDuplicateLabels: RGroupLabels
