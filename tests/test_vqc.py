import unittest

import numpy as np

from quantum.algorithms.vqc import (
    create_vqc_classifier,
    fit_vqc,
    predict_vqc,
    restore_vqc_weights,
)


class VQCTests(unittest.TestCase):
    @staticmethod
    def fixture_data():
        rng = np.random.default_rng(9)
        negative = rng.uniform(0.0, 0.8, size=(8, 2))
        positive = rng.uniform(2.3, 3.14, size=(8, 2))
        return np.vstack([negative, positive]), np.array([0] * 8 + [1] * 8)

    def test_training_produces_predictions_and_probabilities(self):
        x, y = self.fixture_data()
        model = create_vqc_classifier(
            feature_dimension=2, reps=1, maxiter=8, shots=64, seed=5
        )
        outcome = fit_vqc(model, x, y)
        prediction = predict_vqc(model, x[:4])
        self.assertEqual(outcome["status"], "success")
        self.assertGreaterEqual(outcome["runtime_seconds"], 0)
        self.assertGreater(outcome["optimizer_evaluations"], 0)
        self.assertGreater(outcome["objective_evaluations"], 0)
        self.assertIsNotNone(outcome["final_training_loss"])
        self.assertEqual(len(prediction["predictions"]), 4)
        self.assertEqual(np.asarray(prediction["probabilities"]).shape, (4, 2))
        self.assertTrue(np.allclose(np.sum(prediction["probabilities"], axis=1), 1.0))

    def test_seed_reproduces_training_and_predictions(self):
        x, y = self.fixture_data()
        results = []
        for _ in range(2):
            model = create_vqc_classifier(
                feature_dimension=2, reps=1, maxiter=8, shots=64, seed=11
            )
            fit_vqc(model, x, y)
            results.append(predict_vqc(model, x)["predictions"])
        self.assertEqual(results[0], results[1])

    def test_saved_weights_restore_for_inference_without_refitting(self):
        x, y = self.fixture_data()
        trained = create_vqc_classifier(feature_dimension=2, reps=1, maxiter=8, shots=64, seed=13)
        fit_vqc(trained, x, y)
        expected = predict_vqc(trained, x[:3])
        restored = restore_vqc_weights(
            create_vqc_classifier(feature_dimension=2, reps=1, maxiter=8, shots=64, seed=13),
            trained.weights.copy(),
        )
        actual = predict_vqc(restored, x[:3])
        self.assertEqual(actual["predictions"], expected["predictions"])
        self.assertTrue(np.allclose(actual["probabilities"], expected["probabilities"]))

    def test_invalid_model_parameters_are_rejected(self):
        for kwargs in (
            {"feature_dimension": 1},
            {"reps": 0},
            {"maxiter": 0},
            {"shots": 0},
            {"seed": -1},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                create_vqc_classifier(**kwargs)

    def test_invalid_training_data_are_rejected(self):
        model = create_vqc_classifier(feature_dimension=2, maxiter=8, shots=64)
        with self.assertRaisesRegex(ValueError, "finite 2D"):
            fit_vqc(model, [[float("nan"), 0.0]], [0])
        with self.assertRaisesRegex(ValueError, "columns"):
            fit_vqc(model, np.zeros((4, 3)), [0, 0, 1, 1])
        with self.assertRaisesRegex(ValueError, "exactly two classes"):
            fit_vqc(model, np.zeros((4, 2)), [0, 0, 0, 0])

    def test_prediction_rejects_wrong_feature_shape(self):
        x, y = self.fixture_data()
        model = create_vqc_classifier(feature_dimension=2, maxiter=8, shots=64)
        fit_vqc(model, x, y)
        with self.assertRaisesRegex(ValueError, "columns"):
            predict_vqc(model, np.zeros((2, 3)))


if __name__ == "__main__":
    unittest.main()
