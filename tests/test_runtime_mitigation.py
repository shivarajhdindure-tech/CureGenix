import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from dataclasses import dataclass
from unittest.mock import patch

from quantum.chemistry.runtime_mitigation import (
    build_estimator_runtime_options,
    execute_estimator_with_provenance,
    instantiate_estimator_options,
    runtime_defaulted_options,
    serialize_runtime_options,
)


class FakePrimitiveResult(list):
    metadata = {
        "resilience": {"measure_mitigation": True, "zne_mitigation": False, "pec_mitigation": False},
        "twirling": {"enable_gates": False, "enable_measure": True, "num_randomizations": 8},
        "dynamical_decoupling": {"enable": False},
    }


class FakeJob:
    def __init__(self):
        self.identifier = "mock-job-id"

    def job_id(self):
        return self.identifier

    def result(self):
        pub = SimpleNamespace(
            data=SimpleNamespace(evs=-1.0, stds=0.01),
            metadata={"shots": 2048, "target_precision": 0.03, "num_randomizations": 8},
        )
        return FakePrimitiveResult([pub])


class FakeEstimator:
    instances = []

    def __init__(self, mode, **kwargs):
        self.mode = mode
        self.options = kwargs.get("options")
        self.kwargs = kwargs
        self.instances.append(self)

    def run(self, pubs, precision):
        self.pubs = pubs
        self.precision = precision
        return FakeJob()


