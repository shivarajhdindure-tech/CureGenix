from __future__ import annotations
import logging as logging
import sys as sys
from .rdBase import *
__all__: list[str] = ['VECT_WRAPS', 'VectIter', 'log_handler', 'logger', 'logging', 'name', 'object', 'rdBase', 'sys']
class VectIter:
    def __init__(self, vect):
        ...
    def __iter__(self):
        ...
    def __next__(self):
        ...
def __vect__iter__(vect):
    ...
VECT_WRAPS: set = {'UnsignedLong_Vect', 'VectorOfStringVectors', 'VectSizeT', 'MatchTypeVect'}
__version__: str = '2026.09.1'
log_handler: logging.StreamHandler
logger: logging.Logger
name: str = '__file__'
object: str = 'C:\\rdkit\\build\\temp.win-amd64-cpython-312\\Release\\rdkit_install\\Lib\\site-packages\\rdkit\\rdBase.pyd'
