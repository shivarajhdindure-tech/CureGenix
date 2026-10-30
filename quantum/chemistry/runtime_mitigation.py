"""Explicit Qiskit Runtime Estimator settings and safe provenance helpers.

The default ``runtime_default`` profile deliberately passes no ``options`` to
EstimatorV2 so existing workflows retain their prior Runtime-default behavior.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib
import inspect
import json
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints


_PROFILES = {"runtime_default", "raw", "readout_mitigated", "custom"}
_BOOL_FIELDS = (
    "gate_twirling", "measurement_twirling", "dynamical_decoupling",
    "readout_mitigation", "zne_mitigation", "pec_mitigation",
)


class RuntimeEstimatorExecutionError(RuntimeError):
    """Safe failure carrying any submission metadata that was collected."""

    def __init__(self, error_type: str, provenance: dict[str, Any]):
        super().__init__(f"IBM Runtime Estimator execution failed ({error_type}).")
        self.error_type = error_type
        self.provenance = provenance


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def build_estimator_runtime_options(config: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Build exact EstimatorV2 options; ``None`` preserves legacy Runtime defaults.

    Supported profiles are runtime_default, raw, readout_mitigated, and custom.
    The nested field names are the qiskit-ibm-runtime 0.51.0 public options.
    """
    config = dict(config or {})
    profile = config.pop("profile", "runtime_default")
    if profile not in _PROFILES:
        raise ValueError(f"Unsupported Runtime mitigation profile: {profile!r}.")

    allowed = set(_BOOL_FIELDS) | {
        "num_randomizations", "shots_per_randomization", "measure_noise_learning_randomizations",
    }
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"Unsupported Runtime mitigation option(s): {', '.join(sorted(unknown))}.")
    for key in _BOOL_FIELDS:
        if key in config and not _is_bool(config[key]):
            raise ValueError(f"{key} must be a boolean.")

    if profile == "runtime_default":
        if config:
            raise ValueError("runtime_default cannot be combined with explicit mitigation settings; select raw or custom.")
        return None

    if profile == "raw":
        if any(config.get(key) not in (None, False) for key in _BOOL_FIELDS):
            raise ValueError("raw profile explicitly disables all mitigation and suppression options.")
        if any(config.get(key) is not None for key in (
            "num_randomizations", "shots_per_randomization", "measure_noise_learning_randomizations",
        )):
            raise ValueError("raw profile cannot set twirling budgets while twirling is disabled.")
        readout = gate_twirl = measure_twirl = dd = zne = pec = False
    elif profile == "readout_mitigated":
        if config.get("readout_mitigation") is False:
            raise ValueError("readout_mitigated profile cannot disable readout mitigation.")
        readout = True
        gate_twirl = config.get("gate_twirling", False)
        measure_twirl = config.get("measurement_twirling", True)
        dd = config.get("dynamical_decoupling", False)
        zne = config.get("zne_mitigation", False)
        pec = config.get("pec_mitigation", False)
        if measure_twirl is False:
            raise ValueError("Readout mitigation requires measurement twirling in Runtime 0.51.0.")
        measure_twirl = True
    else:
        readout = config.get("readout_mitigation", False)
        gate_twirl = config.get("gate_twirling", False)
        measure_twirl = config.get("measurement_twirling", False)
        dd = config.get("dynamical_decoupling", False)
        zne = config.get("zne_mitigation", False)
        pec = config.get("pec_mitigation", False)
        if readout and not measure_twirl:
            raise ValueError("Readout mitigation requires measurement_twirling=true.")

    if pec and not (gate_twirl and measure_twirl):
        raise ValueError("PEC requires gate and measurement twirling to be explicitly enabled.")

    options: dict[str, Any] = {
        "resilience_level": 0,
        "resilience": {
            "measure_mitigation": readout,
            "zne_mitigation": zne,
            "pec_mitigation": pec,
        },
        "dynamical_decoupling": {"enable": dd},
        "twirling": {
            "enable_gates": gate_twirl,
            "enable_measure": measure_twirl,
        },
    }

    num_randomizations = config.get("num_randomizations")
    shots_per_randomization = config.get("shots_per_randomization")
    if num_randomizations is not None and (
        not isinstance(num_randomizations, int) or isinstance(num_randomizations, bool) or num_randomizations < 1
    ):
        raise ValueError("num_randomizations must be a positive integer; omit it for the Runtime default.")
    if shots_per_randomization is not None and (
        not isinstance(shots_per_randomization, int)
        or isinstance(shots_per_randomization, bool)
        or shots_per_randomization < 1
    ):
        raise ValueError("shots_per_randomization must be a positive integer; omit it for the Runtime default.")
    if gate_twirl or measure_twirl:
        if num_randomizations is not None:
            options["twirling"]["num_randomizations"] = num_randomizations
        if shots_per_randomization is not None:
            options["twirling"]["shots_per_randomization"] = shots_per_randomization
    elif num_randomizations is not None or shots_per_randomization is not None:
        raise ValueError("Twirling budgets require gate or measurement twirling to be enabled.")
    if readout:
        learning_randomizations = config.get("measure_noise_learning_randomizations", num_randomizations)
        if learning_randomizations is not None and (
            not isinstance(learning_randomizations, int)
            or isinstance(learning_randomizations, bool)
            or learning_randomizations < 1
        ):
            raise ValueError("measure_noise_learning_randomizations must be a positive integer; omit it for the Runtime default.")
        if learning_randomizations is not None:
            options["resilience"]["measure_noise_learning"] = {
                "num_randomizations": learning_randomizations,
            }
    elif config.get("measure_noise_learning_randomizations") is not None:
        raise ValueError("Measurement noise learning settings require readout mitigation.")
    return options


