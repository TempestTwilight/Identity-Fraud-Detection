"""
Baseline defense implementations for comparison.

Each baseline implements a `filter_updates(updates, client_ids, round_t)`
interface for drop-in comparison with our defense.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Optional


class Baseline(ABC):
    """Abstract base for all baseline defenses."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def filter_updates(
        self,
        updates: list[np.ndarray],
        client_ids: Optional[list[int]] = None,
        round_t: int = 0,
    ) -> tuple[list[np.ndarray], list[int]]:
        """Filter and/or score client updates.

        Args:
            updates: Per-client gradient updates.
            client_ids: Optional client identifiers.
            round_t: Current training round.

        Returns:
            (filtered_updates, accepted_indices) — updates that pass
            the baseline's filtering, and their original indices.
        """
        ...
