"use client";

import { useEffect } from "react";

export const DESTINATIONS = [
  {
    id: "overview",
    label: "Overview",
    badge: null,
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    id: "target-analysis",
    label: "Target Analysis",
    badge: "PDB / Seq",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
    ),
  },
  {
    id: "molecule-discovery",
    label: "Molecule Discovery",
    badge: "3D Mol",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ),
  },
  {
    id: "quantum-lab",
    label: "Quantum Lab",
    badge: "PySCF WSL",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <circle cx="12" cy="12" r="3" strokeWidth="1.75" />
        <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(30 12 12)" strokeWidth="1.75" />
        <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(-30 12 12)" strokeWidth="1.75" />
      </svg>
    ),
  },
  {
    id: "molecular-activity",
    label: "Molecular Activity AI",
    badge: "VQC/QGNN",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    id: "benchmarks",
    label: "Benchmarks & Validation",
    badge: "5-Split/16D",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    id: "risk-evidence",
    label: "Risk & Evidence",
    badge: "Passports",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  {
    id: "reports-provenance",
    label: "Reports & Provenance",
    badge: "Vault",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

export default function Sidebar({
  activeWorkspace,
  onSelectWorkspace,
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
  engine = "checking",
  targetInfo = null,
}) {
  // Close drawer on Escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape" && mobileOpen) {
        onCloseMobile();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileOpen, onCloseMobile]);

  const engineConfig = {
    online: { text: "PySCF Online", dot: "bg-emerald-400", border: "border-emerald-500/30 text-emerald-300" },
    offline: { text: "Engine Offline", dot: "bg-rose-400", border: "border-rose-500/30 text-rose-300" },
    checking: { text: "Connecting...", dot: "bg-amber-400 animate-pulse", border: "border-amber-500/30 text-amber-300" },
  }[engine] || { text: "Connecting...", dot: "bg-amber-400", border: "border-amber-500/30 text-amber-300" };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          role="presentation"
          aria-hidden="true"
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-950/75 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Main Sidebar Element */}
      <aside
        id="main-sidebar"
        aria-label="CureGenix Navigation"
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col bg-[#0B132B] border-r border-slate-800 transition-all duration-300 ease-in-out ${
          collapsed ? "lg:w-20" : "lg:w-64"
        } ${mobileOpen ? "translate-x-0 w-72" : "-translate-x-full lg:translate-x-0"}`}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3 min-w-0">
            {/* CureGenix Hexagonal Scientific Logo */}
            <div className="shrink-0 flex items-center justify-center w-9 h-9 rounded-lg bg-slate-900 border border-teal-500/40 shadow-sm">
              <svg width="22" height="22" viewBox="0 0 34 34" fill="none">
                <defs>
                  <linearGradient id="cg-sidebar-grad" x1="0" y1="0" x2="34" y2="34">
                    <stop stopColor="#14b8a6" />
                    <stop offset="1" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
                <path
                  d="M17 2.5 29.5 9.75v14.5L17 31.5 4.5 24.25V9.75L17 2.5Z"
                  stroke="url(#cg-sidebar-grad)"
                  strokeWidth="2"
                />
                <circle cx="17" cy="17" r="3.5" fill="url(#cg-sidebar-grad)" />
                <circle cx="17" cy="8.5" r="1.8" fill="#14b8a6" />
                <circle cx="24.4" cy="21.2" r="1.8" fill="#8b5cf6" />
                <circle cx="9.6" cy="21.2" r="1.8" fill="#14b8a6" />
              </svg>
            </div>

            {(!collapsed || mobileOpen) && (
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-base tracking-tight text-white">CureGenix</span>
                  <span className="rounded bg-teal-500/20 text-teal-300 border border-teal-400/30 px-1.5 py-0.2 text-[9px] font-semibold tracking-wider uppercase">
                    v2.0
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 truncate">Quantum Molecular Discovery</p>
              </div>
            )}
          </div>

          {/* Mobile Close Button */}
          <button
            type="button"
            onClick={onCloseMobile}
            aria-label="Close navigation sidebar"
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Engine Connectivity Badge */}
        {(!collapsed || mobileOpen) && (
          <div className="px-4 py-2.5 bg-slate-900/60 border-b border-slate-800/60">
            <div className={`flex items-center justify-between px-2.5 py-1 rounded-md border text-xs ${engineConfig.border} bg-slate-950/40`}>
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${engineConfig.dot}`} />
                <span className="text-[11px] font-medium">{engineConfig.text}</span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Port 8000</span>
            </div>
          </div>
        )}

        {/* Destination Nav List */}
        <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1" aria-label="Workspaces">
          {DESTINATIONS.map((dest) => {
            const isActive = activeWorkspace === dest.id;

            return (
              <a
                key={dest.id}
                href={`#${dest.id}`}
                onClick={(e) => {
                  e.preventDefault();
                  onSelectWorkspace(dest.id);
                  if (mobileOpen) onCloseMobile();
                }}
                aria-current={isActive ? "page" : undefined}
                title={collapsed && !mobileOpen ? dest.label : undefined}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all group ${
                  isActive
                    ? "bg-teal-500/15 text-teal-300 font-semibold border-l-4 border-teal-400 shadow-sm"
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 font-medium"
                } ${collapsed && !mobileOpen ? "justify-center px-2" : ""}`}
              >
                <div className={`shrink-0 ${isActive ? "text-teal-400" : "text-slate-400 group-hover:text-slate-200"}`}>
                  {dest.icon}
                </div>

                {(!collapsed || mobileOpen) && (
                  <div className="flex-1 flex items-center justify-between min-w-0">
                    <span className="truncate">{dest.label}</span>
                    {dest.badge && (
                      <span className={`text-[9px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded ${
                        isActive
                          ? "bg-teal-400/20 text-teal-200 border border-teal-400/30"
                          : "bg-slate-800 text-slate-400 border border-slate-700/60"
                      }`}>
                        {dest.badge}
                      </span>
                    )}
                  </div>
                )}
              </a>
            );
          })}
        </nav>

        {/* Active Target Footer Info */}
        {(!collapsed || mobileOpen) && (
          <div className="p-3 m-2 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Current Target</p>
            <p className="font-semibold text-slate-100 mt-0.5 truncate">
              {targetInfo?.name || "EGFR (Epidermal Growth Factor)"}
            </p>
            <p className="text-[10px] text-teal-400/90 font-mono mt-0.5 truncate">
              UniProt: {targetInfo?.uniprot || "P00533"} · Chain {targetInfo?.chain || "A"}
            </p>
          </div>
        )}

        {/* Desktop Collapse / Expand Toggle */}
        <div className="hidden lg:flex items-center justify-between p-3 border-t border-slate-800">
          {!collapsed && (
            <span className="text-xs text-slate-500">Collapse menu</span>
          )}
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="p-1.5 mx-auto rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <svg
              className={`w-5 h-5 transition-transform ${collapsed ? "rotate-180" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>
      </aside>
    </>
  );
}
