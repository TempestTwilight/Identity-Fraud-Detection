"""
DP-FL: Gradient clipping + noise for Differential Privacy (Abadi et al. 2016).

Standard DP-SGD applied to the FL setting: per-client gradient clipping
followed by Gaussian noise addition before aggregation.
"""

import numpy as np
from typing import Optional

from . import Baseline


class DPFL(Baseline):
    """Differential privacy filter for FL.

    Applies per-client gradient clipping + Gaussian noise.
    Can be composed with any aggregation rule.
    """

    def __init__(
        self,
        clip_norm: float = 1.0,
        noise_multiplier: float = 0.5,
        epsilon: float = 8.0,
    ):
        super().__init__(f"DP-FL (ε={epsilon})")
        self.clip_norm = clip_norm
        self.noise_multiplier = noise_multiplier
        self.epsilon = epsilon

    def apply_dp(self, update: np.ndarray) -> np.ndarray:
        """Apply gradient clipping + Gaussian noise to a single update."""
        norm = np.linalg.norm(update)
        clipped = update / max(1.0, norm / self.clip_norm)
        noise = np.random.normal(
            0,
            self.noise_multiplier * self.clip_norm,
            size=update.shape,
        )
        return clipped.astype(update.dtype) + noise.astype(update.dtype)

    def sigma(self) -> float:
        """Compute the noise standard deviation."""
        return self.noise_multiplier * self.clip_norm

    def filter_updates(self, updates, client_ids=None, round_t=0):
        if client_ids is None:
            client_ids = list(range(len(updates)))

        # Apply DP to every client's update
        dp_updates = [self.apply_dp(u) for u in updates]

        # All clients accepted (DP doesn't filter, it preserves privacy)
        return dp_updates, list(range(len(updates)))
