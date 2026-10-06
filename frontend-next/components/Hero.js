// Decorative orbital graphic: purely visual, carries no data.
function OrbitalGraphic() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute -right-24 -top-24 h-[420px] w-[420px] opacity-40 md:-right-16 md:-top-20"
    >
      <svg viewBox="0 0 400 400" className="h-full w-full">
        <defs>
          <radialGradient id="core" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="200" cy="200" r="46" fill="url(#core)" className="animate-pulseGlow" />
        <g className="origin-center animate-spinSlow" style={{ transformOrigin: "200px 200px" }}>
          <ellipse cx="200" cy="200" rx="170" ry="62" fill="none" stroke="#22d3ee" strokeOpacity="0.28" />
          <circle cx="370" cy="200" r="4.5" fill="#22d3ee" />
        </g>
        <g className="origin-center animate-spinSlowReverse" style={{ transformOrigin: "200px 200px" }}>
          <ellipse cx="200" cy="200" rx="150" ry="62" fill="none" stroke="#8b5cf6" strokeOpacity="0.3" transform="rotate(60 200 200)" />
          <ellipse cx="200" cy="200" rx="150" ry="62" fill="none" stroke="#8b5cf6" strokeOpacity="0.3" transform="rotate(120 200 200)" />
          <circle cx="62" cy="130" r="4" fill="#8b5cf6" />
        </g>
        <circle cx="200" cy="200" r="5" fill="#e0f2fe" />
      </svg>
    </div>
  );
}

const TECH = ["RDKit", "PySCF", "Qiskit Nature", "Jordan-Wigner", "VQE"];

export default function Hero() {
  return (
    <div className="relative">
      <OrbitalGraphic />
      <div className="relative">
        <p className="eyebrow">Quantum Biotech &amp; Chemistry</p>
        <h1 className="mt-4 max-w-2xl text-3xl font-semibold leading-[1.18] tracking-tight text-white sm:text-4xl md:text-[2.75rem]">
          From Molecular Structure to{" "}
          <span className="bg-gradient-to-r from-cyan-300 to-violet-400 bg-clip-text text-transparent">
            Quantum-Assisted
          </span>{" "}
          Candidate Prioritization
        </h1>
        <p className="mt-6 max-w-xl text-base leading-7 text-slate-400 md:text-lg">
          Analyze protein structures, generate candidate molecules, and evaluate
          quantum-derived molecular descriptors alongside classical features.
        </p>
        <ul className="mt-8 flex flex-wrap gap-2" aria-label="Technology stack">
          {TECH.map((t) => (
            <li
              key={t}
              className="font-data rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-slate-300"
            >
              {t}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
