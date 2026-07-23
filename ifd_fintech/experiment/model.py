"""Simple MLP model for fraud detection.

Start simple: 3 hidden layers. Swap for a deeper/wider model later
by changing the `hidden_dims` parameter.
"""

from typing import Optional
import numpy as np
import torch
import torch.nn as nn


class FraudMLP(nn.Module):
    """Multi-layer perceptron for binary fraud classification.

    Default: 256 → 128 → 64 → 1 (sigmoid output).

    Args:
        input_dim: Number of input features.
        hidden_dims: List of hidden layer sizes.
        dropout: Dropout probability (0 = no dropout).
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: Optional[list[int]] = None,
        dropout: float = 0.2,
    ):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [256, 128, 64]

        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev_dim = h_dim

        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

    def get_weights(self) -> list[np.ndarray]:
        """Return model parameters as numpy arrays (for Flower)."""
        return [p.detach().cpu().numpy() for p in self.parameters()]

    def set_weights(self, weights: list[np.ndarray]):
        """Set model parameters from numpy arrays (from Flower)."""
        with torch.no_grad():
            for param, w in zip(self.parameters(), weights):
                param.copy_(torch.tensor(w, dtype=torch.float32))
