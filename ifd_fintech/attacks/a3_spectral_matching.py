"""
A3: Spectral-Matching Attack

The attacker crafts updates that lie in the low-rank "normal" subspace
identified by SVD. The malicious signal is injected in the nullspace
directions that SVD discards, making it invisible to Layer 2.

Reference: attacker-design.md §5
"""

from typing import Optional

import numpy as np

from . import AdaptiveAttacker


class SpectralMatching(AdaptiveAttacker):
    """Attacker that projects malicious gradients onto the honest SVD subspace.

    Observes the spectral basis from previous rounds and crafts updates
    that match the normal subspace structure. The backdoor signal is
    hidden in the residual (nullspace) directions.

    This is the hardest attack for Layer 2 to detect — the gradient
    literally lives in the honest subspace.
    """

    def __init__(
        self,
        n_malicious: int,
        subspace_rank: int = 5,
        nullspace_noise_scale: float = 0.01,
        defense_knowledge: Optional[dict] = None,
        backdoor_trigger: Optional[np.ndarray] = None,
        backdoor_target: int = 0,
    ):
        super().__init__(n_malicious, defense_knowledge, backdoor_trigger, backdoor_target)
        self.subspace_rank = subspace_rank
        self.nullspace_noise_scale = nullspace_noise_scale
        self.V_k: Optional[np.ndarray] = None  # top-k right singular vectors

    def _estimate_spectral_basis(self, updates: list[np.ndarray]):
        """Estimate the top-k right singular vectors from honest updates."""
        # Stack updates: shape (N, d)
        U, S, Vt = np.linalg.svd(np.array(updates), full_matrices=False)
        self.V_k = Vt[:self.subspace_rank, :].T  # shape (d, k) — right singular vectors

    def _project_onto_subspace(self, g: np.ndarray) -> np.ndarray:
        """Project gradient onto the honest subspace."""
        if self.V_k is None:
            return g
        # V_k V_k^T @ g
        return self.V_k @ (self.V_k.T @ g)

    def _nullspace_component(self, g: np.ndarray) -> np.ndarray:
        """Get the component orthogonal to the honest subspace."""
        if self.V_k is None:
            return np.zeros_like(g)
        return g - self._project_onto_subspace(g)

    def craft_update(
        self,
        round_t: int,
        updates: list[np.ndarray],
        global_model: np.ndarray,
        loss_fn=None,
    ) -> list[np.ndarray]:
        n_total = len(updates)
        mal_indices = self._select_malicious_indices(n_total)
        modified = list(updates)

        # Estimate spectral basis from observed updates (excluding previous
        # malicious outputs — we approximate by using all current updates)
        self._estimate_spectral_basis(updates)

        for idx in mal_indices:
            g_mal = updates[idx].copy()

            if self.V_k is not None:
                # Split: honest subspace component + nullspace backdoor
                g_honest_subspace = self._project_onto_subspace(g_mal)

                # The backdoor signal is injected in the nullspace
                nullspace_vec = self._nullspace_component(g_mal)

                # Amplify only the nullspace component that carries backdoor signal
                nullspace_norm = np.linalg.norm(nullspace_vec)
                if nullspace_norm > 0:
                    # Scale nullspace to carry the malicious signal
                    mal_signal = nullspace_vec * (1.0 + self.nullspace_noise_scale * 10)
                    modified[idx] = g_honest_subspace + mal_signal
                else:
                    # If update is entirely in subspace, add minimal noise
                    noise = np.random.randn(*g_mal.shape) * self.nullspace_noise_scale
                    modified[idx] = g_honest_subspace + noise
            else:
                # No spectral basis yet — submit unmodified
                modified[idx] = g_mal

        return modified
