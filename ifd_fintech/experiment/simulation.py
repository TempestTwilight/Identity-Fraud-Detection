"""In-process FL simulation with the cascade defense.

Orchestrates:
  1. Data loading (IEEE-CIS, or synthetic fallback)
  2. Dirichlet-based non-IID partitioning
  3. FraudClient creation per partition
  4. Federated rounds with CascadeRouter defense
  5. Attack injection via AttackSuite
  6. Metric collection

No gRPC or multi-process overhead — each client trains sequentially.
Can be swapped for a full Flower simulation later by reusing FraudClient.
"""

import sys
import time
from pathlib import Path
from typing import Optional
import numpy as np
import torch

from ifd_fintech.data.loader import load_ieee_cis, load_synthetic
from ifd_fintech.data.dataset import FraudDataset
from ifd_fintech.data import dirichlet_split
from ifd_fintech.experiment.client import FraudClient
from ifd_fintech.experiment.model import FraudMLP
from ifd_fintech.experiment.metrics import compute_metrics
from ifd_fintech.layers.layer1_norm_cosine import NormCosineFilter
from ifd_fintech.layers.layer2_spectral import SpectralDetector
from ifd_fintech.layers.layer3_temporal import TemporalReputation
from ifd_fintech.orchestration import CascadeRouter


