"""
Defense explainability module for regulatory compliance.

Provides human-readable explanations of defense decisions for:
- Regulatory audit trail (SR 11-7, FATF Rec. 15)
- GDPR Article 22 compliance (meaningful info about automated decisions)
- Debugging and transparency
"""

import numpy as np
import json


class DefenseRecord:
    """A single defense event: a client flagged at a round."""

    def __init__(
        self,
        round_t: int,
        client_id: int,
        norm: float = 0.0,
        cos_sim: float = 0.0,
        spectral_score: float = 1.0,
        temporal_score: float = 1.0,
        anomaly_score: float = 0.0,
        was_flagged: bool = False,
        layer_responsible: str = "",
    ):
        self.round_t = round_t
        self.client_id = client_id
        self.norm = norm
        self.cos_sim = cos_sim
        self.spectral_score = spectral_score
        self.temporal_score = temporal_score
        self.anomaly_score = anomaly_score
        self.was_flagged = was_flagged
        self.layer_responsible = layer_responsible

    def explain(self) -> str:
        """Generate a human-readable explanation for this event."""
        if not self.was_flagged:
            return f"Client {self.client_id} at round {self.round_t}: benign"

        reasons = []
        if self.layer_responsible in ("layer1", "all"):
            reasons.append(
                f"Layer 1 (Norm/Cosine): norm={self.norm:.3f}, "
                f"cosine_sim={self.cos_sim:.3f} — outside acceptance region"
            )
        if self.layer_responsible in ("layer2", "all"):
            reasons.append(
                f"Layer 2 (Spectral): residual_score={self.spectral_score:.3f} "
                f"— anomalous spectral signature"
            )
        if self.layer_responsible in ("layer3", "all"):
            reasons.append(
                f"Layer 3 (Temporal): reputation={self.temporal_score:.3f} "
                f"— anomalous consistency pattern"
            )

        return (f"Client {self.client_id} FLAGGED at round {self.round_t}: "
                f"aggregate_anomaly={self.anomaly_score:.3f}\n" +
                "\n".join(f"  {r}" for r in reasons))


class DefenseExplainer:
    """Generates regulatory audit reports from defense history."""

    def __init__(self):
        self.history: list[DefenseRecord] = []

    def add_record(self, record: DefenseRecord):
        """Add a defense event to the audit trail."""
        self.history.append(record)

    def explain_flagging(self, client_id: int, round_t: int) -> str:
        """Explain why a specific client was flagged at a specific round."""
        for record in self.history:
            if record.client_id == client_id and record.round_t == round_t:
                return record.explain()
        return f"Client {client_id} was not flagged at round {round_t}."

    def audit_trail(
        self, start_round: int = 0, end_round: int | None = None
    ) -> str:
        """Generate a complete regulatory audit report.

        Returns:
            JSON-formatted audit trail.
        """
        if end_round is None:
            end_round = max((r.round_t for r in self.history), default=0)

        filtered = [
            r for r in self.history
            if start_round <= r.round_t <= end_round
        ]

        report = {
            "purpose": "IFD-Fintech defense audit trail",
            "round_range": [start_round, end_round],
            "total_events": len(filtered),
            "total_flags": sum(1 for r in filtered if r.was_flagged),
            "events": [
                {
                    "round": r.round_t,
                    "client": r.client_id,
                    "flagged": r.was_flagged,
                    "responsible_layer": r.layer_responsible,
                    "anomaly_score": r.anomaly_score,
                    "scores": {
                        "norm": r.norm,
                        "cosine": r.cos_sim,
                        "spectral": r.spectral_score,
                        "temporal": r.temporal_score,
                    },
                }
                for r in filtered
            ],
        }
        return json.dumps(report, indent=2)

    def to_dataframe(self, start_round: int = 0, end_round: int | None = None):
        """Export to pandas DataFrame (for further analysis)."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for to_dataframe(). "
                              "Install with: uv pip install pandas")

        records = [
            {
                "round": r.round_t,
                "client": r.client_id,
                "flagged": r.was_flagged,
                "layer": r.layer_responsible,
                "anomaly_score": r.anomaly_score,
                "norm": r.norm,
                "cosine": r.cos_sim,
                "spectral": r.spectral_score,
                "temporal": r.temporal_score,
            }
            for r in self.history
        ]
        return pd.DataFrame(records)
