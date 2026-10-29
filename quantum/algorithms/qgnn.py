"""Minimal hybrid molecular QGNN built from RDKit graphs and a PQC readout.

One chemically weighted message-passing round creates each graph-level vector.
Training-only SVD/scaling maps vectors to four rotation angles. A trainable,
four-qubit parameterized circuit consumes those angles and its measured first
qubit probability is the graph classifier output. Statevector simulation is
local classical computation, not hardware execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Statevector
from rdkit import Chem
from scipy.optimize import minimize


@dataclass(frozen=True)
class MolecularGraph:
    node_features: np.ndarray
    edges: tuple[tuple[int, int, np.ndarray], ...]


def molecular_graph_from_mol(molecule: Chem.Mol) -> MolecularGraph:
    """Create atom/bond feature arrays from an already validated RDKit molecule."""
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise ValueError("A non-empty valid RDKit molecule is required")
    nodes = []
    for atom in molecule.GetAtoms():
        hybrid = atom.GetHybridization()
        nodes.append([
            atom.GetAtomicNum() / 54.0,
            atom.GetDegree() / 4.0,
            float(np.clip(atom.GetFormalCharge(), -2, 2)) / 2.0,
            float(atom.GetIsAromatic()),
            float(atom.IsInRing()),
            atom.GetTotalNumHs(includeNeighbors=True) / 4.0,
            float(hybrid == Chem.HybridizationType.SP),
            float(hybrid == Chem.HybridizationType.SP2),
            float(hybrid == Chem.HybridizationType.SP3),
            float(hybrid not in (Chem.HybridizationType.SP, Chem.HybridizationType.SP2, Chem.HybridizationType.SP3)),
            float(atom.HasProp("_CIPCode")),
            min(atom.GetTotalValence(), 8) / 8.0,
        ])
    edges = []
    for bond in molecule.GetBonds():
        edges.append((
            bond.GetBeginAtomIdx(),
            bond.GetEndAtomIdx(),
            np.asarray([
                float(bond.GetBondTypeAsDouble()) / 3.0,
                float(bond.GetIsAromatic()),
                float(bond.GetIsConjugated()),
                float(bond.IsInRing()),
                float(bond.GetStereo()) / 6.0,
            ], dtype=np.float64),
        ))
    return MolecularGraph(np.asarray(nodes, dtype=np.float64), tuple(edges))


def graph_message_passing(graph: MolecularGraph) -> np.ndarray:
    """Run one bond-weighted neighbor aggregation and mean/max graph readout."""
    x = np.asarray(graph.node_features, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] == 0 or not np.isfinite(x).all():
        raise ValueError("Graph node features must be a finite non-empty matrix")
    messages = np.zeros_like(x)
    degree = np.zeros(x.shape[0], dtype=np.float64)
    edge_features = []
    for left, right, edge in graph.edges:
        if not (0 <= left < len(x) and 0 <= right < len(x)):
            raise ValueError("Graph edge endpoint is outside the node matrix")
        weight = 1.0 + float(edge[0])
        messages[left] += weight * x[right]
        messages[right] += weight * x[left]
        degree[left] += weight
        degree[right] += weight
        edge_features.append(edge)
    nonzero = degree > 0
    messages[nonzero] /= degree[nonzero, None]
    updated = np.tanh(np.concatenate([x, messages], axis=1))
    pooled = np.concatenate([updated.mean(axis=0), updated.max(axis=0)])
    edge_mean = np.mean(edge_features, axis=0) if edge_features else np.zeros(5)
    return np.concatenate([pooled, edge_mean])


def make_qgnn_circuit(feature_dimension: int = 4, reps: int = 1):
    """Parameterized graph-angle encoder and trainable entangling readout."""
    if feature_dimension != 4 or reps < 1:
        raise ValueError("This minimal QGNN requires four features and reps >= 1")
    features = ParameterVector("graph", feature_dimension)
    weights = ParameterVector("qgnn_theta", feature_dimension * 2 * reps)
    circuit = QuantumCircuit(feature_dimension)
    for qubit in range(feature_dimension):
        circuit.ry(features[qubit], qubit)
    cursor = 0
    for _ in range(reps):
        for qubit in range(feature_dimension - 1):
            circuit.cx(qubit, qubit + 1)
        for qubit in range(feature_dimension):
            circuit.ry(weights[cursor], qubit)
            cursor += 1
        for qubit in range(feature_dimension):
            circuit.rz(weights[cursor], qubit)
            cursor += 1
        for qubit in range(feature_dimension - 1, 0, -1):
            circuit.cx(qubit, qubit - 1)
    return circuit, tuple(features), tuple(weights)


class MolecularQGNN:
    """Trainable PQC graph classifier using cross entropy and COBYLA."""

    def __init__(self, reps: int = 1, maxiter: int = 20, seed: int = 42):
        if not isinstance(maxiter, int) or maxiter < 1:
            raise ValueError("maxiter must be a positive integer")
        if not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        self.reps = reps
        self.maxiter = maxiter
        self.seed = seed
        self.circuit, self.feature_parameters, self.weight_parameters = make_qgnn_circuit(reps=reps)
        self.weights: np.ndarray | None = None
        self.diagnostics: dict = {}

    def predict_proba(self, graph_angles) -> np.ndarray:
        x = np.asarray(graph_angles, dtype=np.float64)
        if x.ndim != 2 or x.shape[1] != 4 or not np.isfinite(x).all():
            raise ValueError("QGNN inputs must be a finite matrix with four graph features")
        if self.weights is None:
            raise RuntimeError("QGNN has not been fitted")
        output = np.empty(len(x), dtype=np.float64)
        for row_index, row in enumerate(x):
            binding = dict(zip(self.feature_parameters, row))
            binding.update(zip(self.weight_parameters, self.weights))
            state = Statevector.from_instruction(self.circuit.assign_parameters(binding))
            output[row_index] = state.probabilities(qargs=[0])[1]
        return np.column_stack([1.0 - output, output])

    def fit(self, graph_angles, labels) -> dict:
        x = np.asarray(graph_angles, dtype=np.float64)
        y = np.asarray(labels, dtype=np.int64)
        if x.ndim != 2 or x.shape[1] != 4 or not np.isfinite(x).all():
            raise ValueError("QGNN training inputs must be a finite matrix with four graph features")
        if y.ndim != 1 or len(y) != len(x) or set(np.unique(y).tolist()) != {0, 1}:
            raise ValueError("QGNN requires aligned binary labels containing both classes")
        initial = np.random.default_rng(self.seed).uniform(-np.pi, np.pi, len(self.weight_parameters))
        evaluations = 0

        def objective(parameters):
            nonlocal evaluations
            evaluations += 1
            self.weights = np.asarray(parameters, dtype=np.float64)
            p = np.clip(self.predict_proba(x)[:, 1], 1e-7, 1 - 1e-7)
            return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

        started = time.perf_counter()
        result = minimize(
            objective,
            initial,
            method="COBYLA",
            options={"maxiter": self.maxiter, "rhobeg": 0.5, "tol": 1e-3},
        )
        elapsed = time.perf_counter() - started
        self.weights = np.asarray(result.x, dtype=np.float64)
        self.diagnostics = {
            "status": (
                "converged" if result.success and np.isfinite(result.fun)
                else "completed_max_evaluations" if np.isfinite(result.fun)
                else "failed"
            ),
            "runtime_seconds": round(elapsed, 6),
            "training_samples": int(len(y)),
            "objective": float(result.fun),
            "objective_evaluations": int(evaluations),
            "optimizer_success": bool(result.success),
            "optimizer_message": str(result.message),
        }
        return dict(self.diagnostics)

    def predict(self, graph_angles) -> np.ndarray:
        return (self.predict_proba(graph_angles)[:, 1] >= 0.5).astype(np.int64)