class Simulation:
    """In-process FL simulation with configurable defense and attacks.

    Usage:
        sim = Simulation(n_clients=20, n_rounds=100)
        sim.load_data(source="synthetic")
        sim.build_defense()
        sim.run()
        sim.report()
    """

    def __init__(
        self,
        n_clients: int = 20,
        n_rounds: int = 50,
        clients_per_round: int = 10,
        n_malicious: int = 2,
        alpha_dirichlet: float = 0.5,
        attack_id: Optional[str] = None,
        seed: int = 42,
        device: str = "cpu",
    ):
        self.n_clients = n_clients
        self.n_rounds = n_rounds
        self.clients_per_round = min(clients_per_round, n_clients)
        self.n_malicious = n_malicious
        self.alpha = alpha_dirichlet
        self.attack_id = attack_id
        self.seed = seed
        self.device = device
        self.rng = np.random.RandomState(seed)

        # Populated by load_data()
        self.dataset_info: dict = {}
        self.clients: list[FraudClient] = []

        # Populated by build_defense()
        self.defense: Optional[CascadeRouter] = None
        self.layers_initialized = False

        # Populated by run()
        self.history: list[dict] = []

    # ── Data pipeline (swap this method to use a different dataset) ──

    def load_data(
        self,
        source: str = "synthetic",
        data_dir: Optional[str | Path] = None,
        n_samples: int = 5000,
        n_features: int = 30,
    ):
        """Load and partition data across clients.

        Args:
            source: 'synthetic' or 'ieee-cis'.
            data_dir: Path to IEEE-CIS CSV files (required if source='ieee-cis').
            n_samples: Synthetic samples (ignored for ieee-cis).
            n_features: Synthetic feature dim (ignored for ieee-cis).
        """
        print(f"\n{'='*60}")
        print(f"  Loading data (source={source})...")
        print(f"{'='*60}")

        if source == "synthetic":
            data = load_synthetic(n_samples=n_samples, n_features=n_features)
        elif source == "ieee-cis":
            data = load_ieee_cis(data_dir or ".")
        else:
            raise ValueError(f"Unknown data source: {source}")

        X_train, y_train = data["X_train"], data["y_train"]
        self.dataset_info = data

        # Partition across clients via Dirichlet label skew
        indices = dirichlet_split(
            labels=y_train,
            n_clients=self.n_clients,
            alpha=self.alpha,
            seed=self.seed,
        )

        self.clients = []
        for cid in range(self.n_clients):
            idx = indices[cid]
            if len(idx) == 0:
                idx = np.array([0])  # ensure at least 1 sample per client
            partition = FraudDataset(X_train[idx], y_train[idx])
            client = FraudClient(
                client_id=cid,
                dataset=partition,
                input_dim=data["n_features"],
                device=self.device,
            )
            self.clients.append(client)

        print(f"  {len(self.clients)} clients created")
        print(f"  Partition sizes: min={min(len(c.dataset) for c in self.clients)}, "
              f"max={max(len(c.dataset) for c in self.clients)}")

    # ── Defense pipeline ──

    def build_defense(self):
        """Build CascadeRouter with all 3 detection layers."""
        n_features = self.dataset_info.get("n_features", 30)

        # Warm-up with random data for L1 statistics
        warmup = [self.rng.randn(n_features).astype(np.float32) * 0.1
                  for _ in range(self.n_clients * 2)]

        l1 = NormCosineFilter(n_features)
        l1.fit(warmup)

        l2 = SpectralDetector(n_features)
        l3 = TemporalReputation(self.n_clients)

        self.defense = CascadeRouter(self.n_clients, n_features)
        self.defense.set_layers(l1, l2, l3)
        self.layers_initialized = True
        print(f"  Defense built: CascadeRouter(n_clients={self.n_clients}, dim={n_features})")

    # ── Attack injection ──

    def _apply_attack(self, round_t: int, updates: list[np.ndarray],
                      global_model: np.ndarray) -> list[np.ndarray]:
        """Apply the configured attack, if any."""
        if self.attack_id is None:
            return updates

        # Lazily import attack suite
        from ifd_fintech.attacks.a1_oracle_whitebox import OracleWhiteBox
        from ifd_fintech.attacks.a2_grinding import GradientGrinding
        from ifd_fintech.attacks.a3_spectral_matching import SpectralMatching

        return updates  # TODO: instantiate attack by self.attack_id

    # ── Main training loop ──

    def run(self):
        """Execute the FL simulation with defense."""
        if not self.clients:
            raise RuntimeError("No clients. Call load_data() first.")
        if self.defense is None:
            self.build_defense()

        print(f"\n{'='*60}")
        print(f"  Running {self.n_rounds} FL rounds with cascade defense")
        if self.attack_id:
            print(f"  Attack: {self.attack_id}")
        print(f"{'='*60}")

        # Initialize global model
        n_features = self.dataset_info["n_features"]
        global_model = FraudMLP(input_dim=n_features).to(self.device)
        global_params = global_model.get_weights()
        # Flatten for gradient representation
        global_flat = np.concatenate([p.ravel() for p in global_params])

        # Warm-up L1 on initial random gradients (not data)
        warmup_grads = [np.random.randn(len(global_flat)).astype(np.float32) * 0.1
                        for _ in range(min(self.n_clients, 10))]
        if self.defense and self.defense.layer1:
            self.defense.layer1.fit(warmup_grads)

        start_time = time.time()

        for rnd in range(1, self.n_rounds + 1):
            # ── Select clients for this round ──
            selected = self.rng.choice(
                self.n_clients,
                size=self.clients_per_round,
                replace=False,
            )

            # ── Each selected client trains and returns gradient ──
            client_updates = []
            for cid in selected:
                grad = self._client_gradient(self.clients[cid], global_model)
                client_updates.append(grad)

            # ── Apply attack ──
            if self.attack_id:
                client_updates = self._apply_attack(
                    rnd, client_updates, global_flat
                )

            # ── Defend and aggregate ──
            if self.defense:
                agg_grad, info = self.defense.process_round(client_updates)
                # Apply aggregated gradient to global model
                global_flat = global_flat + 0.01 * agg_grad
                self._set_model_flat(global_model, global_flat)
            else:
                # Fallback: simple average
                agg_grad = np.mean(client_updates, axis=0)
                global_flat = global_flat + 0.01 * agg_grad
                info = {}

            # ── Track metrics ──
            rep_array = np.array(info.get("reputations", []))
            self.history.append({
                "round": rnd,
                "agg_norm": info.get("agg_norm", float(np.linalg.norm(agg_grad))),
                "tau_1": info.get("tau_1", 0),
                "tau_2": info.get("tau_2", 0),
                "mean_rep": float(rep_array.mean()) if len(rep_array) > 0 else 0,
                "escalation": info.get("escalation_stats", {}),
            })

            # ── Track metrics ──
            rep_array = np.array(info.get("reputations", []))
            self.history.append({
                "round": rnd,
                "agg_norm": info.get("agg_norm", 0),
                "tau_1": info.get("tau_1", 0),
                "tau_2": info.get("tau_2", 0),
                "mean_rep": float(rep_array.mean()) if len(rep_array) > 0 else 0,
                "escalation": info.get("escalation_stats", {}),
            })

            if rnd % 10 == 0 or rnd == 1:
                h = self.history[-1]
                print(f"  Round {rnd:3d}: agg_norm={h['agg_norm']:.4f}  "
                      f"τ₁={h['tau_1']:.3f}  τ₂={h['tau_2']:.3f}  "
                      f"mean_rep={h['mean_rep']:.3f}")

        elapsed = time.time() - start_time
        print(f"\n  Simulation complete: {self.n_rounds} rounds in {elapsed:.1f}s")

    def _client_gradient(
        self, client: FraudClient, global_model: FraudMLP
    ) -> np.ndarray:
        """Compute client gradient: flattened(updated_weights - global_weights).

        Trains the client for 1 epoch starting from global model weights,
        then returns the parameter delta as a flat vector.
        """
        # Set client model to global weights
        client.model.set_weights(global_model.get_weights())

        # Train for 1 local epoch
        loader = torch.utils.data.DataLoader(
            client.dataset, batch_size=min(64, len(client.dataset)), shuffle=True
        )
        client.model.train()
        for X_batch, y_batch in loader:
            X_batch = X_batch.to(client.device)
            y_batch = y_batch.to(client.device)
            client.optimizer.zero_grad()
            logits = client.model(X_batch)
            loss = client.criterion(logits, y_batch)
            loss.backward()
            client.optimizer.step()

        # Compute gradient = updated - global
        updated = client.model.get_weights()
        grad_parts = []
        for p_updated, p_global in zip(updated, global_model.get_weights()):
            grad_parts.append((p_updated - p_global).ravel())
        return np.concatenate(grad_parts).astype(np.float32)

    @staticmethod
    def _set_model_flat(model: FraudMLP, flat_params: np.ndarray):
        """Set model parameters from a flat numpy array."""
        idx = 0
        new_weights = []
        for p in model.parameters():
            size = p.numel()
            new_weights.append(flat_params[idx:idx + size].reshape(p.shape))
            idx += size
        model.set_weights(new_weights)

    # ── Results ──

    def report(self):
        """Print summary of the simulation run."""
        if not self.history:
            print("No history. Run the simulation first.")
            return

        print(f"\n{'='*60}")
        print(f"  Simulation Summary")
        print(f"{'='*60}")
        print(f"  Rounds: {len(self.history)}")
        print(f"  Clients: {self.n_clients} ({self.clients_per_round}/round)")

        final = self.history[-1]
        initial = self.history[0]
        print(f"  Final tau_1: {final['tau_1']:.3f} (from {initial['tau_1']:.3f})")
        print(f"  Final tau_2: {final['tau_2']:.3f} (from {initial['tau_2']:.3f})")
        print(f"  Final mean reputation: {final['mean_rep']:.3f}")

        es = final.get("escalation", {})
        if es:
            total = sum(es.values())
            print(f"  Escalation (last round): L1={es.get('layer1',0)} "
                  f"L2={es.get('layer2',0)} L3={es.get('layer3',0)} "
                  f"(total={total})")

        # Per-client data distribution summary
        sizes = [len(c.dataset) for c in self.clients]
        print(f"  Data per client: min={min(sizes)}, max={max(sizes)}, "
              f"mean={np.mean(sizes):.0f}")

        if self.attack_id:
            print(f"  Attack: {self.attack_id}")
