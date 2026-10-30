import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { getQuantumCalculationDisplay } from "../lib/quantumCalculationDisplay.mjs";

test("completed Evidence Passport values come only from the backend job result", () => {
  const candidate = { id: "GEN-A", quantumState: "resource_skipped", quantum: { message: "too large" } };
  const job = {
    job_id: "molecular-123", experiment_record_id: "molecular-123", status: "completed",
    result: { homo_lumo_gap_hartree: 0.4, vqe: { electronic_energy_hartree: -2.1 } },
  };
  const display = getQuantumCalculationDisplay(candidate, job);
  assert.equal(display.status, "completed");
  assert.equal(display.quantum, job.result);
  assert.equal(display.quantum.vqe.electronic_energy_hartree, -2.1);
  assert.equal(display.experimentRecordId, "molecular-123");
});

test("running, failed and skipped jobs never expose stale or fabricated VQE metrics", () => {
  const candidate = { id: "GEN-A", quantumState: "resource_skipped", quantum: { message: "oversized", vqe: null } };
  for (const status of ["queued", "running", "failed", "skipped"]) {
    const result = status === "skipped" ? { message: "Explicit resource policy skip." } : { status: "failed" };
    const display = getQuantumCalculationDisplay(candidate, { status, result });
    assert.equal(display.status, status);
    assert.equal(display.quantum, null);
  }
  assert.match(getQuantumCalculationDisplay(candidate, { status: "skipped", result: { message: "Oversized by explicit policy." } }).message, /Oversized/);
});

test("Evidence Passport submits explicitly, shows running state and polls backend status", () => {
  const source = readFileSync(new URL("../components/EvidencePassport.js", import.meta.url), "utf8");
  assert.match(source, /setQuantumJob\(\{ status: "queued" \}\)/);
  assert.match(source, /\/api\/quantum-calculations/);
  assert.match(source, /disabled=\{quantumBusy\}/);
  assert.match(source, /Running quantum calculation/);
  assert.match(source, /\["completed", "failed", "skipped"\]/);
});

