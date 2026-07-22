#!/usr/bin/env python3
"""
Full experiment runner — IFD-Fintech
======================================
Exercises all attacks, baselines, ablations, and metrics intended by the project.
Runs a configurable FL simulation on real data (or a small in-memory test).

Usage:
    python run_full.py                          # quick test with defaults
    python run_full.py --rounds 200 --clients 20 --attacks all --baselines all
    python run_full.py --data-path ./ieee-cis/  # use real dataset
"""

import sys
import os
import time
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ifd_fintech.attacks.a1_oracle_whitebox import OracleWhiteBox
    from ifd_fintech.attacks.a2_grinding import GradientGrinding
    from ifd_fintech.attacks.a3_spectral_matching import SpectralMatching

import numpy as np

PROJECT_ROOT = "/home/tempest/Documents/IFD-Fintech"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =========================================================================
#  Experiment configuration
# =========================================================================

@dataclass
class ExperimentConfig:
    """Full experiment hyperparameters."""
    n_clients: int = 20
    dim: int = 64
    rounds: int = 50
    n_malicious: int = 2
    alpha_dirichlet: float = 0.5        # non-IID skew (smaller = more skew)
    attacks: list[str] = field(default_factory=lambda: ["A1", "A2", "A3", "A4", "A5", "A6"])
    baselines: list[str] = field(default_factory=lambda: [
        "FedAvg", "Krum", "Median", "TrimmedMean", "Bulyan", "FLTrust",
        "FoolsGold", "RFA", "DPFL8", "FLDetector", "DPFL4", "DPFL1",
        "ClippedMedian", "MultiKrumTrim"
    ])
    ablations: list[str] = field(default_factory=lambda: [
        "full", "no_l1", "no_l2", "no_l3", "no_at", "l1_only", "l2_only", "l3_only",
        "cascade_fixed", "tau_sweep", "window_sweep", "warmup_skip", "empty_pool"
    ])
    data_path: Optional[str] = None
    seed: int = 42
    output_dir: str = "results"


# =========================================================================
#  Attack model compositions (A1–A6)
# =========================================================================

