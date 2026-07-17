"""
Attack models for robustness evaluation.

Each attack implements `craft_update(round_t, updates, global_model, loss_fn)`
and returns a modified list of updates with some clients compromised.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Optional


class AdaptiveAttacker(ABC):
    """Base class for adaptive attackers with white-box defense knowledge.

    The attacker knows the defense architecture and adapts its strategy
    to evade detection across all 3 layers.
    """

    def __init__(
        self,
        n_malicious: int,
        defense_knowledge: Optional[dict] = None,
        backdoor_trigger: Optional[np.ndarray] = None,
        backdoor_target: int = 0,
    ):
        self.n_malicious = n_malicious
        self.knowledge = defense_knowledge or {}
        self.backdoor_trigger = backdoor_trigger
        self.backdoor_target = backdoor_target
        self.rounds_active = 0

    @abstractmethod
    def craft_update(
        self,
        round_t: int,
        updates: list[np.ndarray],
        global_model: np.ndarray,
        loss_fn=None,
    ) -> list[np.ndarray]:
        """Replace some client updates with crafted malicious gradients.

        Args:
            round_t: Current training round.
            updates: List of per-client gradient updates (len = N clients).
            global_model: Current global model parameters.
            loss_fn: Loss function (needed for computing backdoor gradients).

        Returns:
            Modified list of updates with the last self.n_malicious
            entries replaced with crafted attacks.
        """
        ...

    def _set_backdoor_target(self, trigger: np.ndarray, target: int):
        """Define the backdoor pattern the attacker wants to embed."""
        self.backdoor_trigger = trigger
        self.backdoor_target = target

    def _select_malicious_indices(self, n_total: int) -> list[int]:
        """Select which client indices to compromise (last n entries)."""
        return list(range(n_total - self.n_malicious, n_total))