class RuntimeMitigationTests(unittest.TestCase):
    def setUp(self):
        FakeEstimator.instances.clear()

    def test_explicit_raw_options_disable_mitigation_and_suppression(self):
        options = build_estimator_runtime_options({"profile": "raw"})
        self.assertEqual(options["resilience_level"], 0)
        self.assertEqual(options["resilience"], {
            "measure_mitigation": False,
            "zne_mitigation": False,
            "pec_mitigation": False,
        })
        self.assertEqual(options["twirling"], {"enable_gates": False, "enable_measure": False})
        self.assertEqual(options["dynamical_decoupling"], {"enable": False})

    def test_readout_profile_is_conservative_and_zne_pec_are_opt_in(self):
        options = build_estimator_runtime_options({"profile": "readout_mitigated"})
        self.assertTrue(options["resilience"]["measure_mitigation"])
        self.assertFalse(options["resilience"]["zne_mitigation"])
        self.assertFalse(options["resilience"]["pec_mitigation"])
        self.assertFalse(options["twirling"]["enable_gates"])
        self.assertTrue(options["twirling"]["enable_measure"])
        self.assertFalse(options["dynamical_decoupling"]["enable"])
        self.assertNotIn("num_randomizations", options["twirling"])
        self.assertNotIn("shots_per_randomization", options["twirling"])
        self.assertNotIn("measure_noise_learning", options["resilience"])
        defaults = runtime_defaulted_options({"profile": "readout_mitigated"}, options)
        self.assertEqual(defaults["twirling.num_randomizations"], "runtime_default")
        self.assertEqual(defaults["twirling.shots_per_randomization"], "runtime_default")
        self.assertEqual(defaults["resilience.measure_noise_learning.num_randomizations"], "runtime_default")

    def test_custom_controls_and_randomization_budgets_are_explicit(self):
        options = build_estimator_runtime_options({
            "profile": "custom",
            "gate_twirling": True,
            "measurement_twirling": True,
            "dynamical_decoupling": True,
            "zne_mitigation": True,
            "num_randomizations": 16,
            "shots_per_randomization": 128,
        })
        self.assertTrue(options["resilience"]["zne_mitigation"])
        self.assertFalse(options["resilience"]["pec_mitigation"])
        self.assertTrue(options["twirling"]["enable_gates"])
        self.assertEqual(options["twirling"]["num_randomizations"], 16)
        self.assertEqual(options["twirling"]["shots_per_randomization"], 128)
        self.assertTrue(options["dynamical_decoupling"]["enable"])

    def test_invalid_combinations_and_unpinned_default_are_rejected_or_preserved(self):
        self.assertIsNone(build_estimator_runtime_options({"profile": "runtime_default"}))
        with self.assertRaisesRegex(ValueError, "runtime_default"):
            build_estimator_runtime_options({"profile": "runtime_default", "gate_twirling": False})
        with self.assertRaisesRegex(ValueError, "measurement twirling"):
            build_estimator_runtime_options({"profile": "readout_mitigated", "measurement_twirling": False})
        with self.assertRaisesRegex(ValueError, "PEC requires"):
            build_estimator_runtime_options({"profile": "custom", "pec_mitigation": True})
        with self.assertRaisesRegex(ValueError, "Twirling budgets"):
            build_estimator_runtime_options({"profile": "custom", "num_randomizations": 8})
        with self.assertRaisesRegex(ValueError, "positive integer"):
            build_estimator_runtime_options({"profile": "custom", "gate_twirling": True, "num_randomizations": 0})
        with self.assertRaisesRegex(ValueError, "omit it for the Runtime default"):
            build_estimator_runtime_options({"profile": "readout_mitigated", "num_randomizations": "auto"})
        with self.assertRaisesRegex(ValueError, "omit it for the Runtime default"):
            build_estimator_runtime_options({"profile": "readout_mitigated", "measure_noise_learning_randomizations": "auto"})

    def test_nested_options_are_materialized_as_typed_objects(self):
        @dataclass
        class FakeMeasureNoiseLearningOptions:
            num_randomizations: int | None = None

        @dataclass
        class FakeResilienceOptions:
            measure_mitigation: bool | None = None
            zne_mitigation: bool | None = None
            pec_mitigation: bool | None = None
            measure_noise_learning: FakeMeasureNoiseLearningOptions | None = None

        @dataclass
        class FakeDynamicalDecouplingOptions:
            enable: bool = False

        @dataclass
        class FakeTwirlingOptions:
            enable_gates: bool | None = None
            enable_measure: bool | None = None
            num_randomizations: int | None = None
            shots_per_randomization: int | None = None

        @dataclass
        class FakeEstimatorOptions:
            resilience_level: int = 1
            resilience: FakeResilienceOptions | None = None
            dynamical_decoupling: FakeDynamicalDecouplingOptions | None = None
            twirling: FakeTwirlingOptions | None = None

        options = build_estimator_runtime_options({"profile": "readout_mitigated"})
        typed = instantiate_estimator_options(options, FakeEstimatorOptions)
        self.assertIsInstance(typed, FakeEstimatorOptions)
        self.assertIsInstance(typed.resilience, FakeResilienceOptions)
        self.assertIsInstance(typed.dynamical_decoupling, FakeDynamicalDecouplingOptions)
        self.assertIsInstance(typed.twirling, FakeTwirlingOptions)
        self.assertTrue(typed.resilience.measure_mitigation)
        self.assertIsNone(typed.resilience.measure_noise_learning)

    def test_real_runtime_estimator_options_accept_profiles_when_installed(self):
        try:
            import importlib
            from quantum.chemistry.runtime_mitigation import _load_estimator_options_class
            options_class = _load_estimator_options_class()
        except ImportError:
            options_class = None
        if options_class is None:
            self.skipTest("qiskit-ibm-runtime EstimatorOptions is not installed in this environment")
        for config in (
            {"profile": "raw"},
            {"profile": "readout_mitigated"},
            {"profile": "custom", "gate_twirling": True, "measurement_twirling": True,
             "dynamical_decoupling": True, "zne_mitigation": True},
            {"profile": "custom", "gate_twirling": True, "measurement_twirling": True,
             "pec_mitigation": True},
        ):
            with self.subTest(config=config):
                payload = build_estimator_runtime_options(config)
                runtime_options = instantiate_estimator_options(payload, options_class)
                self.assertIsInstance(runtime_options, options_class)

    def test_provenance_serialization_redacts_secrets_and_handles_missing_metadata(self):
        self.assertEqual(serialize_runtime_options({"public": True, "api_token": "must-not-serialize"}), {"public": True})
        backend = SimpleNamespace(name="fake-backend")

        class SparseResult(list):
            pass

        class SparseJob(FakeJob):
            def result(self):
                return SparseResult([SimpleNamespace(data=SimpleNamespace(evs=0.0, stds=0.1))])

        class SparseEstimator:
            def __init__(self, mode):
                self.mode = mode

            def run(self, _pubs, precision):
                return SparseJob()

        with patch("quantum.chemistry.runtime_mitigation.importlib.metadata.version", return_value="0.51.0"):
            output = execute_estimator_with_provenance(
                SparseEstimator, backend, [("circuit", "observable")], 0.03,
                {"profile": "runtime_default"},
            )
        provenance = output["provenance"]
        self.assertEqual(provenance["runtime_package_version"], "0.51.0")
        self.assertEqual(provenance["configuration_provenance"], "runtime_default_unpinned")
        self.assertEqual(provenance["metadata_status"], "runtime_metadata_unavailable")
        self.assertIsNone(provenance["actual_shots"])
        json.dumps(provenance, allow_nan=False)

    def test_omitted_randomization_values_are_recorded_as_runtime_defaults(self):
        output = execute_estimator_with_provenance(
            FakeEstimator,
            SimpleNamespace(name="mock-readout-backend"),
            [("circuit", "observable")],
            0.03,
            {"profile": "readout_mitigated"},
        )
        provenance = output["provenance"]
        self.assertEqual(
            provenance["runtime_defaulted_options"]["twirling.num_randomizations"],
            "runtime_default",
        )
        self.assertEqual(
            provenance["runtime_defaulted_options"]["twirling.shots_per_randomization"],
            "runtime_default",
        )
        self.assertEqual(
            provenance["runtime_defaulted_options"]["resilience.measure_noise_learning.num_randomizations"],
            "runtime_default",
        )
        self.assertNotIn("auto", json.dumps(provenance["options_requested"]))

    def test_runtime_failure_retains_safe_submission_provenance(self):
        from quantum.chemistry.runtime_mitigation import RuntimeEstimatorExecutionError

        backend = SimpleNamespace(name="mock-failing-backend")

        class FailingJob(FakeJob):
            def result(self):
                raise TimeoutError("private service text should not be copied")

        class FailingEstimator(FakeEstimator):
            def run(self, _pubs, precision):
                return FailingJob()

        with patch("quantum.chemistry.runtime_mitigation.importlib.metadata.version", return_value="0.51.0"):
            with self.assertRaises(RuntimeEstimatorExecutionError) as caught:
                execute_estimator_with_provenance(
                    FailingEstimator,
                    backend,
                    [("circuit", "observable")],
                    0.03,
                    {"profile": "raw"},
                )
        provenance = caught.exception.provenance
        self.assertEqual(provenance["job_id"], "mock-job-id")
        self.assertEqual(provenance["execution_status"], "failed")
        self.assertEqual(provenance["mitigation_method"], "explicit raw execution")
        self.assertNotIn("private service text", json.dumps(provenance))

    def test_h2_estimator_integration_uses_shared_builder_without_side_effects(self):
        from experiments.ibm_results.h2_ibm_fixed_vqe_energy import run_h2_estimator

        backend = SimpleNamespace(name="mock-h2-backend")
        with patch("quantum.chemistry.runtime_mitigation.importlib.metadata.version", return_value="0.51.0"):
            output = run_h2_estimator(
                FakeEstimator, backend, "mock-circuit", "mock-observable", 0.03,
                {"profile": "raw"},
            )
        instance = FakeEstimator.instances[-1]
        effective_options = serialize_runtime_options(instance.kwargs["options"])
        self.assertEqual(effective_options["resilience"]["measure_mitigation"], False)
        self.assertEqual(output["provenance"]["backend"], "mock-h2-backend")
        self.assertEqual(output["provenance"]["job_id"], "mock-job-id")
        self.assertEqual(output["provenance"]["actual_shots"], 2048)
        self.assertEqual(output["provenance"]["twirling_randomizations"], 8)
        self.assertEqual(output["provenance"]["runtime_package_version"], "0.51.0")
        self.assertEqual(len(output["provenance"]["circuit_sha256"]), 64)

    def test_historical_h2_record_is_still_the_original_saved_schema(self):
        path = Path(__file__).resolve().parents[1] / "experiments" / "ibm_results" / "h2_ibm_fixed_vqe_energy.json"
        payload = path.read_bytes()
        record = json.loads(payload)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), "af9a1a8aa8781e374c96719787edc50c7de02d38c9ef2142a910a37b9ffa9ff7")
        self.assertEqual(record["job_id"], "dbho8401h92s73825deg")
        self.assertEqual(record["status"], "completed")


if __name__ == "__main__":
    unittest.main()
