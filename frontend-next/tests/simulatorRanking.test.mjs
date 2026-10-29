import assert from "node:assert/strict";
import test from "node:test";

import { rankSimulatedResults } from "../lib/simulatorRanking.mjs";

test("equal simulated scores at displayed precision share one hypothetical rank", () => {
  const ranked = rankSimulatedResults([
    { candidate: { id: "GEN-46D3EFE3", rank: 1, scoreTie: true }, adjusted: 0.8101 },
    { candidate: { id: "GEN-5B0A564F", rank: 2, scoreTie: true }, adjusted: 0.8102 },
    { candidate: { id: "GEN-LOW" }, adjusted: 0.7000 },
  ]);

  assert.deepEqual(ranked.slice(0, 2).map((item) => item.candidate.id), [
    "GEN-5B0A564F",
    "GEN-46D3EFE3",
  ]);
  assert.deepEqual(ranked.slice(0, 2).map((item) => item.simulatedRank), [1, 1]);
  assert.deepEqual(ranked.slice(0, 2).map((item) => item.simulatedRankLabel), [
    "Tie · #1",
    "Tie · #1",
  ]);
  assert.ok(ranked.slice(0, 2).every((item) => item.simulatedTie));
  assert.deepEqual(ranked.slice(0, 2).map((item) => item.candidate.rank), [2, 1]);
  assert.equal(ranked[2].simulatedRank, 3);
  assert.equal(ranked[2].simulatedTie, false);
});

test("genuinely different displayed scores retain descending simulated ranks", () => {
  const ranked = rankSimulatedResults([
    { candidate: { id: "LOW" }, adjusted: 0.701 },
    { candidate: { id: "HIGH" }, adjusted: 0.812 },
  ]);

  assert.deepEqual(ranked.map((item) => item.candidate.id), ["HIGH", "LOW"]);
  assert.deepEqual(ranked.map((item) => item.simulatedRankLabel), ["#1", "#2"]);
  assert.ok(ranked.every((item) => !item.simulatedTie));
});
