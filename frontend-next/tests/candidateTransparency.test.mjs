import assert from "node:assert/strict";
import test from "node:test";

import {
  deriveCandidateTieDisplay,
  getNoVqeResourceSkipDisclosure,
} from "../lib/candidateTransparency.mjs";

test("equal adjusted scores display as a tie without choosing a best novel candidate", () => {
  const candidates = [
    { id: "GEN-A", category: "novel", isNovel: true, adjustedScore: 0.81, rank: 1, isBestNovel: true },
    { id: "GEN-B", category: "novel", isNovel: true, adjustedScore: 0.81, rank: 2, isBestNovel: false },
  ];
  const result = deriveCandidateTieDisplay(candidates, "GEN-A");

  assert.deepEqual(result.candidates.map((candidate) => candidate.id), ["GEN-A", "GEN-B"]);
  assert.deepEqual(result.candidates.map((candidate) => candidate.adjustedScore), [0.81, 0.81]);
  assert.ok(result.candidates.every((candidate) => candidate.scoreTie));
  assert.ok(result.candidates.every((candidate) => candidate.isBestNovelTie));
  assert.ok(result.candidates.every((candidate) => !candidate.isBestNovel));
  assert.equal(result.bestNovel, null);
  assert.equal(result.bestNovelId, null);
  assert.deepEqual(result.bestNovelCandidates.map((candidate) => candidate.id), ["GEN-A", "GEN-B"]);
  assert.deepEqual(result.topScoreCandidateIds, ["GEN-A", "GEN-B"]);
});

test("a unique top novel candidate retains its existing featured status", () => {
  const candidates = [
    { id: "GEN-A", isNovel: true, adjustedScore: 0.81 },
    { id: "GEN-B", isNovel: true, adjustedScore: 0.79 },
  ];
  const result = deriveCandidateTieDisplay(candidates, "GEN-A");
  assert.equal(result.bestNovel.id, "GEN-A");
  assert.equal(result.candidates[0].isBestNovel, true);
  assert.equal(result.candidates[0].scoreTie, false);
});

test("all-skipped quantum run explicitly discloses absence of VQE results and score independence", () => {
  const notice = getNoVqeResourceSkipDisclosure({ candidateCount: 2, vqeCount: 0, skippedCount: 2 });
  assert.match(notice.title, /No VQE-derived molecular result/);
  assert.match(notice.body, /2 candidates were skipped/);
  assert.match(notice.body, /do not include VQE energies or descriptors/);
  assert.match(notice.body, /not evidence of a successful quantum calculation/);
  assert.equal(getNoVqeResourceSkipDisclosure({ candidateCount: 2, vqeCount: 1, skippedCount: 1 }), null);
});