def _load_estimator_options_class() -> type | None:
    """Find the EstimatorOptions class paired with the installed Runtime API."""
    for module_name in (
        "qiskit_ibm_runtime.options",
        "qiskit_ibm_runtime.options_models",
        "qiskit_ibm_runtime",
    ):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        candidate = getattr(module, "EstimatorOptions", None)
        if isinstance(candidate, type):
            return candidate
    return None


def _model_fields(model_class: type) -> dict[str, Any]:
    fields = getattr(model_class, "model_fields", None)
    if isinstance(fields, Mapping):
        return {name: getattr(field, "annotation", Any) for name, field in fields.items()}
    try:
        return get_type_hints(model_class)
    except (NameError, TypeError):
        return {
            name: parameter.annotation
            for name, parameter in inspect.signature(model_class).parameters.items()
            if parameter.annotation is not inspect.Parameter.empty
        }


def _typed_nested_options(annotation: Any, value: Any) -> Any:
    if not isinstance(value, Mapping):
        return value
    candidates = get_args(annotation) if get_origin(annotation) is not None else (annotation,)
    for candidate in candidates:
        if not isinstance(candidate, type) or candidate is dict:
            continue
        fields = _model_fields(candidate)
        if not fields and not is_dataclass(candidate):
            continue
        nested = {}
        for key, item in value.items():
            nested[key] = _typed_nested_options(fields.get(key, Any), item)
        return candidate(**nested)
    raise TypeError(
        "Installed Runtime option type does not expose a typed nested model for "
        f"{sorted(value)}; refusing to pass an unvalidated dictionary."
    )


def instantiate_estimator_options(
    options: Mapping[str, Any] | None,
    estimator_options_class: type | None = None,
) -> Any:
    """Construct real Runtime option objects, including typed nested models.

    If Runtime is absent (for example, the Windows API process), return the
    serializable mapping so the WSL worker can materialize it in its own env.
    """
    if options is None:
        return None
    option_class = estimator_options_class or _load_estimator_options_class()
    if option_class is None:
        return dict(options)
    annotations = _model_fields(option_class)
    converted = {
        name: _typed_nested_options(annotations.get(name, Any), value)
        for name, value in options.items()
    }
    return option_class(**converted)


