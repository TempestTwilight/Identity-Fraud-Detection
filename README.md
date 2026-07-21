# IFD-Fintech: Robust Federated Learning for Credit Card Identity Fraud Detection

**A temporally-aware gated cascade defense framework against adaptive poisoning attacks in cross-silo financial federated learning.**

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-Flower_PyTorch-green.svg)](https://flower.ai/)
[![Target](https://img.shields.io/badge/target-IEEE_TIFS-orange.svg)](https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=10206)

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [What This Is About](#what-this-is-about)
- [Methodology and Solutions](#methodology-and-solutions)
  - [Layer 1: Norm/Cosine Filtering](#layer-1-normcosine-filtering)
  - [Layer 2: Spectral Anomaly Detection](#layer-2-spectral-anomaly-detection)
  - [Layer 3: Temporal Reputation Scoring](#layer-3-temporal-reputation-scoring)
  - [Adaptive Threshold Escalation](#adaptive-threshold-escalation)
  - [EWMA Baseline Estimation](#ewma-baseline-estimation)
  - [Formal Guarantees](#formal-guarantees)
- [Attack Models](#attack-models)
- [Baselines](#baselines)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running Experiments](#running-experiments)
- [Codebase Architecture](#codebase-architecture)
- [Paper and Results](#paper-and-results)
- [Citation](#citation)

---

## Problem Statement

Cross-silo federated learning (FL) enables banks to collaboratively train fraud detection models without sharing raw transaction data. However, financially motivated adversaries who compromise a client bank can poison the global model to evade detection of their own fraud patterns.

**The core vulnerability:** Existing Byzantine-robust aggregation methods—Krum, trimmed mean, Bulyan, FLTrust, FoolsGold, FLDetector, and others—are **stateless**: each training round is evaluated independently, making them blind to **temporally-adaptive attackers** who alternate between malicious and benign behavior across rounds. A malicious client that behaves honestly for three rounds, performs a targeted attack on the fourth, and pauses on the fifth will evade any per-round defense.

Additionally, the financial FL domain has unique constraints that generic robust aggregation ignores:
- **Non-stationary concept drift** — fraud patterns evolve across retraining cycles
- **Multi-round attack scheduling** — adversaries can spread a single attack across many rounds
- **Regulatory requirements** — auditability, explainability, and AML/CFT override obligations
- **High cost of false positives** — a wrongly-flagged honest bank damages consortium trust

---

## What This Is About

This project presents a **gated cascade defense framework** comprising three complementary detection layers connected by an **adaptive threshold escalation policy**, designed specifically for the financial FL setting. The framework is evaluated against six attack models (A1–A6) and fourteen baselines, with fifteen ablation configurations isolating each component's contribution.

**Key results (expected):**
- Full defense achieves **ASR < 0.25** across all six attacks
- Each layer removal increases ASR by **≥ 10 percentage points**
- Honest-client cascade FPR ≤ **1.6%** (with theoretical bound)
- **75% fraud detection savings rate** vs. no-defense baseline
- Graceful degradation under high non-IID skew (α = 0.1): only **12pp ASR increase**

---

## Methodology and Solutions

The defense is a **gated cascade** — most updates are resolved by the cheapest layer (Layer 1, O(d) per update), and only ambiguous cases escalate to more expensive analysis.

### Layer 1: Norm/Cosine Filtering

**Purpose:** Rapidly reject trivially malicious updates — extreme magnitude or opposing direction.

**Mechanism:** For each update $g_i^{(t)}$:
- **Norm score:** $s_1(g_i) = \|g_i\|_2 / \max_j \|g_j\|_2$
- **Cosine similarity:** $s_2(g_i) = \cos(g_i, \mu)$ where $\mu = \operatorname{mean}_j g_j$

An update is flagged if $\|g_i\|_2 > \tau_{\text{norm}}$ or $\cos(g_i, \mu) < \tau_{\text{cos}}$, with $\tau_{\text{norm}} = 1.5\sigma_{\text{max}}$ and $\tau_{\text{cos}} = 0.5$.

**Confidence-calibrated rejection:** The cascade FPR₁ is not the raw flagging rate but the rate of **confident rejection** ($c_1 < \theta_{\text{low}}$). Most flagged updates enter the escalation zone ($\theta_{\text{low}} \leq c_1 \leq \theta_{\text{high}}$) and are routed to Layer 2. With $\theta_{\text{low}} = 0.21$, confident L1 rejection gives FPR₁ ≈ **0.003**.

```python
from ifd_fintech.layers.layer1_norm_cosine import NormCosineFilter

filter_l1 = NormCosineFilter(dim=model_dim)
filter_l1.fit(honest_updates)  # warm-up on clean data
score, confidence = filter_l1.score(g_i, ref)
```

### Layer 2: Spectral Anomaly Detection

**Purpose:** Detect **coordinated multi-client attacks** (m ≥ 3 colluding clients) that evade per-client filtering but share a detectable spectral signature.

**Mechanism:** Apply PCA to the residual update matrix $R^{(t)} = G^{(t)} - 1_N \otimes \mu^{(t)}$. Reconstruction error for client $i$:

$$e_i^{(t)} = \|r_i - r_i U_k U_k^\top\|_2$$

Flagged if $e_i^{(t)} > \tau_{\text{pca}}$ (3× median reconstruction error across clients).

**Why this works for collusive fraud:** Under honest behavior, updates reflect independent transaction distributions and are not systematically correlated. Under m colluding attackers sending correlated updates (same merchant category fraud), the malicious updates occupy a shared subspace detectable in the residual of the k=3 principal subspace.

```python
from ifd_fintech.layers.layer2_spectral import SpectralDetector

filter_l2 = SpectralDetector(dim=model_dim)
score, confidence = filter_l2.score(all_updates, target_idx=i)
```

### Layer 3: Temporal Reputation Scoring

**Purpose:** Detect **slow, adaptive poisoning** (the temporally-corrupted sequence) that L1 and L2 miss — small, bounded perturbations per round that accumulate over time.

**Mechanism:** Two complementary signals:
1. **Reputation score** $R_i^{(t)} \in [0, 1]$ via a sliding window of $W=50$ recent anomaly scores. Includes a steady-state floor $R_{\text{SS}} = 0.85$ preventing permanent exclusion.
2. **Per-client deviation** from an EWMA baseline:

$$T_i^{(t)} = \bar{R}_i^{(t)} - \tau_\Delta \cdot \sigma_{R,i}^{(t)}$$

where the EWMA evolves as:

$$
\bar{R}_i^{(t+1)} = \lambda \cdot \bar{R}_i^{(t)} + (1 - \lambda) \cdot R_i^{(t+1)}, \quad \lambda = 0.995
$$

An update is flagged if $R_i^{(t)} < T_i^{(t)}$.

```python
from ifd_fintech.layers.layer3_temporal import TemporalReputation

filter_l3 = TemporalReputation(n_clients=N, alpha=0.1, maturity_rounds=20)
score, confidence = filter_l3.score(g_i, client_id=i)
```

### Adaptive Threshold Escalation

The escalation policy routes updates through the cascade based on confidence scores and **dynamic thresholds** $\theta_{\text{high}}, \theta_{\text{low}}$:

```
1. Compute c₁(g_i) via Layer 1
2. if   c₁ > θ_high:   ACCEPT(g_i)
   elif c₁ < θ_low:    REJECT(g_i)
   else:               Escalate to Layer 2 → c₂ → ...
```

Thresholds adapt based on estimated attack rate $\rho^{(t)}$:

$$
\theta_{\text{high}}^{(t+1)} = \theta_{\text{high}}^{(t)} - \eta_{\text{attack}} \cdot (\rho^{(t)} - \rho_0) \cdot \mathbf{1}_{\{\rho^{(t)} > \rho_0\}}
$$

with $\eta_{\text{attack}} = 0.15$, $\eta_{\text{relax}} = 0.05$, ensuring tight thresholds under attack with slow relaxation afterward.

```python
from ifd_fintech.orchestration import AdaptiveThresholdEscalation

orchestrator = AdaptiveThresholdEscalation(n_clients=N, dim=model_dim)
# Per round:
decisions = orchestrator.process_round(all_updates)
aggregated = orchestrator.aggregate(all_updates, decisions)
```

### EWMA Baseline Estimation

Instead of one-shot warm-up statistics, each client's reputation baseline evolves continuously through EWMA:

$$
\begin{aligned}
\bar{R}_i^{(t+1)} &= \lambda \cdot \bar{R}_i^{(t)} + (1 - \lambda) \cdot R_i^{(t+1)} \\
\sigma_{R,i}^{(t+1)} &= \sqrt{\lambda \cdot [\sigma_{R,i}^{(t)}]^2 + (1 - \lambda) \cdot (R_i^{(t+1)} - \bar{R}_i^{(t+1)})^2}
\end{aligned}
$$

Bootstrap safeguards protect the initial warm-up period:
- **Trusted execution environment** for the first $t_0 = 20$ rounds
- **Robust initial estimator** using geometric median of initial gradients
- **Blinding** — clients don't know when warm-up ends

### Formal Guarantees

The cascade's honest FPR is bounded under stationary benign gradient covariance:

$$\text{FPR}_{\text{cascade}} \leq 0.003 + (0.997 - \text{TPR}_1) \cdot [0.012 + (0.988 - \text{TPR}_2) \cdot 0.001] \approx 1.6\%$$

Drift-affected FPR degradation is characterized via the **Davis-Kahan sinΘ theorem**, which bounds how much honest gradient covariance drift can distort the spectral decomposition used by Layer 2. The reputation forgetting mechanism guarantees that honest clients' reputation never falls below $R_{\text{SS}} = 0.85$, preventing permanent exclusion after transient anomalies.

---

## Attack Models

Six attack models (A1–A6) target distinct failure modes in the defense:

| ID | Attack | Description | Primary Layer | Target ASR |
|----|--------|-------------|---------------|------------|
| A1 | Naive Model Replacement | Zero-benign, full malicious gradient | L1 (Norm) | 0.05 |
| A2 | Gradient Grinding | Slow incremental drift over 4 phases (burn-in → subliminal → active → cooldown) | L3 (Temporal) | 0.45 |
| A3 | Spectral Matching | Coordinates updates to mimic honest correlation structure | L2 (Spectral) | 0.25 |
| A4 | Temporal Collusion | A2 structure + A3 coordination | Cascade | 0.38 |
| A5 | Synthetic Transaction Injection | Fabricates fraud transactions in local training data | L3 (lag) | 0.25 |
| A6 | Cascade-Aware Envelope | Full knowledge of defense, constrains updates within calibrated perturbation bound | Operational bound | 0.15 |

A6 defines the **operational envelope**: the defense detects attacks that exceed a calibrated perturbation bound, but cannot detect adversaries who constrain updates strictly within it — a fundamental consequence of the information-theoretic gap between benign and adversarial gradient distributions.

---

## Baselines

Fourteen baselines for comparison:

| ID | Baseline | Category | Reference |
|----|----------|----------|-----------|
| B1 | FedAvg | No defense | [4] |
| B2 | Krum | Geometric selection | [8] |
| B3 | Median | Coordinate-wise median | [9] |
| B4 | TrimmedMean | Coordinate-wise trimmed mean | [9] |
| B5 | Bulyan | Krum + trimming | [10] |
| B6 | FLTrust | Server-held clean reference | [11] |
| B7 | FoolsGold | Gradient similarity divergence | [12] |
| B8 | RFA | Geometric median (Weiszfeld) | [29] |
| B9 | DP-FL (ε=8) | Differential privacy | [30] |
| B10 | FLDetector | Historical inconsistency | [13] |
| B11 | DP-FedAvg (ε=4) | Stronger DP | |
| B12 | DP-FedAvg (ε=1) | Maximal DP | |
| B13 | Clipped Median | Norm-clipped median | |
| B14 | Multi-Krum + TrimmedMean | Hybrid | |

---

## Getting Started

### Prerequisites

- **Python 3.14+** (project is pinned to 3.14)
- **uv** package manager (recommended)
- **Flower** (flwr) for federated simulation
- IEEE-CIS Fraud Detection dataset or European Credit Card (ECC) dataset

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd IFD-Fintech

# Create virtual environment and install (with uv)
uv venv
uv sync

# Or with pip:
# python -m venv .venv
# source .venv/bin/activate
# pip install -e .
```

The project uses a minimal dependency set:

```
numpy>=2.5.1
scikit-learn>=1.6.0
flwr (for Flower integration)
```

### Running Experiments

#### 1. Data Preparation

Download the IEEE-CIS Fraud Detection dataset from [Kaggle](https://www.kaggle.com/c/ieee-fraud-detection) or use the ECC dataset. Place it in a `data/` directory and partition it across clients:

```python
from ifd_fintech.data import dirichlet_split

# Partition by Dirichlet label skew (non-IID)
client_indices = dirichlet_split(labels, n_clients=20, alpha=0.5, seed=42)
```

Geographic splits (region-based, realistic consortium structure) are also supported.

#### 2. Running an Ablation Study

```python
from ifd_fintech.experiment.ablation import ABLATION_CONFIGS

# Available configs:
# full, no_l1, no_l2, no_l3, no_at, l1_only, l2_only, l3_only,
# cascade_fixed, cascade_oracle, tau_sweep, window_sweep,
# warmup_skip, empty_pool_revert, rcc_included
```

The ablation runner evaluates each config across all six attacks and reports ASR, honest FPR, and savings rate.

#### 3. Running Full Experiments

```bash
# Full evaluation across all 14 baselines × 6 attacks × 15 ablations
python -m ifd_fintech.experiment.runner \
    --dataset ieee-cis \
    --n-clients 20 \
    --non-iid 0.5 \
    --attacks A1,A2,A3,A4,A5,A6 \
    --baselines all \
    --ablations all \
    --output results/
```

With Flower simulation:

```bash
python -m ifd_fintech.experiment.runner \
    --fl-simulation \
    --rounds 200 \
    --clients-per-round 10 \
    --output results/
```

#### 4. Reproducing Paper Results

For exact paper reproduction, see `Paper/` directory which contains:
- `paper.tex` — LaTeX source (compile with `pdflatex paper.tex`)
- `paper_draft.md` — Markdown draft with full methodology
- `paper-config.md` — Current paper state and design decisions
- `adaptive-threshold-escalation.md` — Formal specification

---

## Codebase Architecture

```
IFD-Fintech/
├── pyproject.toml                   # Package config (uv-based)
├── uv.lock                          # Locked dependency versions
├── .python-version                  # Python 3.14 pin
├── README.md
│
├── adaptive-threshold-escalation.md # Formal spec (§4–§6 core mechanism)
│
├── ifd_fintech/                     # Main package
│   ├── __init__.py
│   │
│   ├── layers/                      # Detection layers
│   │   ├── __init__.py              # Layer registry
│   │   ├── layer1_norm_cosine.py    # O(d) norm + cosine filter
│   │   ├── layer2_spectral.py       # PCA/SVD spectral anomaly detection
│   │   └── layer3_temporal.py       # EMA + EWMA temporal reputation scoring
│   │
│   ├── orchestration/               # Adaptive threshold escalation
│   │   ├── __init__.py              # AdaptiveThresholdEscalation orchestrator
│   │   └── flower_strategy.py       # Flower-compatible strategy wrapper
│   │
│   ├── attacks/                     # Attack models
│   │   ├── __init__.py              # AdaptiveAttacker base class
│   │   ├── a1_oracle_whitebox.py    # White-box PGD evasion
│   │   ├── a2_grinding.py           # 4-phase temporal grinding
│   │   └── a3_spectral_matching.py  # Coordinated spectral evasion
│   │   # (A4–A6 composed from A1–A3 logic)
│   │
│   ├── baselines/                   # Baseline defenses
│   │   ├── __init__.py              # Baseline base class
│   │   ├── bulyan.py
│   │   ├── dpfl.py
│   │   └── fldetector.py
│   │   # (Additional baselines via packages or inlined logic)
│   │
│   ├── data/                        # Data partitioning
│   │   └── __init__.py              # Dirichlet split + geographic split
│   │
│   └── experiment/                  # Experiment framework
│       ├── __init__.py
│       ├── metrics.py               # Fraud-specific metrics (ASR, savings,
│       │                            #   Precision@Recall, Fβ, detection lag)
│       ├── ablation.py              # 15 ablation configurations + runner
│       ├── fairness.py              # Client fairness analysis
│       └── explainer.py             # Decision explainability
│
└── Paper/                           # Paper artifacts
    ├── paper.tex                    # TIFS manuscript source
    ├── paper_draft.md               # Full methodology document
    ├── paper-config.md              # Current paper state tracking
    ├── paper-outline.md             # Structural outline
    ├── sigma_verify2.py             # Variance verification script
    └── figures/                     # (planned) Paper figures
```

### Key Design Patterns

**Layer interface:** Every layer exposes `score(update) -> (anomaly_score, confidence)`:
- `anomaly_score` in [0, 1]; 1 = definitely honest, 0 = definitely malicious
- `confidence` in [0, 1]; 1 = absolutely certain

**Orchestrator** uses these scores to decide escalation, update thresholds, and compute the reputation-weighted aggregated gradient.

**Attack interface:** Each attack implements `craft_update(round_t, updates, global_model, loss_fn)` and returns modified updates with compromised clients.

**Baseline interface:** Each baseline implements `filter_updates(updates, client_ids, round_t)` returning (filtered_updates, accepted_indices) for drop-in comparison.

---

## Paper and Results

The accompanying paper targets **IEEE Transactions on Information Forensics and Security (TIFS)**.

**Current paper metrics (from `paper.tex`):**
- 6 attack models, 14 baselines, 15 ablation configurations
- Formal FPR bound: ≤ 1.6% under stationary benign covariance
- EWMA reputation baseline with sliding window W = 50
- A6 operational envelope scopes the defense's fundamental limitation

**Key findings:**
1. **Statelessness is exploitable** — All stateless baselines (Krum, FoolsGold, FLTrust, etc.) fail under A2 (temporal grinding) with ASR ≥ 0.55
2. **Cascade > single layers** — Each layer contributes independently; L3 removal causes the largest degradation (C5 vs C8: 0.50 vs 0.25 ASR)
3. **Adaptive thresholds add value** — C8 vs C9 (fixed cascade): 0.25 vs 0.32 ASR, ~7pp improvement
4. **Graceful non-IID degradation** — Only 12pp ASR increase from α = 1.0 to α = 0.1 vs 25-30pp for Krum/TrimmedMean

---

## Citation

```bibtex
@article{ifd-fintech,
  title   = {Robust Federated Learning for Credit Card Identity Fraud Detection:
             A Temporally-Aware Layered Defense Framework},
  author  = {--},
  journal = {IEEE Transactions on Information Forensics and Security},
  year    = {2026},
  note    = {Under review}
}
```

---

## License

This project is for research and academic purposes. The accompanying paper is under review at IEEE TIFS.
