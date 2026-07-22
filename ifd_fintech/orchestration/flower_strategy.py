"""
Flower-compatible strategy wrapping the adaptive threshold escalation.

This is the entry point for the Flower simulation. The strategy wraps
AdaptiveThresholdEscalation and handles the Flower protocol (Parameters
serialization, client proxy interface, etc.).
"""

from typing import Optional
from flwr.common import Parameters, ndarrays_to_parameters, parameters_to_ndarrays


class AdaptiveLayeredDefenseStrategy:
    """Flower strategy wrapping the 3-layer defense.

    Converts between Flower's Parameters format and numpy arrays,
    delegates to AdaptiveThresholdEscalation for the core logic.
    """

    def __init__(self, n_clients: int, model_dim: int):
        self.orchestrator = __import__(
            "ifd_fintech.orchestration",
            fromlist=["CascadeRouter"],
        ).CascadeRouter(n_clients, model_dim)
        self.model_dim = model_dim
        self.current_global_model: Optional[np.ndarray] = None

    def initialize_parameters(self, initial_weights: np.ndarray):
        """Set initial global model weights."""
        self.current_global_model = initial_weights.copy()

    def aggregate_fit(self, server_round: int, results, failures):
        """Flower-compatible aggregate_fit.

        Args:
            results: List of (ClientProxy, FitRes) from Flower clients.
        """
        updates = []
        for _, fit_res in results:
            params = parameters_to_ndarrays(fit_res.parameters)
            client_weights = params[0]

            # Compute gradient: g_i = w_i - w_global
            grad = client_weights - self.current_global_model
            updates.append(grad)

        # Run core defense orchestration
        aggregated_grad, info = self.orchestrator.process_round(updates)

        # Update global model
        self.current_global_model = self.current_global_model + aggregated_grad

        # Convert back to Flower Parameters
        new_params = ndarrays_to_parameters([self.current_global_model])
        return new_params, info
