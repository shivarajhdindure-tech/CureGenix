/** Read held-out metrics and optimizer status from their distinct API branches. */
export function getMolecularActivityModelEvaluation(evaluation, modelKey) {
  return {
    test: evaluation?.metrics?.[modelKey]?.test ?? null,
    trainingStatus: evaluation?.models?.[modelKey]?.training?.status ?? null,
  };
}
