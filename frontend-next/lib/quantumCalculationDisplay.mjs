export function getQuantumCalculationDisplay(candidate, job) {
  const result = job?.status === "completed" ? job.result : null;
  const quantum = result || (candidate?.quantumState === "vqe" ? candidate.quantum : null);
  const isTerminalJob = ["failed", "skipped"].includes(job?.status);
  const eligibilityReasons = job
    ? (job.result?.resource_eligibility?.reasons || [])
    : (candidate?.quantum?.resource_eligibility?.reasons || []);
  return {
    quantum,
    status: job?.status || (candidate?.quantumState === "resource_skipped" ? "skipped" : candidate?.quantumState || "not_run"),
    message: job ? (isTerminalJob ? (job.result?.message || "") : "") : (candidate?.quantum?.message || ""),
    eligibilityReasons,
    experimentRecordId: job?.experiment_record_id || job?.job_id || null,
  };
}

