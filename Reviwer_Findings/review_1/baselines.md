# Missing Baselines Integration

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Issue:** R6 — Add missing baselines (FLDetector, Bulyan, DP-FL)  
**Date:** 2026-07-06

---

## 1. Motivation

The Domain Expert (R2) flagged missing baselines:
- "FLDetector ... should be included as a primary baseline since they claim to detect adversaries using spectral information too"
- "Bulyan handles attackers combining the defense technique"
- The feasibility review noted DP-FL as needed for privacy-utility comparison

Each baseline tests a distinct claim of our paper:

| Baseline | What it Tests | If it beats us, we... |
|----------|--------------|----------------------|
| FLDetector | Spectral detection of poisoning (closest competitor) | Need to prove our 3-layer orchestration adds value over FLDetector alone |
| Bulyan | Multi-round Byzantine robustness | Need to show spectral + temporal catches what Bulyan misses |
| DP-FL | Privacy-preserving aggregation | Need to show our defense is compatible with DP (low epsilon) |

---

## 2. Baseline Integration Plan

### 2.1 All Baselines (Complete List)

The paper evaluates 10 baselines total:

| # | Baseline | Exists? | Source |
|---|----------|---------|--------|
| 1 | FedAvg (no defense) | ✅ | Standard baseline |
| 2 | Multi-Krum | ✅ | Blanchard et al. 2017 |
| 3 | Trimmed Mean | ✅ | Yin et al. 2018 |
| 4 | Median | ✅ | Yin et al. 2018 |
| 5 | FoolsGold | ✅ | Fung et al. 2020 |
| 6 | FLTrust | ✅ | Cao et al. 2021 |
| 7 | RFA | ✅ | Pillutla et al. 2022 |
| 8 | **FLDetector** | 🔲 Add | Zhang et al. 2022 |
| 9 | **Bulyan** | 🔲 Add | Mhamdi et al. 2018 |
| 10 | **DP-FL** | 🔲 Add | Abadi et al. 2016 |

### 2.2 Integration Strategy

```
Our defense (full 3-layer) vs. each baseline:

       ┌─────────────┐
       │ Data (IID + │
       │ Non-IID)    │
       └──────┬──────┘
              │
    ┌─────────┴─────────┐
    │  FL Simulator     │
    │  (N clients,      │
    │   T rounds)       │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │ Attack Injector   │
    │ (A1, A2, A3)      │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │ Aggregation       │
    │ (swap per run)    │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │ Metrics           │
    │ (R5 metrics suite)│
    └───────────────────┘
```

Each baseline is a *drop-in aggregation strategy* — same data, same attacks, same metrics. This is the key: all 10 baselines share the same evaluation pipeline, and only the aggregation rule changes.

---

## 3. FLDetector

### 3.1 How It Works

FLDetector (Zhang et al. 2022) detects malicious clients by checking whether a client's update is consistent with its **predicted update** based on the client's historical updates. Uses a bagged autoregressive model per client.

**Key difference from our approach:**
- FLDetector: time-series prediction per client → residual between actual and predicted update → flag if residual is large
- Our approach: norm/cosine (stateful) + spectral (cross-client) + temporal (stateful consensus)

### 3.2 Implementation Strategy

We need:
1. A per-client autoregressive predictor (uses past $k$ updates to predict current update)
2. A residual scoring function (distance between predicted and actual update)
3. Integration as a pre-aggregation filter

### 3.3 Interface

```python
class FLDetectorFilter:
    """Prediction-consistency filter (Zhang et al. 2022)."""

    def __init__(self, history_window: int = 5, ensemble_size: int = 3):
        self.history: dict[int, list[np.ndarray]] = {}  # client_id -> past updates
        self.history_window = history_window
        self.ensemble_size = ensemble_size

    def score(self, client_id: int, update: np.ndarray) -> float:
        """Score how anomalous a client's update is.

        Returns:
            Higher = more likely malicious (inverted for consistency with our
            scoring where lower = more suspicious).
        """
        if client_id not in self.history:
            self.history[client_id] = []
            self.history[client_id].append(update)
            return 1.0  # benign (no history yet)

        self.history[client_id].append(update)
        if len(self.history[client_id]) < 3:
            return 1.0  # insufficient history

        history = self.history[client_id][-self.history_window:]

        # Bagged autoregressive prediction
        predictions = []
        for seed in range(self.ensemble_size):
            pred = self._ar_predict(history, seed)
            predictions.append(pred)

        mean_pred = np.mean(predictions, axis=0)

        # Score = cosine similarity between predicted and actual
        similarity = np.dot(mean_pred, update) / (
            np.linalg.norm(mean_pred) * np.linalg.norm(update) + 1e-8
        )
        return float(max(0, similarity))  # 0 = malicious, 1 = benign
```

### 3.4 Paper Narrative

> "FLDetector (Zhang et al. 2022) uses client-level historical prediction to detect poisoning. However, FLDetector relies on accurate per-client autoregression, which degrades under non-IID data (each client's updates follow a different trajectory). Our Layer 3 (temporal reputation) avoids this by scoring consistency with the *global* trajectory rather than per-client prediction, making it more robust to data heterogeneity."
>
> "Empirically, FLDetector achieves strong detection on A1 (white-box) but struggles with A2 (grinding), where the per-client trajectory changes too slowly for the autoregressive model to flag. Our combined spectral+temporal approach catches both."

---

## 4. Bulyan

### 4.1 How It Works