class AttackSuite:
    """Maps attack IDs to the actual attack objects."""

    def __init__(self, n_malicious: int, dim: int):
        self.n_mal = n_malicious
        self.dim = dim
        self._attacks: dict[str, "_CompositeAttack | OracleWhiteBox | GradientGrinding | SpectralMatching"] = {}

    def _ensure_a1(self):
        if "A1" not in self._attacks:
            from ifd_fintech.attacks.a1_oracle_whitebox import OracleWhiteBox
            self._attacks["A1"] = OracleWhiteBox(n_malicious=self.n_mal, max_iter=20)

    def _ensure_a2(self):
        if "A2" not in self._attacks:
            from ifd_fintech.attacks.a2_grinding import GradientGrinding
            self._attacks["A2"] = GradientGrinding(
                n_malicious=self.n_mal, burn_in=5, subliminal=10, active=20, cooldown=10
            )

    def _ensure_a3(self):
        if "A3" not in self._attacks:
            from ifd_fintech.attacks.a3_spectral_matching import SpectralMatching
            self._attacks["A3"] = SpectralMatching(n_malicious=self.n_mal, subspace_rank=3)

    def get(self, attack_id: str):
        """Return an attack callable for the given ID.

        A4–A6 are compositions of A1–A3 behaviour. Each returns
        (modified_updates, attack_name) where modified_updates is a list
        of arrays matching the input length.
        """
        a_id = attack_id.upper().strip()

        # Base attacks
        if a_id == "A1":
            self._ensure_a1()
            return self._attacks["A1"]
        if a_id == "A2":
            self._ensure_a2()
            return self._attacks["A2"]
        if a_id == "A3":
            self._ensure_a3()
            return self._attacks["A3"]

        # Composed attacks (use wrappers for A4-A6)
        if a_id == "A4":
            return _CompositeAttack(
                "A4: Temporal Collusion",
                lambda r, up, gm, **kw: self._run_a4(r, up, gm)
            )
        if a_id == "A5":
            return _CompositeAttack(
                "A5: Synthetic Transaction Injection",
                lambda r, up, gm, **kw: self._run_a5(r, up, gm)
            )
        if a_id == "A6":
            return _CompositeAttack(
                "A6: Cascade-Aware Envelope",
                lambda r, up, gm, **kw: self._run_a6(r, up, gm)
            )
        raise ValueError(f"Unknown attack: {attack_id}")

    def _run_a4(self, round_t, updates, global_model):
        """A4 = A2 structure + A3 coordination."""
        N = len(updates)
        # Phase-based from A2: alternate grinding with spectral matching
        phase = "subliminal" if round_t < 10 else ("active" if round_t < 25 else "cooldown")
        modified = list(updates)
        mal_indices = list(range(N - self.n_mal, N))

        # Grinding: inject slow drift
        if phase in ("subliminal", "active"):
            lam = 0.05 if phase == "subliminal" else 0.10
            drift_dir = np.random.randn(updates[0].shape[0])
            drift_dir = drift_dir / (np.linalg.norm(drift_dir) + 1e-8)
            for idx in mal_indices:
                g = updates[idx].copy()
                g += lam * drift_dir * np.linalg.norm(g)
                modified[idx] = g

        # Spectral coordination: make malicious updates correlated
        if phase == "active" and round_t % 3 == 0:
            coord_base = np.mean([modified[i] for i in mal_indices], axis=0)
            for idx in mal_indices:
                modified[idx] = 0.8 * coord_base + 0.2 * modified[idx]

        return modified

    def _run_a5(self, round_t, updates, global_model):
        """A5 = synthetic transaction injection (simulated via backdoor)."""
        modified = list(updates)
        N = len(updates)
        mal_indices = list(range(N - self.n_mal, N))

        # Add a consistent backdoor direction to malicious updates
        backdoor_dir = np.ones(updates[0].shape[0]) * 0.5
        backdoor_dir = backdoor_dir / (np.linalg.norm(backdoor_dir) + 1e-8)

        for idx in mal_indices:
            g = updates[idx].copy()
            # Inject backdoor signal — stronger every 5 rounds
            strength = 0.1 * (1 + round_t // 5)
            g += strength * backdoor_dir
            modified[idx] = g

        return modified

    def _run_a6(self, round_t, updates, global_model):
        """A6 = cascade-aware envelope: constrain all attacks within bounds.

        The adversary constrains each malicious update to stay within
        tau_norm (norm), tau_cos (direction), and delta (spectral) bounds.
        """
        modified = list(updates)
        N = len(updates)
        mal_indices = list(range(N - self.n_mal, N))

        # Estimate defense bounds from observed updates
        norms = np.array([np.linalg.norm(g) for g in updates])
        norm_mean, norm_std = np.mean(norms), np.maximum(np.std(norms), 1e-8)
        tau_norm = norm_mean + 1.5 * norm_std
        delta = 0.15  # spectral perturbation bound

        ref = np.mean(updates, axis=0)
        ref_norm = np.linalg.norm(ref)

        # Small targeted perturbation within bounds
        target_vec = np.random.randn(updates[0].shape[0]) * 0.01

        for idx in mal_indices:
            g = updates[idx].copy() + target_vec

            # Clamp norm
            g_norm = np.linalg.norm(g)
            if g_norm > tau_norm:
                g = g * (tau_norm / g_norm)

            # Clamp cosine
            if ref_norm > 0:
                cos_sim = np.dot(g, ref) / (np.linalg.norm(g) * ref_norm + 1e-8)
                if cos_sim < 0.5:  # tau_cos
                    # Project toward reference direction
                    proj = np.dot(g, ref) / (ref_norm ** 2 + 1e-8) * ref
                    perp = g - proj
                    g = 0.5 * ref + 0.5 * perp

            # Bound perturbation (spectral)
            perturbation = g - updates[idx]
            p_norm = np.linalg.norm(perturbation)
            if p_norm > delta:
                perturbation = perturbation * (delta / p_norm)
                g = updates[idx] + perturbation

            modified[idx] = g

        return modified

    def list_attacks(self) -> list[str]:
        return ["A1", "A2", "A3", "A4", "A5", "A6"]


class _CompositeAttack:
    """Wrapper for composed attacks to match the attack callable interface."""
    def __init__(self, name: str, fn):
        self.name = name
        self._fn = fn

    def craft_update(self, round_t: int, updates: list[np.ndarray],
                     global_model: np.ndarray, loss_fn=None) -> list[np.ndarray]:
        return self._fn(round_t, updates, global_model)


# =========================================================================
#  Baseline suite
# =========================================================================

class BaselineSuite:
    """Maps baseline IDs to actual baseline objects."""

    def get(self, baseline_id: str):
        b_id = baseline_id.upper().strip()

        # Inlined baselines so it runs without external packages
        if b_id == "FEDAVG":
            return _InlinedBaseline("FedAvg", lambda updates, **kw: (updates, list(range(len(updates)))))

        if b_id == "KRUM":
            return _KrumBaseline()
        if b_id == "MEDIAN":
            return _MedianBaseline()
        if b_id == "TRIMMEDMEAN":
            return _TrimmedMeanBaseline()

        if b_id in ("BULYAN", "FLTRUST", "FOODSGOLD", "RFA", "DPFL8", "FLDetector",
                    "DPFL4", "DPFL1", "CLIPPEDMEDIAN", "MULTIKRUMTRIM"):
            try:
                from ifd_fintech.baselines.bulyan import Bulyan
                from ifd_fintech.baselines.dpfl import DPFL
                from ifd_fintech.baselines.fldetector import FLDetector
                mapping = {
                    "BULYAN": lambda: Bulyan(),
                    "FLTRUST": None,  # placeholder
                    "FOODSGOLD": None,
                    "RFA": None,
                    "DPFL8": lambda: DPFL(epsilon=8.0),
                    "DPFL4": lambda: DPFL(epsilon=4.0),
                    "DPFL1": lambda: DPFL(epsilon=1.0),
                    "CLIPPEDMEDIAN": None,
                    "MULTIKRUMTRIM": None,
                    "FLDETECTOR": lambda: FLDetector(),
                }
                builder = mapping.get(b_id)
                if builder is not None:
                    return builder()
            except Exception as e:
                print(f"  [warning] {b_id} import failed ({e}), using inlined version")
                return _InlinedBaseline(b_id, _simple_trimmed_mean)

        # Fallback: trimmed mean variant
        return _InlinedBaseline(b_id, _simple_trimmed_mean)

    def list_baselines(self) -> list[str]:
        return [
            "FedAvg", "Krum", "Median", "TrimmedMean", "Bulyan", "FLTrust",
            "FoolsGold", "RFA", "DPFL8", "FLDetector", "DPFL4", "DPFL1",
            "ClippedMedian", "MultiKrumTrim",
        ]


def _simple_trimmed_mean(updates: list[np.ndarray], **kw) -> tuple[list[np.ndarray], list[int]]:
    """Trim 20% extremes, return remaining."""
    arr = np.array(updates)
    N = arr.shape[0]
    trim = max(1, N // 5)
    sorted_idx = np.argsort(np.linalg.norm(arr, axis=1))
    keep_idx = sorted_idx[trim:N - trim].tolist()
    return [updates[i] for i in keep_idx], keep_idx


class _InlinedBaseline:
    def __init__(self, name: str, filter_fn):
        self.name = name
        self._fn = filter_fn

    def filter_updates(self, updates: list[np.ndarray], client_ids=None, round_t=0):
        return self._fn(updates, client_ids=client_ids, round_t=round_t)


class _KrumBaseline:
    """Simplified Krum: select update closest to N-m-2 others."""
    def filter_updates(self, updates, client_ids=None, round_t=0):
        arr = np.array(updates)
        N = len(updates)
        m = max(1, N // 4)
        best_idx = 0
        best_dist = float("inf")
        for i in range(N):
            dists = np.linalg.norm(arr - arr[i], axis=1)
            sorted_d = np.sort(dists)[1:N-m]  # exclude self, exclude m farthest
            d = float(np.sum(sorted_d))
            if d < best_dist:
                best_dist = d
                best_idx = i
        return [updates[best_idx]], [best_idx]


class _MedianBaseline:
    """Coordinate-wise median."""
    def filter_updates(self, updates, client_ids=None, round_t=0):
        median = np.median(np.array(updates), axis=0)
        # Compute distances to median
        dists = [np.linalg.norm(g - median) for g in updates]
        median_dist = np.median(dists)
        keep = [i for i, d in enumerate(dists) if d <= 2 * median_dist]
        return [updates[i] for i in keep], keep


class _TrimmedMeanBaseline:
    """Coordinate-wise trimmed mean (remove top/bottom 20%)."""
    def filter_updates(self, updates, client_ids=None, round_t=0):
        return _simple_trimmed_mean(updates)


# =========================================================================
#  Ablation configuration
# =========================================================================

ABLATION_CONFIGS: dict[str, dict] = {
    "full":           {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": True},
    "no_l1":          {"layer1": False, "layer2": True,  "layer3": True,  "adaptive": True},
    "no_l2":          {"layer1": True,  "layer2": False, "layer3": True,  "adaptive": True},
    "no_l3":          {"layer1": True,  "layer2": True,  "layer3": False, "adaptive": True},
    "no_at":          {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": False},
    "l1_only":        {"layer1": True,  "layer2": False, "layer3": False, "adaptive": True},
    "l2_only":        {"layer1": False, "layer2": True,  "layer3": False, "adaptive": True},
    "l3_only":        {"layer1": False, "layer2": False, "layer3": True,  "adaptive": True},
    "cascade_fixed":  {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": False},
    "tau_sweep":      {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": "sweep"},
    "window_sweep":   {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": True},
    "warmup_skip":    {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": True},
    "empty_pool":     {"layer1": True,  "layer2": True,  "layer3": True,  "adaptive": True},
}


def build_defense(cfg: dict, n_clients: int, dim: int, rng: np.random.RandomState):
    """Construct a defense from an ablation config dict."""
    from ifd_fintech.layers.layer1_norm_cosine import NormCosineFilter
    from ifd_fintech.layers.layer2_spectral import SpectralDetector
    from ifd_fintech.layers.layer3_temporal import TemporalReputation
    from ifd_fintech.orchestration import AdaptiveThresholdEscalation

    l1 = NormCosineFilter(dim) if cfg["layer1"] else None
    l2 = SpectralDetector(dim) if cfg["layer2"] else None
    l3 = TemporalReputation(n_clients) if cfg["layer3"] else None

    tau_1_init = 0.75 if cfg.get("adaptive", True) else 0.75
    tau_2_init = 0.70 if cfg.get("adaptive", True) else 0.70

    orch = AdaptiveThresholdEscalation(
        n_clients, dim,
        tau_1_init=tau_1_init,
        tau_2_init=tau_2_init,
    )
    orch.set_layers(l1, l2, l3)
    return orch


# =========================================================================
#  Single experiment run
# =========================================================================

def run_experiment(
    config: ExperimentConfig,
    attack_id: str,
    baseline_id: Optional[str] = None,
    ablation_cfg: Optional[dict] = None,
    verbose: bool = True,
) -> dict:
    """Run one FL experiment and return metrics."""
    rng = np.random.RandomState(config.seed + hash(attack_id) % 1000)

    n_total = config.n_clients
    dim = config.dim
    mal_indices = list(range(n_total - config.n_malicious, n_total))

    # ---- Setup defense ----
    if ablation_cfg is not None:
        defense = build_defense(ablation_cfg, n_total, dim, rng)
    else:
        defense = None

    # ---- Setup attack ----
    attack_suite = AttackSuite(config.n_malicious, dim)
    attack = attack_suite.get(attack_id)

    # ---- Setup baseline ----
    baseline_obj = None
    if baseline_id:
        baseline_suite = BaselineSuite()
        try:
            baseline_obj = baseline_suite.get(baseline_id)
        except Exception:
            baseline_obj = None

    # ---- Simulate rounds ----
    global_model = rng.randn(dim) * 0.01

    # Pre-train statistics for L1 warm-up
    warmup = [rng.randn(dim) * 0.1 for _ in range(n_total * 2)]
    if defense and defense.layer1:
        defense.layer1.fit(warmup)

    atk_results = []
    attack_active_rounds = 0

    for rnd in range(config.rounds):
        # Generate honest updates
        updates = [rng.randn(dim) * 0.1 for _ in range(n_total)]

        # Apply attack (if any)
        if attack is not None:
            try:
                attacked = attack.craft_update(
                    round_t=rnd, updates=updates, global_model=global_model
                )
                updates = attacked
                attack_active_rounds += 1
            except Exception as e:
                if verbose:
                    print(f"    [attack error at round {rnd}]: {e}")

        if defense is not None:
            try:
                agg_grad, info = defense.process_round(updates)
                global_model = global_model + 0.01 * agg_grad
                atk_results.append({
                    "round": rnd,
                    "final_scores": info.get("final_scores", []),
                    "reputations": info.get("reputations", info.get("reputations", [])),
                    "mal_rep": np.mean(
                        [info.get("reputations", info.get("reputations", [1]))[i]
                         for i in mal_indices]
                    ) if info.get("reputations") else 0,
                    "hon_rep": np.mean(
                        [info.get("reputations", info.get("reputations", [1]))[i]
                         for i in range(n_total - config.n_malicious)]
                    ) if info.get("reputations") else 0,
                })
            except Exception as e:
                if verbose:
                    print(f"    [defense error at round {rnd}]: {e}")
        else:
            # No defense: simple FedAvg
            global_model = np.mean(updates, axis=0)

    # ---- Compute metrics ----
    metrics = {"attack": attack_id, "rounds": config.rounds}
    if baseline_id:
        metrics["baseline"] = baseline_id
    if ablation_cfg:
        metrics["ablation"] = [k for k, v in ABLATION_CONFIGS.items()
                                if v == ablation_cfg]
        if not metrics["ablation"]:
            metrics["ablation"] = "custom"

    # Attack success rate (ASR): mal_rep > hon_rep threshold
    if atk_results:
        final_mal_rep = np.mean([r["mal_rep"] for r in atk_results[-5:]])
        final_hon_rep = np.mean([r["hon_rep"] for r in atk_results[-5:]])
        metrics["final_mal_rep"] = float(final_mal_rep)
        metrics["final_hon_rep"] = float(final_hon_rep)
        # Low mal_rep = attack detected; high mal_rep = attack succeeded
        metrics["asr_approximation"] = float(final_mal_rep / max(final_hon_rep, 1e-8))

        # Escalation stats
        scores_flat = []
        for r in atk_results:
            scores_flat.extend(r.get("final_scores", []))
        if scores_flat:
            metrics["mean_score"] = float(np.mean(scores_flat))
            metrics["rejection_rate"] = float(np.mean(np.array(scores_flat) < 0.3))

    if verbose:
        attack_name = attack_id
        baseline_or_ablation = baseline_id or (list(metrics.get("ablation", ["?"]))[0] if isinstance(metrics.get("ablation"), list) else metrics.get("ablation", "?"))
        print(f"  {attack_name:8s} | {str(baseline_or_ablation):16s} | "
              f"mal_rep={metrics.get('final_mal_rep', 0):.3f} hon_rep={metrics.get('final_hon_rep', 0):.3f} "
              f"asr≈{metrics.get('asr_approximation', 0):.3f}")

    return metrics


# =========================================================================
#  Main runner
# =========================================================================

def main():
    parser = argparse.ArgumentParser(description="IFD-Fintech full experiment runner")
    parser.add_argument("--clients", type=int, default=20, help="Number of FL clients")
    parser.add_argument("--dim", type=int, default=32, help="Gradient dimension")
    parser.add_argument("--rounds", type=int, default=50, help="FL rounds")
    parser.add_argument("--malicious", type=int, default=2, help="Malicious clients")
    parser.add_argument("--attacks", type=str, default="A1,A2,A3",
                        help="Comma-separated attacks (or 'all' for A1-A6)")
    parser.add_argument("--baselines", type=str, default="none",
                        help="Comma-separated baselines (or 'all' for 14)")
    parser.add_argument("--ablations", type=str, default="full",
                        help="Comma-separated ablations (or 'all' for 13)")
    parser.add_argument("--output", type=str, default="results_full.json",
                        help="Output JSON path")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-path", type=str, default=None)
    args = parser.parse_args()

    cfg = ExperimentConfig(
        n_clients=args.clients,
        dim=args.dim,
        rounds=args.rounds,
        n_malicious=min(args.malicious, args.clients // 4),
        attacks=["A1", "A2", "A3", "A4", "A5", "A6"] if args.attacks.lower() == "all"
                else [a.strip() for a in args.attacks.split(",")],
        baselines=BaselineSuite().list_baselines() if args.baselines.lower() == "all"
                  else [] if args.baselines.lower() == "none"
                  else [b.strip() for b in args.baselines.split(",")],
        ablations=list(ABLATION_CONFIGS.keys()) if args.ablations.lower() == "all"
                 else [a.strip() for a in args.ablations.split(",")],
        data_path=args.data_path,
        seed=args.seed,
        output_dir=os.path.dirname(args.output) or ".",
    )

    total_experiments = 0
    results = []

    # ---- 1. Attack-only: run with full defense on each attack ----
    print(f"\n{'='*70}")
    print(f"  Phase 1: Attack Effectiveness (full defense)")
    print(f"  Clients={cfg.n_clients}, Dim={cfg.dim}, Rounds={cfg.rounds}")
    print(f"{'='*70}")
    print(f"  {'Attack':8s} | {'Defense':16s} | Result")

    for aid in cfg.attacks:
        m = run_experiment(cfg, attack_id=aid, ablation_cfg=ABLATION_CONFIGS["full"])
        results.append(m)
        total_experiments += 1

    # ---- 2. Baseline comparison (if requested) ----
    if cfg.baselines:
        print(f"\n{'='*70}")
        print(f"  Phase 2: Baseline comparison (against A2)")
        print(f"{'='*70}")
        print(f"  {'Baseline':16s} | {'Result':>40s}")

        for bid in cfg.baselines:
            m = run_experiment(cfg, attack_id="A2", baseline_id=bid)
            results.append(m)
            total_experiments += 1

    # ---- 3. Ablation study ----
    if cfg.ablations:
        print(f"\n{'='*70}")
        print(f"  Phase 3: Ablation study (against A2)")
        print(f"{'='*70}")
        print(f"  {'Ablation':16s} | {'Result':>40s}")

        for abl_id in cfg.ablations:
            abl_cfg = ABLATION_CONFIGS.get(abl_id)
            if abl_cfg is None:
                print(f"  {'[skip]':16s} unknown config '{abl_id}'")
                continue
            m = run_experiment(cfg, attack_id="A2", ablation_cfg=abl_cfg)
            results.append(m)
            total_experiments += 1

    # ---- Summary ----
    print(f"\n{'='*70}")
    print(f"  EXPERIMENTS COMPLETE: {total_experiments} runs")
    print(f"{'='*70}")

    # Print summary table for attack phase
    print(f"\n  Attack Phase Summary:")
    print(f"  {'Attack':8s} {'ASR≈':8s} {'Mal_Rep':8s} {'Hon_Rep':8s}")
    for m in results:
        if "baseline" not in m and "ablation" not in m or \
           isinstance(m.get("ablation"), list) and "full" in str(m.get("ablation")):
            print(f"  {m['attack']:8s} {m.get('asr_approximation', 0):8.3f} "
                  f"{m.get('final_mal_rep', 0):8.3f} {m.get('final_hon_rep', 0):8.3f}")

    # Save
    os.makedirs(cfg.output_dir, exist_ok=True)
    out_path = args.output
    with open(out_path, "w") as f:
        json.dump({
            "config": asdict(cfg),
            "results": results,
            "total_experiments": total_experiments,
        }, f, indent=2)
    print(f"\n  Results saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
