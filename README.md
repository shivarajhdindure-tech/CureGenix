# 🧬 CureGenix

### Quantum-Enhanced Molecular Analysis & Candidate Prioritization

![Track](https://img.shields.io/badge/Track-Quantum%20Biotech%20%26%20Chemistry-8b5cf6)
![Python](https://img.shields.io/badge/Python-3.12%2B-3b82f6)
![Qiskit](https://img.shields.io/badge/Qiskit-VQE-22d3ee)
![Status](https://img.shields.io/badge/Status-Hackathon%20Prototype-lightgrey)

CureGenix is a **hackathon prototype** that shows how a quantum chemistry workflow can be wired into a molecular analysis and candidate-prioritization pipeline. A user picks a molecule in a Streamlit dashboard. A **Quantum Agent** then orchestrates **MCP quantum tools** that build the electronic-structure problem, reduce it to an active space, map it to qubits, and run a **Variational Quantum Eigensolver (VQE)**. The resulting ground-state energy becomes a quantum-derived feature that feeds a ranking table.

> **Scope note:** CureGenix demonstrates a _software and quantum-computing workflow_ on small molecules. It does not predict drug efficacy, and it does not claim quantum advantage. See [Scientific limitations](#-scientific-limitations).

---

## Table of contents

- [Highlights](#-highlights)
- [How it works](#-how-it-works)
- [Demonstrated results](#-demonstrated-results)
- [The dashboard](#-the-dashboard)
- [Quantum Agent & MCP](#-quantum-agent--mcp)
- [The prototype feature](#-the-prototype-feature)
- [Scientific limitations](#-scientific-limitations)
- [Project structure](#-project-structure)
- [Installation](#-installation)
- [Running CureGenix](#-running-curegenix)
- [Troubleshooting](#-troubleshooting)
- [Demo script](#-demo-script)
- [Roadmap](#-roadmap)
- [Tech stack](#-tech-stack)

---

## ✨ Highlights

- **End-to-end quantum chemistry pipeline:** PySCF → active space → fermionic Hamiltonian → Jordan-Wigner → VQE.
- **Agent-orchestrated:** a Quantum Agent turns a plain-language request ("Calculate the lowest energy of H₂O") into a tool workflow.
- **MCP-based architecture:** quantum capabilities are exposed as reusable tools, so new algorithms can be added without redesigning the app.
- **Honest dashboard:** every number shown comes from the real agent result. Nothing quantum is hardcoded in the UI.
- **Candidate prioritization demo:** quantum-derived features from several molecules are compared in a ranking table.

---

## 🔬 How it works

Candidate Screening
↓
Quantum Agent
↓
MCP quantum tools
↓
Molecular problem construction (PySCF)
↓
Active-space selection
↓
Fermionic Hamiltonian
↓
Jordan-Wigner mapping → qubit Hamiltonian
↓
VQE (Qiskit)
↓
Ground-state molecular energy
↓
Quantum-derived feature
↓
Candidate prioritization

### Architecture

flowchart TD
UI[Streamlit dashboard<br/>frontend/app.py] --> AG[Quantum Agent]
AG --> MCP[MCP client / server<br/>quantum tools]
MCP --> T1[molecular_info]
MCP --> T2[active_space_selection]
MCP --> T3[run_vqe]
T1 --> PY[PySCF]
T2 --> AS[Active space]
T3 --> HAM[Hamiltonian + Jordan-Wigner]
HAM --> VQE[VQE · Qiskit]
PY --> VQE
AS --> VQE
VQE --> E[Ground-state energy]
E --> F[Quantum-derived feature]
F --> R[Candidate prioritization]
R --> UI

### Example request

"Calculate the lowest energy of H2O"
│
▼
Quantum Agent
├── molecular_info
├── active_space_selection
└── run_vqe
│
▼
Ground-state energy

---

## 🧪 Demonstrated results

Three small molecules validate and demonstrate the workflow. They are **not** presented as pharmaceutical candidates.

| Molecule | Purpose                                    | Ground-state energy | Qubits | Pauli terms | Prototype feature |
| -------- | ------------------------------------------ | ------------------: | :----: | :---------: | :---------------: |
| H₂       | Quantum chemistry validation               |         ≈ −1.137 Ha |   4    |     15      |      0.5321       |
| LiH      | Molecular VQE demonstration                |         ≈ −7.862 Ha |   4    |     27      |      0.8872       |
| H₂O      | Chemically meaningful molecular simulation |        ≈ −74.964 Ha |   4    |     15      |      0.9868       |

Energies are in Hartree (Ha). Exact digits can vary slightly between runs. The dashboard always shows the values returned by the live run.

---

## 🖥️ The dashboard

The Streamlit app (`frontend/app.py`) has four parts:

1. **Candidate Screening:** cards for H₂, LiH and H₂O. Analyze one with **Analyze Candidate**, or all three with **Analyze all candidates**.
2. **Quantum Analysis Result:**
   - Metric cards for algorithm, qubits, Pauli terms and active space.
   - The ground-state molecular energy.
   - Active-space details (electrons, spatial orbitals, selected orbitals, selection method).
   - Hamiltonian details (qubits, Pauli terms, Jordan-Wigner mapping).
3. **Quantum-Derived Molecular Feature:** the prototype feature, shown with a scientific disclaimer.
4. **Candidate Prioritization:** a ranked table of Rank, Candidate, Ground-State Energy and Quantum Feature.

If the backend fails, the app shows an error card instead of crashing.

---

## 🤖 Quantum Agent & MCP

Quantum capabilities are exposed through an MCP server (`quantum/mcp/`) and consumed by the agent (`quantum/agent/`).

| MCP tool                 | Role                                                    |
| ------------------------ | ------------------------------------------------------- |
| `molecular_info`         | Build the molecular problem and report basic properties |
| `active_space_selection` | Choose electrons and orbitals for the reduced problem   |
| `run_vqe`                | Build the qubit Hamiltonian and run VQE                 |
| `simulate_hamiltonian`   | Hamiltonian time-evolution simulation                   |
| `run_qaoa`               | QAOA optimization                                       |

The dashboard calls the agent like this:

```python
client = QuantumMCPClient()
await client.connect()
agent = QuantumAgent(client)
result = await agent.run_request("Calculate the lowest energy of H2O")
```

---

## 📊 The prototype feature

The demonstration feature is computed from the absolute ground-state energy:

```text
feature = |E| / (1 + |E|)        E = molecular ground-state energy (Hartree)
```

It exists to show how a quantum-derived descriptor could be passed to a downstream prioritization step. The formula lives in `quantum/demo/scoring.py` and is used by both the dashboard and the CLI demo.

---

## ⚠️ Scientific limitations

**The feature and ranking are a prototype signal only.** They are not a validated:

- drug efficacy score
- binding affinity prediction
- toxicity prediction
- probability of clinical success
- clinical outcome, approval or patient-outcome prediction

Two points to keep in mind when interpreting the ranking:

- Total molecular energy grows with system size, so `|E| / (1 + |E|)` mostly reflects **how large the molecule is**, not its quality as a candidate. The ranking H₂O > LiH > H₂ follows molecule size.
- The molecules are tiny reference systems, and the circuits run on simulators. No quantum hardware is used and **no quantum advantage is claimed**.

The purpose of the current ranking is to demonstrate the software and quantum-computing workflow, not to make pharmaceutical claims.

---

## 📁 Project structure

```text
CureGenix/
├── frontend/
│   └── app.py                    # Streamlit dashboard
├── backend/
├── quantum/
│   ├── chemistry/
│   │   ├── molecule.py
│   │   ├── active_space.py
│   │   ├── hamiltonian.py
│   │   └── molecule_registry.py
│   ├── algorithms/
│   │   ├── vqe.py
│   │   ├── qaoa.py
│   │   └── hamiltonian_simulation.py
│   ├── agent/
│   │   ├── quantum_agent.py
│   │   ├── mcp_client.py
│   │   └── quantum_agent_backup.py
│   ├── mcp/
│   │   ├── quantum_mcp.py
│   │   └── server.py
│   ├── demo/
│   │   ├── candidate_screening.py
│   │   ├── scoring.py
│   │   └── curegenix_demo.py     # CLI demo
│   └── experiments/              # step-by-step H2 / LiH development scripts
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 🛠️ Installation

**Requirements:** Python 3.12 or newer.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CureGenix

# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# install the quantum package and its dependencies
pip install -e .

# the dashboard needs Streamlit
pip install streamlit
```

If you use [uv](https://docs.astral.sh/uv/), run `uv sync` and then `uv pip install streamlit`.

---

## ▶️ Running CureGenix

Always run from the **project root**, with the virtual environment active.

**Dashboard**

```bash
streamlit run frontend/app.py
```

Then open <http://localhost:8501>.

**CLI demo** (screens all three molecules and prints the ranking in the terminal)

```bash
python -m quantum.demo.curegenix_demo
```

---

## 🩺 Troubleshooting

| Symptom                               | Likely cause and fix                                                                                                                                               |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ModuleNotFoundError: quantum`        | Run from the project root and make sure `pip install -e .` completed.                                                                                              |
| "Could not start the quantum backend" | The app starts the MCP server with `python -m quantum.mcp.server`. Activate the same virtual environment that has the dependencies, and run from the project root. |
| First analysis is slow                | PySCF and Qiskit import time plus VQE optimization. LiH and H₂O take longer than H₂.                                                                               |
| HTML appears as raw text in the UI    | Use the current `frontend/app.py`. It flattens HTML before rendering so Markdown cannot turn it into a code block.                                                 |

---

## 🎬 Demo script

1. Open the CureGenix dashboard.
2. Show the candidate cards.
3. Select **H₂O** and click **Analyze Candidate**.
4. Walk through the VQE metrics (qubits, Pauli terms, active space).
5. Show the ground-state energy and Hamiltonian details.
6. Show the quantum-derived feature and its disclaimer.
7. Click **Analyze all candidates**.
8. Show **Candidate Prioritization**, and say clearly that it is a workflow demo.

---

## 🔮 Roadmap

**Phase 1 — Current prototype** ✅
Molecular modelling · active-space reduction · Hamiltonian generation · Jordan-Wigner mapping · VQE · Quantum Agent · MCP integration · candidate screening · quantum-derived feature · prioritization · interactive dashboard

**Phase 2 — Drug-like candidates**
SMILES input · conformer generation · candidate libraries · molecular descriptors · larger active spaces · better preprocessing

**Phase 3 — Hybrid quantum-classical models**

Quantum-derived features + Classical molecular descriptors
│
▼
Machine learning
│
▼
Candidate prioritization

This would give a far more meaningful ranking than a single energy-derived number.

**Phase 4 — Advanced quantum chemistry**
Larger systems · improved active-space strategies · error mitigation · quantum hardware execution · advanced variational algorithms · richer Hamiltonian simulation · quantum molecular dynamics

---

## 💡 Why quantum?

Accurately modelling electronic structure becomes computationally hard as molecules grow. Quantum computing offers a potential route to representing parts of that problem with quantum states. CureGenix explores this through a hybrid workflow of classical chemistry, quantum algorithms, agent-based tool orchestration and classical candidate analysis. The focus is on **demonstrating the integration**, not on claiming an advantage.

---

## 🔧 Tech stack

| Area              | Tools                                                                      |
| ----------------- | -------------------------------------------------------------------------- |
| Quantum computing | Qiskit, Qiskit Nature, Qiskit Algorithms, Qiskit Aer                       |
| Quantum chemistry | PySCF, active-space methods, fermionic Hamiltonians, Jordan-Wigner mapping |
| Algorithms        | VQE, QAOA, Hamiltonian simulation                                          |
| Agent layer       | Quantum Agent, MCP (tool-based orchestration)                              |
| Application       | Python, Streamlit                                                          |

---

## 🏆 Hackathon track

**Quantum Biotech & Chemistry**: quantum molecular simulation, electronic-structure analysis, VQE ground-state estimation, quantum-derived molecular features, agent orchestration and candidate prioritization.

---

## 🧾 Prototype disclaimer

CureGenix is a research and hackathon prototype. Its quantum-derived feature and candidate ranking demonstrate a computational workflow and are **not** validated pharmaceutical predictions. No claim is made that the ranking predicts therapeutic efficacy, toxicity, binding affinity, clinical success, drug approval or patient outcomes.

---

## 🚀 Vision

```text
Molecular candidates
        ↓
Classical chemistry
        ↓
Quantum molecular simulation
        ↓
Quantum-derived descriptors
        ↓
Hybrid quantum-classical models
        ↓
Candidate prioritization
        ↓
Future drug-discovery workflows
```

The current prototype establishes the quantum-computing foundation for that vision.
