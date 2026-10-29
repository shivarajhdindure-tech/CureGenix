const scoreKey = (value) =>
  typeof value === "number" && Number.isFinite(value) ? value.toFixed(3) : null;

/** Mark display-equivalent score ties without changing scores or backend ranks. */
export function deriveCandidateTieDisplay(candidates, bestNovelId) {
  const groups = new Map();
  for (const candidate of candidates) {
    const key = scoreKey(candidate.adjustedScore);
    if (key === null) continue;
    groups.set(key, [...(groups.get(key) || []), candidate]);
  }

  const highlightedNovel = candidates.find(
    (candidate) => candidate.id === bestNovelId && candidate.isNovel,
  );
  const highlightedKey = scoreKey(highlightedNovel?.adjustedScore);
  const tiedBestNovelCandidates = highlightedKey === null
    ? []
    : candidates.filter(
        (candidate) => candidate.isNovel && scoreKey(candidate.adjustedScore) === highlightedKey,
      );
  const bestNovelIsTie = tiedBestNovelCandidates.length > 1;
  const tiedBestIds = new Set(tiedBestNovelCandidates.map((candidate) => candidate.id));

  const annotatedCandidates = candidates.map((candidate) => {
    const key = scoreKey(candidate.adjustedScore);
    const tied = key !== null && (groups.get(key)?.length || 0) > 1;
    return {
      ...candidate,
      scoreTie: tied,
      scoreTieCount: tied ? groups.get(key).length : 1,
      isBestNovel: !bestNovelIsTie && candidate.id === highlightedNovel?.id,
      isBestNovelTie: bestNovelIsTie && tiedBestIds.has(candidate.id),
    };
  });

  const bestNovelCandidates = bestNovelIsTie
    ? annotatedCandidates.filter((candidate) => tiedBestIds.has(candidate.id))
    : annotatedCandidates.filter((candidate) => candidate.id === highlightedNovel?.id);
  const bestNovel = bestNovelIsTie ? null : bestNovelCandidates[0] || null;

  const topKey = [...groups.keys()].sort((a, b) => Number(b) - Number(a))[0] || null;
  const topScoreCandidates = topKey === null ? [] : annotatedCandidates.filter(
    (candidate) => scoreKey(candidate.adjustedScore) === topKey,
  );

  return {
    candidates: annotatedCandidates,
    bestNovel,
    bestNovelCandidates,
    bestNovelIsTie,
    bestNovelId: bestNovel?.id || null,
    bestNovelScore: bestNovelCandidates[0]?.adjustedScore ?? null,
    hasScoreTies: [...groups.values()].some((group) => group.length > 1),
    topScoreIsTie: topScoreCandidates.length > 1,
    topScoreCandidateIds: topScoreCandidates.map((candidate) => candidate.id),
  };
}

/** Disclosure for the case where candidates have no VQE result after skips. */
export function getNoVqeResourceSkipDisclosure({
  candidateCount = 0,
  vqeCount = 0,
  skippedCount = 0,
}) {
  if (candidateCount < 1 || vqeCount > 0 || skippedCount < 1) return null;
  return {
    title: "No VQE-derived molecular result was obtained in this run",
    body: `${skippedCount} candidate${skippedCount === 1 ? " was" : "s were"} skipped by the configured resource policy. Candidate scores use the separate screening and rule-based risk scoring path; they do not include VQE energies or descriptors and are not evidence of a successful quantum calculation.`,
  };
}
