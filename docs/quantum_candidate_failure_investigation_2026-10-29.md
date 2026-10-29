# Quantum candidate failure investigation — 2026-10-29

## Scope and preserved state

This investigation used the existing Windows `.venv-win` Python 3.12.3 environment and the Ubuntu WSL distribution. No dependencies were installed, no benchmark artifacts were changed, and neither candidate's full calculation was repeated after the OOM evidence was found. The initial unprivileged `wsl.exe` call from the execution sandbox returned `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`; an approved elevated check then reached the already-running distribution successfully.

No saved dashboard run record or candidate-specific log for `GEN-46D3EFE3` or `GEN-5B0A564F` was found in the repository. The existing logs under `benchmark_reports/egfr_regression/logs/` are unrelated EGFR benchmark logs.

## What the passing tests exercise

- The H2 smoke test calls PySCF RHF/STO-3G only. It confirms that PySCF can start and converge one tiny system; it does not run the candidate VQE workflow.
- The molecular integration test runs water (`SMILES O`) through RDKit hydrogen addition, ETKDG embedding and MMFF optimization, then `PySCFDriver`, full-system molecular orbitals, two-orbital HOMO/LUMO active-space reduction, Jordan–Wigner mapping and a four-qubit Statevector VQE for 20 optimizer iterations.
- Dashboard candidates go through the same workflow but use `maxiter=50`. The all-orbital PySCF problem is constructed before active-space reduction, so the later four-qubit VQE does not bound the cost of the full molecular integral/SCF step.

The controlled full H2 VQE through the Windows adapter completed in 3.841 seconds (four qubits; 20 iterations). The direct RHF smoke result was `-1.116759307396425 Hartree`, converged, matching the supplied reference.

## Candidate inputs and controlled checks

The IDs were reproduced using the current deterministic RDKit analog enumerator and the configured Erlotinib parent:

| Candidate | SMILES | Formula | Heavy atoms | Explicit atoms | Approx. STO-3G basis functions |
|---|---|---:|---:|---:|---:|
| `GEN-46D3EFE3` | `CC#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1` | C23H25N3O4 | 30 | 55 | 175 |
| `GEN-5B0A564F` | `COCCOc1cc2ncnc(Nc3cccc(C#N)c3)c2cc1OCCOC` | C21H22N4O4 | 29 | 51 | 167 |

The basis-function counts are estimates from the atom composition and standard STO-3G shell counts. RDKit parsed both inputs and generated explicit-hydrogen geometries. No candidate docking or protein-complex calculation is involved.

`GEN-46D3EFE3` previously timed out at the adapter's 180-second default in the dashboard (reported by the user; the exact dashboard trace is not present locally). It was not rerun. After WSL recovered, `GEN-5B0A564F` was run once through the full adapter with a 180-second cap. The worker exited with code 9 and no useful stderr (`Unknown error`); the terminal session remained active about 90–100 seconds, but its Python-side elapsed timer did not print because the process exited through the unhandled adapter exception.

The immediately inspected WSL kernel log contained:

```text
Thu Oct 29 09:28:14 2026 ... oom-kill ... task=python,pid=2166
Out of memory: Killed process 2166 (python) ... anon-rss:7226520kB
```

This is direct evidence of a Linux OOM kill during the candidate retry. The exact internal stage was not logged. Since `PySCFDriver.run()` occurs before the active-space and VQE steps, the large all-orbital PySCF setup is the likely resource-heavy phase, but the logs do not prove the precise function where memory peaked. The event is not evidence of VQE non-convergence.

## WSL service recovery

After the earlier dashboard `Wsl/Service/E_UNEXPECTED`, the approved read-only checks showed Ubuntu `Running`, Python 3.12.3, and PySCF 2.14.0. The H2 RHF and full H2 VQE both succeeded. Thus WSL recovered after the service error. A retry is safe only when the WSL service reports that it failed before worker output; it is not safe to retry timeouts or SIGKILL/OOM failures automatically.

## Changes in this investigation

- `backend/services/wsl_quantum_adapter.py`: one retry for the exact WSL service-start `E_UNEXPECTED` signature; no retry for timeouts or signal-like termination; classify possible resource kills; retain full process/worker error details and elapsed time; attach successful-run attempt and duration diagnostics.
- `backend/agents/quantum_analysis_agent.py`: retain a failed status, error type and elapsed time per candidate and log the candidate identifier; continue to later candidates.
- `tests/test_wsl_quantum_adapter_failures.py`: mocked retry, no-retry, error-detail and partial-result regression tests.
- `docs/wsl_quantum_integration.md`: document workload scope, timeout configuration and failure/retry behavior.

