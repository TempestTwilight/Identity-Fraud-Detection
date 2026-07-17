"""
Layer 3 — Temporal Reputation Scoring

Tracks multi-round client behavior to detect slow, adaptive poisoning that
evades per-round detection. Uses exponential moving average of historical
anomaly scores combined with update consistency.

Reference: adaptive-threshold-escalation.md §3 (L3)
"""

import numpy as np


class TemporalReputation:
    """Layer 3: Multi-round temporal reputation scoring."""

    def __init__(self, n_clients: int, alpha: float = 0.1, maturity_rounds: int = 20):
        self.n_clients = n_clients
        self.alpha = alpha              # EMA smoothing factor
        self.maturity = maturity_rounds  # rounds before full confidence

        # Per-client state
        self.reputations = np.ones(n_clients, dtype=np.float32)  # R_i
        self.update_history: list[np.ndarray] = []  # past updates per client
        self.ema_updates = [np.zeros(1)] * n_clients  # expected update vector
        self.rounds_seen = np.zeros(n_clients, dtype=int)
        self.t = 0

    def score(self, g_i: np.ndarray, client_id: int) -> tuple[float, float]:
        """Compute temporal anomaly score and confidence.

        Args:
            g_i: Client's gradient update.
            client_id: Client index [0, n_clients).

        Returns:
            (anomaly_score, confidence)
        """
        # ---- Anomaly score ----
        # Consistency with client's own history
        if self.rounds_seen[client_id] > 0:
            expected = self.ema_updates[client_id]
            expected_norm = np.linalg.norm(expected)
            if expected_norm > 0 and np.linalg.norm(g_i) > 0:
                consistency = np.dot(g_i, expected) / (
                    np.linalg.norm(g_i) * expected_norm
                )
                consistency = max(-1.0, min(1.0, consistency))
                consistency_score = (consistency + 1.0) / 2.0  # map [-1,1] to [0,1]
            else:
                consistency_score = 0.5
        else:
            consistency_score = 0.5  # Neutral for first round

        # Combine with cumulative reputation
        anomaly_score = float(self.reputations[client_id] * consistency_score)

        # ---- Confidence ----
        # Grows with observation history and current reputation
        history_confidence = min(self.rounds_seen[client_id] / self.maturity, 1.0)
        confidence = history_confidence * float(self.reputations[client_id])

        # ---- Update state ----
        self._update_state(g_i, client_id)

        return anomaly_score, confidence

    def _update_state(self, g_i: np.ndarray, client_id: int):
        """Update EMA and reputation after scoring."""
        # Update EMA of updates
        if self.rounds_seen[client_id] == 0:
            self.ema_updates[client_id] = g_i.copy()
        else:
            self.ema_updates[client_id] = (
                (1 - self.alpha) * self.ema_updates[client_id]
                + self.alpha * g_i
            )

        self.rounds_seen[client_id] += 1
        self.t += 1
