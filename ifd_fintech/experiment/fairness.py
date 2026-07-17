"""
Fairness evaluation for defense across client subgroups.

Ensures the defense does not disproportionately flag honest clients
with unusual but legitimate data distributions (minority-serving banks,
small banks, new entrants).
"""

import numpy as np


# Standard client profiles
PROFILES = ["majority", "minority_serving", "small_bank", "new_entrant"]


class FairnessEvaluator:
    """Evaluates fairness of defense across client subgroups.

    Measures per-subgroup honest FPR and fairness gap ratios.
    """

    def __init__(self, client_profiles: dict[int, str]):
        """Initialize with client-to-profile mapping.

        Args:
            client_profiles: {client_id: profile_name} mapping.
                Profiles are one of PROFILES.
        """
        self.client_profiles = client_profiles

    def _get_profile_clients(self, profile: str) -> list[int]:
        return [c for c, p in self.client_profiles.items() if p == profile]

    def compute_honest_fpr(
        self,
        attack_matrix: np.ndarray,
        anomaly_scores: np.ndarray,
        threshold: float = 0.5,
    ) -> dict:
        """Compute per-subgroup honest FPR.

        Args:
            attack_matrix: Boolean (n_clients, n_rounds) — True = attacking.
            anomaly_scores: Float (n_clients, n_rounds) — 1 = honest, 0 = malicious.
            threshold: Score below which a client is flagged.

        Returns:
            dict with per-profile honest FPR values.
        """
        results = {}
        for profile in PROFILES:
            clients = self._get_profile_clients(profile)
            if not clients:
                continue

            honest = ~attack_matrix[clients].astype(bool)
            flagged = anomaly_scores[clients] < threshold
            honest_flagged = flagged & honest

            total_honest = np.sum(honest)
            if total_honest > 0:
                fpr = float(np.sum(honest_flagged) / total_honest)
            else:
                fpr = 0.0

            results[f"{profile}_fpr"] = fpr

        return results

    def compute_fairness_gap(
        self, per_subgroup_fpr: dict[str, float]
    ) -> dict:
        """Compute fairness disparity metrics.

        Args:
            per_subgroup_fpr: Output from compute_honest_fpr().

        Returns:
            dict with per-profile disparity ratios and max disparity.
        """
        majority_fpr = per_subgroup_fpr.get("majority_fpr", 0.01)
        majority_fpr = max(majority_fpr, 1e-8)

        gaps = {}
        for profile in PROFILES:
            fpr = per_subgroup_fpr.get(f"{profile}_fpr", 0.0)
            gaps[f"{profile}_disparity_ratio"] = fpr / majority_fpr

        if gaps:
            gaps["max_disparity_ratio"] = max(v for v in gaps.values())
        else:
            gaps["max_disparity_ratio"] = 1.0

        return gaps

    def compute_layer_fpr(
        self,
        attack_matrix: np.ndarray,
        layer_scores: dict[str, np.ndarray],
        thresholds: dict[str, float] | None = None,
    ) -> dict:
        """Compute per-layer, per-profile FPR.

        Args:
            attack_matrix: Boolean (n_clients, n_rounds).
            layer_scores: {layer_name: np.ndarray of (n_clients, n_rounds)}.
            thresholds: {layer_name: threshold} or default 0.5.

        Returns:
            dict with per-profile, per-layer FPR.
        """
        if thresholds is None:
            thresholds = {k: 0.5 for k in layer_scores}

        results = {}
        for layer_name, scores in layer_scores.items():
            threshold = thresholds.get(layer_name, 0.5)
            for profile in PROFILES:
                clients = self._get_profile_clients(profile)
                if not clients:
                    continue

                honest = ~attack_matrix[clients].astype(bool)
                flagged = scores[clients] < threshold
                honest_flagged = flagged & honest

                total = np.sum(honest)
                fpr = float(np.sum(honest_flagged) / total) if total > 0 else 0.0
                results[f"{profile}_{layer_name}_fpr"] = fpr

        return results

    def summary(
        self,
        attack_matrix: np.ndarray,
        anomaly_scores: np.ndarray,
        threshold: float = 0.5,
    ) -> dict:
        """Compute a complete fairness summary.

        Returns:
            dict with all fairness metrics.
        """
        fprs = self.compute_honest_fpr(attack_matrix, anomaly_scores, threshold)
        gaps = self.compute_fairness_gap(fprs)
        return {"per_subgroup_fpr": fprs, "fairness_gaps": gaps}
