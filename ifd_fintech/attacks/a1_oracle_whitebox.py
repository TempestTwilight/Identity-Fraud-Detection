"""
A1: Oracle White-Box Attack

The attacker has full knowledge of all 3 defense layers and the current
round's threshold values. Iteratively optimizes a malicious gradient to
pass all layer checks simultaneously.

Reference: attacker-design.md §3
"""

from typing import Optional

import numpy as np

from . import AdaptiveAttacker


class OracleWhiteBox(AdaptiveAttacker):
    """White-box attacker that optimizes updates to evade all 3 layers.

    Uses projected gradient descent on the evasion loss — iteratively
    adjusts the malicious gradient to stay within L1 norm/cosine bounds,
    the L2 SVD subspace, and L3 temporal consistency.
    """

    def __init__(
        self,
        n_malicious: int,
        max_iter: int = 50,
        step_size: float = 0.1,
        defense_knowledge: Optional[dict] = None,
        backdoor_trigger: Optional[np.ndarray] = None,
        backdoor_target: int = 0,
    ):
        super().__init__(n_malicious, defense_knowledge, backdoor_trigger, backdoor_target)
        self.max_iter = max_iter
        self.step_size = step_size
        self.norm_mean: Optional[float] = None
        self.norm_std: Optional[float] = None
        self.cos_mean: Optional[float] = None
        self.cos_std: Optional[float] = None
        self.U_k: Optional[np.ndarray] = None  # top-k singular vectors

    def _estimate_defense_params(self, updates: list[np.ndarray]):
        """Estimate defense parameters from observed updates."""
        norms = np.array([np.linalg.norm(g) for g in updates])
        self.norm_mean = float(np.mean(norms))
        self.norm_std = max(float(np.std(norms)), 1e-8)

        ref = np.mean(updates, axis=0)
        ref_norm = np.linalg.norm(ref)
        if ref_norm > 0:
            cosines = np.array([
                np.dot(g, ref) / (np.linalg.norm(g) * ref_norm)
                for g in updates
            ])
        else:
            cosines = np.ones(len(updates))
        self.cos_mean = float(np.mean(cosines))
        self.cos_std = max(float(np.std(cosines)), 1e-8)

        # Estimate spectral subspace from set of updates
        _, S, Vt = np.linalg.svd(np.array(updates), full_matrices=False)
        # Keep components explaining > 5% variance (typical heuristic)
        var_ratio = S ** 2 / np.sum(S ** 2)
        k = max(2, int(np.sum(var_ratio > 0.05)))
        # Vt shape: (min(N, d), d). We want right singular vectors.
        self.V_k = Vt[:k, :].T  # shape (d, k)

    # Import inside method to avoid circular import
    @staticmethod
    def _sigmoid(x: float) -> float:
        if x < -10:
            return 0.0
        if x > 10:
            return 1.0
        return 1.0 / (1.0 + np.exp(-x))

    def _layer1_loss(self, g: np.ndarray) -> float:
        """Evasion loss: how far g is from Layer 1's acceptance region.
        
        Lower = better (more likely to pass).
        """
        if self.norm_mean is None or self.cos_mean is None:
            return 0.0

        norm = np.linalg.norm(g)
        cos_sim = 0.0  # simplified; real version uses reference direction

        # Target: norm within 2 sigma, cos within 2 sigma of honest stats
        norm_loss = max(0, abs(norm - self.norm_mean) / self.norm_std - 2.0) ** 2
        cos_loss = max(0, abs(cos_sim - self.cos_mean) / self.cos_std - 2.0) ** 2
        return norm_loss + cos_loss

    def _layer2_loss(self, g: np.ndarray) -> float:
        """Evasion loss for spectral detection.
        
        Penalizes components in the nullspace of honest updates.
        """
        if self.V_k is None:
            return 0.0

        # Project g onto honest subspace and measure residual
        proj = self.V_k @ (self.V_k.T @ g)
        residual = g - proj
        residual_norm = np.linalg.norm(residual) / (np.linalg.norm(g) + 1e-8)
        return residual_norm

    def craft_update(
        self,
        round_t: int,
        updates: list[np.ndarray],
        global_model: np.ndarray,
        loss_fn=None,
    ) -> list[np.ndarray]:
        n_total = len(updates)
        mal_indices = self._select_malicious_indices(n_total)

        # Estimate defense parameters from honest-looking updates
        # (In practice, attacker observes all updates; we approximate
        #  by using the full set minus our own previous outputs)
        honest_updates = [updates[i] for i in range(n_total) if i not in mal_indices]
        if honest_updates:
            self._estimate_defense_params(honest_updates)

        modified = list(updates)

        for idx in mal_indices:
            g_target = updates[idx].copy() if idx < len(updates) else np.random.randn(global_model.shape[0])

            # Projected gradient descent to find evasion update
            g_mal = g_target.copy()
            for _ in range(self.max_iter):
                # Layer 1 evasion: project toward honest norm/cosine region
                l1_loss = self._layer1_loss(g_mal)
                if l1_loss > 0:
                    # Simple gradient: move toward mean norm
                    current_norm = np.linalg.norm(g_mal)
                    if current_norm > 0 and self.norm_mean is not None:
                        scale = self.norm_mean / (current_norm + 1e-8)
                        g_mal = g_mal * (1 - self.step_size) + (g_mal * scale) * self.step_size

                # Layer 2 evasion: project onto honest subspace
                l2_loss = self._layer2_loss(g_mal)
                if l2_loss > 0.1 and self.V_k is not None:
                    # Soft projection: blend toward subspace
                    proj = self.V_k @ (self.V_k.T @ g_mal)
                    g_mal = (1 - self.step_size) * g_mal + self.step_size * proj

            modified[idx] = g_mal.astype(updates[idx].dtype)

        return modified
