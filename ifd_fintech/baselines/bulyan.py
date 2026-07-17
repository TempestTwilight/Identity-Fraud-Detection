"""
Bulyan: Byzantine-robust aggregation (Mhamdi et al. 2018).

Two-step robust aggregation:
1. Brute-force Krum selection to identify n-2f candidates
2. Coordinate-wise truncated mean on selected candidates
"""

import numpy as np
from typing import Optional

from . import Baseline


class Bulyan(Baseline):
    """Bulyan robust aggregation.

    Handles up to f Byzantine clients with O(N^2) pairwise distance
    computation per round.
    """

    def __init__(self, n_byzantine: int = 2):
        super().__init__("Bulyan")
        self.f = n_byzantine

    @staticmethod
    def _pairwise_distances(updates: list[np.ndarray]) -> np.ndarray:
        """Compute pairwise squared Euclidean distances.

        Returns:
            Matrix D of shape (N, N) where D[i,j] = ||u_i - u_j||^2.
        """
        stack = np.array(updates)  # shape (N, d)
        # ||u_i - u_j||^2 = ||u_i||^2 + ||u_j||^2 - 2 u_i·u_j
        norms = np.sum(stack ** 2, axis=1, keepdims=True)
        dot = stack @ stack.T
        return norms + norms.T - 2 * dot

    @staticmethod
    def _krum(updates: list[np.ndarray], f: int, n_candidates: int) -> list[int]:
        """Select n_candidates closest-to-the-rest indices."""
        n = len(updates)
        if n < 2 * f + 3:
            return list(range(n))

        distances = Bulyan._pairwise_distances(updates)

        # Sum of distances to the (n - f - 2) nearest neighbors
        scores = []
        for i in range(n):
            d_sorted = np.sort(distances[i])
            score = np.sum(d_sorted[1:(n - f - 1)])  # skip self (distance 0)
            scores.append(score)

        # Select n_candidates with smallest scores
        candidate_indices = np.argsort(scores)[:n_candidates]
        return list(candidate_indices)

    @staticmethod
    def _truncated_mean(updates: list[np.ndarray]) -> list[np.ndarray]:
        """Coordinate-wise truncated mean.

        For each coordinate, discard the top and bottom 25% of values,
        then average the remainder.
        """
        stack = np.array(updates)
        n = len(updates)
        if n <= 3:
            return list(updates)

        low = int(np.floor(n * 0.25))
        high = int(np.ceil(n * 0.75))

        filtered = []
        for vec in stack:
            vec_sorted = np.sort(vec)
            trimmed = vec_sorted[low:high]
            if len(trimmed) > 0:
                filtered.append(np.mean(vec))
            else:
                filtered.append(np.mean(vec))

        # Coordinate-wise trimming
        trimmed = []
        for j in range(stack.shape[1]):  # for each coordinate
            col = stack[:, j]
            col_sorted = np.sort(col)
            col_trimmed = col_sorted[low:high]
            trimmed.append(np.mean(col_trimmed) if len(col_trimmed) > 0 else 0.0)

        return np.array([np.array(trimmed) for _ in range(len(updates))])

    def aggregate(self, updates: list[np.ndarray]) -> np.ndarray:
        """Aggregate updates using Bulyan.

        Returns the single aggregated global update.
        """
        n = len(updates)
        n_candidates = max(n - 2 * self.f, 3)

        # Step 1: Krum selection
        candidates_idx = self._krum(updates, self.f, n_candidates)
        candidates = [updates[i] for i in candidates_idx]

        # Step 2: Coordinate-wise truncated mean on candidates
        stack = np.array(candidates)
        low = int(np.floor(len(candidates) * 0.25))
        high = int(np.ceil(len(candidates) * 0.75))

        agg = np.zeros_like(updates[0])
        for j in range(agg.shape[0]):
            col = stack[:, j]
            col_sorted = np.sort(col)
            col_trimmed = col_sorted[low:high]
            if len(col_trimmed) > 0:
                agg[j] = np.mean(col_trimmed)
            else:
                agg[j] = 0.0

        return agg

    def filter_updates(self, updates, client_ids=None, round_t=0):
        if len(updates) == 0:
            return [], []

        agg = self.aggregate(updates)

        # Bulyan produces one aggregated update — all clients pass through
        # (filtering is implicit in the truncation)
        return list(updates), list(range(len(updates)))
