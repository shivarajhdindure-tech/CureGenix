export const QUANTUM_RESOURCE_DEFAULTS = Object.freeze({
  maxHeavyAtoms: 20,
  maxTotalAtoms: 80,
  maxEstimatedBasisFunctions: 100,
  maxVqeIterations: 100,
  genericDefaultIterations: 50,
  wslTimeoutSeconds: 180,
  h2oSimulatorTimeoutSeconds: 3600,
});

export function optimizerStatusLabel(success) {
  if (success === true) return "optimizer reports success";
  if (success === false) return "optimizer reports unsuccessful termination";
  return "convergence status unavailable";
}
