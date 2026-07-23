"""IEEE-CIS Fraud Detection dataset loader.

Supports two modes:
  1. Local CSV files (fast, offline) — user downloads from Kaggle manually
  2. Kaggle API download via kagglehub (auth required)

Interface is a single function returning a dict so users can swap in
any dataset by writing their own loader with the same return shape.
"""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd


def load_ieee_cis(
    data_dir: str | Path,
    kaggle_auth: bool = False,
    sample_frac: float = 1.0,
    random_state: int = 42,
) -> dict:
    """Load and preprocess the IEEE-CIS Fraud Detection dataset.

    Args:
        data_dir: Directory containing CSV files (train_transaction.csv,
                  train_identity.csv, test_transaction.csv, test_identity.csv)
                  OR the Kaggle download path.
        kaggle_auth: If True, download via kagglehub (requires internet + auth).
        sample_frac: Fraction of rows to sample (for quick testing).
        random_state: Random seed for sampling.

    Returns:
        dict with keys:
          'X_train': ndarray (n_train, n_features)
          'y_train': ndarray (n_train,) — 1 = fraud, 0 = legitimate
          'X_test':  ndarray (n_test, n_features)
          'y_test':  ndarray (n_test,)
          'feature_names': list of column names used
          'n_features': int
    """
    data_dir = Path(data_dir)

    if kaggle_auth:
        data_dir = _download_kaggle(data_dir)

    # ── Load CSVs ──
    train_trans = pd.read_csv(data_dir / "train_transaction.csv")
    train_identity = pd.read_csv(data_dir / "train_identity.csv")
    test_trans = pd.read_csv(data_dir / "test_transaction.csv")

    # Merge transaction + identity on TransactionID (left join — identity is sparse)
    train = train_trans.merge(train_identity, on="TransactionID", how="left")
    test = test_trans  # test has no identity table in IEEE-CIS

    # ── Sample (for quick iteration) ──
    if sample_frac < 1.0:
        train = train.sample(frac=sample_frac, random_state=random_state)

    # ── Separate features and target ──
    y_train = train["isFraud"].values.astype(np.float32)
    train = train.drop(columns=["isFraud", "TransactionID"])

    X_test = test.drop(columns=["TransactionID"]).values.astype(np.float32)

    # ── Basic preprocessing ──
    from sklearn.preprocessing import StandardScaler

    # Select numeric columns (exclude object/categorical for now)
    numeric_cols = train.select_dtypes(include=[np.number]).columns
    train_numeric = train[numeric_cols].fillna(0).values.astype(np.float32)
    X_test_numeric = X_test[:, :len(numeric_cols)]  # align columns

    scaler = StandardScaler()
    X_train = scaler.fit_transform(train_numeric)
    X_test = scaler.transform(X_test_numeric[:, :X_train.shape[1]])

    print(f"  Loaded IEEE-CIS: {X_train.shape[0]} train, {X_test.shape[0]} test, "
          f"{X_train.shape[1]} features")
    print(f"  Fraud rate: {y_train.mean():.4f} ({y_train.sum()}/{len(y_train)})")

    return {
        "X_train": X_train,
        "y_train": y_train,
        "X_test": X_test,
        "y_test": np.zeros(len(X_test), dtype=np.float32),  # test has no labels
        "feature_names": list(numeric_cols),
        "n_features": X_train.shape[1],
    }


def _download_kaggle(target_dir: Path) -> Path:
    """Download IEEE-CIS via kagglehub."""
    try:
        import kagglehub
    except ImportError:
        raise ImportError(
            "kagglehub not installed. Run: pip install kagglehub\n"
            "Then set up Kaggle API credentials:\n"
            "  1. Download kaggle.json from https://www.kaggle.com/settings\n"
            "  2. Place in ~/.kaggle/kaggle.json"
        )
    path = kagglehub.dataset_download("kaggle/ieee-fraud-detection")
    return Path(path)


# ── Stub for easy modification ──
# To use a different dataset, write a function with the same return shape:
#
#   def load_my_dataset(data_dir: str) -> dict:
#       ...
#       return {"X_train": ..., "y_train": ..., "X_test": ..., "y_test": ...,
#               "feature_names": ..., "n_features": ...}


def load_synthetic(n_samples: int = 5000, n_features: int = 30, seed: int = 42):
    """Generate synthetic fraud-like data for testing without IEEE-CIS.

    Produces imbalanced binary classification data with ~3% fraud rate.
    """
    rng = np.random.RandomState(seed)
    n_fraud = int(n_samples * 0.03)
    n_legit = n_samples - n_fraud

    X_legit = rng.randn(n_legit, n_features).astype(np.float32)
    X_fraud = rng.randn(n_fraud, n_features).astype(np.float32) + 2.0

    X = np.vstack([X_legit, X_fraud])
    y = np.zeros(n_samples, dtype=np.float32)
    y[n_legit:] = 1.0

    # Shuffle
    idx = rng.permutation(n_samples)
    X, y = X[idx], y[idx]

    print(f"  Generated synthetic: {n_samples} samples, {n_features} features, "
          f"fraud rate {y.mean():.4f}")
    return {
        "X_train": X[:n_samples * 3 // 4],
        "y_train": y[:n_samples * 3 // 4],
        "X_test": X[n_samples * 3 // 4:],
        "y_test": y[n_samples * 3 // 4:],
        "feature_names": [f"f{i}" for i in range(n_features)],
        "n_features": n_features,
    }
