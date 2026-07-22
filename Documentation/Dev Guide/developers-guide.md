# Developer Onboarding Guide — IFD-Fintech

> **Project:** Robust Federated Learning for Credit Card Identity Fraud Detection  
> **Venue:** IEEE Transactions on Information Forensics and Security (IEEE TIFS)  
> **Repository:** `/home/tempest/Documents/IFD-Fintech/`  
> **Python:** 3.14+  
> **Package manager:** `uv`  
> **FL framework:** Flower (flwr)

---

## 1. Project Overview

IFD-Fintech implements a **gated cascade defense framework** for cross-silo federated learning in the financial domain. Banks (clients) collaboratively train a credit-card fraud detection model without sharing raw transaction data. The core vulnerability is that a compromised client bank can poison the global model via malicious gradient updates.

The defense consists of **three complementary detection layers** connected by an **adaptive threshold escalation policy** — the paper's core novelty. Each layer catches a different class of attack, and uncertain cases are escalated up the cascade. The thresholds automatically **tighten under attack** (more scrutiny) and **relax during normal operation** (higher efficiency).

The project also implements six attack models (A1–A6), three baseline defenses (Bulyan, DP-FL, FLDetector), 15 ablation configurations, and a full suite of fraud-specific evaluation metrics.

---

## 2. Getting Started

### Prerequisites

