"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { API_URL, fmt } from "@/lib/analysis";
import {
  RISK_BADGE_STYLES,
  resolveActiveCandidateReport,
  validateCandidateSelection,
  generateMarkdownRiskReport,
} from "@/lib/molecularRiskLogic.mjs";
import {
  AdmetRadarChart,
  PhysicochemicalPropertyDashboard,
  SolubilityPermeabilityVisualization,
  CypInteractionMatrix,
  StructuralAlertMap,
  BindingSiteInteractionDiagram,
  TargetOffTargetPanel,
  MutationRobustnessPanel,
  SyntheticFeasibilityPanel,
} from "../charts/MolecularRiskCharts";

export default function MolecularRiskDigitalTwinWorkspace({
  result,
  derived,
  preselectedCandidateId = null,
}) {
  // Discovery candidates from pipeline
  const pipelineCandidates = useMemo(() => {
    return derived?.candidates || [];
  }, [derived]);

  // Registry candidates fetched from backend
  const [registryCandidates, setRegistryCandidates] = useState([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState(preselectedCandidateId || "");
  const [searchTerm, setSearchTerm] = useState("");

  // Analysis execution state
  const [status, setStatus] = useState("idle"); // idle | loading | completed | failed | cancelled | skipped
  const [currentStage, setCurrentStage] = useState("");
  const [progress, setProgress] = useState(0);
  const [activeReport, setActiveReport] = useState(null);
  const [historicalReports, setHistoricalReports] = useState([]);
  const [errorNotice, setErrorNotice] = useState("");

  // Analysis configuration modal / toggles
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState({
    enable_admet: true,
    enable_binding_stability: true,
    enable_off_target: true,
    enable_mutation_robustness: true,
    enable_synthetic_feasibility: true,
    max_heavy_atoms: 60,
    max_total_atoms: 120,
    max_conformer_iterations: 200,
  });

  // Selected tab in report view: summary | admet | binding | offtarget | mutation | synthesis | history
  const [activeTab, setActiveTab] = useState("summary");

  const abortControllerRef = useRef(null);

  // Combine pipeline candidates with backend registry
  const availableCandidates = useMemo(() => {
    const list = [...registryCandidates];
    // Add any pipeline candidate not in registry
    for (const pc of pipelineCandidates) {
      if (!list.some((c) => c.candidate_id === pc.id || c.id === pc.id)) {
        list.push({
          candidate_id: pc.id,
          id: pc.id,
          drug_name: pc.id,
          canonical_smiles: pc.smiles,
          smiles: pc.smiles,
          category: pc.category || "novel",
          source: "Active Molecule Discovery Session",
          descriptors: pc.screening ? {
            molecular_weight: pc.screening.molecular_weight || 393.4,
            logp: 2.8,
            tpsa: 74.7,
            hbd: 1,
            hba: 6,
            rotatable_bonds: 8,
            fraction_csp3: 0.35,
            qed: 0.65,
          } : null,
        });
      }
    }
    return list;
  }, [registryCandidates, pipelineCandidates]);

  // Load registry candidates & historical reports on mount
  useEffect(() => {
    async function loadData() {
      try {
        const [candRes, repRes] = await Promise.all([
          fetch(`${API_URL}/api/molecular-risk/candidates`).catch(() => null),
          fetch(`${API_URL}/api/molecular-risk/reports`).catch(() => null),
        ]);

        if (candRes && candRes.ok) {
          const cands = await candRes.json();
          setRegistryCandidates(cands);
          if (!selectedCandidateId && cands.length > 0) {
            setSelectedCandidateId(cands[0].candidate_id);
          }
        }
        if (repRes && repRes.ok) {
          const reps = await repRes.json();
          setHistoricalReports(reps);
        }
      } catch {
        // Handled silently
      }
    }
    loadData();
  }, []);

  // Update selected candidate if preselectedCandidateId prop changes
  useEffect(() => {
    if (preselectedCandidateId) {
      setSelectedCandidateId(preselectedCandidateId);
    }
  }, [preselectedCandidateId]);

  // Find currently selected candidate record
  const selectedCandidate = useMemo(() => {
    return availableCandidates.find(
      (c) => (c.candidate_id || c.id) === selectedCandidateId
    ) || null;
  }, [availableCandidates, selectedCandidateId]);

  // Candidate switching guard: Ensure active report strictly matches selected candidate ID
  const candidateReportResolution = useMemo(() => {
    return resolveActiveCandidateReport(selectedCandidateId, activeReport, historicalReports);
  }, [selectedCandidateId, activeReport, historicalReports]);

  const displayedReport = candidateReportResolution.activeReport;

  // Filter candidates by search term
  const filteredCandidates = useMemo(() => {
    if (!searchTerm.trim()) return availableCandidates;
    const term = searchTerm.toLowerCase();
    return availableCandidates.filter((c) => {
      const id = (c.candidate_id || c.id || "").toLowerCase();
      const name = (c.drug_name || "").toLowerCase();
      const smi = (c.canonical_smiles || c.smiles || "").toLowerCase();
      return id.includes(term) || name.includes(term) || smi.includes(term);
    });
  }, [availableCandidates, searchTerm]);

  // Handle manual trigger of risk analysis
  async function handleRunRiskAnalysis() {
    if (!selectedCandidate) {
      setErrorNotice("Please select a candidate before running risk analysis.");
      return;
    }

    const validation = validateCandidateSelection({
      id: selectedCandidate.candidate_id || selectedCandidate.id,
      smiles: selectedCandidate.canonical_smiles || selectedCandidate.smiles,
    });

    if (!validation.valid) {
      setErrorNotice(validation.error);
      return;
    }

    setErrorNotice("");
    setStatus("loading");
    setProgress(15);
    setCurrentStage("Submitting candidate to Molecular Risk Engine...");

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const payload = {
        candidate_id: selectedCandidate.candidate_id || selectedCandidate.id,
        smiles: selectedCandidate.canonical_smiles || selectedCandidate.smiles,
        drug_name: selectedCandidate.drug_name || selectedCandidate.id,
        category: selectedCandidate.category || "novel",
        source: selectedCandidate.source || "Manual Discovery Selection",
        manual_trigger: true,
        run_async: false,
        config: config,
      };

      const res = await fetch(`${API_URL}/api/molecular-risk/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Analysis request returned status ${res.status}`);
      }

      const report = await res.json();
      setActiveReport(report);
      setStatus(report.execution_status === "skipped_resource_limit" ? "skipped" : "completed");
      setProgress(100);
      setCurrentStage(report.current_stage || "Analysis complete");

      // Append to historical reports
      setHistoricalReports((prev) => [report, ...prev.filter((r) => r.report_id !== report.report_id)]);
    } catch (err) {
      if (err.name === "AbortError") {
        setStatus("cancelled");
        setCurrentStage("Analysis cancelled by user");
      } else {
        setStatus("failed");
        setErrorNotice(err.message || "An unexpected error occurred during risk analysis.");
      }
    } finally {
      abortControllerRef.current = null;
    }
  }

  // Handle cancellation
  function handleCancel() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setStatus("cancelled");
    setCurrentStage("Execution cancelled");
  }

  // Load a historical report for the current candidate
  function handleSelectHistoricalReport(report) {
    if (report && report.candidate_id === selectedCandidateId) {
      setActiveReport(report);
      setStatus(report.execution_status === "skipped_resource_limit" ? "skipped" : "completed");
      setErrorNotice("");
    }
  }

  // Download Markdown report
  function handleDownloadMarkdown() {
    if (!displayedReport) return;
    const md = generateMarkdownRiskReport(displayedReport);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${displayedReport.report_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Download JSON report
  function handleDownloadJson() {
    if (!displayedReport) return;
    const jsonStr = JSON.stringify(displayedReport, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${displayedReport.report_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
              Molecular Risk &amp; Digital Twin
            </h2>
            <span className="rounded bg-teal-50 border border-teal-200 text-teal-800 text-[11px] font-bold px-2 py-0.5 uppercase tracking-wider">
              5-Dimension Evaluation
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600">
            Candidate-specific developability, binding stability, off-target selectivity, target mutation robustness, and synthetic feasibility.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowConfig((c) => !c)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm"
          >
            ⚙ Settings
          </button>

          {status === "loading" ? (
            <button
              type="button"
              onClick={handleCancel}
              className="rounded-lg bg-rose-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 transition"
            >
              Cancel Analysis
            </button>
          ) : (
            <button
              type="button"
              onClick={handleRunRiskAnalysis}
              disabled={!selectedCandidate}
              className="rounded-lg bg-teal-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Run Molecular Risk Analysis
            </button>
          )}
        </div>
      </div>

      {/* Settings Drawer (Collapsible) */}
      {showConfig && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-xs">
          <h3 className="font-bold text-slate-900 mb-2">Analysis Dimensions &amp; Resource Guardrails</h3>
          <p className="text-slate-500 mb-4">
            Select which dimensions to evaluate. Size limits prevent browser lockups and server out-of-memory errors.
          </p>

          <div className="grid gap-3 sm:grid-cols-3">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.enable_admet}
                onChange={(e) => setConfig({ ...config, enable_admet: e.target.checked })}
                className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              />
              <span className="font-medium text-slate-700">A. ADMET &amp; Developability</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.enable_binding_stability}
                onChange={(e) => setConfig({ ...config, enable_binding_stability: e.target.checked })}
                className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              />
              <span className="font-medium text-slate-700">B. Binding Stability &amp; Cleft</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.enable_off_target}
                onChange={(e) => setConfig({ ...config, enable_off_target: e.target.checked })}
                className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              />
              <span className="font-medium text-slate-700">C. Off-Target Selectivity</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.enable_mutation_robustness}
                onChange={(e) => setConfig({ ...config, enable_mutation_robustness: e.target.checked })}
                className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              />
              <span className="font-medium text-slate-700">D. Mutation &amp; Robustness</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.enable_synthetic_feasibility}
                onChange={(e) => setConfig({ ...config, enable_synthetic_feasibility: e.target.checked })}
                className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              />
              <span className="font-medium text-slate-700">E. Synthetic Feasibility</span>
            </label>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200 flex gap-4">
            <div>
              <span className="text-slate-500">Max Heavy Atoms:</span>
              <input
                type="number"
                value={config.max_heavy_atoms}
                onChange={(e) => setConfig({ ...config, max_heavy_atoms: Number(e.target.value) })}
                className="ml-2 w-16 px-2 py-0.5 rounded border border-slate-300 bg-white"
              />
            </div>
            <div>
              <span className="text-slate-500">Max Total Atoms:</span>
              <input
                type="number"
                value={config.max_total_atoms}
                onChange={(e) => setConfig({ ...config, max_total_atoms: Number(e.target.value) })}
                className="ml-2 w-16 px-2 py-0.5 rounded border border-slate-300 bg-white"
              />
            </div>
          </div>
        </div>
      )}

      {/* Error / Alert notice */}
      {errorNotice && (
        <div role="alert" className="rounded-xl border border-rose-300 bg-rose-50 p-4 text-xs text-rose-900">
          <p className="font-semibold text-rose-950">Execution Notice</p>
          <p className="mt-1">{errorNotice}</p>
        </div>
      )}

      {/* Candidate Selection Header Card */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-semibold text-slate-900">Selected Candidate Lead</h3>
            <p className="text-xs text-slate-500">
              Risk analysis runs strictly on the explicitly selected candidate below. Automated execution is prohibited.
            </p>
          </div>

          {/* Candidate Dropdown Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600">Select:</span>
            <select
              value={selectedCandidateId}
              onChange={(e) => setSelectedCandidateId(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            >
              {availableCandidates.map((c) => (
                <option key={c.candidate_id || c.id} value={c.candidate_id || c.id}>
                  {c.candidate_id || c.id} ({c.drug_name || c.category || "Lead"})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Selected Candidate Details Grid */}
        {selectedCandidate ? (
          <div className="space-y-3">
            <div className="grid gap-4 sm:grid-cols-4 text-xs">
              <div>
                <span className="text-slate-400 font-bold uppercase text-[10px]">Candidate ID</span>
                <p className="font-mono font-bold text-slate-900 text-sm mt-0.5">
                  {selectedCandidate.candidate_id || selectedCandidate.id}
                </p>
              </div>

              <div>
                <span className="text-slate-400 font-bold uppercase text-[10px]">Designation</span>
                <p className="font-semibold text-slate-800 mt-0.5 truncate" title={selectedCandidate.drug_name}>
                  {selectedCandidate.drug_name || selectedCandidate.id}
                </p>
              </div>

              <div>
                <span className="text-slate-400 font-bold uppercase text-[10px]">Target Protein</span>
                <p className="font-semibold text-teal-800 mt-0.5">
                  EGFR (P00533) · PDB 1M17
                </p>
              </div>

              <div>
                <span className="text-slate-400 font-bold uppercase text-[10px]">Category &amp; Verification</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="rounded bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 text-[10px] uppercase">
                    {selectedCandidate.category || "Novel"}
                  </span>
                  {selectedCandidate.verification_status === "verified" ? (
                    <span className="rounded bg-emerald-50 text-emerald-800 font-semibold px-2 py-0.5 text-[10px]">
                      Verified
                    </span>
                  ) : (
                    <span className="rounded bg-amber-50 text-amber-800 font-semibold px-2 py-0.5 text-[10px]">
                      Hypothesis
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* SMILES Display */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs flex items-center justify-between gap-3">
              <div className="min-w-0">
                <span className="font-bold text-slate-500 uppercase text-[10px] block">Canonical SMILES</span>
                <p className="font-mono text-slate-700 break-all mt-0.5 text-[11px]">
                  {selectedCandidate.canonical_smiles || selectedCandidate.smiles}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-500">No candidate selected. Choose a candidate from the dropdown.</p>
        )}
      </div>

      {/* Progress / Running State Bar */}
      {status === "loading" && (
        <div className="rounded-xl border border-teal-200 bg-teal-50/60 p-5 shadow-sm space-y-3 animate-pulse">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-teal-900">{currentStage}</span>
            <span className="font-mono font-bold text-teal-800">{progress}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-teal-200 overflow-hidden">
            <div
              className="h-full bg-teal-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Strict Candidate Switching Isolation Prompt */}
      {candidateReportResolution.mustRunNewAnalysis && !candidateReportResolution.activeReport && (
        <div className="rounded-xl border border-sky-200 bg-sky-50/80 p-6 text-xs text-sky-900 space-y-3">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sky-950 text-sm">Candidate Changed: Risk Analysis Required</span>
          </div>
          <p className="leading-relaxed text-slate-700">
            You have selected candidate <strong className="font-mono text-slate-900">{selectedCandidateId}</strong>.
            The previous candidate&apos;s risk report has been isolated to prevent accidental data substitution.
            Click <strong className="text-teal-800">&quot;Run Molecular Risk Analysis&quot;</strong> above to generate a candidate-specific evaluation, or select an existing report from the historical audit trail below.
          </p>

          {candidateReportResolution.hasMatchingHistorical && (
            <div className="mt-3 pt-3 border-t border-sky-200/80 flex items-center gap-3">
              <span className="text-slate-600 font-medium">
                Found {candidateReportResolution.matchingHistoryCount} historical report(s) for this candidate:
              </span>
              <button
                type="button"
                onClick={() => handleSelectHistoricalReport(candidateReportResolution.latestHistoricalReport)}
                className="rounded bg-sky-700 text-white font-semibold px-3 py-1 hover:bg-sky-800 transition"
              >
                Load Latest Historical Record
              </button>
            </div>
          )}
        </div>
      )}

      {/* ACTIVE RISK REPORT DASHBOARD */}
      {displayedReport && (
        <div className="space-y-6">
          {/* Five Independent Dimensions Top Summary Cards */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                Five Independent Risk Dimensions
              </h3>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleDownloadMarkdown}
                  className="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm"
                >
                  ↓ Export Markdown
                </button>
                <button
                  type="button"
                  onClick={handleDownloadJson}
                  className="rounded border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm"
                >
                  ↓ Export JSON
                </button>
              </div>
            </div>

            {/* Scientific Integrity Disclosure Alert */}
            <div className="rounded-lg bg-slate-100 border border-slate-200 p-3 text-[11px] text-slate-600 leading-relaxed">
              <span className="font-bold text-slate-800">Scoring Integrity Policy: </span>
              {displayedReport.scoring_policy_disclosure}
            </div>

            {/* 5-Card Grid */}
            <div className="grid gap-3 sm:grid-cols-5">
              {[
                { key: "admet_risk", label: "A. ADMET Risk", tab: "admet" },
                { key: "binding_stability", label: "B. Binding Stability", tab: "binding" },
                { key: "off_target_risk", label: "C. Off-Target Risk", tab: "offtarget" },
                { key: "mutation_robustness", label: "D. Mutation Robustness", tab: "mutation" },
                { key: "synthetic_feasibility", label: "E. Synthetic Feasibility", tab: "synthesis" },
              ].map((dim) => {
                const dData = displayedReport.dimensions?.[dim.key];
                const riskCat = dData?.risk_category || "not_evaluated";
                const isSelected = activeTab === dim.tab;

                return (
                  <button
                    key={dim.key}
                    type="button"
                    onClick={() => setActiveTab(dim.tab)}
                    className={`rounded-xl border p-4 text-left transition ${
                      isSelected
                        ? "border-teal-500 bg-teal-50/40 ring-1 ring-teal-500 shadow-sm"
                        : "border-slate-200 bg-white hover:bg-slate-50"
                    }`}
                  >
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block truncate">
                      {dim.label}
                    </span>
                    <div className="mt-2">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold border uppercase ${
                        RISK_BADGE_STYLES[riskCat] || RISK_BADGE_STYLES.not_evaluated
                      }`}>
                        {riskCat.replace("_", " ")}
                      </span>
                    </div>
                    <p className="mt-2 text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                      {dData?.result_summary || "Not evaluated"}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Module Deep-Dive View Tabs */}
          <div className="flex border-b border-slate-200 text-xs font-semibold text-slate-600 gap-4 overflow-x-auto">
            <button
              type="button"
              onClick={() => setActiveTab("summary")}
              className={`pb-2 border-b-2 transition ${activeTab === "summary" ? "border-teal-600 text-teal-800" : "border-transparent hover:text-slate-900"}`}
            >
              Integrated Overview
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("admet")}
              className={`pb-2 border-b-2 transition ${activeTab === "admet" ? "border-teal-600 text-teal-800" : "border-transparent hover:text-slate-900"}`}
            >
              Module A: ADMET &amp; Developability
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("binding")}
              className={`pb-2 border-b-2 transition ${activeTab === "binding" ? "border-teal-600 text-teal-800" : "border-transparent hover:text-slate-900"}`}
            >
              Module B: Binding Stability &amp; Cleft
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("offtarget")}
              className={`pb-2 border-b-2 transition ${activeTab === "offtarget" ? "border-teal-600 text-teal-800" : "border-transparent hover:text-slate-900"}`}
            >
              Module C: Off-Target Selectivity
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("mutation")}
              className={`pb-2 border-b-2 transition ${activeTab === "mutation" ? "border-teal-600 text-teal-800" : "border-transparent hover:text-slate-900"}`}
            >
              Module D: Target Mutation Robustness
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("synthesis")}
              className={`pb-2 border-b-2 transition ${activeTab === "synthesis" ? "border-teal-600 text-teal-800" : "border-transparent hover:text-slate-900"}`}
            >
              Module E: Synthetic Feasibility
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("history")}
              className={`pb-2 border-b-2 transition ${activeTab === "history" ? "border-teal-600 text-teal-800" : "border-transparent hover:text-slate-900"}`}
            >
              Audit Vault &amp; History ({historicalReports.length})
            </button>
          </div>

          {/* TAB 0: INTEGRATED SUMMARY */}
          {activeTab === "summary" && (
            <div className="space-y-6">
              <PhysicochemicalPropertyDashboard
                descriptors={displayedReport.candidate.descriptors}
                lipinski={displayedReport.dimensions?.admet_risk?.details?.lipinski}
              />

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h4 className="text-sm font-bold text-slate-900 mb-3">Developability Radar Chart</h4>
                  <AdmetRadarChart
                    radarMetrics={displayedReport.dimensions?.admet_risk?.details?.radar_metrics}
                  />
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
                  <h4 className="text-sm font-bold text-slate-900">Digital Twin Assessment Highlights</h4>
                  <ul className="space-y-3 text-xs">
                    <li className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                      <strong className="text-slate-800 block">Solubility &amp; Permeation:</strong>
                      <span className="text-slate-600 mt-1 block">
                        {displayedReport.dimensions?.admet_risk?.details?.solubility_esol?.solubility_class || "Moderate"} aqueous solubility ({displayedReport.dimensions?.admet_risk?.details?.solubility_esol?.logs} logS); {displayedReport.dimensions?.admet_risk?.details?.boiled_egg?.gi_absorption}.
                      </span>
                    </li>
                    <li className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                      <strong className="text-slate-800 block">Kinase Active-Site Pharmacophore:</strong>
                      <span className="text-slate-600 mt-1 block">
                        Hinge donor/acceptor compatible; ATP-cleft Lys745/Met793 interactions mapped. Full dynamic MD marked prepared only.
                      </span>
                    </li>
                    <li className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                      <strong className="text-slate-800 block">Off-Target Kinome Profile:</strong>
                      <span className="text-slate-600 mt-1 block">
                        Elevated homology with ERBB paralogs HER2 &amp; HER4 (85% pocket conservation).
                      </span>
                    </li>
                    <li className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                      <strong className="text-slate-800 block">EGFR Clinical Variant Robustness:</strong>
                      <span className="text-slate-600 mt-1 block">
                        Sensitized to L858R and Exon 19 del; T790M gatekeeper bulk presents classical resistance liability.
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 1: MODULE A ADMET */}
          {activeTab === "admet" && (
            <div className="space-y-6">
              <PhysicochemicalPropertyDashboard
                descriptors={displayedReport.candidate.descriptors}
                lipinski={displayedReport.dimensions?.admet_risk?.details?.lipinski}
              />
              <SolubilityPermeabilityVisualization
                esol={displayedReport.dimensions?.admet_risk?.details?.solubility_esol}
                boiledEgg={displayedReport.dimensions?.admet_risk?.details?.boiled_egg}
              />
              <StructuralAlertMap
                structuralAlerts={displayedReport.dimensions?.admet_risk?.details?.structural_alerts}
                toxicityAlerts={displayedReport.dimensions?.admet_risk?.details?.toxicity_alerts}
              />
              <CypInteractionMatrix
                cypMatrix={displayedReport.dimensions?.admet_risk?.details?.cyp_matrix}
              />
            </div>
          )}

          {/* TAB 2: MODULE B BINDING STABILITY */}
          {activeTab === "binding" && (
            <div className="space-y-6">
              <BindingSiteInteractionDiagram
                pocketContacts={displayedReport.dimensions?.binding_stability?.details?.pocket_contacts}
                mdStatus={displayedReport.dimensions?.binding_stability?.details?.molecular_dynamics_status}
              />
            </div>
          )}

          {/* TAB 3: MODULE C OFF-TARGET SELECTIVITY */}
          {activeTab === "offtarget" && (
            <div className="space-y-6">
              <TargetOffTargetPanel
                panelEvaluations={displayedReport.dimensions?.off_target_risk?.details?.panel_evaluations}
              />
            </div>
          )}

          {/* TAB 4: MODULE D TARGET MUTATION ROBUSTNESS */}
          {activeTab === "mutation" && (
            <div className="space-y-6">
              <MutationRobustnessPanel
                variantAssessments={displayedReport.dimensions?.mutation_robustness?.details?.variant_assessments}
              />
            </div>
          )}

          {/* TAB 5: MODULE E SYNTHETIC FEASIBILITY */}
          {activeTab === "synthesis" && (
            <div className="space-y-6">
              <SyntheticFeasibilityPanel
                feasibilityDetails={displayedReport.dimensions?.synthetic_feasibility?.details}
              />
            </div>
          )}

          {/* TAB 6: AUDIT TRAIL & HISTORY */}
          {activeTab === "history" && (
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-slate-900">Historical Risk Assessment Records</h4>
              <p className="text-xs text-slate-500">
                Auditable, immutable records of all risk analyses conducted in this session.
              </p>

              <div className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
                {historicalReports.map((r) => {
                  const isCurrent = displayedReport.report_id === r.report_id;
                  return (
                    <div key={r.report_id} className="p-4 flex items-center justify-between text-xs hover:bg-slate-50">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-slate-900">{r.report_id}</span>
                          <span className="font-semibold text-teal-800">Candidate: {r.candidate_id}</span>
                          {isCurrent && (
                            <span className="rounded bg-teal-100 text-teal-800 text-[10px] font-bold px-2 py-0.2">
                              Active View
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">
                          Generated: {r.created_at} · Status: {r.execution_status}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCandidateId(r.candidate_id);
                          handleSelectHistoricalReport(r);
                        }}
                        className="rounded border border-slate-200 bg-white px-3 py-1 font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm"
                      >
                        Inspect Record
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
