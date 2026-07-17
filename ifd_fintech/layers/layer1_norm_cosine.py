"""
Layer 1 — Norm/Cosine Filtering

Fast, stateless filtering based on gradient norm and cosine similarity to the
global model update direction. Handles ~80% of updates without escalation.

Reference: adaptive-threshold-escalation.md §3 (L1)
"""

import numpy as np


class NormCosineFilter:
    """Layer 1: Lightweight norm and cosine-similarity filter."""

    def __init__(self, dim: int):
        self.dim = dim

        # Running statistics of honest updates (initialized during warm-up)
        self.norm_mean: float = 0.0
        self.norm_std: float = 1.0
        self.cos_mean: float = 1.0
        self.cos_std: float = 0.1

        self._initialized = False

    def fit(self, honest_updates: list[np.ndarray]):
        """Initialize running statistics from a set of known-honest updates.
        
        Called during warm-up phase on clean data.
        """
        norms = np.array([np.linalg.norm(g) for g in honest_updates])
        self.norm_mean = float(np.mean(norms))
        self.norm_std = max(float(np.std(norms)), 1e-8)

        ref = np.mean(honest_updates, axis=0)
        ref_norm = np.linalg.norm(ref)
        if ref_norm > 0:
            cosines = np.array([
                np.dot(g, ref) / (np.linalg.norm(g) * ref_norm)
                for g in honest_updates
            ])
        else:
            cosines = np.ones(len(honest_updates))
        self.cos_mean = float(np.mean(cosines))
        self.cos_std = max(float(np.std(cosines)), 1e-8)

        self._initialized = True

    def score(self, g_i: np.ndarray, ref: np.ndarray | None = None) -> tuple[float, float]:
        """Compute anomaly score and confidence for a single update.

        Args:
            g_i: Client gradient update vector.
            ref: Reference direction (mean update). If None, uses stored
                 statistics for a neutral assessment.

        Returns:
            (anomaly_score, confidence)
            - anomaly_score in [0, 1]; 1 = definitely honest, 0 = definitely malicious
            - confidence in [0, 1]; 1 = absolutely certain
        """
        if not self._initialized:
            return 0.5, 0.5  # Neutral before initialization

        norm = np.linalg.norm(g_i)

        # Compute cosine similarity if reference is provided
        if ref is not None and np.linalg.norm(ref) > 0 and norm > 0:
            cos_sim = float(np.dot(g_i, ref) / (norm * np.linalg.norm(ref)))
        else:
            cos_sim = 0.0

        # ---- Anomaly score ----
        # Sigmoid-based scaling relative to running statistics
        norm_score = self._sigmoid(
            (self.norm_mean - norm) / self.norm_std
        )
        cos_score = self._sigmoid(
            (cos_sim - self.cos_mean) / self.cos_std
        )
        anomaly_score = 0.5 * (norm_score + cos_score)

        # ---- Confidence ----
        # Confidence drops near the decision boundary
        norm_near_boundary = (norm >= self.norm_mean - 2 * self.norm_std and
                              norm <= self.norm_mean + 2 * self.norm_std)
        cos_near_boundary = (cos_sim >= self.cos_mean - 2 * self.cos_std and
                             cos_sim <= self.cos_mean + 2 * self.cos_std)

        penalty = 0.0
        if norm_near_boundary:
            penalty += 0.15
        if cos_near_boundary:
            penalty += 0.15

        confidence = 1.0 - penalty * 0.5

        return anomaly_score, confidence

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Numerically stable sigmoid clipped to [0, 1]."""
        if x < -10:
            return 0.0
        if x > 10:
            return 1.0
        return 1.0 / (1.0 + np.exp(-x))
