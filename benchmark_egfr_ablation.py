import json
import numpy as np
from pathlib import Path

from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

root = Path("benchmark_reports/egfr_regression")
data = np.load(root / "fingerprints_and_targets.npz", allow_pickle=False)
X, y, splits = data["X"], data["y"], data["splits"]

tr = np.flatnonzero(splits == "train")
va = np.flatnonzero(splits == "validation")
te = np.flatnonzero(splits == "test")

def metrics(actual, pred):
    return {
        "mae": float(mean_absolute_error(actual, pred)),
        "rmse": float(np.sqrt(mean_squared_error(actual, pred))),
        "r2": float(r2_score(actual, pred)),
    }

results = {}

# Full-fingerprint classical RBF SVR.
full = make_pipeline(StandardScaler(), SVR(C=10, epsilon=0.2))
full.fit(X[tr], y[tr])
results["full_fingerprint_rbf_svr"] = {
    "validation": metrics(y[va], full.predict(X[va])),
    "test": metrics(y[te], full.predict(X[te])),
}

# Same four-feature representation used in the quantum experiment.
svd = TruncatedSVD(n_components=4, random_state=42)
Xtr = svd.fit_transform(X[tr])
Xva = svd.transform(X[va])
Xte = svd.transform(X[te])

scaled_svr = make_pipeline(StandardScaler(), SVR(C=10, epsilon=0.2))
scaled_svr.fit(Xtr, y[tr])
results["four_feature_rbf_svr"] = {
    "validation": metrics(y[va], scaled_svr.predict(Xva)),
    "test": metrics(y[te], scaled_svr.predict(Xte)),
}

# Random Forest on the same four features.
rf = RandomForestRegressor(
    n_estimators=400, min_samples_leaf=2, max_features=0.7,
    random_state=42, n_jobs=-1
)
rf.fit(Xtr, y[tr])
results["four_feature_random_forest"] = {
    "validation": metrics(y[va], rf.predict(Xva)),
    "test": metrics(y[te], rf.predict(Xte)),
}

results["svd_explained_variance_ratio_sum"] = float(
    svd.explained_variance_ratio_.sum()
)

out = root / "ablation_results.json"
out.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
print("\nSaved:", out)
