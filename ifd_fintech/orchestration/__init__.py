"""
Orchestration — Adaptive Threshold Escalation

Core module implementing the multi-layer defense orchestration with
adaptive thresholds. This is the mechanism by which the paper's novelty
(principled orchestration) is realized.

Reference: adaptive-threshold-escalation.md §4–§6
"""

from typing import Optional
import numpy as np


class AdaptiveThresholdEscalation:
    """Orchestrates the 3-layer defense with adaptive thresholds.

    Design principle: most updates resolved by Layer 1 (cheap, O(d)).
    Ambiguous cases escalate to Layer 2 (SVD, O(Nd²)) or Layer 3 (temporal).
    Thresholds tighten under attack and relax during normal operation.

    This class implements the core novelty of the paper: the principled
    orchestration that makes the layered defense more than the sum of its parts.
    """

    def __init__(
        self,
        n_clients: int,
        dim: int,
        # Layer 1 threshold bounds
        tau_1_min: float = 0.55,
        tau_1_max: float = 0.90,
        tau_1_init: float = 0.75,
        # Layer 2 threshold bounds
        tau_2_min: float = 0.55,
        tau_2_max: float = 0.85,
        tau_2_init: float = 0.70,
        # Adaptation rates
        eta_attack: float = 0.15,
        eta_relax: float = 0.05,
        # Decision thresholds
        theta_accept: float = 0.60,
        theta_reject: float = 0.30,
        suspicious_weight: float = 0.50,
        # Attack detection
        rho_0: float = 0.10,
        sigma_rho: float = 0.05,
        alarm_window: int = 20,
    ):
        # Thresholds — adapt across rounds
        self.tau_1 = tau_1_init
        self.tau_2 = tau_2_init
        self.TAU_1_MIN, self.TAU_1_MAX = tau_1_min, tau_1_max
        self.TAU_2_MIN, self.TAU_2_MAX = tau_2_min, tau_2_max

        # Adaptation hyperparameters
        self.eta_attack = eta_attack
        self.eta_relax = eta_relax

        # Decision thresholds
        self.theta_accept = theta_accept
        self.theta_reject = theta_reject
        self.suspicious_weight = suspicious_weight

        # Attack alarm
        self.rho_0 = rho_0
        self.sigma_rho = sigma_rho
        self.rho_history: list[float] = []
        self.alarm_window = alarm_window

        # Per-client reputation
        self.reputations = np.ones(n_clients, dtype=np.float32)
        self.t = 0  # round counter

        # Layer instances (initialized later)
        self.layer1: Optional["NormCosineFilter"] = None
        self.layer2: Optional["SpectralDetector"] = None
        self.layer3: Optional["TemporalReputation"] = None

    def set_layers(self, layer1, layer2, layer3):
        """Inject detection layer instances."""
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

        for i in range(N):
            g_i = updates[i]

            # ---- Layer 1: Norm/Cosine (cheap, O(d)) ----
            a1, c1 = self.layer1.score(g_i)

            if c1 >= self.tau_1:
                final_scores[i] = a1
                escalation_stats["layer1"] += 1
                # Update reputation (skipped layers are still scored)
                self._update_reputation(i, a1)
                continue

            # ---- Layer 2: Spectral (SVD, O(Nd²)) ----
            a2, c2 = self.layer2.score(updates, i)

            if c2 >= self.tau_2:
                final_scores[i] = a2
                escalation_stats["layer2"] += 1
                self._update_reputation(i, a2)
                continue

            # ---- Layer 3: Temporal (always decides) ----
            a3, _ = self.layer3.score(g_i, i)
            final_scores[i] = a3
            escalation_stats["layer3"] += 1
            self._update_reputation(i, a3)

        # ---- Aggregate ----
        aggregated_grad = self._reputation_weighted_aggregate(updates, final_scores)

        # ---- Update thresholds ----
        self._update_thresholds(final_scores)

        self.t += 1

        info = {
            "round": self.t,
            "final_scores": final_scores.tolist(),
            "escalation_stats": escalation_stats,
            "tau_1": self.tau_1,
            "tau_2": self.tau_2,
            "reputations": self.reputations.tolist(),
            "agg_norm": float(np.linalg.norm(aggregated_grad)),
        }

        return aggregated_grad, info

    # ----- Reputation management -----

    ALPHA = 0.1   # EMA smoothing factor for reputation
    GAMMA = 0.02  # Forgetting/restoration rate (S7 fairness mitigation)
    R_SS = 0.85   # Steady-state reputation pull target (S7)
    PROBATION_LIMIT = 10  # Rounds before permanent exclusion

    def _update_reputation(self, client_id: int, score: float):
        """Update per-client reputation with forgetting mechanism (S7).

        Standard EMA with an additional forgetting term that pulls reputation
        toward a steady-state value R_SS. This prevents a single bad round
        from permanently tanking an honest client's reputation.

        R_i(t+1) = R_i(t) + ALPHA·(score - R_i(t)) + GAMMA·(R_SS - R_i(t))
        """
        r = self.reputations[client_id]
        r = r + self.ALPHA * (score - r) + self.GAMMA * (self.R_SS - r)
        self.reputations[client_id] = float(np.clip(r, 0.0, 1.0))

    # ----- Aggregation -----

    def _reputation_weighted_aggregate(
        self,
        updates: list[np.ndarray],
        scores: np.ndarray,
    ) -> np.ndarray:
        """Aggregate accepted and down-weighted suspicious updates."""
        N = len(updates)
        weights = np.zeros(N)

        for i in range(N):
            if scores[i] >= self.theta_accept:
                weights[i] = self.reputations[i]
            elif scores[i] >= self.theta_reject:
                weights[i] = self.reputations[i] * self.suspicious_weight
            # else: rejected — weight stays 0

        if weights.sum() == 0:
            return np.zeros_like(updates[0])

        agg = np.sum(
            [w * g for w, g in zip(weights, updates)],
            axis=0,
        )
        return agg / weights.sum()

    # ----- Adaptive threshold update -----

    def _detect_attack(self, scores: np.ndarray) -> bool:
        """Fire attack alarm if flag rate deviates from baseline.

        Uses a rolling window of historical flag rates to detect
        statistically significant deviations.
        """
        # Fraction of clients NOT fully accepted
        rho_t = float(np.mean(scores < self.theta_accept))

        self.rho_history.append(rho_t)
        if len(self.rho_history) > self.alarm_window:
            self.rho_history.pop(0)

        # Need minimum history for stable detection
        if len(self.rho_history) < 10:
            return False

        rho_mean = float(np.mean(self.rho_history))
        rho_std = max(float(np.std(self.rho_history)), 1e-8)

        # Statistical test: 2-sigma deviation from rolling baseline
        return rho_t > rho_mean + 2 * rho_std

    def _update_thresholds(self, scores: np.ndarray):
        """Adapt τ₁, τ₂ based on detected attack intensity.

        Under attack: tighten thresholds (escalate more → stronger scrutiny).
        Normal: relax thresholds (escalate less → efficiency).
        """
        under_attack = self._detect_attack(scores)

        if under_attack:
            rho_t = float(np.mean(scores < self.theta_accept))
            # Tighten: lower thresholds → more escalation
            self.tau_1 = max(
                self.TAU_1_MIN,
                self.tau_1 - self.eta_attack * rho_t,
            )
            self.tau_2 = max(
                self.TAU_2_MIN,
                self.tau_2 - self.eta_attack * rho_t,
            )
        else:
            # Relax: raise thresholds toward max (less escalation)
            self.tau_1 = min(
                self.TAU_1_MAX,
                self.tau_1 + self.eta_relax * (self.TAU_1_MAX - self.tau_1),
            )
            self.tau_2 = min(
                self.TAU_2_MAX,
                self.tau_2 + self.eta_relax * (self.TAU_2_MAX - self.tau_2),
            )

    # ----- Utility -----

    def get_stats(self) -> dict:
        """Return current state for logging."""
        return {
            "tau_1": self.tau_1,
            "tau_2": self.tau_2,
            "round": self.t,
            "mean_reputation": float(np.mean(self.reputations)),
            "min_reputation": float(np.min(self.reputations)),
        }
