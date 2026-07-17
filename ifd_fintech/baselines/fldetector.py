"""
FLDetector: Prediction-consistency filter (Zhang et al. 2022).

Detects malicious clients by checking if a client's update is consistent
with its predicted update based on historical trajectory.
Uses bagged autoregressive prediction per client.
"""

import numpy as np
from typing import Optional

from . import Baseline


class FLDetector(Baseline):
    """Prediction-consistency filter.

    Each client's update is compared to a bagged autoregressive prediction
    based on that client's historical updates. Low similarity = malicious.
    """

    def __init__(
        self,
        history_window: int = 5,
        ensemble_size: int = 3,
        similarity_threshold: float = 0.3,
    ):
        super().__init__("FLDetector")
        self.history_window = history_window
        self.ensemble_size = ensemble_size
        self.similarity_threshold = similarity_threshold
        self.history: dict[int, list[np.ndarray]] = {}

    def _ar_predict(self, history: list[np.ndarray], seed: int) -> np.ndarray:
        """Autoregressive prediction from a client's history.

        Uses weighted linear combination of past updates where more recent
        updates have higher weight. The seed adds noise to the weights
        for bagging diversity.
        """
        rng = np.random.RandomState(seed)
        n = len(history)

        # Weighted combination: more recent = higher weight
        weights = np.array([1.0 + rng.random() * 0.1 for _ in range(n)])
        weights = weights / np.sum(weights)

        return np.sum([w * h for w, h in zip(weights, history)], axis=0)

    def score(self, client_id: int, update: np.ndarray) -> float:
        """Score how anomalous a client's update is.

        Returns a value in [0, 1] where 0 = likely malicious,
        1 = benign. This matches our convention for compatibility.
        """
        if client_id not in self.history:
            self.history[client_id] = []
        self.history[client_id].append(update.copy())

        # Need sufficient history for prediction
        if len(self.history[client_id]) < 3:
            return 1.0  # benign (insufficient data)

        window = self.history[client_id][-self.history_window:]

        # Bagged autoregressive prediction
        predictions = []
        for seed in range(self.ensemble_size):
            pred = self._ar_predict(window, seed)
            predictions.append(pred)

        mean_pred = np.mean(predictions, axis=0)

        # Cosine similarity between predicted and actual
        pred_norm = np.linalg.norm(mean_pred)
        update_norm = np.linalg.norm(update)
        if pred_norm < 1e-10 or update_norm < 1e-10:
            return 0.5  # degenerate case

        similarity = np.dot(mean_pred, update) / (pred_norm * update_norm)
        similarity = max(0.0, min(1.0, float(similarity)))

        return similarity  # 0 = bad, 1 = good

    def filter_updates(self, updates, client_ids=None, round_t=0):
        if client_ids is None:
            client_ids = list(range(len(updates)))

        accepted = []
        accepted_indices = []

        for i, (cid, upd) in enumerate(zip(client_ids, updates)):
            sim = self.score(cid, upd)
            if sim >= self.similarity_threshold:
                accepted.append(upd)
                accepted_indices.append(i)

        # If all would be rejected, keep all (fail-safe)
        if len(accepted) == 0:
            return list(updates), list(range(len(updates)))

        return accepted, accepted_indices
