const NAV = [
  { label: "Analysis", href: "#analysis", always: true },
  { label: "Candidates", href: "#candidates" },
  { label: "Quantum Engine", href: "#quantum" },
  { label: "Risk", href: "#risk" },
];

const ENGINE = {
  checking: {
    text: "Connecting to Engine",
    dot: "bg-amber-400 animate-pulse",
    pill: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  },
  online: {
    text: "Quantum Engine Online",
    dot: "bg-emerald-400",
    pill: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  },
  offline: {
    text: "Engine Unreachable",
    dot: "bg-red-400",
    pill: "border-red-400/30 bg-red-400/10 text-red-300",
  },
};

function Logo() {
  return (
    <svg width="34" height="34" viewBox="0 0 34 34" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="cg-logo" x1="0" y1="0" x2="34" y2="34">
          <stop stopColor="#22d3ee" />
          <stop offset="1" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
      <path
        d="M17 2.5 29.5 9.75v14.5L17 31.5 4.5 24.25V9.75L17 2.5Z"
        stroke="url(#cg-logo)"
        strokeWidth="1.5"
      />
      <circle cx="17" cy="17" r="3.2" fill="url(#cg-logo)" />
      <circle cx="17" cy="8.5" r="1.6" fill="#22d3ee" />
      <circle cx="24.4" cy="21.2" r="1.6" fill="#8b5cf6" />
      <circle cx="9.6" cy="21.2" r="1.6" fill="#22d3ee" />
      <path d="M17 10v4M22.9 20.2l-3.2-1.9M11.1 20.2l3.2-1.9" stroke="url(#cg-logo)" strokeWidth="1" />
    </svg>
  );
}

export default function Header({ engine = "checking", busy = false, hasResults = false }) {
  const status = ENGINE[engine] || ENGINE.checking;

  return (
    <header className="sticky top-0 z-30 border-b border-white/[0.06] bg-ink-950/75 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3.5 md:px-8">
        <a href="#analysis" className="flex items-center gap-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 rounded-lg">
          <Logo />
          <div className="leading-tight">
            <div className="text-[17px] font-semibold tracking-tight text-white">CureGenix</div>
            <div className="hidden text-[11px] text-slate-400 sm:block">
              Quantum-Assisted Molecular Discovery
            </div>
          </div>
        </a>

        <nav aria-label="Sections" className="hidden items-center gap-1 md:flex">
          {NAV.map((item) => {
            const enabled = item.always || hasResults;
            return enabled ? (
              <a
                key={item.label}
                href={item.href}
                className="rounded-lg px-3 py-1.5 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
              >
                {item.label}
              </a>
            ) : (
              <span
                key={item.label}
                aria-disabled="true"
                title="Available after an analysis completes"
                className="cursor-default rounded-lg px-3 py-1.5 text-sm text-slate-600"
              >
                {item.label}
              </span>
            );
          })}
        </nav>

        <div
          role="status"
          className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${status.pill}`}
        >
          <span className={`h-2 w-2 rounded-full ${status.dot}`} />
          <span className="hidden sm:inline">{busy ? "Analysis Running" : status.text}</span>
          <span className="sm:hidden">{busy ? "Running" : engine === "online" ? "Online" : engine === "offline" ? "Offline" : "Connecting"}</span>
        </div>
      </div>
    </header>
  );
}
