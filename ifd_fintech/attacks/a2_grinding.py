"""
A2: Gradient Grinding Attack

Slow, incremental model poisoning that stays below per-round detection
thresholds. The attacker submits barely-noticeable malicious signals each
round, accumulating the backdoor over many rounds.

Reference: attacker-design.md §4
"""

from typing import Optional

import numpy as np

from . import AdaptiveAttacker


class GradientGrinding(AdaptiveAttacker):
    """Grinding attacker that slowly drifts the global model.

    Maintains an honest reputation initially, then gradually injects
    malicious signal below the adaptive threshold alarm sensitivity.
    Uses a 4-phase schedule: burn-in → subliminal → active → cooldown.
    """

    def __init__(
        self,
        n_malicious: int,
        burn_in: int = 20,
        subliminal: int = 60,
        active: int = 100,
        cooldown: int = 120,
        lambda_max: float = 0.15,
        defense_knowledge: Optional[dict] = None,
        backdoor_trigger: Optional[np.ndarray] = None,
        backdoor_target: int = 0,
    ):
        super().__init__(n_malicious, defense_knowledge, backdoor_trigger, backdoor_target)
        self.burn_in = burn_in
        self.subliminal = subliminal
        self.active = active
        self.cooldown = cooldown
        self.lambda_max = lambda_max
        self._drift_direction: Optional[np.ndarray] = None

    def _get_phase(self, round_t: int) -> str:
        """Determine which phase of the attack we're in."""
        if round_t <= self.burn_in:
            return "burn_in"
        elif round_t <= self.subliminal:
            return "subliminal"
        elif round_t <= self.active:
            return "active"
        else:
            return "cooldown"

    def _lambda(self, phase: str) -> float:
        """Grinding coefficient per phase."""
        mapping = {
            "burn_in": 0.0,
            "subliminal": self.lambda_max * 0.3,
            "active": self.lambda_max * 0.6,
            "cooldown": 0.0,
        }
        return mapping[phase]

    def _estimate_norm_bound(self, updates: list[np.ndarray]) -> float:
        """Estimate the maximum safe gradient magnitude.

        Uses the upper bound of Layer 1's acceptance region.
        """
        norms = np.array([np.linalg.norm(g) for g in updates])
        mu = np.mean(norms)
        sigma = max(np.std(norms), 1e-8)
        return mu + 2.0 * sigma  # 2-sigma bound

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

        # Initialize drift direction on first active round
        if self._drift_direction is None:
            self._drift_direction = np.random.randn(updates[0].shape[0])
            self._drift_direction = self._drift_direction / (np.linalg.norm(self._drift_direction) + 1e-8)

        phase = self._get_phase(round_t)
        lam = self._lambda(phase)
        norm_bound = self._estimate_norm_bound(updates)

        for idx in mal_indices:
            g_honest = updates[idx].copy()

            if phase == "burn_in":
                # Submit fully honest updates
                modified[idx] = g_honest
            elif phase == "cooldown":
                # Back to honest (detoxify reputation)
                modified[idx] = g_honest
            else:
                # Inject drift, bounded by Layer 1 acceptance
                drift = lam * self._drift_direction

                # Scale drift to not exceed the norm bound
                mal_norm = np.linalg.norm(g_honest + drift)
                if mal_norm > norm_bound:
                    scale = (norm_bound - 1e-8) / (mal_norm + 1e-8)
                    drift = drift * scale

                modified[idx] = g_honest + drift

        return modified
