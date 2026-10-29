const displayScoreKey = (value, digits) =>
  Number.isFinite(value) ? value.toFixed(digits) : null;

/** Sort simulated scores and mark equal displayed scores as a shared rank. */
export function rankSimulatedResults(results, digits = 3) {
  const sorted = [...results].sort((a, b) => {
    if (a.adjusted === null) return b.adjusted === null ? 0 : 1;
    if (b.adjusted === null) return -1;
    return b.adjusted - a.adjusted;
  });

  const groups = new Map();
  for (const item of sorted) {
    const key = displayScoreKey(item.adjusted, digits);
    if (key === null) continue;
    groups.set(key, [...(groups.get(key) || []), item]);
  }

  const firstRank = new Map();
  let position = 1;
  for (const item of sorted) {
    const key = displayScoreKey(item.adjusted, digits);
    if (key !== null && !firstRank.has(key)) firstRank.set(key, position);
    position += 1;
  }

  return sorted.map((item) => {
    const key = displayScoreKey(item.adjusted, digits);
    if (key === null) {
      return { ...item, simulatedRank: null, simulatedTie: false, simulatedRankLabel: "Not ranked" };
    }
    const rank = firstRank.get(key);
    const tied = groups.get(key).length > 1;
    return {
      ...item,
      simulatedRank: rank,
      simulatedTie: tied,
      simulatedRankLabel: tied ? `Tie · #${rank}` : `#${rank}`,
    };
  });
}
