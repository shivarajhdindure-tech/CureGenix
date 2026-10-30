"use client";

import { useState } from "react";

/**
 * Reusable Scientific Cartesian X-Y Bar Chart Component (Pure Responsive SVG)
 * Features:
 * - Visible X and Y axes with directional arrows and labels
 * - Numeric scale ticks with horizontal dashed gridlines
 * - Data bars with positive and negative value support (relative to Y=0 baseline)
 * - Optional sample standard deviation error bars (T-stems)
 * - Reference benchmark threshold lines (e.g. 50% chance baseline)
 * - Interactive hover tooltips and accessible SVG titles
 */
function CartesianBarChart({
  title,
  subtitle,
  yAxisTitle,
  xAxisTitle = "Model Architecture",
  data = [],
  yMin = 0,
  yMax = 1,
  yTicks = [],
  yFormat = (val) => val.toString(),
  referenceLines = [],
  zeroBaseline = false,
  lowerIsBetter = false,
  badge = null,
}) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  // SVG Canvas dimensions and margins
  const width = 480;
  const height = 300;
  const marginLeft = 62;
  const marginRight = 24;
  const marginTop = 36;
  const marginBottom = 54;

  const plotWidth = width - marginLeft - marginRight;
  const plotHeight = height - marginTop - marginBottom;
  const chartLeft = marginLeft;
  const chartRight = width - marginRight;
  const chartBottom = height - marginBottom;
  const chartTop = marginTop;

  // Domain to range mapper
  function getY(val) {
    const clamped = Math.max(yMin, Math.min(yMax, val));
    const ratio = (clamped - yMin) / (yMax - yMin);
    return chartBottom - ratio * plotHeight;
  }

  const yZero = getY(0);
  const slotWidth = data.length > 0 ? plotWidth / data.length : plotWidth;
  const barWidth = Math.min(54, slotWidth * 0.52);

  const hoveredItem = hoveredIndex !== null ? data[hoveredIndex] : null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 sm:p-5 shadow-xs flex flex-col justify-between transition hover:border-slate-300">
      {/* Chart Title and Header */}
      <div>
        <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-2.5 mb-2">
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs sm:text-sm font-bold text-slate-900 tracking-tight">
                {title}
              </h4>
              {badge && (
                <span className="rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[9px] px-1.5 py-0.2 uppercase font-semibold">
                  {badge}
                </span>
              )}
            </div>
            {subtitle && (
              <p className="text-[11px] text-slate-500 mt-0.5 leading-tight">{subtitle}</p>
            )}
          </div>
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border shrink-0 ${
            lowerIsBetter
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-sky-50 text-sky-800 border-sky-200"
          }`}>
            {lowerIsBetter ? "Lower is Better ↓" : "Higher is Better ↑"}
          </span>
        </div>

        {/* SVG Cartesian Graphic */}
        <div className="relative w-full aspect-[480/300] overflow-visible">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-full select-none"
            role="img"
            aria-label={`${title} chart`}
          >
            {/* Gridlines & Y-Axis Ticks */}
            {yTicks.map((tickVal, idx) => {
              const yPos = getY(tickVal);
              return (
                <g key={`ytick-${idx}`}>
                  <line
                    x1={chartLeft}
                    y1={yPos}
                    x2={chartRight}
                    y2={yPos}
                    stroke="#e2e8f0"
                    strokeWidth="1"
                    strokeDasharray="3 3"
                  />
                  <line
                    x1={chartLeft - 4}
                    y1={yPos}
                    x2={chartLeft}
                    y2={yPos}
                    stroke="#94a3b8"
                    strokeWidth="1.25"
                  />
                  <text
                    x={chartLeft - 8}
                    y={yPos + 3.5}
                    textAnchor="end"
                    className="font-mono text-[9px] fill-slate-500 font-medium"
                  >
                    {yFormat(tickVal)}
                  </text>
                </g>
              );
            })}

            {/* Optional Reference Lines (e.g. 50% random chance baseline) */}
            {referenceLines.map((ref, idx) => {
              const refY = getY(ref.value);
              return (
                <g key={`refline-${idx}`}>
                  <line
                    x1={chartLeft}
                    y1={refY}
                    x2={chartRight}
                    y2={refY}
                    stroke={ref.color || "#f59e0b"}
                    strokeWidth="1.5"
                    strokeDasharray={ref.strokeDash || "4 3"}
                  />
                  <text
                    x={chartRight - 4}
                    y={refY - 4}
                    textAnchor="end"
                    className="font-sans text-[8.5px] font-bold fill-amber-700"
                  >
                    {ref.label}
                  </text>
                </g>
              );
            })}

            {/* Zero Baseline (Highlighted if enabled or if domain includes negative values) */}
            {(zeroBaseline || yMin < 0) && (
              <line
                x1={chartLeft}
                y1={yZero}
                x2={chartRight}
                y2={yZero}
                stroke="#475569"
                strokeWidth="1.5"
              />
            )}

            {/* Main Axes */}
            {/* Y-Axis Line */}
            <line
              x1={chartLeft}
              y1={chartTop - 6}
              x2={chartLeft}
              y2={chartBottom}
              stroke="#64748b"
              strokeWidth="1.5"
            />
            {/* Y-Axis Arrow */}
            <path
              d={`M ${chartLeft - 3} ${chartTop - 4} L ${chartLeft} ${chartTop - 10} L ${chartLeft + 3} ${chartTop - 4} Z`}
              fill="#64748b"
            />

            {/* X-Axis Line */}
            <line
              x1={chartLeft}
              y1={chartBottom}
              x2={chartRight + 6}
              y2={chartBottom}
              stroke="#64748b"
              strokeWidth="1.5"
            />
            {/* X-Axis Arrow */}
            <path
              d={`M ${chartRight + 4} ${chartBottom - 3} L ${chartRight + 10} ${chartBottom} L ${chartRight + 4} ${chartBottom + 3} Z`}
              fill="#64748b"
            />

            {/* Y-Axis Title */}
            <text
              transform={`rotate(-90 ${chartLeft - 44} ${chartTop + plotHeight / 2})`}
              x={chartLeft - 44}
              y={chartTop + plotHeight / 2}
              textAnchor="middle"
              className="font-sans text-[10px] font-bold uppercase tracking-wider fill-slate-600"
            >
              {yAxisTitle}
            </text>

            {/* Plotted Data Bars */}
            {data.map((item, idx) => {
              const centerX = chartLeft + slotWidth * (idx + 0.5);
              const barX = centerX - barWidth / 2;
              const valY = getY(item.value);
              const isNegative = item.value < 0;

              let rectY = valY;
              let rectHeight = Math.abs(valY - (zeroBaseline || yMin < 0 ? yZero : chartBottom));

              if (isNegative) {
                rectY = yZero;
                rectHeight = valY - yZero;
              }

              // Ensure minimal visible height for small non-zero values
              rectHeight = Math.max(3, rectHeight);

              const isHovered = hoveredIndex === idx;

              return (
                <g
                  key={item.id || idx}
                  className="cursor-pointer transition-opacity"
                  onMouseEnter={() => setHoveredIndex(idx)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  <title>{`${item.label}: ${item.formattedValue || yFormat(item.value)} (${item.executionType || ""})`}</title>

                  {/* Highlight Column on Hover */}
                  {isHovered && (
                    <rect
                      x={centerX - slotWidth / 2}
                      y={chartTop}
                      width={slotWidth}
                      height={plotHeight}
                      fill="#f1f5f9"
                      opacity="0.6"
                      rx="4"
                    />
                  )}

                  {/* Main Data Bar */}
                  <rect
                    x={barX}
                    y={rectY}
                    width={barWidth}
                    height={rectHeight}
                    fill={isNegative ? "#f43f5e" : item.color || "#0d9488"}
                    rx={isNegative ? 0 : 3}
                    className="transition-all duration-300"
                    stroke={isHovered ? "#0f172a" : "none"}
                    strokeWidth={isHovered ? 1.5 : 0}
                  />

                  {/* Value Label on Top/Bottom of Bar */}
                  <text
                    x={centerX}
                    y={isNegative ? rectY + rectHeight + 11 : rectY - 5}
                    textAnchor="middle"
                    className={`font-mono text-[9px] font-bold ${
                      isNegative ? "fill-rose-700" : isHovered ? "fill-slate-900" : "fill-slate-700"
                    }`}
                  >
                    {item.formattedValue || yFormat(item.value)}
                  </text>

                  {/* Sample Standard Deviation Error Bar (T-Stem) if provided */}
                  {typeof item.errorStd === "number" && item.errorStd > 0 && (
                    <g className="error-bar">
                      {(() => {
                        const topY = getY(item.value + item.errorStd);
                        const botY = getY(item.value - item.errorStd);
                        const capWidth = 10;
                        return (
                          <>
                            {/* Vertical error stem */}
                            <line
                              x1={centerX}
                              y1={topY}
                              x2={centerX}
                              y2={botY}
                              stroke="#0f172a"
                              strokeWidth="1.5"
                            />
                            {/* Top cap */}
                            <line
                              x1={centerX - capWidth / 2}
                              y1={topY}
                              x2={centerX + capWidth / 2}
                              y2={topY}
                              stroke="#0f172a"
                              strokeWidth="1.5"
                            />
                            {/* Bottom cap */}
                            <line
                              x1={centerX - capWidth / 2}
                              y1={botY}
                              x2={centerX + capWidth / 2}
                              y2={botY}
                              stroke="#0f172a"
                              strokeWidth="1.5"
                            />
                          </>
                        );
                      })()}
                    </g>
                  )}

                  {/* X-Axis Ticks & Labels */}
                  <line
                    x1={centerX}
                    y1={chartBottom}
                    x2={centerX}
                    y2={chartBottom + 4}
                    stroke="#64748b"
                    strokeWidth="1.25"
                  />
                  <text
                    x={centerX}
                    y={chartBottom + 16}
                    textAnchor="middle"
                    className={`font-sans text-[9px] font-bold ${
                      isHovered ? "fill-teal-700 font-extrabold" : "fill-slate-700"
                    }`}
                  >
                    {item.shortLabel || item.label}
                  </text>
                  {item.subLabel && (
                    <text
                      x={centerX}
                      y={chartBottom + 27}
                      textAnchor="middle"
                      className="font-sans text-[7.5px] fill-slate-400 font-medium"
                    >
                      {item.subLabel}
                    </text>
                  )}
                </g>
              );
            })}

            {/* X-Axis Title */}
            <text
              x={chartLeft + plotWidth / 2}
              y={height - 8}
              textAnchor="middle"
              className="font-sans text-[10px] font-bold uppercase tracking-wider fill-slate-500"
            >
              {xAxisTitle}
            </text>
          </svg>
        </div>
      </div>

      {/* Interactive Tooltip Card on Hover */}
      <div className="mt-2.5 rounded-lg border border-slate-150 bg-slate-50 p-2.5 min-h-[50px] flex items-center justify-between text-xs">
        {hoveredItem ? (
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-900 truncate">{hoveredItem.label}</span>
              <span className="font-data font-bold text-teal-800 text-sm ml-2">
                {hoveredItem.formattedValue || yFormat(hoveredItem.value)}
                {typeof hoveredItem.errorStd === "number" ? ` ± ${hoveredItem.errorStd.toFixed(4)}` : ""}
              </span>
            </div>
            <p className="text-[11px] text-slate-600 mt-0.5 truncate">
              {hoveredItem.notes || hoveredItem.executionType || "Benchmark evaluation record"}
            </p>
          </div>
        ) : (
          <p className="text-[11px] text-slate-400 italic">
            Hover over any plotted bar or error stem to inspect detailed metrics, model architecture, and execution mode.
          </p>
        )}
      </div>
    </div>
  );
}

export default function ClassicalVsQuantumComparisonGraph() {
  const [activeTab, setActiveTab] = useState("all"); // "all" | "classification" | "pilot-regression" | "five-split"

  // 1. Classification: Balanced Accuracy (%)
  const classificationBalAccData = [
    {
      id: "rbf_svm",
      label: "Classical RBF-SVM",
      shortLabel: "RBF-SVM",
      subLabel: "Classical CPU",
      value: 84.96,
      formattedValue: "84.96%",
      color: "#0284c7", // sky-600
      executionType: "Classical Baseline (Scikit-Learn)",
      notes: "Highest accuracy and balanced score; fit in 2.2ms on 4D Morgan FP features.",
    },
    {
      id: "vqc",
      label: "Quantum VQC",
      shortLabel: "VQC",
      subLabel: "Quantum Sim",
      value: 64.79,
      formattedValue: "64.79%",
      color: "#0d9488", // teal-600
      executionType: "Quantum Simulator (StatevectorSampler)",
      notes: "4-qubit ZZFeatureMap + RealAmplitudes; 15 objective evaluations. Convergence was not reported in the saved artifact.",
    },
    {
      id: "qgnn",
      label: "Molecular QGNN",
      shortLabel: "QGNN",
      subLabel: "Hybrid Sim",
      value: 59.39,
      formattedValue: "59.39%",
      color: "#7c3aed", // violet-600
      executionType: "Hybrid Quantum Simulator (MP-GNN + PQC)",
      notes: "1-round message passing + 4-qubit PQC ansatz; reached the 24-evaluation maximum (optimizer_success=false).",
    },
  ];

  // 2. Classification: ROC-AUC (0–1)
  const classificationRocAucData = [
    {
      id: "rbf_svm",
      label: "Classical RBF-SVM",
      shortLabel: "RBF-SVM",
      subLabel: "Classical CPU",
      value: 0.9112,
      formattedValue: "0.9112",
      color: "#0284c7",
      executionType: "Classical Baseline (Scikit-Learn)",
      notes: "ROC-AUC 0.9112 indicates strong discriminative rank-ordering on heldout test split.",
    },
    {
      id: "vqc",
      label: "Quantum VQC",
      shortLabel: "VQC",
      subLabel: "Quantum Sim",
      value: 0.6605,
      formattedValue: "0.6605",
      color: "#0d9488",
      executionType: "Quantum Simulator (StatevectorSampler)",
      notes: "ROC-AUC 0.6605. Lags classical RBF-SVM by 0.2507.",
    },
    {
      id: "qgnn",
      label: "Molecular QGNN",
      shortLabel: "QGNN",
      subLabel: "Hybrid Sim",
      value: 0.6145,
      formattedValue: "0.6145",
      color: "#7c3aed",
      executionType: "Hybrid Quantum Simulator",
      notes: "ROC-AUC 0.6145. Hybrid message-passing prototype; uncalibrated probabilities.",
    },
  ];

  // 3. Matched 16D Regression: MAE (pIC50) - Lower is better
  const pilotMaeData = [
    {
      id: "rf_16d",
      label: "Classical Random Forest",
      shortLabel: "Random Forest",
      subLabel: "Classical CPU",
      value: 0.6166,
      formattedValue: "0.6166",
      color: "#0284c7",
      executionType: "Classical Baseline (Scikit-Learn)",
      notes: "Lowest error on the matched 16D activity-proxy pilot split (400 trees, min_samples_leaf=2).",
    },
    {
      id: "rbf_svr_16d",
      label: "Classical RBF-SVR",
      shortLabel: "RBF-SVR",
      subLabel: "Classical CPU",
      value: 0.6476,
      formattedValue: "0.6476",
      color: "#0d9488",
      executionType: "Classical Baseline (Scikit-Learn)",
      notes: "Direct classical kernel counterpart on identical 16D pilot SVD angles and test compounds.",
    },
    {
      id: "quantum_svr_16d",
      label: "Quantum-Kernel SVR",
      shortLabel: "Quantum SVR",
      subLabel: "Quantum Sim",
      value: 0.9435,
      formattedValue: "0.9435",
      color: "#7c3aed",
      executionType: "Quantum Simulator (ZZFeatureMap)",
      notes: "16D ZZFeatureMap fidelity kernel with 4 landmarks; classical StatevectorSampler simulation. MAE is 0.2959 pIC50 points higher than RBF-SVR.",
    },
  ];

  // 4. Matched 16D Regression: RMSE (pIC50) - Lower is better
  const pilotRmseData = [
    {
      id: "rf_16d",
      label: "Classical Random Forest",
      shortLabel: "Random Forest",
      subLabel: "Classical CPU",
      value: 0.7839,
      formattedValue: "0.7839",
      color: "#0284c7",
      executionType: "Classical Baseline (Scikit-Learn)",
      notes: "Lowest RMSE (0.7839) on matched 16D test split (N=64).",
    },
    {
      id: "rbf_svr_16d",
      label: "Classical RBF-SVR",
      shortLabel: "RBF-SVR",
      subLabel: "Classical CPU",
      value: 0.9045,
      formattedValue: "0.9045",
      color: "#0d9488",
      executionType: "Classical Baseline (Scikit-Learn)",
      notes: "Classical RBF-SVR RMSE 0.9045. Better outlier resistance than Quantum SVR.",
    },
    {
      id: "quantum_svr_16d",
      label: "Quantum-Kernel SVR",
      shortLabel: "Quantum SVR",
      subLabel: "Quantum Sim",
      value: 1.1234,
      formattedValue: "1.1234",
      color: "#7c3aed",
      executionType: "Quantum Simulator (ZZFeatureMap)",
      notes: "Quantum RMSE is 0.2188 pIC50 points higher than classical RBF-SVR; penalizes large prediction errors.",
    },
  ];

  // 5. Matched 16D Regression: R² Score - Higher is better (Shows zero baseline & negative value)
  const pilotR2Data = [
    {
      id: "rf_16d",
      label: "Classical Random Forest",
      shortLabel: "Random Forest",
      subLabel: "Classical CPU",
      value: 0.4872,
      formattedValue: "0.4872",
      color: "#0284c7",
      executionType: "Classical Baseline",
      notes: "Explains 48.72% of pIC50 target variance on the matched 16D pilot split.",
    },
    {
      id: "rbf_svr_16d",
      label: "Classical RBF-SVR",
      shortLabel: "RBF-SVR",
      subLabel: "Classical CPU",
      value: 0.3172,
      formattedValue: "0.3172",
      color: "#0d9488",
      executionType: "Classical Baseline",
      notes: "Explains 31.72% of target variance on identical 16D pilot features.",
    },
    {
      id: "quantum_svr_16d",
      label: "Quantum-Kernel SVR",
      shortLabel: "Quantum SVR",
      subLabel: "Quantum Sim",
      value: -0.0531,
      formattedValue: "-0.0531",
      color: "#f43f5e", // Rose-500 for negative R2
      executionType: "Quantum Simulator",
      notes: "Negative R² indicates predictions are worse than simply predicting the training target mean.",
    },
  ];

  // 6. Full-Cohort Classical Scaffold Validation (5 Seeds, 2,995 Compounds with Error Bars)
  const fiveSplitMaeData = [
    {
      id: "rf_5split",
      label: "Random Forest (2048-bit)",
      shortLabel: "Random Forest",
      subLabel: "Full Cohort (5 Seeds)",
      value: 0.5270,
      errorStd: 0.0672,
      formattedValue: "0.5270",
      color: "#0284c7",
      executionType: "Classical Baseline (5 Seeds Repeated)",
      notes: "Mean MAE: 0.5270 ± 0.0672 across 5 independent Murcko scaffold splits.",
    },
    {
      id: "svr_5split",
      label: "RBF-SVR (128D SVD)",
      shortLabel: "RBF-SVR",
      subLabel: "Full Cohort (5 Seeds)",
      value: 0.5607,
      errorStd: 0.0689,
      formattedValue: "0.5607",
      color: "#0d9488",
      executionType: "Classical Baseline (5 Seeds Repeated)",
      notes: "Mean MAE: 0.5607 ± 0.0689 across 5 independent Murcko scaffold splits.",
    },
  ];

  const fiveSplitRmseData = [
    {
      id: "rf_5split",
      label: "Random Forest (2048-bit)",
      shortLabel: "Random Forest",
      subLabel: "Full Cohort (5 Seeds)",
      value: 0.7286,
      errorStd: 0.0758,
      formattedValue: "0.7286",
      color: "#0284c7",
      executionType: "Classical Baseline (5 Seeds Repeated)",
      notes: "Mean RMSE: 0.7286 ± 0.0758 across 5 independent Murcko scaffold splits.",
    },
    {
      id: "svr_5split",
      label: "RBF-SVR (128D SVD)",
      shortLabel: "RBF-SVR",
      subLabel: "Full Cohort (5 Seeds)",
      value: 0.7609,
      errorStd: 0.0883,
      formattedValue: "0.7609",
      color: "#0d9488",
      executionType: "Classical Baseline (5 Seeds Repeated)",
      notes: "Mean RMSE: 0.7609 ± 0.0883 across 5 independent Murcko scaffold splits.",
    },
  ];

  const fiveSplitR2Data = [
    {
      id: "rf_5split",
      label: "Random Forest (2048-bit)",
      shortLabel: "Random Forest",
      subLabel: "Full Cohort (5 Seeds)",
      value: 0.6386,
      errorStd: 0.0394,
      formattedValue: "0.6386",
      color: "#0284c7",
      executionType: "Classical Baseline (5 Seeds Repeated)",
      notes: "Mean R²: 0.6386 ± 0.0394 across 5 independent Murcko scaffold splits.",
    },
    {
      id: "svr_5split",
      label: "RBF-SVR (128D SVD)",
      shortLabel: "RBF-SVR",
      subLabel: "Full Cohort (5 Seeds)",
      value: 0.6061,
      errorStd: 0.0496,
      formattedValue: "0.6061",
      color: "#0d9488",
      executionType: "Classical Baseline (5 Seeds Repeated)",
      notes: "Mean R²: 0.6061 ± 0.0496 across 5 independent Murcko scaffold splits.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Workspace Section Header & View Selector */}
      <div className="rounded-xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 sm:text-lg">
                Scientific Cartesian Performance Evaluation
              </h3>
              <span className="rounded bg-indigo-100 text-indigo-800 border border-indigo-200 px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase">
                Cartesian X-Y Graphs
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500 max-w-2xl">
              Publication-grade Cartesian plots with numerical axes, tick scales, reference baselines, and sample standard deviation error bars. Evaluates classification and regression separately under rigorous Bemis-Murcko scaffold isolation.
            </p>
          </div>

          {/* Section Filter Pills */}
          <div className="flex flex-wrap items-center gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab("all")}
              className={`rounded-md px-3 py-1 font-semibold transition ${
                activeTab === "all" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All Graphs (8)
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("classification")}
              className={`rounded-md px-3 py-1 font-semibold transition ${
                activeTab === "classification" ? "bg-white text-slate-900 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Classification (2)
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("pilot-regression")}
              className={`rounded-md px-3 py-1 font-semibold transition ${
                activeTab === "pilot-regression" ? "bg-white text-slate-900 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Matched 16D Pilot (3)
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("five-split")}
              className={`rounded-md px-3 py-1 font-semibold transition ${
                activeTab === "five-split" ? "bg-white text-slate-900 shadow-sm font-bold" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Full 5-Split Error Bars (3)
            </button>
          </div>
        </div>

        {/* =========================================================================
            SECTION 1: CLASSIFICATION PERFORMANCE GRAPHS (Balanced Acc & ROC-AUC)
            ========================================================================= */}
        {(activeTab === "all" || activeTab === "classification") && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h4 className="text-sm font-bold text-slate-900">
                  1. Biochemical Activity Classification Performance (Held-Out Test N=311)
                </h4>
                <p className="text-[11px] text-slate-500">
                  Scaffold-disjoint test partition (Seed 42). Compares Classical RBF-SVM against Quantum VQC and Hybrid QGNN simulators.
                </p>
              </div>
              <span className="rounded bg-teal-50 border border-teal-200 text-teal-800 text-[10px] font-bold px-2 py-0.5 uppercase">
                Seed 42 &middot; 4D SVD
              </span>
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              {/* Graph 1: Balanced Accuracy */}
              <CartesianBarChart
                title="Classification Balanced Accuracy (%)"
                subtitle="Accounts for active/inactive imbalance in test cohort (N=311)"
                yAxisTitle="Balanced Accuracy (%)"
                data={classificationBalAccData}
                yMin={0}
                yMax={100}
                yTicks={[0, 20, 40, 60, 80, 100]}
                yFormat={(v) => `${v}%`}
                referenceLines={[
                  { value: 50, label: "50% Random Guess", color: "#f59e0b", strokeDash: "4 3" },
                ]}
                badge="Primary Metric"
              />

              {/* Graph 2: ROC-AUC */}
              <CartesianBarChart
                title="Classification ROC-AUC (Area Under ROC)"
                subtitle="Threshold-independent discriminative performance"
                yAxisTitle="ROC-AUC Score (0–1)"
                data={classificationRocAucData}
                yMin={0.0}
                yMax={1.0}
                yTicks={[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]}
                yFormat={(v) => v.toFixed(1)}
                referenceLines={[
                  { value: 0.5, label: "0.50 Chance", color: "#f59e0b", strokeDash: "4 3" },
                ]}
                badge="Discrimination"
              />
            </div>

            <p className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
              <strong>Training status from the saved run:</strong> VQC convergence was not reported. QGNN reached its maximum of 24 objective evaluations and reports <code>optimizer_success=false</code>.
            </p>

            {/* Hardware Diagnostic Note */}
            <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-3 text-xs flex items-start gap-2.5">
              <svg className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1 text-amber-950 leading-relaxed">
                <strong>IBM Fez QPU Execution Context:</strong> Jobs dbhnetune4hc73bd8h70 (VQC) and dbhm4ntep8hs73amelf0 (QGNN) are separate 256-shot circuit diagnostics, not activity predictions. Their absolute probability divergences from local statevector outputs were 11.28 and approximately 3.0 percentage points, respectively. These hardware measurements are isolated from the held-out molecular activity metrics.
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            SECTION 2: MATCHED 16D PILOT REGRESSION (MAE, RMSE, and R²)
            ========================================================================= */}
        {(activeTab === "all" || activeTab === "pilot-regression") && (
          <div className="mt-8 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h4 className="text-sm font-bold text-slate-900">
                  2. Matched 16D Pilot Biochemical Activity-Proxy Regression (Direct Head-to-Head &middot; N=64 Test)
                </h4>
                <p className="text-[11px] text-slate-500">
                  Curated biochemical IC50 activity-proxy cohort; identical 256 train / 64 validation / 64 test compounds and 16D TruncatedSVD features (Seed 42). This is not validated binding affinity, clinical efficacy, or drug performance.
                </p>
              </div>
              <span className="rounded bg-indigo-50 border border-indigo-200 text-indigo-800 text-[10px] font-bold px-2 py-0.5 uppercase">
                16D PCA Split 42
              </span>
            </div>

            <div className="grid gap-5 md:grid-cols-3">
              {/* Graph 3: MAE */}
              <CartesianBarChart
                title="Matched 16D Pilot MAE (pIC50)"
                subtitle="Mean absolute prediction error"
                yAxisTitle="MAE (pIC50 Points)"
                data={pilotMaeData}
                yMin={0.0}
                yMax={1.2}
                yTicks={[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2]}
                yFormat={(v) => v.toFixed(1)}
                lowerIsBetter
                badge="Error Metric"
              />

              {/* Graph 4: RMSE */}
              <CartesianBarChart
                title="Matched 16D Pilot RMSE (pIC50)"
                subtitle="Root mean squared error (penalizes outliers)"
                yAxisTitle="RMSE (pIC50 Points)"
                data={pilotRmseData}
                yMin={0.0}
                yMax={1.4}
                yTicks={[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]}
                yFormat={(v) => v.toFixed(1)}
                lowerIsBetter
                badge="Outlier Metric"
              />

              {/* Graph 5: R² Score (With Zero Baseline & Negative Bar) */}
              <CartesianBarChart
                title="Matched 16D Pilot R² Score"
                subtitle="Variance explained (Quantum SVR is negative)"
                yAxisTitle="R² Coefficient of Determination"
                data={pilotR2Data}
                yMin={-0.15}
                yMax={0.60}
                yTicks={[-0.10, 0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60]}
                yFormat={(v) => v.toFixed(2)}
                zeroBaseline
                referenceLines={[
                  { value: 0.0, label: "0.0 Mean Baseline", color: "#475569", strokeDash: "1 0" },
                ]}
                badge="Variance Score"
              />
            </div>
          </div>
        )}

        {/* =========================================================================
            SECTION 3: FULL-COHORT CLASSICAL SCAFFOLD VALIDATION (WITH ERROR BARS)
            ========================================================================= */}
        {(activeTab === "all" || activeTab === "five-split") && (
          <div className="mt-8 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div>
                <h4 className="text-sm font-bold text-slate-900">
                  3. Full-Cohort Classical Scaffold Validation (5 Seeds &middot; Mean &plusmn; Sample SD)
                </h4>
                <p className="text-[11px] text-slate-500">
                  Evaluated across 2,995 compounds and 1,129 unique Murcko scaffold groups. T-stems plot exact sample standard deviations across seeds 11, 23, 42, 87, 101.
                </p>
              </div>
              <span className="rounded bg-teal-50 border border-teal-200 text-teal-800 text-[10px] font-bold px-2 py-0.5 uppercase">
                5-Seed Repeated Holdout
              </span>
            </div>

            <div className="grid gap-5 md:grid-cols-3">
              {/* Graph 6A: Full-Cohort MAE with Error Bars */}
              <CartesianBarChart
                title="Full-Cohort 5-Split MAE (pIC50)"
                subtitle="Random Forest: 0.5270 ± 0.0672 | RBF-SVR: 0.5607 ± 0.0689"
                yAxisTitle="MAE (pIC50 Points)"
                data={fiveSplitMaeData}
                yMin={0.0}
                yMax={0.8}
                yTicks={[0.0, 0.2, 0.4, 0.6, 0.8]}
                yFormat={(v) => v.toFixed(1)}
                lowerIsBetter
                badge="5-Seed Mean ± SD"
              />

              {/* Graph 6B: Full-Cohort RMSE with Error Bars */}
              <CartesianBarChart
                title="Full-Cohort 5-Split RMSE (pIC50)"
                subtitle="Random Forest: 0.7286 ± 0.0758 | RBF-SVR: 0.7609 ± 0.0883"
                yAxisTitle="RMSE (pIC50 Points)"
                data={fiveSplitRmseData}
                yMin={0.0}
                yMax={1.0}
                yTicks={[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]}
                yFormat={(v) => v.toFixed(1)}
                lowerIsBetter
                badge="5-Seed Mean ± SD"
              />

              {/* Graph 6C: Full-Cohort R² with Error Bars */}
              <CartesianBarChart
                title="Full-Cohort 5-Split R² Score"
                subtitle="Random Forest: 0.6386 ± 0.0394 | RBF-SVR: 0.6061 ± 0.0496"
                yAxisTitle="R² Coefficient of Determination"
                data={fiveSplitR2Data}
                yMin={0.0}
                yMax={0.8}
                yTicks={[0.0, 0.2, 0.4, 0.6, 0.8]}
                yFormat={(v) => v.toFixed(1)}
                badge="5-Seed Mean ± SD"
              />
            </div>

            <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs text-slate-600 leading-relaxed">
              <strong>Methodological Boundary Disclosure:</strong> The classical five-seed evaluation covers 2,995 eligible compounds and 1,129 Murcko scaffolds; test compound counts vary by seed because scaffold groups differ in size. The separate quantum-kernel pilot uses a curated biochemical activity-proxy cohort with 64 test compounds. No quantum results are available for the five-seed splits. Full-cohort quantum kernel construction is pending; the panels are separated to avoid implying matched cohorts.
            </div>
          </div>
        )}

        {/* =========================================================================
            MANDATORY SCIENTIFIC DISCLOSURE (NO QUANTUM ADVANTAGE)
            ========================================================================= */}
        <div className="mt-8 rounded-xl border border-amber-300 bg-amber-50/80 p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-700 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h4 className="text-sm font-bold text-amber-950">
              Mandatory Scientific Disclosure &amp; Empirical Findings
            </h4>
          </div>

          <div className="text-xs text-amber-950 space-y-2 leading-relaxed">
            <p>
              <strong>1. Scope of These Results:</strong> On the specific EGFR activity-proxy splits shown here, the saved classical models score higher than the tested quantum models in the matched classification and 16D pilot comparisons. The five-seed results are classical-only. These limited experiments do not establish a general ordering between classical and quantum methods, and no quantum advantage is demonstrated.
            </p>
            <p>
              <strong>2. Classification Gap:</strong> On the 311-compound Murcko scaffold-disjoint test partition, Classical RBF-SVM achieved <strong>84.96%</strong> balanced accuracy and <strong>0.9112</strong> ROC-AUC, outperforming the Quantum VQC (<strong>64.79%</strong> balanced accuracy, <strong>0.6605</strong> ROC-AUC) and Quantum QGNN (<strong>59.39%</strong> balanced accuracy, <strong>0.6145</strong> ROC-AUC).
            </p>
            <p>
              <strong>3. Regression Error &amp; Negative R²:</strong> On the 64-compound test portion of the curated biochemical activity-proxy pilot, Random Forest (MAE <strong>0.6166</strong>, R² <strong>0.4872</strong>) and RBF-SVR (MAE <strong>0.6476</strong>, R² <strong>0.3172</strong>) had lower error than Quantum-Kernel SVR (MAE <strong>0.9435</strong>, R² <strong>-0.0531</strong>). The negative R² is below the test-set mean baseline. These scores do not validate binding, clinical efficacy, or drug performance.
            </p>
            <p>
              <strong>4. Hardware Diagnostics Only:</strong> Separate 256-shot circuit diagnostics on <code className="font-mono text-indigo-900 font-bold">ibm_fez</code> showed absolute probability divergence from local statevector outputs of <strong>11.28 percentage points for VQC</strong> and <strong>approximately 3.0 percentage points for QGNN</strong>. These hardware measurements are not the molecular activity benchmark scores above.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
