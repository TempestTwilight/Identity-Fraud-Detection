"""PyTorch Dataset wrapper for FL client partitions.

Wraps a (features, labels) numpy pair into a torch Dataset.
Each client in the FL simulation holds its own Dataset instance.
"""

from typing import Optional
import numpy as np
import torch
from torch.utils.data import Dataset


class FraudDataset(Dataset):
    """PyTorch dataset for fraud detection FL partitions.

    Args:
        X: Feature matrix, shape (n_samples, n_features).
        y: Label vector, shape (n_samples,) — 1 = fraud, 0 = legitimate.
        transform: Optional transform to apply to features.
    """

    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        transform: Optional[callable] = None,
    ):
        assert len(X) == len(y), f"X ({len(X)}) and y ({len(y)}) length mismatch"
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.X[idx]
        if self.transform:
            x = self.transform(x)
        return x, self.y[idx]
