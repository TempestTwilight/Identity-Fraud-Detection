"""
Layer 2 — Spectral Anomaly Detection (PCA/SVD)

Detects coordinated multi-client attacks by analyzing the spectral decomposition
of the per-round update matrix. Correlated malicious updates occupy a different
subspace than independent honest-client variation.

Reference: adaptive-threshold-escalation.md §3 (L2)
"""

import numpy as np
from numpy.linalg import svd


class SpectralDetector:
    """Layer 2: PCA-based spectral anomaly detection on client updates."""

    def __init__(self, dim: int, variance_ratio: float = 0.95):
        self.dim = dim
        self.variance_ratio = variance_ratio  # γ: variance explained threshold
        self._initialized = False

    def score(
        self,
        updates: list[np.ndarray],
        target_idx: int,
    ) -> tuple[float, float]:
        """Compute spectral anomaly score and confidence for one client.

        Args:
            updates: All N client updates in current round.
            target_idx: Index of the client to score.

        Returns:
            (anomaly_score, confidence)
        """
        G = np.array(updates)  # shape: (N, d)
        N, d = G.shape

        if N < 3:
            return 0.5, 0.3  # Not enough clients for spectral analysis

        # Centre the matrix
        mean_update = np.mean(G, axis=0)
        R = G - mean_update  # residual matrix, shape: (N, d)

        # SVD on residual matrix
        # Note: for efficiency, can use randomized SVD for large d
        U, S, Vt = svd(R, full_matrices=False)

        # Determine number of components to retain
        explained_ratio = np.cumsum(S**2) / np.sum(S**2)
        k = int(np.searchsorted(explained_ratio, self.variance_ratio) + 1)
        k = min(k, N - 1, d - 1)

        # Principal subspace V_k (top k right singular vectors)
        V_k = Vt[:k, :].T  # shape: (d, k)

        # Compute projection residual for target client
        g_i = updates[target_idx] - mean_update
        proj = V_k @ (V_k.T @ g_i)  # projection onto principal subspace
        residual = np.linalg.norm(g_i - proj)

        # Normalize across all clients for score
        residuals = []
        for j, g_j in enumerate(G - mean_update):
            if j == target_idx:
                continue
            proj_j = V_k @ (V_k.T @ g_j)
            residuals.append(np.linalg.norm(g_j - proj_j))

        max_residual = max(residuals) if residuals else 1.0
        normalized_residual = residual / (max_residual + 1e-8)

        # ---- Anomaly score ----
        # 1 - normalized residual: 0 = far from principal subspace (suspicious)
        anomaly_score = 1.0 - min(normalized_residual, 1.0)

        # ---- Confidence ----
        # High confidence when:
        # 1. The principal subspace explains variance cleanly (λ_k / λ_1)
        # 2. The eigengap is clear (detectable structure)
        spectral_quality = S[k - 1] / (S[0] + 1e-8) if k > 0 else 0.0
        confidence = min(float(spectral_quality), 0.9)

        return anomaly_score, confidence
