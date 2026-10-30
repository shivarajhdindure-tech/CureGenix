import test from "node:test";
import assert from "node:assert/strict";
import { isIdealSimulatorStatevector, sortStatevectorProbabilities } from "../lib/statevectorDisplay.mjs";

test("statevector display accepts only ideal simulator results, not hardware output", () => {
  const simulatorResult = {
    execution_type: "ideal_statevector_simulation",
    hardware_execution: false,
    qubit_count: 1,
    statevector_dimension: 2,
    states: [{ basis_state: "0", probability: 1 }, { basis_state: "1", probability: 0 }],
  };
  assert.equal(isIdealSimulatorStatevector(simulatorResult), true);
  assert.equal(isIdealSimulatorStatevector({ ...simulatorResult, hardware_execution: true }), false);
  assert.equal(isIdealSimulatorStatevector({ ...simulatorResult, execution_type: "hardware_measurement_probabilities" }), false);
  assert.equal(isIdealSimulatorStatevector({ ...simulatorResult, states: [] }), false);
});

test("basis-state probabilities sort largest first with deterministic ties", () => {
  const states = [
    { basis_state: "01", probability: 0.2 },
    { basis_state: "10", probability: 0.6 },
    { basis_state: "00", probability: 0.2 },
  ];
  assert.deepEqual(sortStatevectorProbabilities(states).map((state) => state.basis_state), ["10", "00", "01"]);
});
