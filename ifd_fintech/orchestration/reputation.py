"""ReputationManager — per-client reputation state with forgetting.

Extracted from the original AdaptiveThresholdEscalation monolith.
Responsible for:
  1. Maintaining per-client reputation values R_i
  2. EMA-based update with steady-state floor (R_SS) and forgetting
  3. Providing reputation-weighted coefficients for aggregation
"""

import numpy as np


class ReputationManager:
    """Tracks per-client reputation with EMA forgetting toward R_SS.

    The reputation R_i ∈ [0, 1] evolves as:
      R_i(t+1) = R_i(t) + alpha · (score_i - R_i(t)) + gamma · (R_SS - R_i(t))

    Key properties:
    - R_SS = 0.85 floor prevents permanent exclusion from a single bad round
    - gamma = 0.02 pulls reputation toward R_SS (forgetting)
    - alpha = 0.1 EMA smoothing factor
    """

    def __init__(
        self,
        n_clients: int,
        alpha: float = 0.1,
        gamma: float = 0.02,
        r_ss: float = 0.85,
        suspicious_weight: float = 0.50,
    ):
        self.n_clients = n_clients
        self.alpha = alpha
        self.gamma = gamma
        self.r_ss = r_ss
        self.suspicious_weight = suspicious_weight

        self.reputations: np.ndarray = np.ones(n_clients, dtype=np.float32)

    # ----- Core update -----

    def update(self, client_id: int, anomaly_score: float):
        """Update one client's reputation after scoring.

        Args:
            client_id: Client index [0, n_clients).
            anomaly_score: Score from the cascade (0=malicious, 1=honest).
        """
        r = self.reputations[client_id]
        r = r + self.alpha * (anomaly_score - r) + self.gamma * (self.r_ss - r)
        self.reputations[client_id] = float(np.clip(r, 0.0, 1.0))

    # ----- Aggregation helpers -----

    def get_weight(self, client_id: int, anomaly_score: float,
                   theta_accept: float = 0.60,
                   theta_reject: float = 0.30) -> float:
        """Compute aggregation weight for a client based on score and reputation.

        Args:
            client_id: Client index.
            anomaly_score: Final anomaly score from the cascade.
            theta_accept: Score above which updates are fully trusted.
            theta_reject: Score below which updates are rejected.
            theta_accept and theta_reject come from the CascadeRouter.

        Returns:
            Weight in [0, 1] for the weighted average.
        """
        r = self.reputations[client_id]
        if anomaly_score >= theta_accept:
            return float(r)
        elif anomaly_score >= theta_reject:
            return float(r * self.suspicious_weight)
        return 0.0

    def compute_weights(self, scores: np.ndarray,
                        theta_accept: float = 0.60,
                        theta_reject: float = 0.30) -> np.ndarray:
        """Compute aggregation weights for all clients.

        Args:
            scores: Per-client anomaly scores, shape (n_clients,).
            theta_accept: Score above which updates are fully trusted.
            theta_reject: Score below which updates are rejected.

        Returns:
            Weight array, shape (n_clients,).
        """
        weights = np.zeros(self.n_clients, dtype=np.float64)
        for i in range(self.n_clients):
            weights[i] = self.get_weight(i, scores[i], theta_accept, theta_reject)
        return weights
