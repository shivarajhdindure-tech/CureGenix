"use client";

import { useMemo, useState } from "react";
import { rankSimulatedResults } from "@/lib/simulatorRanking.mjs";

const DEFAULT_WEIGHTS = {
  drug_likeness: 25,
  bbb_permeability: 20,
  potency_proxy: 30,
  toxicity_freedom: 25,
};

const METRICS = [
  { key: "drug_likeness", label: "Drug-likeness" },
  { key: "bbb_permeability", label: "BBB permeability" },
  { key: "potency_proxy", label: "Potency proxy" },
  { key: "toxicity_freedom", label: "Toxicity freedom" },
];

const RISK_PENALTIES = {
  low: 0,
  medium: 0.08,
  high: 0.2,
};

function getMetric(candidate, key) {
  const screening = candidate.screening || {};

  if (key === "toxicity_freedom") {
    const penalty = screening.toxicity_penalty;

    return Number.isFinite(penalty)
      ? Math.max(0, Math.min(1, 1 - penalty))
      : null;
  }

  const value = screening[key];

  return Number.isFinite(value)
    ? Math.max(0, Math.min(1, value))
    : null;
}

function getRiskPenalty(candidate) {
  const risk = String(candidate.riskLevel || "").toLowerCase();

  return Object.prototype.hasOwnProperty.call(RISK_PENALTIES, risk)
    ? RISK_PENALTIES[risk]
    : 0.1;
}

function formatScore(value) {
  return Number.isFinite(value) ? value.toFixed(3) : "—";
}

function normalizeWeights(weights) {
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);

  if (total <= 0) {
    return { ...DEFAULT_WEIGHTS };
  }

  return Object.fromEntries(
    Object.entries(weights).map(([key, value]) => [
      key,
      (value / total) * 100,
    ]),
  );
}

function calculateScore(candidate, weights) {
  let weightedSum = 0;
  let availableWeight = 0;

  for (const metric of METRICS) {
    const value = getMetric(candidate, metric.key);

    if (value === null) continue;

    const weight = weights[metric.key] / 100;
    weightedSum += value * weight;
    availableWeight += weight;
  }

  if (availableWeight === 0) {
    return {
      composite: null,
      adjusted: null,
      riskPenalty: getRiskPenalty(candidate),
      availableMetrics: 0,
    };
  }

  // Renormalize over available metrics instead of treating missing data as zero.
  const composite = weightedSum / availableWeight;
  const riskPenalty = getRiskPenalty(candidate);

  return {
    composite,
    adjusted: composite - riskPenalty,
    riskPenalty,
    availableMetrics: METRICS.filter(
      (metric) => getMetric(candidate, metric.key) !== null,
    ).length,
  };
}

