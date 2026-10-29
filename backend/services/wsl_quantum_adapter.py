"""
WSL Quantum Adapter for CureGenix

Provides a secure, validated local interface between the Windows FastAPI backend
and the Linux calculation environment in WSL 2 where PySCF and Qiskit Nature run.

Features:
- Subprocess-based local execution over standard I/O (zero open network ports).
- Strict argument list execution (no shell interpolation, immune to command injection).
- Structured JSON request/response contract.
- Configurable timeouts, error mapping, and health/smoke testing.
"""

import os
import json
import shutil
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from backend.services.quantum_resource_policy import assess_geometry_resources

logger = logging.getLogger("curegenix.quantum.wsl_adapter")


class WSLQuantumError(Exception):
    """Base exception for WSL quantum adapter operations."""


class WSLNotAvailableError(WSLQuantumError):
    """Raised when WSL or wsl.exe cannot be found or executed."""


class WSLEnvironmentError(WSLQuantumError):
    """Raised when the WSL distribution or Linux Python venv is missing."""


class WSLServiceError(WSLEnvironmentError):
    """Raised when WSL itself fails to launch the worker after one safe retry."""


class WSLResourceError(WSLEnvironmentError):
    """Raised when the worker is externally terminated, often by the Linux OOM killer."""


class WSLTimeoutError(WSLQuantumError):
    """Raised when a quantum calculation in WSL exceeds the configured timeout."""


class WSLCalculationError(WSLQuantumError):
    """Raised when the molecular quantum calculation in WSL fails."""


class WSLInputValidationError(WSLQuantumError, ValueError):
    """Raised when input parameters fail validation prior to execution."""


def _windows_to_wsl_path(win_path: Path | str) -> str:
    """
    Convert a Windows filesystem path to its WSL /mnt/<drive>/... equivalent.

    Example:
        D:\\Projects\\quantum\\CureGenix -> /mnt/d/Projects/quantum/CureGenix
    """
    p = Path(win_path).resolve()
    drive = p.drive.replace(":", "").lower()
    rest = p.as_posix()[len(p.drive):].lstrip("/")
    return f"/mnt/{drive}/{rest}"


