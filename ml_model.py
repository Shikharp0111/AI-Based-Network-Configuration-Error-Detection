import numpy as np
from sklearn.ensemble import RandomForestClassifier

FEATURES = ["ip_issue", "duplicate_ip", "gateway_issue", "link_down",
            "acl_issue", "disabled_host", "issue_count"]

def train_demo_model():
    """Synthetic training data demonstrates the ML pipeline; it is not real-world validation."""
    rng = np.random.default_rng(23)
    X, y = [], []
    for _ in range(2400):
        ip, dup, gw, link, acl, disabled = [int(rng.random() < p)
            for p in (0.12, 0.06, 0.14, 0.13, 0.12, 0.04)]
        count = ip + dup + gw + link + acl + disabled
        risky = int(dup or ip or link or (gw and count >= 2) or acl or count >= 3)
        X.append([ip, dup, gw, link, acl, disabled, count])
        y.append(risky)
    model = RandomForestClassifier(n_estimators=140, max_depth=8,
                                   class_weight="balanced", random_state=23)
    return model.fit(np.asarray(X), np.asarray(y))

def predict_risk(model, features):
    p = float(model.predict_proba([[features[k] for k in FEATURES]])[0][1])
    label = "High" if p >= .70 else ("Moderate" if p >= .35 else "Low")
    return label, p
