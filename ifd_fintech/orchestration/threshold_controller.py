"""ThresholdController — adaptive threshold adaptation + attack alarm.

Extracted from the original AdaptiveThresholdEscalation monolith.
Responsible for:
  1. Detecting attack conditions via rolling flag-rate alarm
  2. Adapting tau_1, tau_2 thresholds (tighten under attack, relax otherwise)
"""

from typing import Optional
import numpy as np


class ThresholdController:
    """Manages tau_1/tau_2 adaptation and the attack alarm signal.

    The alarm fires when the fraction of non-fully-accepted clients deviates
    beyond 2 sigma from its rolling baseline. Under attack, thresholds tighten
    (more escalation) at eta_attack per round; in benign periods they relax
    toward max at eta_relax per round.
    """

    def __init__(
        self,
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
        # Alarm parameters
        rho_0: float = 0.10,
        sigma_rho: float = 0.05,
        alarm_window: int = 20,
    ):
        # Threshold state
        self.tau_1 = tau_1_init
        self.tau_2 = tau_2_init
        self.TAU_1_MIN, self.TAU_1_MAX = tau_1_min, tau_1_max
        self.TAU_2_MIN, self.TAU_2_MAX = tau_2_min, tau_2_max

        # Adaptation rates
        self.eta_attack = eta_attack
        self.eta_relax = eta_relax

        # Alarm state
        self.rho_0 = rho_0
        self.sigma_rho = sigma_rho
        self.rho_history: list[float] = []
        self.alarm_window = alarm_window

    # ----- Alarm -----

    def detect_attack(self, scores: np.ndarray) -> bool:
        """Fire attack alarm if flag rate deviates from rolling baseline.

        Args:
            scores: Per-client anomaly scores for the current round.

        Returns:
            True if attack conditions detected.
        """
        theta_accept = 0.60  # matches CascadeRouter default; could be injected
        rho_t = float(np.mean(scores < theta_accept))

        self.rho_history.append(rho_t)
        if len(self.rho_history) > self.alarm_window:
            self.rho_history.pop(0)

        if len(self.rho_history) < 10:
            return False

        rho_mean = float(np.mean(self.rho_history))
        rho_std = max(float(np.std(self.rho_history)), 1e-8)
        return rho_t > rho_mean + 2 * rho_std

    # ----- Threshold adaptation -----

    def adapt(self, scores: np.ndarray):
        """Adapt tau_1, tau_2 based on detected attack intensity.

        Args:
            scores: Per-client anomaly scores for the current round.
        """
        under_attack = self.detect_attack(scores)

        if under_attack:
            rho_t = float(np.mean(scores < 0.60))  # theta_accept default
            self.tau_1 = max(self.TAU_1_MIN, self.tau_1 - self.eta_attack * rho_t)
            self.tau_2 = max(self.TAU_2_MIN, self.tau_2 - self.eta_attack * rho_t)
        else:
            self.tau_1 = min(self.TAU_1_MAX, self.tau_1 + self.eta_relax * 0.1)
            self.tau_2 = min(self.TAU_2_MAX, self.tau_2 + self.eta_relax * 0.1)

    # ----- Properties -----

    @property
    def current_thresholds(self) -> tuple[float, float]:
        """(tau_1, tau_2) for the current round."""
        return self.tau_1, self.tau_2
