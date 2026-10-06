"use client";

import { useState } from "react";
import { STAGES, fmtSeconds, isNum } from "@/lib/analysis";

function Row({ label, value }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-white/[0.05] py-2.5 last:border-0">
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="font-data text-right text-sm text-slate-100">{value ?? "—"}</dd>
    </div>
  );
}

export default function TechnicalDetails({ derived }) {
  const [open, setOpen] = useState(false);
  const { vqeMolecules, steps, durationMs, quantumStep } = derived;
  const q = vqeMolecules[0]?.quantum_analysis;
  const byAgent = {};
  steps.forEach((s) => s?.agent_name && (byAgent[s.agent_name] = s));

  return (
    <section id="technical" className="scroll-mt-24">
      <div className="panel overflow-hidden">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="technical-panel"
          className="flex w-full items-center justify-between px-5 py-4 text-left transition hover:bg-white/[0.03] focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-cyan-300 md:px-6"
        >
          <span>
            <span className="block text-base font-semibold text-white">Technical Details</span>
            <span className="mt-0.5 block text-xs text-slate-500">
              Pipeline, quantum method and run parameters
            </span>
          </span>
          <span aria-hidden="true" className={`text-slate-400 transition ${open ? "rotate-180" : ""}`}>▾</span>
        </button>

        {open && (
          <div id="technical-panel" className="grid gap-8 border-t border-white/[0.06] px-5 py-5 md:grid-cols-2 md:px-6">
            <div>
              <h3 className="metric-label mb-2">Pipeline</h3>
              <dl>
                {STAGES.map((s) => (
                  <Row
                    key={s.agent}
                    label={s.agent}
                    value={byAgent[s.agent] ? `${byAgent[s.agent].status} · ${fmtSeconds(byAgent[s.agent].duration_ms)}` : "not reported"}
                  />
                ))}
                <Row label="Total analysis duration" value={fmtSeconds(durationMs)} />
              </dl>
            </div>

            <div>
              <h3 className="metric-label mb-2">Quantum method</h3>
              {q ? (
                <dl>
                  <Row label="Quantum method" value={q.method} />
                  <Row label="Basis" value={q.basis} />
                  <Row
                    label="Active space"
                    value={q.active_space ? `${q.active_space.electrons} e / ${q.active_space.spatial_orbitals} orbitals (${q.active_space.selection_method})` : null}
                  />
                  <Row label="Qubits" value={q.hamiltonian?.qubits} />
                  <Row label="Pauli terms" value={q.hamiltonian?.pauli_terms} />
                  <Row label="Qubit mapping" value={q.hamiltonian?.mapping} />
                  <Row label="Optimizer" value={q.vqe?.optimizer} />
                  <Row label="Ansatz" value={q.vqe?.ansatz} />
                  <Row label="Max iterations" value={q.vqe?.max_iterations} />
                  <Row label="Charge / spin" value={isNum(q.charge) ? `${q.charge} / ${q.spin}` : null} />
                  <Row label="Quantum stage duration" value={fmtSeconds(quantumStep?.duration_ms)} />
                </dl>
              ) : (
                <p className="text-sm text-slate-500">
                  No VQE parameters are available in this response.
                </p>
              )}
              <p className="mt-4 text-[11px] leading-5 text-slate-600">
                Values are read directly from the API response for the first
                quantum-analyzed candidate.
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
