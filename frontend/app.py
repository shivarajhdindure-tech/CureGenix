"""
CureGenix - Quantum-Enhanced Molecular Analysis & Candidate Prioritization.

Streamlit dashboard. Every number shown comes from the result returned by
QuantumAgent (via QuantumMCPClient); nothing quantum is hardcoded here.

Run from the project root:
    streamlit run frontend/app.py
"""

import asyncio
import html
import sys
from pathlib import Path

import streamlit as st

# Make `quantum` importable even when Streamlit is launched from elsewhere.
ROOT = str(Path(__file__).resolve().parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from quantum.agent.mcp_client import QuantumMCPClient  # noqa: E402
from quantum.agent.quantum_agent import QuantumAgent  # noqa: E402
from quantum.demo.scoring import calculate_quantum_score  # noqa: E402

st.set_page_config(
    page_title="CureGenix | Quantum Biotech & Chemistry",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# DATA
# ============================================================

CANDIDATES = {
    "H2": {
        "label": "H₂",
        "name": "Hydrogen",
        "tagline": "Quantum chemistry validation",
    },
    "LiH": {
        "label": "LiH",
        "name": "Lithium Hydride",
        "tagline": "Molecular VQE demonstration",
    },
    "H2O": {
        "label": "H₂O",
        "name": "Water",
        "tagline": "Chemically meaningful molecular simulation",
    },
}

PIPELINE = [
    "Candidate",
    "Quantum Agent",
    "Active Space",
    "Hamiltonian",
    "VQE",
    "Quantum Feature",
    "Ranking",
]


# ============================================================
# STYLING
# (plain string, not an f-string, so CSS braces are safe)
# ============================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
  --bg: #070b14;
  --panel: rgba(15, 23, 42, .72);
  --line: rgba(125, 150, 255, .16);
  --text: #e6edf7;
  --muted: #8794ab;
  --cyan: #22d3ee;
  --blue: #3b82f6;
  --violet: #8b5cf6;
  --mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.stApp {
  font-family: 'Space Grotesk', system-ui, -apple-system, 'Segoe UI', sans-serif;
  color: var(--text);
  background:
    radial-gradient(900px 500px at 10% -5%, rgba(34,211,238,.10), transparent 60%),
    radial-gradient(800px 500px at 95% 0%, rgba(139,92,246,.12), transparent 60%),
    var(--bg);
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stSidebar"],
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {
  display: none !important;
}
.block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }

/* ---- Streamlit native widgets ---- */
.stButton > button {
  width: 100%;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: linear-gradient(135deg, rgba(34,211,238,.14), rgba(139,92,246,.18));
  color: var(--text);
  font-weight: 600;
  padding: .6rem 1rem;
  transition: border-color .2s, box-shadow .2s;
}
.stButton > button p { color: inherit !important; font-weight: 600; }
.stButton > button:hover, .stButton > button:focus:not(:active) {
  border-color: var(--cyan);
  color: #fff;
  box-shadow: 0 0 0 1px rgba(34,211,238,.35), 0 8px 24px rgba(34,211,238,.12);
}
div[role="radiogroup"] label p { color: var(--text) !important; }
[data-testid="stSpinner"] * { color: var(--muted) !important; }

/* ---- Layout pieces ---- */
.cg-brand { display: flex; align-items: center; gap: 14px; margin-bottom: 1.5rem; }
.cg-logo {
  position: relative; width: 42px; height: 42px; border-radius: 12px;
  background: conic-gradient(from 210deg, var(--cyan), var(--blue), var(--violet), var(--cyan));
}
.cg-logo::after {
  content: ""; position: absolute; inset: 11px; border-radius: 50%; background: var(--bg);
}
.cg-title { font-size: 1.7rem; font-weight: 700; letter-spacing: -.02em; line-height: 1.1; }
.cg-tag { color: var(--muted); font-size: .95rem; margin-top: 2px; }

.cg-hero {
  padding: 36px; border-radius: 20px; border: 1px solid var(--line);
  background: linear-gradient(135deg, rgba(34,211,238,.07), rgba(139,92,246,.10)), var(--panel);
}
.cg-hero-title {
  font-size: 2.5rem; font-weight: 700; letter-spacing: -.03em; line-height: 1.1;
  background: linear-gradient(90deg, #fff, #a5b4fc 60%, #67e8f9);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.cg-hero-text { color: #aab6cb; max-width: 620px; line-height: 1.6; margin-top: 12px; font-size: 1.05rem; }
.cg-flow { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 22px; }
.cg-step {
  padding: 5px 12px; border-radius: 999px; border: 1px solid var(--line);
  font-size: .8rem; color: #c3cde0; background: rgba(255,255,255,.03);
}
.cg-sep { color: var(--muted); font-size: .8rem; }

.cg-sec-title { font-size: 1.3rem; font-weight: 700; margin: 2.6rem 0 .3rem; letter-spacing: -.01em; }
.cg-sec-sub { color: var(--muted); font-size: .92rem; margin-bottom: 1rem; }

.cg-card {
  padding: 20px; border-radius: 16px; border: 1px solid var(--line);
  background: var(--panel);
}
.cg-grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
.cg-grid.two { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }

.cand { min-height: 168px; margin-bottom: 10px; }
.cand.active {
  border-color: rgba(34,211,238,.55);
  box-shadow: 0 0 0 1px rgba(34,211,238,.22), 0 10px 30px rgba(34,211,238,.08);
}
.cand-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.cand-sym { font-size: 2.1rem; font-weight: 700; letter-spacing: -.02em; line-height: 1.1; }
.cand-name { font-weight: 600; margin-top: 6px; }
.cand-desc { color: var(--muted); font-size: .9rem; margin-top: 4px; }
.cand-energy { font-family: var(--mono); font-size: .8rem; color: #9fb3d1; margin-top: 12px; }
.chip {
  font-size: .72rem; padding: 3px 10px; border-radius: 999px; white-space: nowrap;
  border: 1px solid var(--line); color: var(--muted);
}
.chip.ok { color: var(--cyan); border-color: rgba(34,211,238,.4); background: rgba(34,211,238,.08); }
.chip.err { color: #fda4af; border-color: rgba(251,113,133,.4); background: rgba(251,113,133,.08); }

.cg-label { font-size: .85rem; color: var(--muted); font-weight: 500; }
.cg-metric { font-family: var(--mono); font-size: 1.55rem; font-weight: 600; margin-top: 8px; }

.cg-energy {
  text-align: center; padding: 44px 20px; margin: 14px 0; border-radius: 22px;
  border: 1px solid rgba(34,211,238,.28);
  background: radial-gradient(520px 200px at 50% 0, rgba(34,211,238,.13), transparent 70%), var(--panel);
}
.cg-energy-label { font-size: .85rem; letter-spacing: .14em; color: var(--muted); font-weight: 600; }
.cg-energy-val {
  font-family: var(--mono); font-size: 3.6rem; font-weight: 600; letter-spacing: -.02em;
  background: linear-gradient(90deg, var(--cyan), #818cf8 70%, var(--violet));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.cg-unit { font-size: 1.15rem; color: var(--muted); margin-left: 10px; }
.cg-energy-row { margin-top: 12px; }
.cg-energy-sub { color: var(--muted); font-size: .88rem; margin-top: 10px; }

.cg-panel-title { font-weight: 700; margin-bottom: 8px; }
.cg-kv {
  display: flex; justify-content: space-between; gap: 16px; padding: 10px 0;
  border-bottom: 1px solid rgba(125,150,255,.09); font-size: .93rem;
}
.cg-kv:last-child { border-bottom: none; }
.cg-kv .k { color: var(--muted); }
.cg-kv .v { font-family: var(--mono); text-align: right; }

.cg-feature-label { font-size: .85rem; letter-spacing: .14em; color: var(--muted); font-weight: 600; }
.cg-feature-val { font-family: var(--mono); font-size: 3.1rem; font-weight: 600; margin: 10px 0 6px; color: #c4b5fd; }
.cg-note { color: #9aa7bd; font-size: .9rem; line-height: 1.6; }
.cg-warn { border-color: rgba(251,191,36,.28); background: rgba(251,191,36,.05); }
.cg-warn .cg-panel-title { color: #fcd34d; }
.cg-error { border-color: rgba(251,113,133,.35); background: rgba(251,113,133,.06); margin-bottom: 10px; }
.cg-error .cg-panel-title { color: #fda4af; }
.cg-empty { text-align: center; color: var(--muted); padding: 34px 20px; }

.cg-table-wrap { overflow-x: auto; }
.cg-table { width: 100%; border-collapse: collapse; }
.cg-table th {
  text-align: left; color: var(--muted); font-weight: 500; font-size: .85rem;
  padding: 0 14px 12px;
}
.cg-table td { padding: 14px; border-top: 1px solid rgba(125,150,255,.1); vertical-align: middle; }
.cg-table tr.pending td { opacity: .5; }
.cg-num { font-family: var(--mono); }
.cg-rank {
  display: inline-flex; width: 28px; height: 28px; border-radius: 50%;
  align-items: center; justify-content: center; font-weight: 700; font-size: .85rem;
  background: rgba(255,255,255,.07);
}
.cg-rank.top { background: linear-gradient(135deg, var(--cyan), var(--violet)); color: #06101c; }
.cg-bar { height: 5px; border-radius: 99px; background: rgba(255,255,255,.07); margin-top: 8px; min-width: 110px; }
.cg-bar i { display: block; height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--cyan), var(--violet)); }
.cg-foot { color: var(--muted); font-size: .82rem; text-align: center; margin-top: 3rem; }
</style>
"""


# ============================================================
# HTML HELPERS
#
# Why this exists: Streamlit renders st.markdown() text as Markdown.
# Markdown treats any line indented by 4+ spaces as a code block, and a
# blank line ends an HTML block. So indented, multi-line HTML inside a
# triple-quoted string gets shown as literal code. render() flattens the
# markup onto a single line so neither rule can apply.
# ============================================================

def esc(value):
    return html.escape(str(value))


def render(markup):
    flat = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(flat, unsafe_allow_html=True)


def section(title, subtitle):
    render(
        f'<div class="cg-sec-title">{esc(title)}</div>'
        f'<div class="cg-sec-sub">{esc(subtitle)}</div>'
    )


def fmt_energy(value):
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return "N/A"


def fmt_value(value):
    if value is None:
        return "N/A"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value).replace("_", " ")


def kv_rows(rows):
    return "".join(
        f'<div class="cg-kv"><span class="k">{esc(k)}</span>'
        f'<span class="v">{esc(v)}</span></div>'
        for k, v in rows
    )


# ============================================================
# QUANTUM ANALYSIS  (real backend - no mock data)
# ============================================================

async def run_quantum_analysis(molecules):
    """Run QuantumAgent for each molecule over one MCP connection."""
    client = QuantumMCPClient()
    responses = {}

    try:
        await client.connect()
        agent = QuantumAgent(client)

        for molecule in molecules:
            try:
                responses[molecule] = await agent.run_request(
                    f"Calculate the lowest energy of {molecule}"
                )
            except Exception as exc:
                responses[molecule] = {"status": "error", "message": str(exc)}

    except Exception as exc:
        for molecule in molecules:
            responses.setdefault(
                molecule,
                {
                    "status": "error",
                    "message": f"Could not start the quantum backend: {exc}",
                },
            )

    finally:
        try:
            await client.close()
        except Exception:
            pass

    return responses


def store_response(molecule, response):
    """Keep the agent's actual output; derive the feature with the project's own scoring."""
    state = st.session_state
    formatted = response.get("result") if isinstance(response, dict) else None

    if (
        isinstance(response, dict)
        and response.get("status") == "success"
        and isinstance(formatted, dict)
    ):
        state.results[molecule] = {
            "data": formatted,
            "feature": calculate_quantum_score(response),
        }
        state.errors.pop(molecule, None)
        return True

    message = "Quantum analysis failed."
    if isinstance(response, dict):
        message = response.get("message", message)
    state.errors[molecule] = message
    return False


# ============================================================
# SESSION STATE
# ============================================================

st.session_state.setdefault("results", {})
st.session_state.setdefault("errors", {})
st.session_state.setdefault("view", None)

render(CSS)


# ============================================================
# HEADER + HERO
# ============================================================

render(
    """
    <div class="cg-brand">
        <div class="cg-logo"></div>
        <div>
            <div class="cg-title">CureGenix</div>
            <div class="cg-tag">Quantum-Enhanced Molecular Analysis &amp; Candidate Prioritization</div>
        </div>
    </div>
    """
)

flow = '<span class="cg-sep">→</span>'.join(
    f'<span class="cg-step">{esc(step)}</span>' for step in PIPELINE
)

render(
    f"""
    <div class="cg-hero">
        <div class="cg-hero-title">Quantum Biotech &amp; Chemistry</div>
        <div class="cg-hero-text">
            Use quantum molecular simulation to derive quantum-informed
            molecular features for candidate prioritization.
        </div>
        <div class="cg-flow">{flow}</div>
    </div>
    """
)


# ============================================================
# CANDIDATE SCREENING
# ============================================================

section(
    "Candidate Screening",
    "Choose a molecule and run it through the quantum analysis pipeline.",
)

requested = []
columns = st.columns(3, gap="medium")

for column, (symbol, info) in zip(columns, CANDIDATES.items()):
    with column:
        entry = st.session_state.results.get(symbol)

        if entry:
            chip = '<span class="chip ok">Analyzed</span>'
            energy_line = (
                f'<div class="cand-energy">'
                f'E = {fmt_energy(entry["data"].get("ground_state_energy"))} Ha</div>'
            )
        elif symbol in st.session_state.errors:
            chip = '<span class="chip err">Failed</span>'
            energy_line = ""
        else:
            chip = '<span class="chip">Ready</span>'
            energy_line = ""

        active = " active" if st.session_state.view == symbol else ""

        render(
            f"""
            <div class="cg-card cand{active}">
                <div class="cand-top">
                    <div class="cand-sym">{esc(info["label"])}</div>
                    {chip}
                </div>
                <div class="cand-name">{esc(info["name"])}</div>
                <div class="cand-desc">{esc(info["tagline"])}</div>
                {energy_line}
            </div>
            """
        )

        if st.button("Analyze Candidate", key=f"analyze_{symbol}"):
            requested = [symbol]

_, all_col = st.columns([2, 1])
with all_col:
    if st.button("Analyze all candidates", key="analyze_all"):
        requested = list(CANDIDATES)

if requested:
    names = ", ".join(CANDIDATES[m]["label"] for m in requested)
    with st.spinner(f"Running quantum VQE analysis for {names}..."):
        responses = asyncio.run(run_quantum_analysis(requested))

    for molecule in requested:
        if store_response(molecule, responses[molecule]):
            st.session_state.view = molecule

    st.rerun()


# ============================================================
# QUANTUM ANALYSIS RESULT
# ============================================================

section(
    "Quantum Analysis Result",
    "Output of the VQE workflow returned by the Quantum Agent.",
)

for molecule, message in st.session_state.errors.items():
    render(
        f"""
        <div class="cg-card cg-error">
            <div class="cg-panel-title">Analysis failed for {esc(CANDIDATES[molecule]["label"])}</div>
            <div class="cg-note">{esc(message)}</div>
        </div>
        """
    )

analyzed = [m for m in CANDIDATES if m in st.session_state.results]

if not analyzed:
    render(
        """
        <div class="cg-card cg-empty">
            No analysis yet. Select <b>Analyze Candidate</b> on a molecule above to run VQE.
        </div>
        """
    )
else:
    if st.session_state.view not in analyzed:
        st.session_state.view = analyzed[-1]

    if len(analyzed) > 1:
        st.session_state.view = st.radio(
            "Candidate",
            analyzed,
            index=analyzed.index(st.session_state.view),
            format_func=lambda m: f'{CANDIDATES[m]["label"]} · {CANDIDATES[m]["name"]}',
            horizontal=True,
            label_visibility="collapsed",
        )

    molecule = st.session_state.view
    entry = st.session_state.results[molecule]
    data = entry["data"]
    feature = entry["feature"]
    active_space = data.get("active_space") or {}
    hamiltonian = data.get("hamiltonian") or {}
    energy = data.get("ground_state_energy")

    electrons = active_space.get("electrons")
    orbitals = active_space.get("spatial_orbitals")
    active_label = (
        f"{electrons}e / {orbitals} orbitals"
        if electrons is not None and orbitals is not None
        else "N/A"
    )

    metrics = [
        ("Algorithm", data.get("method", "VQE")),
        ("Qubits", hamiltonian.get("qubits", "N/A")),
        ("Pauli Terms", hamiltonian.get("pauli_terms", "N/A")),
        ("Active Space", active_label),
    ]
    render(
        '<div class="cg-grid">'
        + "".join(
            f'<div class="cg-card"><div class="cg-label">{esc(label)}</div>'
            f'<div class="cg-metric">{esc(value)}</div></div>'
            for label, value in metrics
        )
        + "</div>"
    )

    subtitle = f'{CANDIDATES[molecule]["label"]} · {CANDIDATES[molecule]["name"]}'
    if data.get("basis"):
        subtitle += f' · basis {data["basis"]}'

    render(
        f"""
        <div class="cg-energy">
            <div class="cg-energy-label">GROUND-STATE MOLECULAR ENERGY</div>
            <div class="cg-energy-row">
                <span class="cg-energy-val">{esc(fmt_energy(energy))}</span>
                <span class="cg-unit">{esc(data.get("energy_unit", "Hartree"))}</span>
            </div>
            <div class="cg-energy-sub">{esc(subtitle)}</div>
        </div>
        """
    )

    render(
        f"""
        <div class="cg-grid two">
            <div class="cg-card">
                <div class="cg-panel-title">Active Space</div>
                {kv_rows([
                    ("Electrons", fmt_value(electrons)),
                    ("Spatial orbitals", fmt_value(orbitals)),
                    ("Selected orbitals", fmt_value(active_space.get("selected_orbitals"))),
                    ("Selection method", fmt_value(active_space.get("selection_method"))),
                ])}
            </div>
            <div class="cg-card">
                <div class="cg-panel-title">Hamiltonian</div>
                {kv_rows([
                    ("Qubits", fmt_value(hamiltonian.get("qubits"))),
                    ("Pauli terms", fmt_value(hamiltonian.get("pauli_terms"))),
                    ("Mapping", "Jordan-Wigner"),
                ])}
            </div>
        </div>
        """
    )

    # --------------------------------------------------------
    # Quantum-derived feature + disclaimer
    # --------------------------------------------------------

    if energy is None:
        feature_value = "N/A"
    else:
        feature_value = f"{feature:.4f}"

    render(
        f"""
        <div class="cg-sec-title">Quantum-Derived Molecular Feature</div>
        <div class="cg-grid two">
            <div class="cg-card">
                <div class="cg-feature-label">QUANTUM-DERIVED MOLECULAR FEATURE</div>
                <div class="cg-feature-val">{esc(feature_value)}</div>
                <div class="cg-note">
                    Prototype feature computed from the ground-state energy as
                    |E| / (1 + |E|).
                </div>
            </div>
            <div class="cg-card cg-warn">
                <div class="cg-panel-title">Prototype ranking feature only</div>
                <div class="cg-note">
                    This value is derived solely from the quantum molecular energy.
                    It is not a measure of drug efficacy, probability of success,
                    toxicity, binding affinity, or clinical outcome, and should not
                    be read as one.
                </div>
            </div>
        </div>
        """
    )


# ============================================================
# CANDIDATE PRIORITIZATION
# ============================================================

section(
    "Candidate Prioritization",
    "Analyzed candidates ordered by their quantum-derived feature. Prototype demonstration only.",
)

ranked = sorted(
    (
        (m, e)
        for m, e in st.session_state.results.items()
        if e["data"].get("ground_state_energy") is not None
    ),
    key=lambda item: item[1]["feature"],
    reverse=True,
)
pending = [m for m in CANDIDATES if m not in dict(ranked)]

if not ranked:
    render(
        """
        <div class="cg-card cg-empty">
            Analyze candidates above to populate the ranking.
        </div>
        """
    )
else:
    rows = ""
    for rank, (molecule, entry) in enumerate(ranked, start=1):
        info = CANDIDATES[molecule]
        top = " top" if rank == 1 else ""
        width = max(0.0, min(1.0, float(entry["feature"]))) * 100
        rows += f"""
            <tr>
                <td><span class="cg-rank{top}">{rank}</span></td>
                <td><b>{esc(info["label"])}</b> <span class="cg-note">{esc(info["name"])}</span></td>
                <td class="cg-num">{esc(fmt_energy(entry["data"].get("ground_state_energy")))} Ha</td>
                <td>
                    <span class="cg-num">{entry["feature"]:.4f}</span>
                    <div class="cg-bar"><i style="width:{width:.1f}%"></i></div>
                </td>
            </tr>
        """

    for molecule in pending:
        info = CANDIDATES[molecule]
        rows += f"""
            <tr class="pending">
                <td><span class="cg-rank">-</span></td>
                <td><b>{esc(info["label"])}</b> <span class="cg-note">{esc(info["name"])}</span></td>
                <td class="cg-num">Not analyzed</td>
                <td class="cg-num">-</td>
            </tr>
        """

    render(
        f"""
        <div class="cg-card cg-table-wrap">
            <table class="cg-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Candidate</th>
                        <th>Ground-State Energy</th>
                        <th>Quantum Feature</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
    )

render(
    """
    <div class="cg-foot">
        CureGenix hackathon prototype. Quantum-derived features are for
        demonstration and are not validated predictions.
    </div>
    """
)