- **Python 3.14+** (enforced by `.python-version` and `pyproject.toml`)
- **uv** — the Python package and project manager (install via `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Setup

```bash
# Navigate to the project root
cd /home/tempest/Documents/IFD-Fintech

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync

# Verify the install
uv run python -c "import ifd_fintech; print('OK')"
```

This installs the two core dependencies:

- **`numpy>=2.5.1`** — all gradient/matrix operations
- **`scikit-learn>=1.6.0`** — metrics (precision–recall curve, ROC-AUC)
- **`flwr`** (implicit) — federated learning simulation framework

### Verify Python Version

```bash
python --version   # Must be 3.14 or higher
```

If your system Python is older, `uv` automatically downloads and uses the correct version via `uv python install 3.14`.

---

## 3. Architecture Overview

### 3.1 Layered Defense Architecture

The defense is designed as a **cascade** — most updates are resolved by the cheapest layer (Layer 1, O(d) per update). Only updates that produce low-confidence scores at a given layer are escalated to the next, more expensive layer. This mirrors how fraud operations teams triage alerts: automated rules handle 80% of cases, ambiguous ones go to an analyst, and the hardest cases get a full investigation.

```
   ┌─────────────────────────────────────┐
   │  All Client Updates (N × d)         │
   └────────────┬────────────────────────┘
                ▼
   ┌──────────────────────┐
   │  Layer 1: Norm/Cosine │  O(d), stateless, ~80% resolved here
   │  [confidence ≥ τ₁]   │
   └───┬────────┬─────────┘
       │ accept │ escalate
       ▼        ▼
   ┌──────────────────────┐
   │  Layer 2: Spectral   │  O(Nd²), multi-client context
   │  [confidence ≥ τ₂]   │
   └───┬────────┬─────────┘
       │ accept │ escalate
       ▼        ▼
   ┌──────────────────────┐
   │  Layer 3: Temporal   │  O(d), multi-round history
   │  [always decides]    │  (with adaptive threshold decay)
   └────────┬─────────────┘
            ▼
   ┌──────────────────────┐
   │  Weighted Aggregate  │  reputation × anomaly score
   └──────────────────────┘
```

**Cascade philosophy (three key principles):**

1. **Efficiency first** — Layer 1 handles ~80% of updates cheaply.
2. **Context matters** — Layer 2 uses all clients' updates together; Layer 3 uses all rounds.
3. **Adaptivity closes the loop** — thresholds self-tune based on observed attack rate.

### 3.2 Key Interfaces

Every component follows a consistent protocol:

#### Layer Interface (`score` → `(anomaly_score, confidence)`)

Each detection layer implements a single method:

```python
def score(g_i: np.ndarray, **kwargs) -> tuple[float, float]:
    """Evaluate a client update.

    Returns:
        anomaly_score: float in [0, 1], where 1 = definitely honest.
        confidence: float in [0, 1], where 1 = absolutely certain.
    """
```

- `anomaly_score` — the layer's assessment of how normal the update looks
- `confidence` — the layer's certainty in its own score
- Scores near `[0, 1]` are meaningful: a score of 0.85 with confidence 0.9 means the layer is 90% sure the update is 85%-normal

**Example usage:**
```python
from ifd_fintech.layers.layer1_norm_cosine import NormCosineFilter

filter_l1 = NormCosineFilter(dim=model_dim)
filter_l1.fit(honest_updates=initial_clean_updates)
score, confidence = filter_l1.score(g_i)
```

#### Attack Interface (`craft_update`)

Each attack subclasses `AdaptiveAttacker` and implements:

```python
def craft_update(
    self,
    round_t: int,
    updates: list[np.ndarray],
    global_model: np.ndarray,
    loss_fn=None,
) -> list[np.ndarray]:
    """Replace last n_malicious updates with crafted adversarial gradients.
    
    Returns the full list of updates with malicious ones injected.
    """
```

The attacker replaces the **last `self.n_malicious` entries** in the update list, controlled via `_select_malicious_indices()`.

#### Baseline Interface (`filter_updates`)

Each baseline subclasses `Baseline` and implements:

```python
def filter_updates(
    self,
    updates: list[np.ndarray],
    client_ids: list[int] | None = None,
    round_t: int = 0,
) -> tuple[list[np.ndarray], list[int]]:
    """Filter malicious updates and return accepted ones.
    
    Returns:
        (filtered_updates, accepted_indices)
    """
```

### 3.3 Data Flow (Per FL Round)

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Server   │────▶│ Client 1 │     │ Client N │
│ (global  │     │ (train)  │ ... │ (train)  │
│  model)  │◀────│          │     │          │
└──────────┘     └──────────┘     └──────────┘

Server-side processing per round:

1. Receive client updates {g₁, g₂, ..., gₙ}
2. orchestrator.process_round(updates)
   └── For each client i:
       ├── Layer 1 score(g_i) → (a₁, c₁)
       ├── if c₁ ≥ τ₁:  accept (final_score = a₁)
       ├── else:        Layer 2 score(all_updates, i) → (a₂, c₂)
       │   └── if c₂ ≥ τ₂:  accept
       │       else:         Layer 3 score(g_i, i) → (a₃, c₃) — always decides
       └── Update reputation
   ├── Weighted aggregation: final_grad = Σ weight_i · g_i / Σ weight_i
   └── Adapt thresholds τ₁, τ₂ based on estimated attack rate ρ(t)
3. Apply aggregated gradient → new global model
4. Distribute new model to clients
```

---

## 4. Module Reference

### 4.1 Layers

#### `NormCosineFilter` (`layers/layer1_norm_cosine.py`)

**Purpose:** Fast, stateless filter based on gradient norm and cosine similarity to the global update direction.

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `dim` | `int` | (required) | Model dimension |

**State (set via `fit()`):**

| Attribute | Description |
|-----------|-------------|
| `norm_mean`, `norm_std` | Running statistics of honest update norms |
| `cos_mean`, `cos_std` | Running statistics of cosine similarities |

**`fit(honest_updates: list[np.ndarray])`:** Calibrates statistics from a set of known-honest updates (warm-up phase).

**`score(g_i, ref=None)` → `(anomaly_score, confidence)`:**

1. Computes norm score via sigmoid: `s₁ = σ((norm_mean - ‖g_i‖₂) / norm_std)`
2. Computes cosine score via sigmoid: `s₂ = σ((cos_sim(g_i, μ) - cos_mean) / cos_std)`
3. Final anomaly score = `0.5 · s₁ + 0.5 · s₂`
4. Confidence decreases by 0.15 per component near its decision boundary (±2σ)

**Math summary:**

```
norm_score    = σ((μ_norm - ‖g_i‖₂) / σ_norm)
cos_score     = σ((cos_sim - μ_cos) / σ_cos)
anomaly_score = 0.5 · norm_score + 0.5 · cos_score
confidence    = 1.0 - 0.5 · (𝟙[|norm - μ_norm| < 2σ_norm]·0.15
                              + 𝟙[|cos - μ_cos| < 2σ_cos]·0.15)
```

**Aggregate method:** `_sigmoid(x)` — numerically stable sigmoid clipped to [0,1].

---

#### `SpectralDetector` (`layers/layer2_spectral.py`)

**Purpose:** Detects **coordinated multi-client attacks** by analyzing the spectral decomposition (SVD) of the per-round update matrix. Malicious updates from colluding clients occupy a different subspace than independent honest variation.

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `dim` | `int` | (required) | Model dimension |
| `variance_ratio` | `float` | `0.95` | γ: explained variance threshold for k components |

**`score(updates, target_idx)` → `(anomaly_score, confidence)`:**

1. Stack all N updates into matrix **G** ∈ ℝ^(N×d)
2. Center: **R** = **G** − mean(**G**)
3. Full SVD: **R** = **USV**^T
4. Choose k components explaining γ variance (default 95%)
5. Project target residual onto principal subspace: `ĝ = V_k V_k^T g_i`
6. Reconstruction error: `e_i = ‖g_i − ĝ‖₂`
7. Normalize error across all clients
8. `anomaly_score = 1 - min(normalized_residual, 1.0)`
9. `confidence = spectral_quality = S[k-1] / S[0]` (eigengap ratio, capped at 0.9)

**Edge case:** If N < 3, returns (0.5, 0.3) — insufficient clients for spectral analysis.

---

#### `TemporalReputation` (`layers/layer3_temporal.py`)

**Purpose:** Detects **slow, adaptive poisoning** that evades per-round detection by spreading a tiny malicious signal across many rounds.

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `n_clients` | `int` | (required) | Total number of clients |
| `alpha` | `float` | `0.1` | EMA smoothing factor for update tracking |
| `maturity_rounds` | `int` | `20` | Rounds before full confidence |

**State (per client):**

| Attribute | Shape | Description |
|-----------|-------|-------------|
| `reputations` | `(n_clients,)` | Cumulative reputation R_i ∈ [0,1] |
| `ema_updates` | `list[np.ndarray]` | Exponentially smoothed update history |
| `rounds_seen` | `(n_clients,)` | Number of rounds observed per client |

**`score(g_i, client_id)` → `(anomaly_score, confidence)`:**

1. **Consistency score:** cosine similarity between current update and EMA history
2. **Anomaly score:** `reputation[client_id] × consistency_score`
3. **Confidence:** `min(rounds_seen / maturity, 1.0) × reputation[client_id]`

**`update(g_i, client_id, is_anomaly)`:** (via `_update_state`)

- EMA of updates: `ema ← (1-α)·ema + α·g_i`
- Reputation adjustment (called externally by orchestrator):
  - Accepted: reputation increases toward R_SS
  - Anomalous: reputation decays exponentially
- Increments `rounds_seen[client_id]`

---

### 4.2 Orchestration

#### `AdaptiveThresholdEscalation` (`orchestration/__init__.py`)

**Purpose:** The core novelty of the paper — orchestrates the 3-layer cascade with self-tuning thresholds.

**Constructor Parameters (all have sensible defaults):**

| Category | Param | Default | Description |
|----------|-------|---------|-------------|
| **L1 thresholds** | `tau_1_min` | `0.55` | Floor for Layer 1 confidence threshold |
| | `tau_1_max` | `0.90` | Ceiling for Layer 1 confidence threshold |
| | `tau_1_init` | `0.75` | Starting value for τ₁ |
| **L2 thresholds** | `tau_2_min` | `0.55` | Floor for Layer 2 confidence threshold |
| | `tau_2_max` | `0.85` | Ceiling for Layer 2 confidence threshold |
| | `tau_2_init` | `0.70` | Starting value for τ₂ |
| **Adaptation** | `eta_attack` | `0.15` | Rate at which thresholds tighten under attack |
| | `eta_relax` | `0.05` | Rate at which thresholds relax in normal operation |
| **Decisions** | `theta_accept` | `0.60` | Score ≥ this → fully accepted |
| | `theta_reject` | `0.30` | Score < this → rejected (weight = 0) |
| | `suspicious_weight` | `0.50` | Weight multiplier for escalated-but-not-rejected updates |
| **Detection** | `rho_0` | `0.10` | Baseline expected flag rate |
| | `sigma_rho` | `0.05` | Standard deviation for alarm threshold |
| | `alarm_window` | `20` | Rolling window for attack rate estimation |

**`process_round(updates)` → `(aggregated_grad, info_dict)`:**

The main pipeline — runs every FL round:

```
for each client i:
    a₁, c₁ = layer1.score(g_i)
    if c₁ ≥ τ₁:  final_score[i] = a₁;  continue (accept at L1)
    
    a₂, c₂ = layer2.score(all_updates, i)
    if c₂ ≥ τ₂:  final_score[i] = a₂;  continue (accept at L2)
    
    a₃, _ = layer3.score(g_i, i)        # L3 always decides
    final_score[i] = a₃

# Aggregation
aggregate = Σ( weight_i · g_i ) / Σ( weight_i )
where weight_i = reputation[i]          if score ≥ theta_accept
                 reputation[i] × 0.50   if theta_reject ≤ score < theta_accept
                 0                      if score < theta_reject

# Threshold adaptation
ρ(t) = fraction of clients flagged (score < theta_accept)
if ρ(t) > ρ_mean + 2·ρ_std (over alarm_window):
    tighten:  τ₁ ← max(τ₁_min, τ₁ - η_attack · ρ(t))
              τ₂ ← max(τ₂_min, τ₂ - η_attack · ρ(t))
else:
    relax:    τ₁ ← min(τ₁_max, τ₁ + η_relax)
              τ₂ ← min(τ₂_max, τ₂ + η_relax)
```

**`info_dict` contains:** `round`, `final_scores` (list), `escalation_stats` (counts per layer), `tau_1`, `tau_2`, `reputations` (list), `agg_norm`.

**Reputation management:**

```
R_i(t+1) = R_i(t) + 0.1 · (score - R_i(t)) + 0.02 · (0.85 - R_i(t))
```

This combines EMA smoothing with a forgetting term that pulls reputation toward a steady-state of 0.85, preventing a single bad round from permanently tanking an honest client.

---

#### `AdaptiveLayeredDefenseStrategy` (`orchestration/flower_strategy.py`)

**Purpose:** Wraps the orchestrator into a Flower-compatible strategy for FL simulation.

```python
strategy = AdaptiveLayeredDefenseStrategy(n_clients=20, model_dim=model_dim)
strategy.initialize_parameters(initial_weights)

# Inside Flower simulation, strategy.aggregate_fit() is called each round:
#   1. Deserialize client parameters → numpy gradients
#   2. Compute g_i = w_i - w_global
#   3. Call orchestrator.process_round(updates)
#   4. Return aggregated gradient + metadata
```

The strategy computes gradients as `g_i = client_weights - global_model` before feeding them to the orchestrator.

---

### 4.3 Attacks

#### Base Class: `AdaptiveAttacker` (`attacks/__init__.py`)

```python
class AdaptiveAttacker(ABC):
    def __init__(self, n_malicious, defense_knowledge=None, 
                 backdoor_trigger=None, backdoor_target=0):
        self.n_malicious = n_malicious
        self.knowledge = defense_knowledge or {}
        self.backdoor_trigger = backdoor_trigger
        self.backdoor_target = backdoor_target
    
    @abstractmethod
    def craft_update(self, round_t, updates, global_model, loss_fn=None) -> list[np.ndarray]:
        ...
    
    def _set_backdoor_target(self, trigger, target): ...
    def _generate_backdoor_gradient(self, model, loss_fn) -> np.ndarray: ...
    def _select_malicious_indices(self, n_total) -> list[int]: ...  # last n entries
```

All attackers replace the **last n_malicious entries** in the update list. The `defense_knowledge` dict can carry estimated defense params (norms, thresholds, SVD components) leaked to the attacker.

#### A1: `OracleWhiteBox` (`attacks/a1_oracle_whitebox.py`)

**Strategy:** White-box PGD (projected gradient descent) that knows the exact defense parameters and optimizes the malicious gradient to pass all three layer checks simultaneously.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_malicious` | (required) | Number of compromised clients |
| `max_iter` | 50 | PGD iterations |
| `step_size` | 0.1 | Gradient step size |
| `defense_knowledge` | None | Leaked defense parameters |

**Algorithm:**
1. `_estimate_defense_params(updates)` — estimates norm/cosine statistics and SVD subspace from honest-looking updates
2. PGD loop: compute backdoor gradient → project onto L1 norm/cosine constraints → project onto L2 SVD subspace → enforce L3 temporal consistency
3. Returns crafted gradients that lie within the acceptance region of all layers

#### A2: `GradientGrinding` (`attacks/a2_grinding.py`)

**Strategy:** Slow, incremental poisoning using a **4-phase temporal schedule** that stays below per-round detection thresholds.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `burn_in` | 20 | Phase 1: completely honest behavior |
| `subliminal` | 60 | Phase 2: tiny, barely-detectable drift |
| `active` | 100 | Phase 3: full attack at λ_max |
| `cooldown` | 120 | Phase 4: tapering off |
| `lambda_max` | 0.15 | Maximum drift scaling factor |

**Phases:**
- **burn_in** (rounds 0–20): Submit honest gradients only. Build reputation.
- **subliminal** (21–60): Inject tiny malicious signal with λ scaling from 0→λ_max.
- **active** (61–100): Full attack at λ_max. Periodically normalize gradient to stay within norm bounds.
- **cooldown** (101–120): Gradually reduce λ back to 0. Evade post-attack scrutiny.

#### A3: `SpectralMatching` (`attacks/a3_spectral_matching.py`)

**Strategy:** Projects malicious gradients onto the honest principal subspace (SVD basis), hiding the attack signal in the nullspace that Layer 2 discards.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `subspace_rank` | 5 | Number of top SVD components to match |
| `nullspace_noise_scale` | 0.01 | Noise added to matched gradient |

**Algorithm:**
1. `_estimate_spectral_basis(updates)` — SVD of honest updates, extract top-k right singular vectors V_k
2. Project backdoor gradient onto V_k subspace: `g_malicious = V_k V_k^T · g_backdoor`
3. Add small isotropic noise (scale = `nullspace_noise_scale`) to avoid perfect identifiability
4. The attack literally lives in the honest subspace — extremely hard for Layer 2 to detect

#### A4–A6: Composed Attacks

Higher attacks build on A1–A3:

| Attack | Composition | Description |
|--------|-------------|-------------|
| **A4** | A2 + A3 | **Grinding + Spectral Matching** — slow temporal drift that also lives in the honest SVD subspace. The worst case for Layer 2 (spectral blindness) combined with Layer 3 evasion (small deltas). |
| **A5** | A1 + A2 | **Oracle + Grinding** — white-box knowledge projected onto a grinding schedule. The attacker knows the exact thresholds and phases the attack to stay just below them. |
| **A6** | A1 + A2 + A3 | **Full composition** — white-box spectral matching with grinding schedule. The attacker knows everything, hides in the subspace, and paces the attack temporally. This is the strongest attack in the paper. |

To implement a composed attack, instantiate the base attack classes and combine their `craft_update` outputs (e.g., apply A1's projection, then A2's scaling, then A3's subspace projection).

---

### 4.4 Baselines

#### Base Class: `Baseline` (`baselines/__init__.py`)

```python
class Baseline(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def filter_updates(self, updates, client_ids=None, round_t=0):
        """Returns (filtered_updates, accepted_indices)."""
```

#### Bulyan (`baselines/bulyan.py`)

**Algorithm:** Two-step robust aggregation (Mhamdi et al., 2018):
1. **Krum selection** — compute pairwise distances, select n−2f candidates closest to their neighbors (O(N²))
2. **Coordinate-wise trimmed mean** — for each coordinate, remove extreme values and average

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_byzantine` | 2 | Assumed number of Byzantine (malicious) clients |

**Requirement:** `n ≥ 2f + 3` for Krum to function.

#### DP-FL (`baselines/dpfl.py`)

**Algorithm:** Standard differential privacy (Abadi et al., 2016):
1. **Gradient clipping:** `ĝ_i = g_i / max(1, ‖g_i‖₂ / C)` (project onto L2 ball of radius C)
2. **Gaussian noise:** `g̃_i = ĝ_i + 𝒩(0, σ²·I)` where `σ = noise_multiplier × C`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `clip_norm` | 1.0 | L2 clipping threshold C |
| `noise_multiplier` | 0.5 | Noise scaling factor |
| `epsilon` | 8.0 | Target ε (informative label only) |

**Note:** DP-FL does **not** filter clients — it accepts all of them. Privacy comes from noise, not exclusion. Useful as a baseline to compare utility cost of DP vs. selective aggregation.

#### FLDetector (`baselines/fldetector.py`)

**Algorithm:** Prediction-consistency filter (Zhang et al., 2022):
1. Maintain per-client historical update buffer
2. Bagged autoregressive prediction: weighted combination of past updates with randomly perturbed weights (ensemble_size bagging models)
3. Compare actual update to predicted update via cosine similarity
4. Flag clients whose similarity is below `similarity_threshold`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `history_window` | 5 | Number of past updates to keep per client |
| `ensemble_size` | 3 | Number of AR predictors in bagging ensemble |
| `similarity_threshold` | 0.3 | Minimum cosine similarity to be accepted |

---

### 4.5 Data (`data/__init__.py`)

#### `dirichlet_split(labels, n_clients, alpha, seed=42, min_samples_per_client=1)`

Partitions data indices using a Dirichlet distribution per class (Hsu et al., 2019).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `labels` | `np.ndarray` | — | Class labels for all samples |
| `n_clients` | `int` | — | Number of federated clients |
| `alpha` | `float` | — | Dirichlet concentration. α < 1 → extreme non-IID, α > 1 → more IID |
| `seed` | `int` | 42 | RNG seed for reproducibility |
| `min_samples_per_client` | `int` | 1 | Minimum samples per client |

**Alpha interpretation:**

| α value | Non-IID degree | Example use case |
|---------|----------------|------------------|
| 0.1 | Extreme | Each client has 1–2 classes (small regional bank serving one industry) |
| 0.5 | Moderate | Each client has 3–5 classes (medium bank with diverse customers) |
| 1.0 | Mild | All clients have all classes but with varying proportions |
| 10.0 | Near-IID | All clients have nearly identical class distributions |

**Geographic splits:** Also supported (in code stubs) for realistic consortium scenarios — partition by geographic region rather than Dirichlet.

**Usage:**
```python
from ifd_fintech.data import dirichlet_split

# Partition CIFAR-10/credit-card data across 20 clients with α=0.5
client_indices = dirichlet_split(labels=all_labels, n_clients=20, alpha=0.5, seed=42)

# client_indices[i] contains the data indices for client i
```

---

### 4.6 Experiment Module

#### Metrics (`experiment/metrics.py`)

A comprehensive fraud-specific evaluation suite.

**`compute_metrics(y_true, y_pred, y_scores, fraud_amounts=None, cost_per_fp=5.0, avg_fraud_loss=450.0)`**

Returns a dict with:

| Metric | Description |
|--------|-------------|
| `precision` | TP / (TP + FP) |
| `recall` | TP / (TP + FN) |
| `f1` | Harmonic mean of precision and recall |
| `accuracy` | (TP + TN) / total |
| `savings` | Net savings = fraud prevented - false positive cost |
| `savings_rate` | savings / total_fraud_loss (as a percentage) |
| `precision_at_recall_80` | Interpolated precision at 80% recall |
| `precision_at_recall_90` | Interpolated precision at 90% recall |
| `precision_at_recall_95` | Interpolated precision at 95% recall |
| `auasr` | Area Under the Attack Success Rate curve |
| `f_beta_1` | F1 score |
| `f_beta_2` | F2 score (recall-weighted) |
| `f_beta_5` | F5 score (heavily recall-weighted) |
| `f_beta_10` | F10 score (extremely recall-weighted) |

**Savings calculation:**
```
fraud_prevented = tp × avg_fraud_loss
false_positive_cost = fp × cost_per_fp
net_savings = fraud_prevented - false_positive_cost
savings_rate = net_savings / (total_fraud_count × avg_fraud_loss)
```

The default numbers (`cost_per_fp=5.0`, `avg_fraud_loss=450.0`) reflect a ~90:1 fraud-to-review cost ratio typical in card issuing.

Additional functions:
- `compute_savings()` — standalone savings calculation
- `compute_precision_at_recall()` — interpolated precision at arbitrary recall levels
- `compute_auasr()` — area under ASR curve (evaluates defense robustness across attack intensities)

#### Ablation (`experiment/ablation.py`)

**`ABLATION_CONFIGS` dict:** Maps config names to `{layer1, layer2, layer3, adaptive}` boolean flags.

| Config Name | L1 | L2 | L3 | Adaptive | Purpose |
|-------------|----|----|----|----------|---------|
| `full` | ✓ | ✓ | ✓ | ✓ | Full defense (reference) |
| `no_l1` | ✗ | ✓ | ✓ | ✓ | Isolate L1 contribution |
| `no_l2` | ✓ | ✗ | ✓ | ✓ | Isolate L2 contribution |
| `no_l3` | ✓ | ✓ | ✗ | ✓ | Isolate L3 contribution |
| `no_at` | ✓ | ✓ | ✓ | ✗ | Isolate adaptive thresholds |
| `l1_only` | ✓ | ✗ | ✗ | ✓ | L1 alone |
| `l2_only` | ✗ | ✓ | ✗ | ✓ | L2 alone |
| `l3_only` | ✗ | ✗ | ✓ | ✓ | L3 alone |
| `cascade_fixed` | ✓ | ✓ | ✓ | ✗ | Cascade without adaptive thresholds |
| `cascade_oracle` | ✓ | ✓ | ✓ | oracle | Oracle-optimal thresholds (upper bound) |
| `tau_sweep` | ns | — | — | — | Sweep τ₁, τ₂ for sensitivity analysis |
| `window_sweep` | ns | — | — | — | Sweep alarm_window for robustness |
| `warmup_skip` | ✓ | ✓ | ✓ | ✓ | Skip warm-up phase |
| `empty_pool_revert` | ✓ | ✓ | ✓ | ✓ | Test empty pool fallback behavior |
| `rcc_included` | ✓ | ✓ | ✓ | ✓ | Randomized Controlled Comparison variant |

**`AblationRunner(config, n_runs=5, n_rounds=200, n_clients=20)`:**

```python
from ifd_fintech.experiment.ablation import AblationRunner, ABLATION_CONFIGS

# Run the "no_l1" ablation
runner = AblationRunner(
    layer_config=ABLATION_CONFIGS["no_l1"],
    n_runs=5,           # repeat 5 times for statistical significance
    n_rounds=200,       # 200 FL rounds per run
    n_clients=20,       # 20 clients
)
results = runner.run()  # returns aggregated metrics dict with mean ± std
```

**To add a new ablation config:**
```python
# 1. Add to ABLATION_CONFIGS
ABLATION_CONFIGS["my_config"] = {
    "layer1": True, "layer2": False, "layer3": True, "adaptive": False,
}

# 2. Use it
runner = AblationRunner(layer_config=ABLATION_CONFIGS["my_config"])
```

#### Fairness (`experiment/fairness.py`)

**`FairnessEvaluator(client_profiles)`:** Evaluates whether the defense disproportionately flags honest clients from specific subgroups.

```python
from ifd_fintech.experiment.fairness import FairnessEvaluator

# Define profiles: {client_id: profile_name}
profiles = {0: "majority", 1: "minority_serving", 2: "small_bank", 3: "new_entrant"}
evaluator = FairnessEvaluator(profiles)

# metrics per subgroup
results = evaluator.compute_honest_fpr(attack_matrix, anomaly_scores)
# Returns: {"majority": 0.02, "minority_serving": 0.05, "small_bank": 0.03, ...}
```

Standard profiles: `"majority"`, `"minority_serving"`, `"small_bank"`, `"new_entrant"`.

**Metrics computed:**
- Per-subgroup honest FPR (false positive rate on benign clients)
- Fairness gap ratio (max FPR / min FPR across subgroups)

#### Explainer (`experiment/explainer.py`)

**`DefenseRecord`:** Human-readable explanation for each defense decision, designed for regulatory compliance (GDPR Art. 22, SR 11-7, FATF Rec. 15).

```python
from ifd_fintech.experiment.explainer import DefenseRecord

# Create a record for a flagged client
record = DefenseRecord(
    round_t=42,
    client_id=7,
    norm=3.2,
    cos_sim=0.15,
    spectral_score=0.1,
    temporal_score=0.3,
    anomaly_score=0.2,
    was_flagged=True,
    layer_responsible="layer2",
)

# Generate human-readable explanation
print(record.explain())
# → "Client 7 at round 42: FLAGGED
#    Layer 2 (Spectral): residual_score=0.100 — anomalous spectral signature
#    Explanation: Client's gradient exhibits statistically unusual structure
#    compared to peer clients in this round; pattern suggests coordinated
#    adversarial modification."
```

Records can be serialized to JSON for audit trails:
```python
with open("audit_log.json", "w") as f:
    json.dump(record.to_dict(), f, indent=2)
```

---

## 5. How to Add New Components

### 5.1 Adding a New Attack

**Steps:**

1. **Create the file** at `ifd_fintech/attacks/a4_your_attack.py`

2. **Subclass `AdaptiveAttacker`** and implement `craft_update`:

```python
from typing import Optional
import numpy as np
from . import AdaptiveAttacker

class YourAttack(AdaptiveAttacker):
    def __init__(
        self,
        n_malicious: int,
        your_param: float = 1.0,
        defense_knowledge: Optional[dict] = None,
        backdoor_trigger: Optional[np.ndarray] = None,
        backdoor_target: int = 0,
    ):
        super().__init__(n_malicious, defense_knowledge, backdoor_trigger, backdoor_target)
        self.your_param = your_param

    def craft_update(self, round_t, updates, global_model, loss_fn=None):
        # 1. Compute backdoor gradient
        malicious_grad = self._generate_backdoor_gradient(global_model, loss_fn)
        
        # 2. Apply evasion strategy — your logic here
        crafted_grad = self._evasion_transform(malicious_grad, updates)
        
        # 3. Replace last n_malicious entries
        return self.replace_last_n_updates(updates, [crafted_grad] * self.n_malicious)
    
    def _evasion_transform(self, g, updates):
        # Your evasion logic
        return g
```

3. **Export** in `attacks/__init__.py`:
```python
from .a4_your_attack import YourAttack
__all__ = [..., "YourAttack"]
```

4. **Register in the test suite** (if one exists under `tests/`).

### 5.2 Adding a New Baseline

**Steps:**

1. **Create the file** at `ifd_fintech/baselines/your_baseline.py`

2. **Subclass `Baseline`** and implement `filter_updates`:

```python
import numpy as np
from typing import Optional
from . import Baseline

class YourBaseline(Baseline):
    def __init__(self, your_param: float = 0.5):
        super().__init__("YourBaseline")
        self.your_param = your_param

    def filter_updates(self, updates, client_ids=None, round_t=0):
        if client_ids is None:
            client_ids = list(range(len(updates)))
        
        # Your filtering logic
        accepted_indices = [i for i, g in enumerate(updates) if self._is_ok(g)]
        filtered = [updates[i] for i in accepted_indices]
        
        return filtered, accepted_indices
    
    def _is_ok(self, g):
        # Your detection logic
        return True
```

3. **Export** in `baselines/__init__.py` and **add to the ablation runner** comparison loop.

### 5.3 Adding a New Ablation Configuration

**Steps:**

1. **Add an entry** to `ABLATION_CONFIGS` in `experiment/ablation.py`:

```python
ABLATION_CONFIGS["my_config"] = {
    "layer1": True,
    "layer2": False,
    "layer3": True,
    "adaptive": False,
}
```

2. **Run the comparison:**

```python
runner = AblationRunner(
    layer_config=ABLATION_CONFIGS["my_config"],
    n_runs=5, n_rounds=200, n_clients=20
)
results = runner.run()
```

3. **Compare** against the `"full"` config and other relevant ablations.

### 5.4 Adding a New Dataset

**Steps:**

1. **Load your data** (in a notebook or script) — assume you have `X_train, y_train, X_test, y_test` numpy arrays.

2. **Partition using `dirichlet_split`:**

```python
from ifd_fintech.data import dirichlet_split

# Non-IID partition across 20 clients
client_indices = dirichlet_split(
    labels=y_train,
    n_clients=20,
    alpha=0.5,       # moderate non-IID
    seed=42,
    min_samples_per_client=100,
)

# Each client gets its own data
client_data = []
for idx in client_indices:
    X_c = X_train[idx]
    y_c = y_train[idx]
    client_data.append((X_c, y_c))
```

3. **Feed into a Flower client** — implement a standard `flwr.client.NumPyClient` that trains on its partition.

4. **Use `geographic_split`** for a consortium scenario mimicking real banks by region.

---

## 6. Running Experiments

### 6.1 Local Testing

For a quick sanity check with minimal compute:

```python
# test_small.py
import numpy as np
from ifd_fintech.layers.layer1_norm_cosine import NormCosineFilter
from ifd_fintech.orchestration import AdaptiveThresholdEscalation

# Small config
dim = 10
n_clients = 5

# Create filter
l1 = NormCosineFilter(dim)
honest = [np.random.randn(dim) * 0.1 for _ in range(20)]
l1.fit(honest)

# Run a round
orchestrator = AdaptiveThresholdEscalation(n_clients=n_clients, dim=dim)
orchestrator.set_layers(l1, None, None)  # L1-only for quick test
updates = [np.random.randn(dim) * 0.1 for _ in range(n_clients)]
agg, info = orchestrator.process_round(updates)

print(f"Aggregated gradient norm: {np.linalg.norm(agg):.4f}")
print(f"Escalation stats: {info['escalation_stats']}")
```

Run with:
```bash
uv run python test_small.py
```

### 6.2 Full Experiment

The full benchmark evaluates all baselines × attacks × ablations. This is computationally heavy (O(N²) pairwise distances for Bulyan, SVD per round for L2).

```python
# run_benchmark.py
from ifd_fintech.experiment.ablation import AblationRunner, ABLATION_CONFIGS

# Run a single ablation across multiple attacks
for config_name, config in ABLATION_CONFIGS.items():
    if config_name not in ("full", "no_l1", "no_l2", "no_l3", "no_at"):
        continue  # focus on the 5 key ablations
    
    runner = AblationRunner(
        layer_config=config,
        n_runs=5,          # statistical significance
        n_rounds=200,      # full training
        n_clients=20,
    )
    results = runner.run()
    print(f"{config_name}: ASR={results.get('asr', 'N/A'):.3f}")
```

To run the full 14 baselines × 6 attacks × 15 ablations, use the experimental runner (orchestrates parallel runs):

```bash
uv run python -m ifd_fintech.experiment.runner  # if implemented
```

For now, each combination can be run independently via `AblationRunner`.

### 6.3 Flower Simulation

For a full Flower federated learning simulation:

```python
import flwr as fl
from ifd_fintech.orchestration.flower_strategy import AdaptiveLayeredDefenseStrategy

# Strategy wraps the defense
strategy = AdaptiveLayeredDefenseStrategy(n_clients=20, model_dim=model_dim)

# Flower simulation
history = fl.simulation.start_simulation(
    client_fn=client_fn,        # your function returning flwr.client.Client
    num_clients=20,
    config=fl.server.ServerConfig(num_rounds=200),
    strategy=strategy,
)
```

Key points:
- `client_fn(round)` must return a Flower client that trains a model and returns `Parameters`
- The strategy handles gradient extraction (`client_weight - global_model`)
- The orchestrator works purely on **gradients**, not model weights
- All layer state (TemporalReputation) persists inside the strategy across rounds

---

## 7. Evaluation and Metrics

### 7.1 Fraud-Specific Metrics

The project measures defense quality using metrics tailored to financial fraud detection:

| Metric | Interpretation | Target |
|--------|---------------|--------|
| **ASR** | Attack Success Rate — fraction of malicious updates that influence the global model | < 0.25 |
| **AUASR** | Area Under ASR curve — robustness across attack intensities | Lower = better |
| **Savings Rate** | Net savings (fraud prevented − FP review costs) / total fraud | Higher = better |
| **Precision@Recall 80** | Precision when we catch 80% of fraud | > 0.90 |
| **Precision@Recall 95** | Precision when we catch 95% of fraud | > 0.70 |
| **Fβ** | Cost-sensitive F-score with β favoring recall (β ∈ {2, 5, 10}) | Higher = better |

**Savings curve** — plots net savings as `cost_per_fp / avg_fraud_loss` ratio varies. A good defense maintains positive savings even at unfavorable cost ratios.

```python
from ifd_fintech.experiment.metrics import compute_metrics

results = compute_metrics(
    y_true=y_test,
    y_pred=y_pred,
    y_scores=model_scores,
    fraud_amounts=fraud_amounts,          # optional per-transaction loss
    cost_per_fp=5.0,                      # $5 to review a false alert
    avg_fraud_loss=450.0,                 # $450 average fraud loss
)

print(f"ASR: {results.get('asr', 0):.3f}")
print(f"Savings rate: {results.get('savings_rate', 0):.1f}%")
print(f"P@R 90: {results.get('precision_at_recall_90', 0):.3f}")
```

### 7.2 Interpreting Results

| Observation | Interpretation |
|-------------|----------------|
| ASR < 0.25 | Defense is effectively blocking most attacks |
| ASR 0.25–0.50 | Defense is partially effective; attack is leaking through some layers |
| ASR > 0.50 | Attack is largely succeeding; check which layer is failing |
| L1 resolves < 70% | Thresholds may be too tight; check τ₁ adaptation |
| L3 resolves > 20% | Too many updates reaching deep cascade; high computational cost |
| Savings rate < 0 | The FP cost of the defense exceeds the fraud prevented |
| Large fairness gap | Defense disproportionately flags certain client subgroups |

**Cascade FPR interpretation:** If honest FPR at L1 is 2% and overall cascade FPR is 5%, that means 3% of honest clients were initially cleared by L1 but escalated and incorrectly flagged by L2 or L3.

### 7.3 Fairness and Explainability

#### `FairnessEvaluator` (`experiment/fairness.py`)

```python
from ifd_fintech.experiment.fairness import FairnessEvaluator

# Profile your clients
client_profiles = {
    0: "majority",      # large bank, diverse portfolio
    1: "majority",
    2: "minority_serving",  # bank primarily serving minority communities
    3: "small_bank",
    4: "new_entrant",       # recently joined consortium
    # ...
}

evaluator = FairnessEvaluator(client_profiles)
fairness_metrics = evaluator.compute_honest_fpr(
    attack_matrix=attack_matrix,      # (n_clients, n_rounds) boolean
    anomaly_scores=final_scores,       # (n_clients, n_rounds) float
    threshold=0.5,
)

print(fairness_metrics)
# {"majority": 0.02, "minority_serving": 0.05, "small_bank": 0.03, "new_entrant": 0.08}
```

If the fairness gap (max/min FPR) exceeds 3×, investigate potential bias in the defense parameters (e.g., initialization statistics may not represent minority-serving banks).

#### `DefenseRecord` (`experiment/explainer.py`)

```python
from ifd_fintech.experiment.explainer import DefenseRecord
import json

# Build audit trail
audit_log = []
for round_t, decisions in enumerate(round_decisions):
    for client_id, decision in enumerate(decisions):
        if decision["flagged"]:
            record = DefenseRecord(
                round_t=round_t,
                client_id=client_id,
                norm=decision["norm"],
                cos_sim=decision["cos_sim"],
                spectral_score=decision["spectral_score"],
                temporal_score=decision["temporal_score"],
                anomaly_score=decision["anomaly_score"],
                was_flagged=True,
                layer_responsible=decision["layer"],
            )
            audit_log.append(record.to_dict())

# Export for regulatory review
with open("defense_audit.json", "w") as f:
    json.dump(audit_log, f, indent=2, default=str)

# Generate human-readable summary
for record in audit_log[:5]:
    print(DefenseRecord(**record).explain())
```

Explainability output is designed to satisfy:
- **GDPR Article 22** (meaningful information about automated decisions)
- **SR 11-7** (model risk management — audit trail)
- **FATF Recommendation 15** (AML/CFT technology governance)

---

## 8. Project Structure Reference

```
IFD-Fintech/
│
├── pyproject.toml                  # Package metadata, dependencies (numpy, sklearn)
├── uv.lock                         # Locked dependency versions
├── .python-version                 # Python 3.14
├── README.md                       # Project overview and methodology docs
├── adaptive-threshold-escalation.md  # Formal specification of the core mechanism
│
├── ifd_fintech/                    # Main package
│   ├── __init__.py                 # Package root
│   │
│   ├── layers/                     # Detection layers (the "what")
│   │   ├── __init__.py             # Exports: NormCosineFilter, SpectralDetector, TemporalReputation
│   │   ├── layer1_norm_cosine.py   # L1: Fast norm + cosine-similarity filter
│   │   ├── layer2_spectral.py      # L2: PCA/SVD spectral anomaly detection
│   │   └── layer3_temporal.py      # L3: EMA reputation + temporal consistency
│   │
│   ├── orchestration/              # The core novelty (the "how")
│   │   ├── __init__.py             # AdaptiveThresholdEscalation — orchestrator
│   │   └── flower_strategy.py      # Flower wrapper for FL simulation
│   │
│   ├── attacks/                    # Attack models for robustness evaluation
│   │   ├── __init__.py             # AdaptiveAttacker (ABC) + exports
│   │   ├── a1_oracle_whitebox.py   # A1: White-box PGD evasion attack
│   │   ├── a2_grinding.py          # A2: 4-phase temporal grinding attack
│   │   └── a3_spectral_matching.py # A3: Spectral subspace matching attack
│   │
│   ├── baselines/                  # Comparative baseline defenses
│   │   ├── __init__.py             # Baseline (ABC) + exports
│   │   ├── bulyan.py               # Bulyan: Krum + coordinate-wise trimmed mean
│   │   ├── dpfl.py                 # DP-FL: gradient clipping + Gaussian noise
│   │   └── fldetector.py           # FLDetector: historical inconsistency filter
│   │
│   ├── data/                       # Data partitioning utilities
│   │   └── __init__.py             # dirichlet_split() for non-IID partitioning
│   │
│   └── experiment/                 # Evaluation and analysis
│       ├── __init__.py             # Exports metric functions
│       ├── metrics.py              # Fraud metrics (ASR, savings, P@R, Fβ, AUASR)
│       ├── ablation.py             # 15 ablation configs + AblationRunner
│       ├── fairness.py             # Per-subgroup fairness analysis
│       └── explainer.py            # Regulatory-compliant decision explanation
│
├── Paper/                          # Paper materials
│   ├── paper.tex                   # LaTeX source
│   ├── paper_draft.md              # Draft in markdown
│   ├── paper-config.md             # Paper configuration
│   ├── paper-outline.md            # Paper outline
│   └── sigma_verify2.py            # Verification script
│
└── Documentation/                  # Documentation (this guide lives here)
    └── Dev Guide/
        └── developers-guide.md     # ← You are here
```

---

*Last updated: July 2026*
