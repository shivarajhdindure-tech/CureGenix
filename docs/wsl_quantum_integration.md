# CureGenix: Windows-to-WSL PySCF Quantum Integration

## 1. Overview & Architecture

PySCF is a quantum chemistry engine with compiled C/Fortran routines that currently only ships binary wheels for Linux and macOS. To enable real PySCF electronic-structure calculations and Qiskit Nature VQE without breaking the existing Windows FastAPI backend or frontend, CureGenix uses a **Windows-to-WSL Local Execution Adapter**.

```
+-------------------------------------------------------------+
|                     Windows Host Environment                |
|                                                             |
|  [FastAPI Backend / Uvicorn]    [Next.js Frontend (Port 3000)|
|          |                                                  |
|  [Orchestrator & Agents]                                    |
|          |                                                  |
|  [QuantumAnalysisAgent]                                     |
|          |                                                  |
|  [quantum.chemistry.quantum_analysis.analyze_smiles]        |
|          |                                                  |
|  [WSLQuantumAdapter (backend/services/wsl_quantum_adapter)] |
+----------|--------------------------------------------------+
           | Subprocess invocation: wsl.exe -d Ubuntu -- python quantum/wsl_worker.py
           | (JSON over stdin / stdout, zero open network ports, argument list only)
+----------v--------------------------------------------------+
|                   WSL 2 Ubuntu (Linux Environment)          |
|  Python: ~/curegenix-quantum/.venv/bin/python               |
|                                                             |
|  [WSL Calculation Worker (quantum/wsl_worker.py)]           |
|          |                                                  |
|  [PySCF 2.14.0] (RHF SCF, integrals, orbital energies)      |
|  [Qiskit Nature 0.8.0] (ActiveSpaceTransformer, JW Mapper)  |
|  [Qiskit Algorithms 0.4.0] (VQE, StatevectorEstimator)      |
+-------------------------------------------------------------+
```

### Key Security & Reliability Properties
- **Zero Network Exposure:** No HTTP ports, sockets, or daemon listeners are opened. Communication is purely standard I/O pipes via `wsl.exe`.
- **No Command Injection:** Subprocess arguments are passed as discrete token lists (`[wsl_exe, "-d", distro, "--", python_path, worker_path]`) rather than interpolated shell strings.
- **Strict Process Isolation:** If a PySCF calculation encounters a numerical error or memory limit, the isolated Linux process terminates cleanly without crashing the Windows FastAPI server.
- **Timeouts:** Configurable via `CUREGENIX_WSL_TIMEOUT` (default: 180 seconds). Automatically terminates frozen processes.

---

## 2. Environment Setup

### Windows Python Environment
- **Path:** `.venv-win` (or Windows Python 3.12)
- **Role:** Runs FastAPI backend, Uvicorn, RDKit, Next.js proxy, and agent orchestration.
- **Dependencies:** `fastapi`, `uvicorn`, `rdkit`, `requests`, `python-dotenv`, `scikit-learn`, `qiskit`.
- **Note:** `pyproject.toml` marks PySCF as `sys_platform == 'linux'` so Windows pip will not fail trying to install PySCF wheels.

### WSL 2 Ubuntu Environment
- **Path:** `~/curegenix-quantum/.venv` (e.g. `/home/shivaraj/curegenix-quantum/.venv`)
- **Role:** Runs PySCF 2.14.0, Qiskit Nature 0.8.0, and Qiskit Algorithms 0.4.0.
- **Dependencies:** `pyscf==2.14.0`, `qiskit>=2.5.0`, `qiskit-nature==0.8.0`, `qiskit-algorithms==0.4.0`, `numpy<3,>=2.0`, `scipy>=1.14`, `h5py`.

---

## 3. Operational Commands

### A. Run PySCF Smoke Test
From Windows PowerShell:
```powershell
.venv-win\Scripts\python -c "from backend.services.wsl_quantum_adapter import wsl_quantum_adapter; res = wsl_quantum_adapter.run_smoke_test(); print(res)"
```
Expected output:
```json
{"status": "success", "action": "smoke_test", "pyscf_version": "2.14.0", "basis": "sto-3g", "scf_energy_hartree": -1.1167593073964255, "converged": true}
```

Directly inside WSL:
```bash
~/curegenix-quantum/.venv/bin/python -c "import pyscf; from pyscf import gto, scf; mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g'); mf = scf.RHF(mol); print('HF energy:', mf.kernel())"
```

### B. Run Integration Tests
From Windows PowerShell:
```powershell
.venv-win\Scripts\python -m unittest tests/test_wsl_quantum_adapter.py
```
Runs 7 targeted unit and integration tests:
1. PySCF H₂ smoke test (-1.117 Hartree convergence).
2. Full VQE molecular request via `analyze_smiles("O")`.
3. Input validation (empty/malformed geometry, invalid SMILES, invalid maxiter).
4. Calculation timeout handling and subprocess cleanup.
5. Missing WSL distribution/environment detection.
6. Error propagation to `QuantumAnalysisAgent`.
7. Existing API endpoints integrity (`/api/health`, `/api/benchmarks/egfr`, `/api/molecule/3d`, `/api/mcp-tools`).