The existing `CUREGENIX_WSL_TIMEOUT` setting already applies a configurable per-worker/per-molecule timeout. Increasing it is not a remedy for the observed OOM. No memory-based candidate cutoff was introduced because this investigation only provides two similarly sized candidate failures and is insufficient to calibrate a general molecular-size threshold.

## Commands and test outcomes

The WSL smoke and candidate checks were run from `.venv-win` via `wsl.exe -d Ubuntu`; official WSL commands required elevated execution because the default execution sandbox returned `E_ACCESSDENIED`.

The main controlled commands were:

```powershell
wsl.exe --list --verbose
wsl.exe -d Ubuntu -- /bin/bash -lc 'pwd; python3 --version; /home/shivaraj/curegenix-quantum/.venv/bin/python -c "import pyscf; print(pyscf.__version__)"'
.venv-win\Scripts\python.exe -c "from backend.services.wsl_quantum_adapter import WSLQuantumAdapter; WSLQuantumAdapter(timeout_seconds=60).analyze_geometry('H 0 0 0; H 0 0 0.74', basis='sto-3g', maxiter=20)"
.venv-win\Scripts\python.exe -m unittest tests.test_wsl_quantum_adapter tests.test_wsl_quantum_adapter_failures -v
```

The IDs and SMILES were recovered with:

```powershell
.venv-win\Scripts\python.exe -c "from backend.mcp.molecule_mcp import MoleculeMCPServer; from backend.services.target_aware_generation import SUPPORTED_TARGETS; r=SUPPORTED_TARGETS['P00533']['references'][0]; x=MoleculeMCPServer()._generate_analogs(r['smiles'],r['name'],'target_reference_analog',2); [print(a['id'],a['smiles'],a['modification']) for a in x['analogs']]"
```

The candidate retry was run with this adapter call (`GEN-5B0A564F`, `basis='sto3g'`, `maxiter=50`, `timeout=180`):

```powershell
.venv-win\Scripts\python.exe -c "import time,json; from quantum.chemistry.smiles_adapter import smiles_to_geometry; from backend.services.wsl_quantum_adapter import WSLQuantumAdapter; s='COCCOc1cc2ncnc(Nc3cccc(C#N)c3)c2cc1OCCOC'; g=smiles_to_geometry(s); a=WSLQuantumAdapter(timeout_seconds=180); t=time.perf_counter(); r=a.analyze_geometry(g,basis='sto3g',maxiter=50,timeout=180); print(json.dumps({'candidate_id':'GEN-5B0A564F','atom_count':len(g.split(';')),'elapsed_seconds':round(time.perf_counter()-t,3),'status':r.get('status'),'method':r.get('method'),'vqe':r.get('vqe'),'qubits':r.get('hamiltonian',{}).get('qubits')},indent=2))"
```

It returned worker exit code 9 and no useful stderr; the process exited before the Python elapsed/result print. The terminal session stayed active for approximately 90–100 seconds, so exact process runtime is unavailable. The subsequent read-only WSL kernel-log query was:

```powershell
wsl.exe -d Ubuntu -- /bin/bash -lc 'dmesg -T 2>/dev/null | grep -Ei "out of memory|oom-kill|killed process" | tail -10; grep MemAvailable /proc/meminfo; uptime'
```

That log confirmed the OOM kill. The `GEN-46D3EFE3` full run was not repeated.

Test result: **12 tests passed** (the existing 7 WSL integration tests plus 5 new fast failure regressions). The suite included H2 RHF, water full VQE, timeout handling, error propagation, endpoints and mocked WSL service/OOM/partial-result behavior.

## Remaining uncertainty and limitations

- No dashboard-side persisted traceback exists for the original `GEN-46D3EFE3` timeout, so its stage and whether memory pressure contributed are unknown.
- Code 9 alone is not a definitive OOM diagnosis; in this run the separate kernel log provides the OOM evidence.
- Runtime is host- and memory-limit-dependent. The two examples do not justify a general AO or atom-count cutoff.
- These calculations are isolated-molecule electronic-structure workflows. They do not predict protein binding, affinity, target engagement, efficacy, safety, or quantum advantage.