def runtime_defaulted_options(config: Mapping[str, Any] | None, options: Mapping[str, Any] | None) -> dict[str, str]:
    """Describe omitted settings without passing sentinel strings to Runtime."""
    config = dict(config or {})
    profile = config.get("profile", "runtime_default")
    if profile == "runtime_default":
        return {"primitive_options": "runtime_default"}
    options = options or {}
    defaults: dict[str, str] = {}
    twirling = options.get("twirling", {})
    if twirling.get("enable_gates") or twirling.get("enable_measure"):
        if "num_randomizations" not in twirling:
            defaults["twirling.num_randomizations"] = "runtime_default"
        if "shots_per_randomization" not in twirling:
            defaults["twirling.shots_per_randomization"] = "runtime_default"
    resilience = options.get("resilience", {})
    if resilience.get("measure_mitigation"):
        if "measure_noise_learning" not in resilience:
            defaults["resilience.measure_noise_learning"] = "runtime_default"
            defaults["resilience.measure_noise_learning.num_randomizations"] = "runtime_default"
    return defaults


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
            if not any(secret in str(key).casefold() for secret in ("token", "secret", "password", "credential"))
        }
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump(mode="python", exclude_unset=False))
    if hasattr(value, "asdict"):
        try:
            return _json_safe(value.asdict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    rendered = str(value)
    return "Unset" if "unset" in rendered.casefold() else rendered


def serialize_runtime_options(options: Any) -> Any:
    """Serialize Runtime option objects/dicts without leaking credentials."""
    if options is None:
        return None
    return _json_safe(options)


def _digest_circuit(circuit: Any) -> str | None:
    if circuit is None:
        return None
    try:
        from io import BytesIO
        from qiskit import qpy

        stream = BytesIO()
        qpy.dump(circuit, stream)
        payload = stream.getvalue()
    except Exception:
        payload = repr(circuit).encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()


def _digest_observable(observable: Any) -> str | None:
    if observable is None:
        return None
    try:
        terms = [
            [str(label), float(complex(coeff).real), float(complex(coeff).imag)]
            for label, coeff in observable.to_list()
        ]
        payload = json.dumps(terms, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except Exception:
        payload = repr(observable).encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump(mode="python", exclude_unset=False)
            return dict(dumped) if isinstance(dumped, Mapping) else {}
        except Exception:
            return {}
    if hasattr(value, "items"):
        try:
            return dict(value.items())
        except Exception:
            return {}
    return {}


def _package_version() -> str | None:
    try:
        return importlib.metadata.version("qiskit-ibm-runtime")
    except importlib.metadata.PackageNotFoundError:
        return None


def _mitigation_method(profile: str, options: dict[str, Any] | None) -> str:
    if profile == "runtime_default":
        return "runtime_default_unpinned"
    options = options or {}
    resilience = options.get("resilience", {})
    twirling = options.get("twirling", {})
    dynamical_decoupling = options.get("dynamical_decoupling", {})
    method_parts = []
    if resilience.get("measure_mitigation"):
        method_parts.append("TREX/readout mitigation")
    if resilience.get("zne_mitigation"):
        method_parts.append("ZNE")
    if resilience.get("pec_mitigation"):
        method_parts.append("PEC")
    if twirling.get("enable_gates"):
        method_parts.append("gate twirling")
    if twirling.get("enable_measure") and "TREX/readout mitigation" not in method_parts:
        method_parts.append("measurement twirling")
    if dynamical_decoupling.get("enable"):
        method_parts.append("dynamical decoupling")
    return "+".join(method_parts) if method_parts else "explicit raw execution"


def execute_estimator_with_provenance(
    estimator_class: Any,
    backend: Any,
    pubs: list[Any],
    precision: float,
    mitigation_config: Mapping[str, Any] | None = None,
    *,
    circuit: Any = None,
    observable: Any = None,
    on_submitted: Any = None,
) -> dict[str, Any]:
    """Run an Estimator with explicit options when requested and collect metadata."""
    config = dict(mitigation_config or {})
    profile = config.get("profile", "runtime_default")
    options = build_estimator_runtime_options(config)
    if options is None:
        estimator = estimator_class(mode=backend)
        options_source = "runtime_default_unpinned"
    else:
        runtime_options = instantiate_estimator_options(options)
        estimator = estimator_class(mode=backend, options=runtime_options)
        options_source = "explicitly_configured"

    options_effective = serialize_runtime_options(getattr(estimator, "options", None))
    backend_name = getattr(backend, "name", None)
    if callable(backend_name):
        backend_name = backend_name()

    runtime_version = _package_version()
    method = _mitigation_method(profile, options)
    submitted_at = datetime.now(timezone.utc).isoformat()
    base_provenance = {
        "schema_version": 1,
        "configuration_provenance": options_source,
        "profile": profile,
        "mitigation_method": method,
        "runtime_package_version": runtime_version,
        "backend": str(backend_name) if backend_name is not None else None,
        "submitted_at_utc": submitted_at,
        "precision_requested": float(precision),
        "options_requested": options,
        "runtime_defaulted_options": runtime_defaulted_options(config, options),
        "options_effective": options_effective,
        "effective_options_status": "captured" if options_effective is not None else "unavailable",
        "circuit_sha256": _digest_circuit(circuit),
        "observable_sha256": _digest_observable(observable),
    }
    job = None
    job_id = None
    try:
        job = estimator.run(pubs, precision=float(precision))
        job_id = str(job.job_id())
        if callable(on_submitted):
            on_submitted(job_id, {
                **base_provenance,
                "job_id": job_id,
                "execution_status": "submitted",
            })
        result = job.result()
        completed_at = datetime.now(timezone.utc).isoformat()
        pub = result[0]
    except Exception as exc:
        failed_provenance = {
            **base_provenance,
            "job_id": job_id,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "actual_shots": None,
            "actual_target_precision": None,
            "twirling_randomizations": None,
            "runtime_result_metadata": None,
            "pub_metadata": None,
            "metadata_status": "runtime_metadata_unavailable",
            "execution_status": "failed",
        }
        raise RuntimeEstimatorExecutionError(type(exc).__name__, failed_provenance) from exc

    pub_metadata = _mapping(getattr(pub, "metadata", None))
    result_metadata = _mapping(getattr(result, "metadata", None))
    twirling_metadata = _mapping(result_metadata.get("twirling"))
    randomizations = pub_metadata.get("num_randomizations")
    if randomizations is None:
        randomizations = twirling_metadata.get("num_randomizations")

    return {
        "job": job,
        "result": result,
        "pub_result": pub,
        "job_id": job_id,
        "provenance": {
            **base_provenance,
            "job_id": job_id,
            "completed_at_utc": completed_at,
            "actual_shots": pub_metadata.get("shots"),
            "actual_target_precision": pub_metadata.get("target_precision"),
            "twirling_randomizations": randomizations,
            "runtime_result_metadata": _json_safe(result_metadata) if result_metadata else None,
            "pub_metadata": _json_safe(pub_metadata) if pub_metadata else None,
            "metadata_status": "captured" if result_metadata or pub_metadata else "runtime_metadata_unavailable",
            "execution_status": "completed",
        },
    }