export default function DiscoveryStrategySimulator({ candidates = [] }) {
  const [weights, setWeights] = useState({ ...DEFAULT_WEIGHTS });

  const normalizedWeights = useMemo(
    () => normalizeWeights(weights),
    [weights],
  );

  const results = useMemo(() => {
    const scored = candidates.map((candidate) => {
      const originalScore = Number.isFinite(candidate.adjustedScore)
        ? candidate.adjustedScore
        : null;

      const simulated = calculateScore(candidate, normalizedWeights);

      return {
        candidate,
        originalScore,
        ...simulated,
      };
    });
    return rankSimulatedResults(scored, 3);
  }, [candidates, normalizedWeights]);

  const weightTotal = Object.values(weights).reduce(
    (sum, value) => sum + value,
    0,
  );

  function updateWeight(key, value) {
    setWeights((current) => ({ ...current, [key]: Number(value) }));
  }

  return (
    <section
      id="strategy-simulator"
      className="panel space-y-6 p-5 sm:p-6"
    >
      <div>
        <p className="eyebrow !text-cyan-300/80">Interactive decision lab</p>
        <h2 className="mt-2 text-xl font-semibold text-white sm:text-2xl">
          Discovery Strategy Simulator
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Explore how different screening priorities change computational
          candidate rankings. This simulation does not rerun molecular
          calculations or establish safety, target binding, or drug efficacy.
        </p>
      </div>

      <div className="rounded-lg border border-amber-400/20 bg-amber-400/[0.05] p-3 text-xs leading-5 text-amber-100/80">
          Hypothetical prioritization only. Simulated scores and ranks are based
          on your selected heuristic weights; original pipeline ranks remain
          separate. Changing weights does not validate the scoring model.
      </div>

      <div className="space-y-5">
        {METRICS.map((metric) => (
          <div key={metric.key}>
            <div className="mb-2 flex items-center justify-between gap-3">
              <label
                htmlFor={`strategy-${metric.key}`}
                className="text-sm text-slate-200"
              >
                {metric.label}
              </label>
              <span className="font-data text-sm text-cyan-200">
                {weights[metric.key]}%
              </span>
            </div>

            <input
              id={`strategy-${metric.key}`}
              type="range"
              min="0"
              max="100"
              step="5"
              value={weights[metric.key]}
              onChange={(event) =>
                updateWeight(metric.key, event.target.value)
              }
              className="w-full accent-cyan-400"
            />
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.08] pt-4">
        <div>
          <p className="text-sm text-slate-300">
            Raw weight total:{" "}
            <span className="font-data text-white">{weightTotal}%</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Weights are normalized automatically for scoring.
          </p>
        </div>

        <button
          type="button"
          className="btn-ghost"
          onClick={() => setWeights({ ...DEFAULT_WEIGHTS })}
        >
          Reset weights
        </button>
      </div>

      <div>
        <h3 className="text-base font-semibold text-white">
          Simulated ranking
        </h3>
        <p className="mt-1 text-xs leading-5 text-slate-500">
          Original score is the pipeline's adjusted score. Simulated score
          uses the selected weights and the existing risk-level penalty.
          Missing screening metrics are excluded and remaining weights are
          renormalized. Equal scores at displayed precision are shown as ties.
        </p>
      </div>

      {results.length === 0 ? (
        <p className="text-sm text-slate-400">
          Run an analysis to populate the simulator with candidates.
        </p>
      ) : (
        <div className="space-y-3">
          {results.some((item) => item.simulatedTie) && (
            <p role="note" className="rounded-lg border border-sky-400/20 bg-sky-400/[0.05] p-3 text-xs text-sky-100/90">
              Candidates with the same simulated score to three decimals share a simulated rank; their display order does not imply superiority.
            </p>
          )}
          {results.map((item) => {
            const { candidate } = item;
            const moved =
              !candidate.scoreTie &&
              !item.simulatedTie &&
              Number.isFinite(candidate.rank) &&
              item.simulatedRank !== null
                ? candidate.rank - item.simulatedRank
                : null;

            return (
              <article
                key={candidate.id}
                className="rounded-lg border border-white/[0.08] bg-white/[0.02] p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{candidate.id}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {candidate.category || "Uncategorized"}
                      {" · "}
                      {candidate.verificationStatus === "verified" &&
                      candidate.targetAssociationVerified
                        ? "Verification status reported complete"
                        : "Unverified"}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="font-data text-lg text-cyan-200">
                      {formatScore(item.adjusted)}
                    </p>
            <p className="text-xs text-slate-500">Hypothetical score</p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <div>
                    <p className="metric-label">Simulated rank · hypothetical</p>
                    <p className="mt-1 font-data text-sm text-white">
                      {item.simulatedRankLabel}
                    </p>
                  </div>

                  <div>
                    <p className="metric-label">Original rank</p>
                    <p className="mt-1 font-data text-sm text-white">
                      {candidate.scoreTie
                        ? "Tie"
                        : Number.isFinite(candidate.rank)
                        ? `#${candidate.rank}`
                        : "—"}
                    </p>
                  </div>

                  <div>
                    <p className="metric-label">Original score</p>
                    <p className="mt-1 font-data text-sm text-white">
                      {formatScore(item.originalScore)}
                    </p>
                  </div>

                  <div>
                    <p className="metric-label">Risk penalty</p>
                    <p className="mt-1 font-data text-sm text-white">
                      {formatScore(item.riskPenalty)}
                    </p>
                  </div>
                </div>

                {moved !== null && moved !== 0 && (
                  <p className="mt-3 text-xs text-cyan-200">
                    {moved > 0
                      ? `Moved up ${moved} position${moved === 1 ? "" : "s"}`
                      : `Moved down ${Math.abs(moved)} position${moved === -1 ? "" : "s"}`}
                    {" "}under the simulated priorities.
                  </p>
                )}

                {item.availableMetrics < METRICS.length && (
                  <p className="mt-2 text-xs text-amber-200/80">
                    Only {item.availableMetrics} of {METRICS.length} screening
                    metrics were available for this candidate.
                  </p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