### C. Start the CureGenix Application
1. **Start Backend (Windows PowerShell):**
   ```powershell
   .venv-win\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Start Frontend (Windows PowerShell):**
   ```powershell
   cd frontend-next
   node node_modules/next/dist/bin/next dev -p 3000
   ```
3. Open `http://localhost:3000`.

---

## 4. Configuration Variables

| Environment Variable | Default | Purpose |
|---|---|---|
| `CUREGENIX_QUANTUM_MODE` | `full` | `full` runs real PySCF+VQE via WSL; `light` runs lightweight RDKit descriptor mode. |
| `CUREGENIX_WSL_DISTRO` | `Ubuntu` | Target WSL 2 distribution name. |
| `CUREGENIX_WSL_PYTHON` | Auto-detected | Path to Linux venv Python (e.g. `/home/shivaraj/curegenix-quantum/.venv/bin/python`). |
| `CUREGENIX_WSL_TIMEOUT` | `180` | Maximum calculation runtime in seconds before timing out. |
| `CUREGENIX_QUANTUM_MAX_HEAVY_ATOMS` | `20` | Preflight limit for heavy atoms in full quantum jobs. |
| `CUREGENIX_QUANTUM_MAX_ATOMS` | `80` | Preflight limit for total atoms after hydrogen addition. |
| `CUREGENIX_QUANTUM_MAX_ESTIMATED_AO` | `100` | Preflight limit for rough STO-3G basis-function count. |
| `CUREGENIX_QUANTUM_MAX_VQE_ITERATIONS` | `100` | Maximum configured VQE iterations accepted by preflight. |

The size limits are configurable operational guardrails, not a memory estimator. The STO-3G count uses tabulated atom shell counts and does not predict PySCF integral storage, peak resident memory, geometry-dependent behavior, or the machine's available memory. Defaults are conservative relative to the observed OOM at roughly 167–175 estimated STO-3G functions; they have not been calibrated as universal safe limits. A resource-ineligible calculation is returned as `skipped_resource_limit` with the measured counts, configured limits, and reason. It is not a failed calculation or a negative scientific result. Unknown basis sets/elements are skipped because this policy cannot assess them.

---

## 5. Scientific Findings & Scope Disclosures

1. **Standalone Molecule vs. Protein Complex:**
   - Quantum calculations are executed **only on isolated candidate small molecules** (e.g., novel analogs generated from the base scaffold).
   - Neither the uploaded PDB protein, nor binding pocket residues, nor protein-ligand complexes are passed into PySCF or VQE.
2. **Candidate Generation & Scoring:**
   - Candidate generation currently produces analogs of an aspirin scaffold (`CC(=O)Oc1ccccc1`) and web-searched drugs.
   - Candidate ranking is property/rule-based (Lipinski rules, QED, TPSA, BBB permeability, synthetic accessibility heuristics).
   - No molecular docking or binding free energy ($\Delta G_{\text{bind}}$) calculation against the protein pocket is currently performed.
3. **Valid Scientific Claims:**
   - **Supported:** Valid STO-3G Hartree-Fock and active-space VQE simulation for candidate molecules; automated orchestration pipeline from PDB upload to property analysis.
   - **Not Supported:** Protein-ligand docking, binding affinity prediction, or quantum advantage.

## 6. Candidate-sized calculation failures

- Each novel candidate is processed as an isolated molecule. The complete PySCF molecular problem is built before reduction to the two-orbital HOMO/LUMO active space; a small VQE active space does not make the preceding all-orbital PySCF step small.
- `CUREGENIX_WSL_TIMEOUT` applies to each worker invocation. A timeout is recorded as a failed candidate and is not retried.
- Only the known WSL startup error `Wsl/Service/E_UNEXPECTED` receives one bounded retry. Worker termination codes associated with SIGKILL are surfaced as possible resource exhaustion and are not retried.
- Quantum analysis continues candidate-by-candidate. A failed candidate remains marked `failed`; other candidates can still return results. Check WSL kernel logs (`dmesg`) when a worker exits with a signal-like code.
- Full-mode jobs are checked before 3D embedding and again in the WSL worker before PySCF setup. Worker stages report bounded elapsed-time diagnostics. Timeouts remain failures with an unknown in-progress stage because the host cannot inspect a worker after it is terminated.
- Molecular energy calculations are isolated-molecule electronic-structure outputs. They do not establish binding, affinity, target engagement, therapeutic efficacy, or quantum advantage.
