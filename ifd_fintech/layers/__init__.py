"""
IFD-Fintech detection layers.

Each layer implements a .score(update) -> (anomaly_score, confidence) interface.
"""

from .layer1_norm_cosine import NormCosineFilter
from .layer2_spectral import SpectralDetector
from .layer3_temporal import TemporalReputation

__all__ = ["NormCosineFilter", "SpectralDetector", "TemporalReputation"]
