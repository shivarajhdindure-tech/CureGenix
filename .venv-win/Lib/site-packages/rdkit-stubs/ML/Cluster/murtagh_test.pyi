from __future__ import annotations
import numpy as numpy
from rdkit.ML.Cluster import Murtagh
__all__: list[str] = ['Murtagh', 'clusters', 'd', 'dist', 'dists', 'i', 'j', 'numpy']
clusters: list
d: numpy.ndarray
dist: numpy.float64
dists: numpy.ndarray
i: int = 4
j: int = 3
