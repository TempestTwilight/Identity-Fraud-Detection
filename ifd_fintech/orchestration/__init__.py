"""CascadeRouter — orchestrates the 3-layer gated cascade.

The router is responsible for:
  1. Running each round through the 3-layer scoring pipeline
  2. Delegating threshold adaptation to ThresholdController
  3. Delegating reputation tracking to ReputationManager
  4. Computing the reputation-weighted aggregate gradient

This is the surviving core of the original AdaptiveThresholdEscalation
monolith, after extracting ThresholdController and ReputationManager.
"""

from typing import Optional
import numpy as np

from .threshold_controller import ThresholdController
from .reputation import ReputationManager


class CascadeRouter:
    """Orchestrates the 3-layer defense with adaptive thresholds.

    Design: most updates resolved by Layer 1 (cheap, O(d)).
    Ambiguous cases escalate to Layer 2 (SVD, O(Nd²)) or Layer 3 (temporal).
    Thresholds tighten under attack (via ThresholdController) and relax
    during normal operation. Reputation tracked per-client (via
    ReputationManager) with steady-state floor preventing exclusion.
    """

    def __init__(
        self,
        n_clients: int,
        dim: int,
        # Decision boundaries
        theta_accept: float = 0.60,
        theta_reject: float = 0.30,
        # Reputation (passed to ReputationManager)
        alpha: float = 0.1,
        gamma: float = 0.02,
        r_ss: float = 0.85,
        suspicious_weight: float = 0.50,
        # Threshold control (passed to ThresholdController)
        tau_1_min: float = 0.55,
        tau_1_max: float = 0.90,
        tau_1_init: float = 0.75,
        tau_2_min: float = 0.55,
        tau_2_max: float = 0.85,
        tau_2_init: float = 0.70,
        eta_attack: float = 0.15,
        eta_relax: float = 0.05,
        rho_0: float = 0.10,
        sigma_rho: float = 0.05,
        alarm_window: int = 20,
    ):
        self.n_clients = n_clients
        self.dim = dim
        self.theta_accept = theta_accept
        self.theta_reject = theta_reject

        # Sub-modules
        self.reputation = ReputationManager(
            n_clients=n_clients,
            alpha=alpha,
            gamma=gamma,
            r_ss=r_ss,
            suspicious_weight=suspicious_weight,
        )
        self.thresholds = ThresholdController(
            tau_1_min=tau_1_min,
            tau_1_max=tau_1_max,
            tau_1_init=tau_1_init,
            tau_2_min=tau_2_min,
            tau_2_max=tau_2_max,
            tau_2_init=tau_2_init,
            eta_attack=eta_attack,
            eta_relax=eta_relax,
            rho_0=rho_0,
            sigma_rho=sigma_rho,
            alarm_window=alarm_window,
        )

        # Layer instances (injected via set_layers)
        self.layer1: Optional[object] = None
        self.layer2: Optional[object] = None
        self.layer3: Optional[object] = None

        self.t = 0  # round counter

    def set_layers(self, layer1, layer2, layer3):
        """Inject detection layer instances.

        Each must implement .score(...) -> (anomaly_score, confidence).
        See layers/ for the concrete signatures.
        """
        self.layer1 = layer1
        self.layer2 = layer2
        self.layer3 = layer3

    # ----- Main pipeline -----

    def process_round(
        self,
        updates: list[np.ndarray],
    ) -> tuple[np.ndarray, dict]:
        """Process one FL round through the 3-layer defense.

        Args:
            updates: List of N client gradient updates, each shape (d,).

        Returns:
            (aggregated_gradient, info_dict)
        """
        N = len(updates)
        final_scores = np.zeros(N)
        escalation_stats = {"layer1": 0, "layer2": 0, "layer3": 0}

        tau_1, tau_2 = self.thresholds.current_thresholds

        for i in range(N):
            g_i = updates[i]

            # ---- Layer 1: Norm/Cosine (cheap, O(d)) ----
            a1, c1 = self.layer1.score(g_i)  # type: ignore[union-attr]

            if c1 >= tau_1:
                final_scores[i] = a1
                escalation_stats["layer1"] += 1
                self.reputation.update(i, a1)
                continue

            # ---- Layer 2: Spectral (SVD, O(Nd²)) ----
            a2, c2 = self.layer2.score(updates, i)  # type: ignore[union-attr]

            if c2 >= tau_2:
                final_scores[i] = a2
                escalation_stats["layer2"] += 1
                self.reputation.update(i, a2)
                continue

            # ---- Layer 3: Temporal (always decides) ----
            a3, _ = self.layer3.score(g_i, i)  # type: ignore[union-attr]
            final_scores[i] = a3
            escalation_stats["layer3"] += 1
            self.reputation.update(i, a3)

        # ---- Aggregate ----
        aggregated_grad = self._reputation_weighted_aggregate(updates, final_scores)

        # ---- Update thresholds ----
        self.thresholds.adapt(final_scores)

        self.t += 1

        info = {
            "round": self.t,
            "final_scores": final_scores.tolist(),
            "escalation_stats": escalation_stats,
            "tau_1": tau_1,
            "tau_2": tau_2,
            "reputations": self.reputation.reputations.tolist(),
            "agg_norm": float(np.linalg.norm(aggregated_grad)),
        }

        return aggregated_grad, info

    # ----- Aggregation -----

    def _reputation_weighted_aggregate(
        self,
        updates: list[np.ndarray],
        scores: np.ndarray,
    ) -> np.ndarray:
        """Aggregate accepted and down-weighted suspicious updates.

        Uses ReputationManager.compute_weights for the per-client weights.
        """
        weights = self.reputation.compute_weights(
            scores,
            theta_accept=self.theta_accept,
            theta_reject=self.theta_reject,
        )

        if weights.sum() == 0:
            return np.zeros_like(updates[0])

        agg = np.sum(
            [w * g for w, g in zip(weights, updates)],
            axis=0,
        )
        return agg / weights.sum()
