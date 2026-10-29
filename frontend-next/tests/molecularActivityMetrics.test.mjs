import assert from "node:assert/strict";
import test from "node:test";

import { getMolecularActivityModelEvaluation } from "../lib/molecularActivityMetrics.mjs";

test("maps held-out metrics and training statuses from their API branches", () => {
  const response = {
    models: {
      vqc: { training: { status: "success" } },
      qgnn: { training: { status: "completed_max_evaluations" } },
      classical_rbf_svm: { training_runtime_seconds: 0.0022 },
    },
    metrics: {
      vqc: { test: { balanced_accuracy: 0.6478688524590164, roc_auc: 0.6604918032786885 } },
      qgnn: { test: { balanced_accuracy: 0.5938688524590163, roc_auc: 0.6144918032786886 } },
      classical_rbf_svm: { test: { balanced_accuracy: 0.8496065573770492, roc_auc: 0.9112131147540983 } },
    },
  };

  assert.deepEqual(getMolecularActivityModelEvaluation(response, "vqc"), {
    test: response.metrics.vqc.test,
    trainingStatus: "success",
  });
  assert.deepEqual(getMolecularActivityModelEvaluation(response, "qgnn"), {
    test: response.metrics.qgnn.test,
    trainingStatus: "completed_max_evaluations",
  });
  assert.deepEqual(getMolecularActivityModelEvaluation(response, "classical_rbf_svm"), {
    test: response.metrics.classical_rbf_svm.test,
    trainingStatus: null,
  });
});

test("missing evaluation data stays explicitly absent", () => {
  assert.deepEqual(getMolecularActivityModelEvaluation(null, "qgnn"), {
    test: null,
    trainingStatus: null,
  });
});