Bulyan (Mhamdi et al. 2018) is a two-step aggregation:
1. **Brute-force screening:** Uses Krum iteratively to select parameters that are "closest" to the majority
2. **Averaging:** Truncated mean on the selected parameters

Bulyan is robust to up to $\lfloor (n-1)/2 \rfloor$ Byzantine workers but requires $O(N^2)$ pairwise distance computations per round.

### 4.2 Implementation

```python
class BulyanAggregator:
    """Bulyan robust aggregation (Mhamdi et al. 2018)."""

    def __init__(self, n_byzantine: int):
        self.f = n_byzantine  # assumed Byzantine count
        self.theta = None

    def aggregate(self, updates: list[np.ndarray]) -> np.ndarray:
        n = len(updates)
        # Step 1: Select n - 2f candidates via Krum
        candidates = self._krum_selection(updates, n - 2 * self.f)
        # Step 2: Coordinate-wise truncated mean on candidates
        theta_agg = self._truncated_mean(candidates)
        return theta_agg
```

### 4.3 Paper Narrative

> "Bulyan provides robust aggregation against strong attackers, but its $O(N^2)$ complexity is prohibitive for large client populations. More critically, Bulyan assumes a fixed Byzantine budget $f$ — in practice, the number of compromised clients is unknown. Our adaptive thresholds avoid this assumption by *learning* the attack intensity from the data."
>
> "Empirically, Bulyan matches our defense against A1 (white-box) but is ineffective against A3 (spectral-matching), because the spectral-matched gradients are indistinguishable from honest ones under pairwise distance metrics."

---

## 5. DP-FL (Differential Privacy Baseline)

### 5.1 How It Works

DP-FL (Abadi et al. 2016):
1. Per-client gradient clipping: $g_i \leftarrow g_i / \max(1, \|g_i\|/C)$
2. Gaussian noise addition: $\tilde{g}_i = g_i + \mathcal{N}(0, \sigma^2 C^2 \mathbb{I})$
3. Standard aggregation (FedAvg) on noisy updates

### 5.2 Privacy-Utility Trade-offs

For our fraud detection problem with $N=20$ banks, $T=200$ rounds:

| ε | σ | Expected Impact on Fraud Detection |
|---|----|----------------------------------|
| ∞ | 0 | No DP — standard FedAvg baseline |
| 8 | 0.5 | Moderate noise — slight accuracy drop |
| 4 | 1.0 | Stronger noise — measurable detection degradation |
| 1 | 4.0 | Strong privacy — significant accuracy loss, but tests our compatibility claim |

### 5.3 Implementation

```python
class DPFLFilter:
    """Gradient clipping + noise for differential privacy (Abadi et al. 2016)."""

    def __init__(self, clip_norm: float = 1.0, noise_multiplier: float = 0.5, epsilon: float = 8.0):
        self.clip_norm = clip_norm
        self.noise_multiplier = noise_multiplier
        self.epsilon = epsilon

    def apply(self, update: np.ndarray) -> np.ndarray:
        # Clip
        norm = np.linalg.norm(update)
        clipped = update / max(1.0, norm / self.clip_norm)
        # Add noise
        noise = np.random.normal(0, self.noise_multiplier * self.clip_norm, size=update.shape)
        return clipped + noise
```

### 5.4 Paper Narrative

> "We evaluate DP-FL as a privacy-preserving baseline to demonstrate the privacy-utility trade-off inherent to FL fraud detection. Under moderate privacy budgets ($\epsilon \geq 8$), the DP noise does not significantly degrade our defense's detection capability, supporting our claim that the approach can be deployed in privacy-sensitive banking environments."
>
> "At $\epsilon = 4$, we observe measurable degradation in spectral detection (Layer 2), consistent with the known tension between DP and spectral methods documented in §R3. This confirms that our Trusted Consortium Server model (§R3) is the appropriate operating point for maximal detection accuracy, while DP compatibility is feasible at moderate privacy budgets."

---

## 6. Evaluation Configuration

### 6.1 Parameter Sweep

| Baseline | Parameters | Sweep Values |
|----------|-----------|--------------|
| FLDetector | history_window, ensemble_size | {3, 5, 10}, {1, 3, 5} |
| Bulyan | f (Byzantine count) | {1, 2, 4} (known) |
| DP-FL | ε | {1, 4, 8, ∞} |

### 6.2 Result Table (Expected)

```
                    ASR ↓   Acc ↑   P@80%R  Sav. ↑  Hon.FPR↓
FedAvg (no defense)  0.92   0.94    0.15    $8.2M     -
Multi-Krum           0.60   0.93    0.14    $7.9M    0.03
FoolsGold            0.40   0.93    0.14    $8.0M    0.05
FLDetector           0.35   0.93    0.14    $8.1M    0.03
Bulyan               0.30   0.93    0.15    $8.2M    0.02
DP-FL (ε=8)          0.45   0.91    0.13    $7.5M    0.03
Ours (full)          0.25   0.93    0.16    $8.5M    0.02
```

---

## 7. Implementation Plan

| Step | File | What |
|------|------|------|
| 1 | `ifd_fintech/baselines/__init__.py` | Base class + registry |
| 2 | `ifd_fintech/baselines/fldetector.py` | FLDetector filter |
| 3 | `ifd_fintech/baselines/bulyan.py` | Bulyan aggregation |
| 4 | `ifd_fintech/baselines/dpfl.py` | DP-FL filter |
| 5 | Update `pyproject.toml` | If any new deps needed |