class WSLQuantumAdapter:
    """
    Manages communication with the WSL PySCF / Qiskit Nature worker.
    """

    DEFAULT_DISTRO = "Ubuntu"
    DEFAULT_TIMEOUT_SECONDS = 180
    MAX_TRANSIENT_SERVICE_RETRIES = 1

    def __init__(
        self,
        distro: Optional[str] = None,
        python_path: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.distro = (
            distro
            or os.getenv("CUREGENIX_WSL_DISTRO")
            or self.DEFAULT_DISTRO
        )
        self._configured_python_path = python_path or os.getenv("CUREGENIX_WSL_PYTHON")
        self.timeout_seconds = int(
            timeout_seconds
            or os.getenv("CUREGENIX_WSL_TIMEOUT")
            or self.DEFAULT_TIMEOUT_SECONDS
        )
        self._resolved_python_path: Optional[str] = None
        self._cached_wsl_exe: Optional[str] = None

    @property
    def wsl_exe(self) -> str:
        """Resolve path to wsl.exe on Windows."""
        if self._cached_wsl_exe:
            return self._cached_wsl_exe

        # Standard PATH lookup
        found = shutil.which("wsl.exe") or shutil.which("wsl")
        if found:
            self._cached_wsl_exe = found
            return found

        # Fallback to standard System32 location
        system32 = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "wsl.exe"
        if system32.is_file():
            self._cached_wsl_exe = str(system32)
            return str(system32)

        raise WSLNotAvailableError(
            "wsl.exe was not found. Verify that Windows Subsystem for Linux (WSL 2) is enabled."
        )

    def resolve_wsl_python(self) -> str:
        """
        Determine the path to the Linux virtualenv Python in WSL.
        Resolves ~/curegenix-quantum/.venv/bin/python to /home/<user>/... if needed.
        """
        if self._resolved_python_path:
            return self._resolved_python_path

        candidate = self._configured_python_path

        # If user explicitly supplied an absolute path
        if candidate and candidate.startswith("/"):
            clean = candidate.replace("\x00", "").strip()
            self._resolved_python_path = clean
            return clean

        # Resolve WSL username safely, stripping potential Windows console null bytes
        username = "shivaraj"
        try:
            res = subprocess.run(
                [self.wsl_exe, "-d", self.distro, "--", "whoami"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            clean_out = (res.stdout or "").replace("\x00", "").strip()
            if res.returncode == 0 and clean_out:
                username = clean_out
        except Exception:
            pass

        if candidate and candidate.startswith("~"):
            resolved = candidate.replace("~", f"/home/{username}", 1)
        else:
            resolved = f"/home/{username}/curegenix-quantum/.venv/bin/python"

        clean_resolved = resolved.replace("\x00", "").strip()
        self._resolved_python_path = clean_resolved
        return clean_resolved

    def get_worker_wsl_path(self) -> str:
        """Get the WSL path to quantum/wsl_worker.py in the repository."""
        current_file = Path(__file__).resolve()
        repo_root = current_file.parents[2]
        worker_file = repo_root / "quantum" / "wsl_worker.py"
        if not worker_file.is_file():
            raise WSLEnvironmentError(f"Worker script not found: {worker_file}")
        return _windows_to_wsl_path(worker_file)

    def is_available(self) -> Tuple[bool, str]:
        """
        Check if WSL, the distribution, and the Python virtualenv are ready.
        Returns (is_ready, message).
        """
        try:
            wsl_bin = self.wsl_exe
        except WSLNotAvailableError as exc:
            return False, str(exc)

        python_bin = self.resolve_wsl_python()

        try:
            cmd = [
                wsl_bin,
                "-d",
                self.distro,
                "--",
                python_bin,
                "-c",
                "import pyscf; print('OK')",
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            clean_stdout = (res.stdout or "").replace("\x00", "").strip()
            clean_stderr = (res.stderr or "").replace("\x00", "").strip()
            if res.returncode == 0 and "OK" in clean_stdout:
                return True, f"WSL ready with PySCF in {self.distro} ({python_bin})"
            return False, (
                f"WSL environment verification failed (code {res.returncode}): "
                f"{clean_stderr or clean_stdout}"
            )
        except subprocess.TimeoutExpired:
            return False, "WSL verification check timed out."
        except Exception as exc:
            return False, f"WSL check error: {exc}"

    def _execute_worker(self, payload: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute wsl_worker.py with a JSON payload via stdin.
        """
        effective_timeout = timeout if timeout is not None else self.timeout_seconds
        if effective_timeout <= 0:
            raise WSLInputValidationError(f"Timeout must be positive (got {effective_timeout}).")
        wsl_bin = self.wsl_exe
        python_bin = self.resolve_wsl_python()
        worker_path = self.get_worker_wsl_path()

        cmd = [
            wsl_bin,
            "-d",
            self.distro,
            "--",
            python_bin,
            worker_path,
        ]

        payload_str = json.dumps(payload)

        started = time.perf_counter()
        service_retries = 0
        for attempt in range(self.MAX_TRANSIENT_SERVICE_RETRIES + 1):
            try:
                process = subprocess.run(
                    cmd,
                    input=payload_str,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=effective_timeout,
                )
            except subprocess.TimeoutExpired as exc:
                elapsed = time.perf_counter() - started
                details = self._clean_process_text(exc.stderr) or self._clean_process_text(exc.stdout)
                suffix = f" Process output: {details[:2000]}" if details else ""
                raise WSLTimeoutError(
                    f"WSL quantum calculation timed out after {effective_timeout}s "
                    f"(elapsed {elapsed:.2f}s).{suffix}"
                ) from exc
            except FileNotFoundError as exc:
                raise WSLNotAvailableError(f"Could not execute '{cmd[0]}': {exc}") from exc
            except Exception as exc:
                raise WSLQuantumError(f"Failed to launch WSL calculation process: {exc}") from exc

            stdout = self._clean_process_text(process.stdout)
            stderr = self._clean_process_text(process.stderr)

            if process.returncode != 0:
                elapsed = time.perf_counter() - started
                error_detail = stderr or stdout or "No stdout or stderr was returned by WSL."
                if self._is_transient_wsl_service_failure(process.returncode, error_detail):
                    if attempt < self.MAX_TRANSIENT_SERVICE_RETRIES:
                        service_retries += 1
                        logger.warning(
                            "Transient WSL service failure (%s); retrying worker launch once.",
                            error_detail[:500],
                        )
                        time.sleep(0.25)
                        continue
                    raise WSLServiceError(
                        f"WSL service failed before returning worker output after "
                        f"{attempt + 1} attempt(s) (elapsed {elapsed:.2f}s); "
                        f"exit code {process.returncode}. "
                        f"Full WSL detail: {error_detail[:4000]}"
                    )
                if process.returncode in {9, 137, -9, 4294967287}:
                    raise WSLResourceError(
                        f"WSL worker was terminated with code {process.returncode}; "
                        "this can indicate an external kill or Linux memory exhaustion. "
                        f"Elapsed {elapsed:.2f}s. The calculation was not retried. "
                        "Check WSL dmesg/kernel logs. "
                        f"Full WSL detail: {error_detail[:4000]}"
                    )
                raise WSLEnvironmentError(
                    f"WSL worker process exited with code {process.returncode} "
                    f"after {elapsed:.2f}s. "
                    f"Full WSL detail: {error_detail[:4000]}"
                )
            break

        elapsed = time.perf_counter() - started

        if not stdout:
            raise WSLCalculationError(
                f"WSL worker produced empty output. Stderr: {stderr[:400] if stderr else 'None'}"
            )

        try:
            result = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise WSLCalculationError(
                f"Invalid JSON returned from WSL worker: '{stdout[:200]}...'. "
                f"Stderr: {stderr[:200]}"
            ) from exc

        if not isinstance(result, dict):
            raise WSLCalculationError("Worker output was not a JSON dictionary.")

        if result.get("status") == "error":
            err_msg = result.get("error_message") or "Unknown calculation error"
            err_type = result.get("error_type", "CalculationError")
            worker_traceback = result.get("traceback")
            details = f"\nWorker traceback:\n{worker_traceback[:6000]}" if worker_traceback else ""
            error = WSLCalculationError(f"[{err_type}] {err_msg}{details}")
            error.failed_stage = result.get("failed_stage")
            error.stage_diagnostics = result.get("stage_diagnostics", {})
            error.worker_error_type = err_type
            raise error

        result["adapter_diagnostics"] = {
            "attempts": attempt + 1,
            "transient_service_retries": service_retries,
            "elapsed_seconds": round(elapsed, 3),
            "timeout_seconds": effective_timeout,
        }
        logger.info(
            "WSL worker action=%s completed in %.2fs after %d attempt(s).",
            payload.get("action", "analyze_molecule"), elapsed, attempt + 1,
        )

        return result

    @staticmethod
    def _clean_process_text(value: Any) -> str:
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        return str(value or "").replace("\x00", "").strip()

    @staticmethod
    def _is_transient_wsl_service_failure(returncode: int, detail: str) -> bool:
        """Only retry the known service-start E_UNEXPECTED, never worker failures."""
        normalized = detail.replace("\x00", "").casefold()
        return returncode in {-1, 4294967295} and "wsl/service/e_unexpected" in normalized

    def run_smoke_test(self, basis: str = "sto-3g", timeout: int = 30) -> Dict[str, Any]:
        """
        Run an H2 PySCF calculation in WSL to verify the integration.
        Returns the parsed worker result.
        """
        payload = {
            "action": "smoke_test",
            "basis": basis,
        }
        res = self._execute_worker(payload, timeout=timeout)
        return res

    def analyze_geometry(
        self,
        atom: str,
        basis: str = "sto3g",
        charge: int = 0,
        spin: int = 0,
        maxiter: int = 50,
        benchmark: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run the full electronic structure + active space + VQE workflow in WSL.

        Parameters:
        -----------
        atom: str
            Cartesian coordinates string: "H 0 0 0; H 0 0 0.74"
        basis: str
            Basis set (e.g. "sto3g")
        charge: int
            Molecular charge
        spin: int
            Spin multiplicity (2*S)
        maxiter: int
            Maximum VQE optimizer iterations
        benchmark: bool
            Whether to run exact diagonalization reference

        Returns:
        --------
        dict:
            Standard CureGenix quantum analysis result dictionary.
        """
        if not atom or not isinstance(atom, str) or not atom.strip():
            raise WSLInputValidationError("Molecular geometry string 'atom' cannot be empty.")

        if not isinstance(basis, str) or not basis.strip():
            raise WSLInputValidationError("Invalid basis set specification.")

        if not isinstance(charge, int):
            raise WSLInputValidationError(f"Charge must be an integer (got {type(charge).__name__}).")

        if not isinstance(spin, int) or spin < 0:
            raise WSLInputValidationError(f"Spin must be a non-negative integer (got {spin}).")

        if not isinstance(maxiter, int) or maxiter < 1 or maxiter > 1000:
            raise WSLInputValidationError(f"maxiter must be an integer between 1 and 1000 (got {maxiter}).")

        eligibility = assess_geometry_resources(
            atom, basis=basis, maxiter=maxiter, charge=charge, benchmark=benchmark
        )
        if eligibility.get("status") == "skipped_resource_limit":
            return {
                "status": "skipped_resource_limit",
                "message": "Quantum calculation skipped by the configured resource eligibility policy.",
                "resource_eligibility": eligibility,
                "adapter_diagnostics": {"stage": "resource_preflight", "elapsed_seconds": 0.0},
            }
        if eligibility.get("status") == "invalid_input":
            raise WSLInputValidationError("Geometry is malformed; resource preflight could not be evaluated.")
        if eligibility.get("status") != "eligible":
            raise WSLInputValidationError("Quantum resource policy error: " + "; ".join(eligibility.get("reasons", [])))

        payload = {
            "action": "analyze_molecule",
            "atom": atom.strip(),
            "basis": basis.strip(),
            "charge": charge,
            "spin": spin,
            "maxiter": maxiter,
            "benchmark": benchmark,
        }

        response = self._execute_worker(payload, timeout=timeout)
        result = response.get("result")
        if not isinstance(result, dict):
            raise WSLCalculationError("Worker response did not contain a 'result' object.")

        result["adapter_diagnostics"] = response.get("adapter_diagnostics", {})

        return result


# Singleton adapter instance for application reuse
wsl_quantum_adapter = WSLQuantumAdapter()
