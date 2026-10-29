"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import { RunningPipeline } from "@/components/AnalysisPipeline";
import Footer from "@/components/Footer";

// Workspaces
import OverviewWorkspace from "@/components/workspaces/OverviewWorkspace";
import TargetAnalysisWorkspace from "@/components/workspaces/TargetAnalysisWorkspace";
import MoleculeDiscoveryWorkspace from "@/components/workspaces/MoleculeDiscoveryWorkspace";
import QuantumLabWorkspace from "@/components/workspaces/QuantumLabWorkspace";
import MolecularActivityWorkspace from "@/components/workspaces/MolecularActivityWorkspace";
import BenchmarksWorkspace from "@/components/workspaces/BenchmarksWorkspace";
import RiskEvidenceWorkspace from "@/components/workspaces/RiskEvidenceWorkspace";
import ReportsProvenanceWorkspace from "@/components/workspaces/ReportsProvenanceWorkspace";

import {
  API_URL,
  REQUEST_TIMEOUT_MS,
  deriveResults,
  validatePdb,
} from "@/lib/analysis";

const VALID_WORKSPACES = [
  "overview",
  "target-analysis",
  "molecule-discovery",
  "quantum-lab",
  "molecular-activity",
  "benchmarks",
  "risk-evidence",
  "reports-provenance",
];

