import unittest

import numpy as np
from rdkit import Chem

from quantum.algorithms.qgnn import (
    MolecularQGNN,
    graph_message_passing,
    make_qgnn_circuit,
    molecular_graph_from_mol,
)


class MolecularQGNNTests(unittest.TestCase):
    def test_graph_uses_atom_and_bond_features_and_message_passing(self):
        mol = Chem.MolFromSmiles("CCO")
        graph = molecular_graph_from_mol(mol)
        self.assertEqual(graph.node_features.shape, (3, 12))
        self.assertEqual(len(graph.edges), 2)
        self.assertEqual(graph.edges[0][2].shape, (5,))
        representation = graph_message_passing(graph)
        self.assertEqual(representation.shape, (53,))
        self.assertFalse(np.allclose(representation, graph_message_passing(molecular_graph_from_mol(Chem.MolFromSmiles("CCN")))))

    def test_parameterized_entangling_circuit_participates_in_graph_output(self):
        circuit, feature_params, weight_params = make_qgnn_circuit()
        self.assertEqual(circuit.num_qubits, 4)
        self.assertEqual(len(feature_params), 4)
        self.assertEqual(len(weight_params), 8)
        self.assertGreater(sum(1 for instruction in circuit.data if instruction.operation.name == "cx"), 0)
        model = MolecularQGNN(maxiter=3)
        with self.assertRaisesRegex(RuntimeError, "not been fitted"):
            model.predict_proba(np.zeros((1, 4)))
        model.weights = np.zeros(8)
        p0 = model.predict_proba(np.zeros((1, 4)))
        p1 = model.predict_proba(np.full((1, 4), 1.7))
        self.assertEqual(p0.shape, (1, 2))
        self.assertFalse(np.allclose(p0, p1))

    def test_training_prediction_and_seed_reproducibility(self):
        x = np.asarray([[0.1, 0.2, 0.3, 0.4], [0.3, 0.1, 0.2, 0.1], [2.5, 2.4, 2.8, 2.7], [2.8, 2.7, 2.4, 2.9],
                        [0.2, 0.4, 0.1, 0.2], [2.7, 2.5, 2.3, 2.6], [0.4, 0.1, 0.3, 0.2], [2.3, 2.9, 2.7, 2.5]])
        y = np.asarray([0, 0, 1, 1, 0, 1, 0, 1])
        outputs = []
        for _ in range(2):
            model = MolecularQGNN(maxiter=12, seed=17)
            diagnostic = model.fit(x, y)
            probabilities = model.predict_proba(x)
            self.assertIn(diagnostic["status"], {"converged", "completed_max_evaluations"})
            self.assertGreater(diagnostic["objective_evaluations"], 0)
            self.assertEqual(model.predict(x).shape, (len(y),))
            self.assertTrue(np.allclose(probabilities.sum(axis=1), 1.0))
            outputs.append(probabilities)
        self.assertTrue(np.allclose(outputs[0], outputs[1]))

    def test_invalid_graph_and_training_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            molecular_graph_from_mol(None)
        with self.assertRaises(ValueError):
            MolecularQGNN(maxiter=0)
        model = MolecularQGNN(maxiter=2)
        with self.assertRaisesRegex(ValueError, "four graph features"):
            model.fit(np.zeros((3, 5)), [0, 1, 0])
        with self.assertRaisesRegex(ValueError, "both classes"):
            model.fit(np.zeros((3, 4)), [1, 1, 1])


if __name__ == "__main__":
    unittest.main()
