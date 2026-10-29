import json
import time
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

root = Path("benchmark_reports/egfr_regression")
data = np.load(root / "fingerprints_and_targets.npz", allow_pickle=False)
X, y, splits = data["X"], data["y"], data["splits"]

train = np.flatnonzero(splits == "train")
val = np.flatnonzero(splits == "validation")
test = np.flatnonzero(splits == "test")

def metrics(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }

results = {}
for n_components in (4, 8, 16):
    start = time.perf_counter()

    reducer = TruncatedSVD(n_components=n_components, random_state=42)
    X_train = reducer.fit_transform(X[train])
    X_val = reducer.transform(X[val])
    X_test = reducer.transform(X[test])

    model = make_pipeline(
        StandardScaler(),
        SVR(C=10.0, epsilon=0.2, gamma="scale"),
    )
    model.fit(X_train, y[train])

    results[str(n_components)] = {
        "components": n_components,
        "explained_variance_ratio_sum": float(
            reducer.explained_variance_ratio_.sum()
        ),
        "validation": metrics(y[val], model.predict(X_val)),
        "test_diagnostic_only": metrics(y[test], model.predict(X_test)),
        "runtime_seconds": round(time.perf_counter() - start, 2),
    }

    print(
        f"{n_components} features: "
        f"validation MAE={results[str(n_components)]['validation']['mae']:.4f}, "
        f"variance={results[str(n_components)]['explained_variance_ratio_sum']:.3f}"
    )

# Select solely by validation MAE. Test values are recorded for diagnostics,
# but must not be used to choose a feature dimension.
best = min(results, key=lambda k: results[k]["validation"]["mae"])

output = {
    "experiment": "EGFR classical dimensionality sweep",
    "seed": 42,
    "selection_metric": "validation MAE",
    "selected_components": int(best),
    "results": results,
    "warning": (
        "Test metrics are diagnostic only and must not guide selection. "
        "This sweep uses one fixed SVR configuration and one seed."
    ),
}
path = root / "dimension_sweep_results.json"
path.write_text(json.dumps(output, indent=2), encoding="utf-8")

print("\nSelected dimension from validation:", best)
print("Saved:", path)
print(json.dumps(output, indent=2))