export default function Home() {
  const [activeWorkspace, setActiveWorkspace] = useState("overview");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const [file, setFile] = useState(null);
  const [targetUniprotId, setTargetUniprotId] = useState("");
  const [targetChainId, setTargetChainId] = useState("");
  const [validation, setValidation] = useState(null);
  const [phase, setPhase] = useState("idle"); // idle | running | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [engine, setEngine] = useState("checking"); // checking | online | offline

  const abortRef = useRef(null);
  const cancelledRef = useRef(false);
  const validationToken = useRef(0);

  // ---- Hash Routing Synchronization --------------------------------------
  useEffect(() => {
    function handleHashChange() {
      const hash = window.location.hash.replace("#", "");
      if (VALID_WORKSPACES.includes(hash)) {
        setActiveWorkspace(hash);
      }
    }
    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  function handleSelectWorkspace(id) {
    setActiveWorkspace(id);
    if (window.location.hash !== `#${id}`) {
      window.location.hash = id;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ---- Backend health (GET /api/health) -----------------------------------
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 90_000);
    fetch(`${API_URL}/api/health`, { signal: controller.signal })
      .then((r) => setEngine(r.ok ? "online" : "offline"))
      .catch(() => setEngine("offline"))
      .finally(() => clearTimeout(timer));
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, []);

  // ---- Elapsed timer for pipeline ----------------------------------------
  useEffect(() => {
    if (phase !== "running") return undefined;
    const start = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed((Date.now() - start) / 1000), 500);
    return () => clearInterval(id);
  }, [phase]);

  // ---- Warn before leaving mid-analysis ----------------------------------
  useEffect(() => {
    if (phase !== "running") return undefined;
    const handler = (e) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [phase]);

  // ---- File handling -----------------------------------------------------
  async function handleSelect(selected) {
    const token = ++validationToken.current;
    setFile(selected);
    setError("");
    setNotice("");
    setValidation({ status: "checking" });
    const v = await validatePdb(selected);
    if (token === validationToken.current) setValidation(v);
  }

  function handleRemove() {
    validationToken.current++;
    setFile(null);
    setValidation(null);
    setError("");
  }

  // ---- Analysis request --------------------------------------------------
  async function runAnalysis() {
    if (!file || validation?.status !== "valid") {
      // If user clicks run without file, guide them to target analysis
      handleSelectWorkspace("target-analysis");
      return;
    }

    setPhase("running");
    setResult(null);
    setError("");
    setNotice("");
    cancelledRef.current = false;

    const controller = new AbortController();
    abortRef.current = controller;
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (targetUniprotId.trim()) {
        formData.append("target_uniprot_id", targetUniprotId.trim());
      }
      if (targetChainId.trim()) {
        formData.append("target_chain_id", targetChainId.trim());
      }

      const response = await fetch(`${API_URL}/api/discover`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      const text = await response.text();
      let data = null;
      try {
        data = JSON.parse(text);
      } catch {
        /* non-JSON body */
      }

      if (!response.ok) {
        const detail = data?.detail;
        throw new Error(
          typeof detail === "string"
            ? detail
            : detail
              ? JSON.stringify(detail)
              : `The server responded with status ${response.status}.`,
        );
      }
      if (!data) throw new Error("The server returned an unreadable response.");

      setResult(data);
      setPhase("done");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      if (cancelledRef.current) {
        setPhase("idle");
        setNotice("Analysis cancelled.");
      } else if (err?.name === "AbortError") {
        setError(
          "The request exceeded the maximum wait time. The backend may still be processing; please try again.",
        );
        setPhase("error");
      } else if (err instanceof TypeError) {
        setError(
          "Could not reach the analysis backend. It may be waking up or the connection was interrupted.",
        );
        setPhase("error");
      } else {
        setError(err?.message || "An unexpected error occurred.");
        setPhase("error");
      }
    } finally {
      clearTimeout(timeout);
      abortRef.current = null;
    }
  }

  function cancelAnalysis() {
    cancelledRef.current = true;
    abortRef.current?.abort();
  }

  function resetAll() {
    validationToken.current++;
    setResult(null);
    setFile(null);
    setValidation(null);
    setError("");
    setNotice("");
    setPhase("idle");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const derived = useMemo(() => (result ? deriveResults(result) : null), [result]);

  const targetInfo = {
    name: result?.protein_name || result?.protein?.name || (file ? file.name : "EGFR (P00533)"),
    pdbId: result?.protein?.pdb_id || (file ? file.name.replace(".pdb", "") : "1M17"),
    uniprot: result?.protein_info?.target_identity?.uniprot_id || targetUniprotId || "P00533",
    chain: result?.protein_info?.target_identity?.selected_chain_id || targetChainId || "A",
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Persistent Left Sidebar */}
      <Sidebar
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={handleSelectWorkspace}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
        mobileOpen={mobileDrawerOpen}
        onCloseMobile={() => setMobileDrawerOpen(false)}
        engine={engine}
        targetInfo={targetInfo}
      />

      {/* Main Workspace Area (Offset by sidebar width on desktop) */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${
        sidebarCollapsed ? "lg:pl-20" : "lg:pl-64"
      }`}>
        {/* Top Header Bar */}
        <TopBar
          activeWorkspace={activeWorkspace}
          onOpenMobile={() => setMobileDrawerOpen(true)}
          phase={phase}
          engine={engine}
          targetInfo={targetInfo}
          onStartAnalysis={runAnalysis}
          onReset={resetAll}
          onCancel={cancelAnalysis}
          canStart={file && validation?.status === "valid"}
        />

        {/* Workspace Content Container */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-8 max-w-7xl w-full mx-auto">
          {/* Notification / Banner */}
          {notice && (
            <div role="status" className="mb-6 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-xs text-sky-900 flex items-center justify-between">
              <span>{notice}</span>
              <button type="button" onClick={() => setNotice("")} className="text-sky-600 hover:text-sky-800">
                Dismiss
              </button>
            </div>
          )}

          {/* Error Alert */}
          {phase === "error" && (
            <div role="alert" className="mb-6 rounded-xl border border-rose-300 bg-rose-50 p-4 text-xs text-rose-900">
              <h3 className="font-semibold text-rose-950 text-sm">Analysis Execution Notice</h3>
              <p className="mt-1 leading-relaxed">{error}</p>
              <div className="mt-3 flex gap-2">
                <button
                  type="button"
                  onClick={runAnalysis}
                  disabled={!file || validation?.status !== "valid"}
                  className="rounded bg-rose-600 text-white px-3 py-1.5 font-semibold text-xs hover:bg-rose-700"
                >
                  Retry Analysis
                </button>
                <button
                  type="button"
                  onClick={handleRemove}
                  className="rounded border border-rose-300 bg-white text-rose-700 px-3 py-1.5 font-semibold text-xs hover:bg-rose-50"
                >
                  Choose Another PDB File
                </button>
              </div>
            </div>
          )}

          {/* Running Pipeline View (When analysis is executing) */}
          {phase === "running" ? (
            <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-sm">
              <RunningPipeline elapsedSeconds={elapsed} onCancel={cancelAnalysis} />
            </div>
          ) : (
            /* Render Selected Workspace */
            <>
              {activeWorkspace === "overview" && (
                <OverviewWorkspace
                  result={result}
                  derived={derived}
                  onNavigate={handleSelectWorkspace}
                  onStartAnalysis={runAnalysis}
                />
              )}

              {activeWorkspace === "target-analysis" && (
                <TargetAnalysisWorkspace
                  result={result}
                  derived={derived}
                  file={file}
                  validation={validation}
                  onSelect={handleSelect}
                  onRemove={handleRemove}
                  onStart={runAnalysis}
                  disabled={phase === "running"}
                  targetUniprotId={targetUniprotId}
                  onTargetUniprotIdChange={setTargetUniprotId}
                  targetChainId={targetChainId}
                  onTargetChainIdChange={setTargetChainId}
                />
              )}

              {activeWorkspace === "molecule-discovery" && (
                <MoleculeDiscoveryWorkspace
                  result={result}
                  derived={derived}
                />
              )}

              {activeWorkspace === "quantum-lab" && (
                <QuantumLabWorkspace
                  result={result}
                  derived={derived}
                />
              )}

              {activeWorkspace === "molecular-activity" && (
                <MolecularActivityWorkspace />
              )}

              {activeWorkspace === "benchmarks" && (
                <BenchmarksWorkspace />
              )}

              {activeWorkspace === "risk-evidence" && (
                <RiskEvidenceWorkspace
                  derived={derived}
                />
              )}

              {activeWorkspace === "reports-provenance" && (
                <ReportsProvenanceWorkspace
                  derived={derived}
                />
              )}
            </>
          )}
        </main>

        {/* Global SaaS Footer */}
        <Footer />
      </div>
    </div>
  );
}
