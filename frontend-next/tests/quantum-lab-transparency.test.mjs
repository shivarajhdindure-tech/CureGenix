import test from "node:test";
import assert from "node:assert/strict";
import { optimizerStatusLabel, QUANTUM_RESOURCE_DEFAULTS } from "../lib/quantumLabTransparency.mjs";

test("optimizer status distinguishes explicit outcomes from unavailable status", () => {
  assert.equal(optimizerStatusLabel(true), "optimizer reports success");
  assert.equal(optimizerStatusLabel(false), "optimizer reports unsuccessful termination");
  assert.equal(optimizerStatusLabel(undefined), "convergence status unavailable");
  assert.equal(optimizerStatusLabel(null), "convergence status unavailable");
});

test("Quantum Lab displayed resource defaults match backend policy and adapters", () => {
  assert.deepEqual(QUANTUM_RESOURCE_DEFAULTS, {
    maxHeavyAtoms: 20,
    maxTotalAtoms: 80,
    maxEstimatedBasisFunctions: 100,
    maxVqeIterations: 100,
    genericDefaultIterations: 50,
    wslTimeoutSeconds: 180,
    h2oSimulatorTimeoutSeconds: 3600,
  });
});
