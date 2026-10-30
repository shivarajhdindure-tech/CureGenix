import json
import unittest

from quantum.chemistry.readout_mitigation import run_readout_mitigation_validation


class ReadoutMitigationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_readout_mitigation_validation(shots=8192, seed=20261030)

    def test_seeded_aer_result_is_reproducible_and_json_safe(self):
        repeated = run_readout_mitigation_validation(shots=8192, seed=20261030)
        self.assertEqual(self.result, repeated)
        json.dumps(self.result, allow_nan=False)
        self.assertEqual(self.result["execution_type"], "local_noisy_simulation")
        self.assertEqual(self.result["measurement_setup"]["ideal_expectation_z"], -1.0)
        self.assertEqual(self.result["shots_per_scenario"], 8192)

    def test_matching_readout_calibration_improves_controlled_scenario(self):
        scenario = self.result["controlled_readout_noise"]
        errors = scenario["absolute_error_from_ideal"]
        self.assertLess(errors["readout_mitigated"], errors["raw"])
        self.assertGreater(scenario["raw_unmitigated"]["standard_error"], 0.0)
        self.assertGreater(
            scenario["readout_mitigated"]["standard_error_conditional_on_calibration"], 0.0,
        )

    def test_miscalibrated_readout_can_make_estimate_worse(self):
        scenario = self.result["calibration_mismatch_counterexample"]
        errors = scenario["absolute_error_from_ideal"]
        self.assertGreater(errors["readout_mitigated"], errors["raw"])

    def test_invalid_shots_and_seed_are_rejected(self):
        with self.assertRaises(ValueError):
            run_readout_mitigation_validation(shots=1)
        with self.assertRaises(ValueError):
            run_readout_mitigation_validation(seed=True)


if __name__ == "__main__":
    unittest.main()
