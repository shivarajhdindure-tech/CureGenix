# 🧬 CureGenix

### Hybrid AI + Quantum Drug Candidate Analysis Platform

![Track](https://img.shields.io/badge/Track-Quantum%20Biotech%20%26%20Chemistry-8b5cf6)
![Python](https://img.shields.io/badge/Python-3.12-3b82f6)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)
![Qiskit](https://img.shields.io/badge/Quantum-Qiskit-6929C4)
![Status](https://img.shields.io/badge/Status-Hackathon%20Prototype-lightgrey)

CureGenix is a **hybrid AI–quantum drug candidate analysis platform** designed for the **Quantum Biotech & Chemistry** track. It accepts a protein structure in PDB format, parses the structure, runs a sequential multi-agent discovery workflow, generates molecular candidates, performs computational screening and risk analysis, and uses a quantum-chemistry workflow to derive molecular descriptors in full quantum mode.

The project combines **FastAPI, Next.js, MCP-style tool orchestration, RDKit, PySCF, Qiskit Nature and VQE** into a single end-to-end prototype.

> **Scientific scope:** CureGenix is a research/hackathon prototype. It does not claim quantum advantage, clinical efficacy, drug approval, or therapeutic effectiveness. Quantum-derived descriptors are used as computational features alongside classical molecular information for candidate analysis and prioritization.

---

## 🎯 What CureGenix Does

CureGenix follows this pipeline:

```text
PDB Protein Structure
        │
        ▼
   PDB Parsing
        │
        ▼
   FastAPI Backend
        │
        ▼
     Orchestrator
        │
        ├───────────────┐
        ▼               ▼
   Target Agent    Research Agent
        │               │
        └───────┬───────┘
                ▼
        Molecule Agent
                │
                ▼
     Quantum Analysis Agent
                │
       ┌────────┴────────┐
       │                 │
   Full Mode          Light Mode
       │                 │
       ▼                 ▼
     RDKit             RDKit
     PySCF          Molecular Descriptors
       │
   Active Space
       │
Jordan-Wigner Mapping
       │
      VQE
       │
       └────────┬────────┘
                ▼
       Screening Agent
                │
                ▼
          Risk Agent
                │
                ▼
        Decision Agent
                │
                ▼
      Candidate Prioritization
                │
                ▼
          Next.js UI
```

The important design principle is:

> **Classical computation handles the large workflow, while the quantum module is applied to selected molecular candidates in full quantum mode.**

---

# ✨ Key Features

- **PDB-based workflow** — upload a protein structure instead of manually entering a disease query.
- **Seven-agent pipeline** — specialized agents execute target analysis, research, candidate generation, quantum analysis, screening, risk analysis and final decision-making.
- **MCP-style tool architecture** — agents interact with shared tools through Web, Memory, Filesystem, Compute and Molecule MCP servers.
- **Protein structure parsing** — Node.js PDB parser converts uploaded structures into structured protein information.
- **Candidate generation** — Molecule MCP generates novel analog candidates and collects reference compounds.
- **Classical molecular analysis** — RDKit is used for molecular properties and lightweight molecular analysis.
- **Quantum molecular analysis** — full mode uses RDKit → PySCF → HOMO/LUMO active space → Jordan-Wigner → VQE.
- **Memory-safe deployment mode** — lightweight mode avoids loading PySCF/Qiskit and uses RDKit descriptors for constrained cloud environments.
- **Candidate screening** — drug-likeness, BBB-related scoring and structural toxicity checks.
- **Risk analysis** — computational structural risk flags.
- **Final prioritization** — deterministic risk-adjusted candidate ranking with optional LLM-generated scientific reasoning.
- **Modern web UI** — Next.js + React + Tailwind dashboard with upload validation, live pipeline progress, quantum analysis cards, risk analysis and candidate prioritization.
- **Docker support** — backend can be containerized for deployment.

---

# 🧠 Multi-Agent Architecture

CureGenix currently contains **7 specialized software agents**.

| Agent | Responsibility |
|---|---|
| **Target Agent** | Parses and analyzes the uploaded protein target and stores structural information |
| **Research Agent** | Retrieves target context, checks AlphaFold availability, searches for known binders and produces research reasoning |
| **Molecule Agent** | Generates novel molecular analogs and collects known/reference compounds |
| **Quantum Analysis Agent** | Performs full quantum molecular analysis or memory-safe lightweight analysis depending on deployment mode |
| **Screening Agent** | Computes drug-likeness, BBB-related and structural toxicity screening scores |
| **Risk Agent** | Builds a computational risk profile using structural alerts |
| **Decision Agent** | Combines screening and risk information and produces the final candidate prioritization |

The agents are executed sequentially by the central `Orchestrator`.

```text
Target
  ↓
Research
  ↓
Molecule
  ↓
Quantum Analysis
  ↓
Screening
  ↓
Risk
  ↓
Decision
```

Each agent inherits from `BaseAgent`, which provides execution timing, result handling and MCP access.

---

# 🔌 MCP Tool Layer

CureGenix uses an MCP-style architecture in which agents access capabilities through registered tool servers.

## Current MCP servers

| MCP Server | Purpose |
|---|---|
| **WebMCP** | Protein information, binder searches, literature/drug/clinical-trial style lookups and external web-backed utilities |
| **MemoryMCP** | Shared context and intermediate state between agents |
| **FilesystemMCP** | Knowledge-base access, caching and result file operations |
| **ComputeMCP** | Drug-likeness, BBB-related scoring, toxicity, similarity and composite scoring |
| **MoleculeMCP** | Analog generation, molecular properties, similarity search, scaffold hopping and molecular modifications |

The `MemoryMCP` server is particularly important because agents do not need to pass large objects directly between one another. They can store and retrieve shared pipeline state.

The backend also exposes:

```text
GET /api/mcp-tools
```

so the available MCP tools can be inspected for demonstration and transparency.

> **Implementation note:** the MCP layer in this project is implemented as Python tool-server classes and an internal registry. The agents use these registered tools directly.

---

# ⚛️ Quantum Computing Module

The quantum module is the core component for the **Quantum Biotech & Chemistry** track.

## Full quantum workflow

```text
SMILES
  ↓
RDKit
3D geometry generation
  ↓
PySCF
Molecular electronic structure
  ↓
HOMO / LUMO identification
  ↓
2-electron / 2-spatial-orbital active space
  ↓
Fermionic Hamiltonian
  ↓
Jordan-Wigner transformation
  ↓
Qubit Hamiltonian
  ↓
Parameterized VQE
  ↓
Quantum-derived molecular descriptors
```

### Current full-mode configuration

| Component | Current implementation |
|---|---|
| Molecular input | SMILES generated by the Molecule Agent |
| Geometry | RDKit 3D embedding + MMFF optimization |
| Electronic structure | PySCF |
| Basis | STO-3G |
| Active space | 2 electrons / 2 spatial orbitals |
| Orbital selection | HOMO + LUMO |
| Qubit mapping | Jordan-Wigner |
| Qubits | 4 for the 2-spatial-orbital active space |
| VQE | Qiskit Algorithms |
| VQE optimizer | SLSQP |
| Ansatz | Qiskit `n_local` |
| Rotation gates | `RY` |
| Entanglement | CZ |
| Repetitions | 2 |
| Maximum iterations | 50 in the integrated pipeline |
| Execution | Statevector simulation |

The VQE implementation uses a deterministic initial parameter point to make repeated runs more reproducible.

### Quantum-derived outputs

The full quantum analysis returns:

- HOMO energy
- LUMO energy
- HOMO–LUMO gap
- active-space information
- total electrons/orbitals
- qubit count
- Pauli-term count
- Jordan-Wigner mapping
- VQE electronic energy
- optimizer and ansatz information

These values are treated as **molecular descriptors/features**, not as direct measures of drug efficacy.

---

# 🧪 Two Quantum Analysis Modes

The current implementation supports two deployment modes through:

```text
CUREGENIX_QUANTUM_MODE
```

## 1. Full quantum mode

```text
CUREGENIX_QUANTUM_MODE=full
```

This is the default when the variable is not set.

It loads:

- RDKit
- PySCF
- Qiskit
- Qiskit Nature
- VQE

and performs the actual quantum-chemistry workflow.

Use this mode when sufficient CPU/RAM is available.

---

## 2. Lightweight cloud mode

```text
CUREGENIX_QUANTUM_MODE=light
```

This mode was added for memory-constrained cloud deployments.

It:

- uses RDKit only for the molecular analysis stage
- does **not** load PySCF
- does **not** build the quantum Hamiltonian
- does **not** run VQE
- computes molecular descriptors such as:
  - molecular weight
  - LogP
  - TPSA
  - hydrogen-bond donors
  - hydrogen-bond acceptors
  - rotatable bonds
  - heavy atoms
  - formal charge

The returned result explicitly marks VQE and Hamiltonian construction as **not run**.

This is intentionally transparent: lightweight mode is a **memory-safe classical deployment mode**, not a simulated replacement for the quantum calculation.

---

# 🧬 Protein Structure Processing

CureGenix accepts `.pdb` files through:

```text
POST /api/discover
```

The backend:

1. validates the uploaded file
2. saves it temporarily
3. invokes the Node.js PDB parser
4. converts the PDB structure into structured protein information
5. extracts protein metadata
6. stores the parsed structure in shared memory
7. starts the seven-agent pipeline
8. returns structured JSON to the frontend
9. removes the temporary uploaded file

The PDB parser is located under:

```text
parse-pdb/
```

and uses Node.js built-ins without requiring a separate external PDB parsing service.

---

# 🧪 Molecular Candidate Processing

The Molecule Agent uses `MoleculeMCP` to generate novel analog candidates and collect reference compounds.

The Molecule MCP currently exposes tools for:

- analog generation
- 3D structure simulation
- molecular property calculation
- similarity search
- scaffold hopping
- modification enumeration

Generated candidates are represented using molecular identifiers and SMILES strings so they can be passed into downstream screening and, in full mode, the quantum chemistry workflow.

---

# 📊 Screening, Risk & Prioritization

After molecular analysis, the pipeline evaluates candidates using classical computational tools.

### Screening

The Screening Agent evaluates:

- drug-likeness
- BBB-related score
- toxicity penalty
- a composite screening score
- a potency proxy based on candidate category

### Risk

The Risk Agent evaluates structural toxicity alerts and produces:

- risk level
- structural alerts
- computational risk details
- risk distribution

### Decision

The Decision Agent:

1. retrieves screening results
2. retrieves risk flags
3. applies deterministic risk penalties
4. ranks candidates
5. assigns confidence based on candidate category
6. optionally uses the LLM service for scientific reasoning and explanation

> These screening and risk outputs are **computational prototype signals**. They are not clinical toxicity, efficacy or approval predictions.

---

# 🤖 Optional LLM Reasoning

The project includes a centralized LLM service:

```text
backend/services/llm_service.py
```

It supports:

- **Groq API** when `GROQ_API_KEY` is available
- a built-in template fallback when no API key is available

The LLM is used for:

- reasoning
- interpretation
- explanation
- scientific justification

It is **not required for the core deterministic scoring, PDB parsing or quantum chemistry implementation**.

### Optional environment variables

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Never commit API keys or `.env` files to GitHub.

---

# 🖥️ Frontend

The primary frontend is the Next.js application:

```text
frontend-next/
```

It provides:

- PDB upload
- client-side PDB validation
- backend health status
- live elapsed analysis time
- cancellable analysis requests
- pipeline progress
- candidate comparison
- quantum analysis results
- risk analysis
- final prioritization
- technical details
- reset/re-analysis flow

The frontend communicates with the backend using:

```text
NEXT_PUBLIC_API_URL
```

Example:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The older Streamlit application remains in:

```text
frontend/
```

but the **Next.js application is the primary current web interface**.

---

# 🏗️ Repository Structure

```text
CureGenix/
│
├── backend/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── target_agent.py
│   │   ├── research_agent.py
│   │   ├── molecule_agent.py
│   │   ├── quantum_analysis_agent.py
│   │   ├── screening_agent.py
│   │   ├── risk_agent.py
│   │   └── decision_agent.py
│   │
│   ├── mcp/
│   │   ├── base_mcp.py
│   │   ├── web_mcp.py
│   │   ├── memory_mcp.py
│   │   ├── filesystem_mcp.py
│   │   ├── compute_mcp.py
│   │   └── molecule_mcp.py
│   │
│   ├── services/
│   │   ├── llm_service.py
│   │   └── pdb_parser.py
│   │
│   ├── main.py
│   └── orchestrator.py
│
├── frontend-next/
│   ├── app/
│   ├── components/
│   └── lib/
│
├── frontend/
│   └── app.py
│
├── parse-pdb/
│   ├── cli.js
│   └── lib/
│
├── quantum/
│   ├── algorithms/
│   │   └── vqe.py
│   └── chemistry/
│       ├── molecule.py
│       ├── active_space.py
│       ├── hamiltonian.py
│       ├── quantum_analysis.py
│       └── smiles_adapter.py
│
├── Dockerfile
├── .dockerignore
├── pyproject.toml
├── uv.lock
├── .gitignore
└── README.md
```

---

# 🛠️ Requirements

### Backend

- Python 3.12
- Node.js
- `uv` recommended for Python dependency management
- RDKit
- PySCF
- Qiskit
- Qiskit Nature
- FastAPI
- Uvicorn

### Frontend

- Node.js
- npm
- Next.js
- React
- Tailwind CSS

---

# ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/shivarajhdindure-tech/CureGenix.git
cd CureGenix
```

## Backend / Quantum environment

Using `uv`:

```bash
uv sync
```

Activate the environment:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

The project is constrained to Python 3.12:

```text
requires-python = ">=3.12,<3.13"
```

Install frontend dependencies:

```bash
cd frontend-next
npm install
```

---

# ▶️ Run Locally

## 1. Start the backend

From the repository root:

```bash
cd CureGenix
source .venv/bin/activate

uvicorn backend.main:app --reload --port 8000
```

The backend provides:

```text
http://localhost:8000/api/health
http://localhost:8000/api/mcp-tools
http://localhost:8000/api/discover
```

---

## 2. Start the Next.js frontend

In a second terminal:

```bash
cd CureGenix/frontend-next
npm run dev
```

Open:

```text
http://localhost:3000
```

Set the frontend API URL if required:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

# 🐳 Docker

The repository contains a production-oriented Dockerfile for the FastAPI backend.

Build:

```bash
docker build -t curegenix-backend .
```

Run:

```bash
docker run --rm -p 8000:10000 curegenix-backend
```

Health check:

```bash
curl http://localhost:8000/api/health
```

For a memory-constrained deployment, configure:

```text
CUREGENIX_QUANTUM_MODE=light
```

For a machine with enough resources for the complete quantum workflow:

```text
CUREGENIX_QUANTUM_MODE=full
```

---

# 🔗 API Endpoints

## Health

```http
GET /api/health
```

Returns the backend health status.

## Discover

```http
POST /api/discover
```

Accepts a PDB file as multipart form data:

```text
file=<protein.pdb>
```

Runs the complete agent pipeline and returns the analysis result.

## MCP tools

```http
GET /api/mcp-tools
```

Returns the registered MCP servers and their available tools.

---

# 🌐 Deployment

The current project is structured for separate frontend and backend deployment.

### Frontend

The Next.js application can be deployed from:

```text
frontend-next/
```

For Vercel, configure the project root directory as:

```text
frontend-next
```

and set:

```env
NEXT_PUBLIC_API_URL=<your-backend-url>
```

### Backend

The FastAPI backend can be deployed using the included Dockerfile.

For constrained free-tier infrastructure, use:

```env
CUREGENIX_QUANTUM_MODE=light
```

For a full quantum deployment, use a host with sufficient CPU and RAM and:

```env
CUREGENIX_QUANTUM_MODE=full
```

---

# 🔐 Environment Variables

| Variable | Required | Purpose |
|---|---:|---|
| `NEXT_PUBLIC_API_URL` | Frontend | URL of the FastAPI backend |
| `CUREGENIX_QUANTUM_MODE` | No | `full` for PySCF/Qiskit/VQE or `light` for memory-safe RDKit mode |
| `GROQ_API_KEY` | No | Optional Groq LLM access |
| `GROQ_MODEL` | No | Optional Groq model selection |

If `GROQ_API_KEY` is not provided, the built-in LLM fallback is used.

---

# ⚠️ Scientific Limitations

CureGenix is a **hackathon/research prototype**, not a validated drug-discovery system.

The current implementation:

- uses a small quantum active space
- uses statevector simulation rather than demonstrating quantum advantage
- does not execute the integrated workflow on physical quantum hardware
- does not establish binding affinity
- does not establish therapeutic efficacy
- does not establish clinical safety
- does not predict regulatory approval
- does not replace experimental validation
- uses computational screening and risk heuristics
- uses lightweight mode on constrained infrastructure when configured

The quantum module should therefore be interpreted as:

> **Quantum-assisted molecular analysis and feature generation within a hybrid computational workflow.**

It should not be interpreted as proof that a generated candidate is an effective drug.

---

# 🔬 Current Quantum Contribution

The quantum contribution is deliberately focused rather than attempting to run an entire drug-discovery pipeline on a quantum computer.

### Classical layer

```text
PDB
 ↓
Protein analysis
 ↓
Candidate generation
 ↓
Molecular preprocessing
 ↓
Screening
 ↓
Risk analysis
```

### Quantum layer

```text
Selected molecular candidate
 ↓
RDKit geometry
 ↓
PySCF
 ↓
HOMO/LUMO active space
 ↓
Fermionic Hamiltonian
 ↓
Jordan-Wigner
 ↓
VQE
 ↓
Quantum-derived molecular descriptors
```

### Decision layer

```text
Quantum-derived features
        +
Classical molecular features
        +
Screening
        +
Risk
        ↓
Candidate prioritization
```

This hybrid architecture keeps the quantum computation focused on the molecular electronic-structure component rather than attempting to replace the complete classical discovery stack.

---

# 🚧 Known Constraints

### Memory

The full PySCF + Qiskit + VQE workflow is significantly more memory-intensive than the rest of the application.

For this reason the project supports a lightweight mode:

```text
CUREGENIX_QUANTUM_MODE=light
```

This allows the application to remain usable on constrained cloud instances while keeping the full quantum implementation available for local or sufficiently provisioned environments.

### Runtime

The full quantum calculation is CPU-intensive and can take substantially longer than lightweight molecular descriptor analysis.

The Next.js frontend therefore allows long-running analysis requests and displays elapsed analysis time.

---

# 🗺️ Future Scope

## Phase 1 — Current MVP

- PDB upload and parsing
- Seven-agent orchestration
- MCP tool layer
- Candidate generation
- Classical molecular screening
- Risk analysis
- Candidate prioritization
- Full PySCF + Jordan-Wigner + VQE workflow
- Lightweight deployment mode
- Next.js dashboard
- Docker backend

## Phase 2 — Expanded molecular analysis

- Larger and more chemically meaningful active spaces
- More robust conformer generation
- Larger candidate libraries
- Better molecular descriptors
- More rigorous quantum/classical benchmarking
- Improved candidate generation strategies

## Phase 3 — Hybrid quantum-classical modelling

```text
Quantum-derived descriptors
            +
Classical molecular descriptors
            ↓
     Machine learning
            ↓
 Candidate prioritization
```

## Phase 4 — Advanced quantum chemistry

- Larger molecular systems
- Improved active-space selection
- Error mitigation
- Physical quantum hardware execution
- More advanced variational algorithms
- More sophisticated Hamiltonian simulation
- Quantum molecular dynamics research

---

# 🧪 Reproducibility & Transparency

The project intentionally exposes intermediate information rather than returning only a final candidate.

The API response includes:

- agent execution status
- execution duration
- pipeline steps
- candidate information
- quantum analysis information
- screening information
- risk information
- final decisions
- MCP statistics

This allows the hackathon demo to show **how the result was produced**, rather than presenting the system as a black box.

---

# 🏆 Hackathon Positioning

### Track

**Quantum Biotech & Chemistry**

### Core contribution

CureGenix demonstrates how quantum chemistry can be integrated into a broader AI-driven candidate analysis workflow.

The key innovation is not claiming that a quantum computer independently solves drug discovery. Instead, the project explores a **hybrid architecture** in which:

```text
AI Agents
    +
MCP Tool Orchestration
    +
Classical Chemistry
    +
Quantum Chemistry
    +
Candidate Prioritization
```

work together in a single application.

---

# 📚 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, Tailwind CSS |
| Backend | FastAPI, Uvicorn |
| Agent architecture | Python multi-agent orchestration |
| Tool architecture | MCP-style Python tool servers |
| Molecular processing | RDKit |
| Electronic structure | PySCF |
| Quantum SDK | Qiskit |
| Quantum chemistry | Qiskit Nature |
| VQE | Qiskit Algorithms |
| Quantum simulation | StatevectorEstimator |
| Protein parsing | Node.js PDB parser |
| Optional LLM | Groq API with template fallback |
| Containerization | Docker |
| Frontend deployment | Vercel-compatible |
| Backend deployment | Docker-compatible |

---

# 📁 Important Files

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI application and API endpoints |
| `backend/orchestrator.py` | Central seven-agent pipeline controller |
| `backend/agents/` | Specialized discovery agents |
| `backend/mcp/` | MCP tool servers |
| `backend/services/pdb_parser.py` | PDB parsing integration |
| `backend/services/llm_service.py` | Optional LLM service |
| `quantum/chemistry/quantum_analysis.py` | Main quantum molecular workflow |
| `quantum/chemistry/molecule.py` | PySCF molecular problem construction |
| `quantum/chemistry/active_space.py` | Active-space reduction |
| `quantum/chemistry/hamiltonian.py` | Qubit Hamiltonian construction |
| `quantum/chemistry/smiles_adapter.py` | SMILES → 3D geometry |
| `quantum/algorithms/vqe.py` | VQE implementation |
| `frontend-next/` | Primary web application |
| `parse-pdb/` | Node.js PDB parser |
| `Dockerfile` | Backend container configuration |
| `pyproject.toml` | Python dependencies and project configuration |

---

# 🚀 Vision

CureGenix is designed as a foundation for a future hybrid drug-discovery workflow:

```text
Protein Structure
       ↓
AI-driven Target Analysis
       ↓
Candidate Generation
       ↓
Classical Molecular Analysis
       ↓
Quantum Electronic-Structure Analysis
       ↓
Quantum + Classical Features
       ↓
Candidate Prioritization
       ↓
Experimental Validation
```

The current prototype establishes the software architecture and quantum-computing foundation needed to explore this direction.

---

## ⚖️ Disclaimer

CureGenix is a **research and hackathon prototype**.

Its candidate rankings, molecular descriptors, risk assessments and quantum-derived features are computational outputs and are **not validated pharmaceutical predictions**.

Nothing in this project should be interpreted as medical advice or as evidence of therapeutic efficacy, clinical safety, drug approval, or patient benefit.
