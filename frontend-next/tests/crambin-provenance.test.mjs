import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const chartSource = readFileSync(new URL("../components/charts/ScientificCharts.js", import.meta.url), "utf8");
const discoverySource = readFileSync(new URL("../components/workspaces/MoleculeDiscoveryWorkspace.js", import.meta.url), "utf8");
const analysisSource = readFileSync(new URL("../lib/analysis.js", import.meta.url), "utf8");

test("candidate screening chart renders an honest empty state without demo candidates", () => {
  assert.match(chartSource, /candidatePool\.length === 0/);
  assert.match(chartSource, /No primary candidates were returned for this target/);
  assert.doesNotMatch(chartSource, /CAN-003|Pyrazolopyrimidine/);
});

test("discovery workspace keeps demonstration candidates separate from primary candidates", () => {
  assert.match(discoverySource, /CandidateScreeningComparisonChart candidates=\{candidates\}/);
  assert.match(discoverySource, /demonstrationCandidates/);
  assert.match(analysisSource, /demonstrationCandidates/);
  assert.match(analysisSource, /category === "mock"/);
});
