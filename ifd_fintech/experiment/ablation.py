"""
Ablation study configuration and runner.

Defines ablation configs (which layers are active) and the runner
that orchestrates evaluations across configs and attacks.
"""

from typing import Optional
import numpy as np

# Each entry maps layer name -> enabled flag
# "adaptive" controls whether thresholds adapt via the attack alarm signal.
# When adaptive=False, thresholds are fixed at tau_1=0.75, tau_2=0.70.
ABLATION_CONFIGS: dict[str, dict[str, bool]] = {
    # --- Existing configs ---
    "full":    {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": True},
    "no_l1":   {"layer1": False, "layer2": True,  "layer3": True,  "adaptive": True},
    "no_l2":   {"layer1": True,  "layer2": False, "layer3": True,  "adaptive": True},
    "no_l3":   {"layer1": True,  "layer2": True,  "layer3": False, "adaptive": True},
    "no_at":   {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": False},
    "l1_only": {"layer1": True,  "layer2": False, "layer3": False, "adaptive": True},
    "l2_only": {"layer1": False, "layer2": True,  "layer3": False, "adaptive": True},
    "l3_only": {"layer1": False, "layer2": False, "layer3": True,  "adaptive": True},

    # --- NEW: Cascade controls (S4) ---
    # cascade_fixed: Full 3-layer cascade with fixed thresholds (no adaptivity).
    # Isolates the value of the cascade structure from adaptive threshold novelty.
    "cascade_fixed": {
        "layer1": True, "layer2": True, "layer3": True, "adaptive": False,
    },
    # cascade_oracle: Full cascade with per-round optimal thresholds chosen by
    # an oracle that knows which clients are malicious. Provides an upper bound
    # on adaptive threshold performance. In practice, thresholds sweep over
    # tau_1, tau_2 in [0.55, 0.90] and pick the best ASR@fixed FPR.
    "cascade_oracle": {
        "layer1": True, "layer2": True, "layer3": True, "adaptive": False, "oracle": True,
    },
}


def get_active_layers(config_name: str) -> tuple[bool, bool, bool, bool]:
    """Get the active layer flags for a named config.

    Returns:
        (layer1, layer2, layer3, adaptive_thresholds)
    """
    config = ABLATION_CONFIGS.get(config_name)
    if config is None:
        raise ValueError(f"Unknown ablation config: {config_name}. "
                         f"Available: {list(ABLATION_CONFIGS.keys())}")
    return (
        config["layer1"],
        config["layer2"],
        config["layer3"],
        config["adaptive"],
    )


class AblationRunner:
    """Runs evaluation across ablation configs and attacks.

    Orchestrates the FL simulation with specific layer configuration
    and attack type, collecting evaluation metrics.
    """

    def __init__(
        self,
        layer_config: dict[str, bool],
        n_runs: int = 5,
        n_rounds: int = 200,
        n_clients: int = 20,
    ):
        self.layer_config = layer_config
        self.n_runs = n_runs
        self.n_rounds = n_rounds
        self.n_clients = n_clients
        self.config_name = self._infer_name()

    def _infer_name(self) -> str:
        """Reverse-lookup the config name from flags."""
        for name, cfg in ABLATION_CONFIGS.items():
            if cfg == self.layer_config:
                return name
        return "custom"

    @staticmethod
    def _aggregate(results: list[dict]) -> dict:
        """Aggregate multiple runs with mean and std."""
        if not results:
            return {}
        keys = results[0].keys()
        aggregated = {}
        for k in keys:
            values = [r[k] for r in results if k in r]
            if values and isinstance(values[0], (int, float)):
                aggregated[f"{k}_mean"] = float(np.mean(values))
                aggregated[f"{k}_std"] = float(np.std(values))
            else:
                aggregated[k] = values[0] if values else None
        return aggregated

    # In a full implementation, run() would call the FL simulator
    # with appropriate layer config and attack. For now, we define
    # the interface.
    def run(self) -> dict:
        """Run evaluation and return aggregated results.

        Returns:
            dict with config name, per-attack metrics.
        """
        return {
            "config": self.config_name,
            "layers": self.layer_config,
            "n_runs": self.n_runs,
            "status": "pipeline stub — call run_experiment() for execution",
        }
