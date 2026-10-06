"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import Header from "@/components/Header";
import Hero from "@/components/Hero";
import UploadPanel from "@/components/UploadPanel";
import { RunningPipeline } from "@/components/AnalysisPipeline";
import ResultsDashboard from "@/components/ResultsDashboard";
import Footer from "@/components/Footer";
import {
  API_URL,
  REQUEST_TIMEOUT_MS,
  deriveResults,
  validatePdb,
} from "@/lib/analysis";

export default function Home() {
  const [file, setFile] = useState(null);
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

  // ---- backend health (real check, GET /api/health) -----------------------
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 90_000); // allow cold start
    fetch(`${API_URL}/api/health`, { signal: controller.signal })
      .then((r) => setEngine(r.ok ? "online" : "offline"))
      .catch(() => setEngine("offline"))
      .finally(() => clearTimeout(timer));
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, []);

  // ---- elapsed timer (wall-clock based, robust to background throttling) --
  useEffect(() => {
    if (phase !== "running") return undefined;
    const start = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed((Date.now() - start) / 1000), 500);
    return () => clearInterval(id);
  }, [phase]);

  // ---- warn before leaving mid-analysis ----------------------------------
  useEffect(() => {
    if (phase !== "running") return undefined;
    const handler = (e) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [phase]);

  // ---- file handling -----------------------------------------------------
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

  // ---- analysis request (same endpoint + payload as before) --------------
  async function runAnalysis() {
    if (!file || validation?.status !== "valid") return;

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
        /* non-JSON body (e.g. proxy error page) */
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

  return (
    <div className="min-h-screen">
      <Header engine={engine} busy={phase === "running"} hasResults={phase === "done"} />

      <main id="analysis" className="mx-auto max-w-7xl scroll-mt-20 px-5 py-10 md:px-8 md:py-14">
        {phase === "done" && derived ? (
          <ResultsDashboard result={result} derived={derived} onReset={resetAll} />
        ) : phase === "running" ? (
          <RunningPipeline elapsedSeconds={elapsed} onCancel={cancelAnalysis} />
        ) : (
          <div className="grid items-center gap-12 lg:grid-cols-[1.15fr_1fr] lg:gap-16">
            <Hero />
            <div className="space-y-4">
              <UploadPanel
                file={file}
                validation={validation}
                onSelect={handleSelect}
                onRemove={handleRemove}
                onStart={runAnalysis}
                disabled={phase === "running"}
              />

              {notice && (
                <p role="status" className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
                  {notice}
                </p>
              )}

              {phase === "error" && (
                <div role="alert" className="rounded-2xl border border-red-400/30 bg-red-500/[0.07] p-5">
                  <h3 className="text-base font-semibold text-red-200">
                    Analysis could not be completed.
                  </h3>
                  <p className="mt-2 break-words text-sm leading-6 text-red-100/80">{error}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={runAnalysis}
                      disabled={!file || validation?.status !== "valid"}
                      className="btn-primary !py-2"
                    >
                      Try Again
                    </button>
                    <button type="button" onClick={handleRemove} className="btn-ghost !py-2">
                      Choose another file
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
