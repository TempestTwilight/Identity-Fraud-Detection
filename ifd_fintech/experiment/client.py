"""Flower NumPyClient for local model training on a data partition.

Each FL client holds a FraudDataset partition, trains locally using
the FraudMLP model, and returns updated weights to the server.
"""

from typing import Optional
from collections import OrderedDict
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

try:
    from flwr.client import NumPyClient
except ImportError:
    NumPyClient = object  # fallback for type checking without flwr

from .model import FraudMLP
from ifd_fintech.data.dataset import FraudDataset


class FraudClient(NumPyClient):  # type: ignore[misc]
    """Flower client for fraud detection FL.

    Args:
        client_id: Unique client index.
        dataset: Local data partition.
        input_dim: Number of model input features.
        learning_rate: Local SGD learning rate.
        batch_size: Local training batch size.
        epochs: Local training epochs per round.
        device: 'cpu' or 'cuda'.
    """

    def __init__(
        self,
        client_id: int,
        dataset: FraudDataset,
        input_dim: int,
        learning_rate: float = 0.01,
        batch_size: int = 64,
        epochs: int = 3,
        device: str = "cpu",
    ):
        self.client_id = client_id
        self.dataset = dataset
        self.input_dim = input_dim
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.device = torch.device(device)

        self.model = FraudMLP(input_dim=input_dim).to(self.device)
        self.criterion = nn.BCEWithLogitsLoss()
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=self.learning_rate
        )

    def get_parameters(self, config) -> list[np.ndarray]:
        """Return current model weights as numpy arrays."""
        return self.model.get_weights()

    def fit(self, parameters, config) -> tuple[list[np.ndarray], int, dict]:
        """Train on local data partition.

        Args:
            parameters: Global model weights from server.
            config: Flower config dict (may contain 'epochs', 'lr' overrides).

        Returns:
            (updated_weights, num_samples, metrics)
        """
        self.model.set_weights(parameters)
        epochs = config.get("epochs", self.epochs)
        lr = config.get("lr", self.learning_rate)

        for param_group in self.optimizer.param_groups:
            param_group["lr"] = lr

        loader = DataLoader(
            self.dataset, batch_size=self.batch_size, shuffle=True
        )

        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for _ in range(epochs):
            for X_batch, y_batch in loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                self.optimizer.zero_grad()
                logits = self.model(X_batch)
                loss = self.criterion(logits, y_batch)
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()
                n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        n_samples = len(self.dataset)

        return (
            self.model.get_weights(),
            n_samples,
            {"loss": avg_loss, "client_id": self.client_id},
        )

    def evaluate(self, parameters, config) -> tuple[float, int, dict]:
        """Evaluate on local data partition.

        Returns:
            (loss, num_samples, metrics)
        """
        self.model.set_weights(parameters)
        loader = DataLoader(
            self.dataset, batch_size=self.batch_size, shuffle=False
        )

        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for X_batch, y_batch in loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                logits = self.model(X_batch)
                loss = self.criterion(logits, y_batch)
                total_loss += loss.item()

                preds = (torch.sigmoid(logits) > 0.5).float()
                correct += (preds == y_batch).sum().item()
                total += len(y_batch)

        avg_loss = total_loss / max(len(loader), 1)
        accuracy = correct / max(total, 1)

        return avg_loss, len(self.dataset), {"accuracy": accuracy}
