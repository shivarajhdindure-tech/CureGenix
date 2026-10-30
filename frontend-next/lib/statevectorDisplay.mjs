export function isIdealSimulatorStatevector(value) {
  return value?.execution_type === "ideal_statevector_simulation"
    && value?.hardware_execution === false
    && Number.isInteger(value?.qubit_count)
    && Number.isInteger(value?.statevector_dimension)
    && Array.isArray(value?.states)
    && value.states.length === value.statevector_dimension;
}

export function sortStatevectorProbabilities(states) {
  if (!Array.isArray(states)) return [];
  return [...states].sort((left, right) => {
    const probabilityDifference = Number(right?.probability) - Number(left?.probability);
    return probabilityDifference || String(left?.basis_state).localeCompare(String(right?.basis_state));
  });
}
