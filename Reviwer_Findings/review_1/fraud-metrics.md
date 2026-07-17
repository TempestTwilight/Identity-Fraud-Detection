# Fraud-Specific Evaluation Metrics

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Issue:** R5 — Define fraud-specific evaluation metrics  
**Date:** 2026-07-06

---

## 1. Motivation

The feasibility review (all 5 reviewers) flagged that standard ML metrics are insufficient for fraud detection:

- **R1 (Methodology):** "AUC alone misses the cost asymmetry — a model that catches 90% of fraud at 30% FPR is useless in production."
- **R2 (Domain):** "For fraud detection, the cost of False Positives (friction, customer service, churn) vs. cost of False Negatives (direct fraud loss) defines the evaluation landscape."
- **DA:** "Profit-based evaluation is what matters."

$$\text{Standard ML: maximize AUC} \quad \neq \quad \text{Fraud detection: maximize net savings}$$

---

## 2. Metric Suite Overview

| # | Metric | What it Measures | Section |
|---|--------|-----------------|---------|
| 1 | Attack Success Rate (ASR) | Backdoor effectiveness: % of trigger examples misclassified as benign | §3 |
| 2 | Main Task Accuracy | Stealth: model accuracy on clean test data under attack | §4 |
| 3 | Precision@Recall | Operational: precision at decision thresholds that capture 80/90% of fraud | §5 |
| 4 | Savings Curve | Business value: net savings = (fraud caught × avg loss) - (false positives × review cost) | §6 |
| 5 | Cost-Sensitive Fβ | Weighted F-score with configurable FN penalty | §7 |
| 6 | Honest-Client FPR | Defense-specific: false positive rate on clean federated clients | §8 |
| 7 | Cumulative Detection Lag | Defense-specific: rounds until the defense flags each attacker | §9 |

---

## 3. Attack Success Rate (ASR)

### 3.1 Definition

For a backdoor attack with trigger $p$ and target label $y_{\text{target}}$:

$$\text{ASR} = \frac{|\{x \in \mathcal{D}_{\text{test}} \mid \text{trigger}(x) = p \land f_\theta(x) = y_{\text{target}}\}|}{|\{x \in \mathcal{D}_{\text{test}} \mid \text{trigger}(x) = p\}|}$$

**Interpretation:** ASR = 0.0 means the defense fully blocks the backdoor. ASR = 0.95 means 95% of crafted fraudulent transactions evade detection.

### 3.2 Attack-Specific ASR

| Attack Type | Trigger Definition | Expected ASR (No Defense) | Expected ASR (Our Defense) |
|------------|-------------------|--------------------------|---------------------------|
| A1: White-box | Backdoor on specific transaction pattern | 0.92 | 0.25 (or lower) |
| A2: Grinding | Slow drift causing misclassification | 0.70 | 0.15 (adaptive threshold catches) |
| A3: Spectral | Subspace-hidden trigger | 0.85 | 0.35 (temporal catches) |

### 3.3 Reporting

Report ASR as:

```
ASR@200 (primary): fraction of successful backdoor triggers at round 200
ASR curve:     ASR^{(t)} for t ∈ [1, 200] — show the trajectory
AUASR:         Area Under the ASR Curve — a single number summary
```

---

## 4. Main Task Accuracy

### 4.1 Definition

The model's classification accuracy on a clean held-out test set that contains **no adversarial triggers**. If the defense severely degrades clean accuracy, it's unusable regardless of defense performance.

$$\text{Acc}_{\text{main}} = \frac{1}{|\mathcal{D}_{\text{clean}}|} \sum_{(x,y) \in \mathcal{D}_{\text{clean}}} \mathbb{1}[f_\theta(x) = y]$$

### 4.2 Reporting

| Defense | Acc_main (clean) | Acc_main (under A1) | Acc_main (under A2) | Acc_main (under A3) |
|---------|-----------------|-------------------|-------------------|-------------------|
| FedAvg | 0.94 | 0.91 | 0.89 | 0.90 |
| Krum | 0.93 | 0.91 | 0.90 | 0.91 |
| Ours | 0.93 | 0.92 | 0.93 | 0.92 |

**Key:** The defense should not sacrifice more than 1-2% clean accuracy compared to FedAvg.

---

## 5. Precision@Recall

### 5.1 Definition

Fraud detection requires high recall (you don't want to miss fraud), but at the cost of precision. The operational question is: **"At the recall level we need, what precision do we get?"**

$$\text{Precision@Recall}=R = \max_{\tau} \left\{ \text{Precision}(\tau) \mid \text{Recall}(\tau) \geq R \right\}$$

where $\tau$ is the model's decision threshold.

### 5.2 Standard Reporting Points

| Recall Target | Why It Matters | Typical Acceptable Precision |
|---------------|----------------|---------------------------|
| R@80% | Minimum operational recall | > 10% (10% of flagged cases are fraud) |
| R@90% | High-security regime | > 5% (more false positives acceptable) |
| R@95% | Maximum fraud capture | > 2% (any signal is valuable) |

### 5.3 Reporting Format

```
| Defense | P@80% R  | P@90% R  | P@95% R  |
|---------|----------|----------|----------|
| FedAvg  | 0.15     | 0.08     | 0.03     |
| Krum    | 0.14     | 0.07     | 0.03     |
| Ours    | 0.16     | 0.09     | 0.04     |
```

---

## 6. Savings Curve (Profit-Based Metric)

### 6.1 Motivation

AUC can be gamed — a model that achieves 0.95 AUC by ranking fraud slightly better than non-fraud may still lose money. The savings curve measures **actual profit** under a realistic cost model.

### 6.2 Cost Model

| Parameter | Value | Source |
|-----------|-------|--------|
| Average fraud loss per FN | $450 | IEEE-CIS average transaction value |
| Average fraud loss per FN (high) | $800 | Upper decile transaction value |
| FP review cost | $5 | Fraud analyst time per alert (≈ 5 min at $60/hr) |
| TP review cost | $5 | Same — every alert is reviewed |
| Cost ratio (FN:FP) | 90:1 (base) | $450 / $5 |
| Cost ratio range tested | 10:1 to 200:1 | Sensitivity analysis |

### 6.3 Net Savings Formula

At threshold $\tau$ on a test set with $N_{\text{total}}$ transactions:

$$\text{Savings}(\tau) = \text{TP}(\tau) \times V_{\text{FN}} - \text{FP}(\tau) \times C_{\text{FP}}$$

where $V_{\text{FN}}$ is the value saved per true fraud caught (average fraud loss), and $C_{\text{FP}}$ is the cost per false positive alert.

### 6.4 Normalized Savings

Divide by maximum possible savings (catching all fraud with zero FP):

$$\text{Normalized Savings}(\tau) = \frac{\text{TP}(\tau) \times V_{\text{FN}} - \text{FP}(\tau) \times C_{\text{FP}}}{\text{Total Fraud Loss}}$$

### 6.5 Reporting

```
Savings Curve (FN:FP = 90:1):

  100% |                                             ● FedAvg
       |                                         ●
   80% |                                     ●         ● Ours (defense)
       |                                 ●
   60% |                             ●          ● Krum
       |                         ●
   40% |                     ●
       |                 ●
   20% |             ●
       |         ●
    0% | ●
       |
   ────└─────────────────────────────────────────
       0.0   0.2   0.4   0.6   0.8   1.0
              FP Rate (alerts as % of transactions)
```

Report as a table:

```
| Defense | Max Savings | Savings@80% Rec | Savings@90% Rec | Break-even FPR |
|---------|------------|-----------------|-----------------|----------------|
| FedAvg  | $8.2M      | $5.4M           | $3.1M           | 0.12           |
| Krum    | $7.9M      | $5.1M           | $2.8M           | 0.11           |
| Ours    | $8.5M      | $5.8M           | $3.6M           | 0.14           |
```

### 6.6 Sensitivity: Cost Ratio

Run the savings calculation at multiple cost ratios to ensure results are not an artifact of a specific cost assumption:

| FN:FP | Ours Savings | FedAvg Savings | Delta |
|-------|-------------|----------------|-------|
| 10:1  | $1.2M       | $1.1M         | +9%   |
| 50:1  | $4.8M       | $4.2M         | +14%  |
| 90:1  | $8.5M       | $8.2M         | +4%   |
| 200:1 | $15.2M      | $14.8M        | +3%   |

---

## 7. Cost-Sensitive Fβ

### 7.1 Definition

The standard $F_1$ score weights precision and recall equally. In fraud, False Negatives are far more costly. $F_\beta$ generalizes the trade-off:

$$F_\beta = \frac{(1 + \beta^2) \cdot \text{Precision} \cdot \text{Recall}}{\beta^2 \cdot \text{Precision} + \text{Recall}}$$

where $\beta$ is the relative weight of recall over precision.

### 7.2 Beta Selection

| β | Interpretation | When to Use |
|---|---------------|-------------|
| 1 | Precision = Recall equally important | Baseline comparison with rest of FL literature |
| 2 | Recall 2× more important than precision | Conservative fraud detection |
| 5 | Recall 5× more important | High-security regime (missed fraud is catastrophic) |
| 10 | Recall 10× more important (matches 90:1 cost ratio) | Realistic banking fraud detection |

### 7.3 Reporting

```
| Defense | F₁    | F₂    | F₅    | F₁₀   |
|---------|-------|-------|-------|-------|
| FedAvg  | 0.72  | 0.68  | 0.55  | 0.42  |
| Krum    | 0.70  | 0.65  | 0.52  | 0.40  |
| Ours    | 0.74  | 0.71  | 0.61  | 0.49  |
```

---

## 8. Honest-Client False Positive Rate

### 8.1 Definition

This is the defense-specific metric that answers: **"Does the defense falsely flag honest banks as attackers?"**

$$\text{Honest FPR} = \frac{\text{Honest clients flagged as malicious}}{\text{Total honest clients}}$$

This is measured **per-round** and **cumulatively**.

### 8.2 Reporting

```
Honest-Client FPR (over 200 rounds):

| Defense      | Per-Round FPR (mean ± std) | Cumulative FPR (ever flagged) |
|--------------|---------------------------|-------------------------------|
| Krum         | 0.03 ± 0.02              | 0.12                          |
| FoolsGold    | 0.05 ± 0.03              | 0.20                          |
| Ours (all 3) | 0.02 ± 0.01              | 0.08                          |
| Ours (L1+L3) | 0.01 ± 0.01              | 0.04                          |
```

**Key requirement for TIFS (R10 fairness):** Honest FPR should not be significantly higher for banks with unusual but legitimate data distributions (minority demographics, small banks vs. large banks).

---

## 9. Cumulative Detection Lag

### 9.1 Definition

Number of rounds from the attacker's first malicious action until the defense assigns a non-zero anomaly score to the attacker.

$$\text{Detection Lag} = \min \{ t \mid s_i^{(t)} < \tau_1 \} - t_{\text{attack start}}$$

### 9.2 Reporting

```
| Attack   | Rounds to Detection | Flagged by Layer |
|----------|--------------------|------------------|
| A1: Oracle      | 3.2 ± 1.1      | L2 (spectral)     |
| A2: Grinding    | 14.5 ± 3.8     | L3 (temporal) + adaptive threshold alarm |
| A3: Spectral    | 5.8 ± 2.3      | L3 (temporal)     |
```

---

## 10. Complete Evaluation Matrix

The paper's results table should summarize:

```
┌──────────────────────┬────────┬────────┬────────┬──────────┬───────────┬────────┐
│ Defense              │ ASR ↓  │ Acc ↑  │P@80%R↑ │Savings ↑ │ Hon. FPR↓│β=5↑    │
├──────────────────────┼────────┼────────┼────────┼──────────┼───────────┼────────┤
│ No defense (FedAvg)  │ 0.92   │ 0.94   │ 0.15   │ $8.2M    │ -         │ 0.55   │
│ Krum                 │ 0.60   │ 0.93   │ 0.14   │ $7.9M    │ 0.03      │ 0.52   │
│ Trimmed Mean         │ 0.55   │ 0.93   │ 0.14   │ $8.0M    │ 0.02      │ 0.53   │
│ FoolsGold            │ 0.40   │ 0.93   │ 0.14   │ $8.0M    │ 0.05      │ 0.55   │
│ Ours (full)          │ 0.25   │ 0.93   │ 0.16   │ $8.5M    │ 0.02      │ 0.61   │
│ Ours (no L2, DP ε=4) │ 0.35   │ 0.92   │ 0.15   │ $8.1M    │ 0.01      │ 0.57   │
└──────────────────────┴────────┴────────┴────────┴──────────┴───────────┴────────┘
```

(This is the "one big table" that TIFS reviewers expect — summary metrics accessible at a glance.)

---

## 11. Implementation: `ifd_fintech/experiment/metrics.py`

```python
def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: np.ndarray,
    fraud_amounts: np.ndarray,
    cost_per_fp: float = 5.0,
    fn_loss_ratio: float = 90.0,
) -> dict:
    """
    Compute all fraud-specific metrics.

    Returns dict with:
      - asr, main_acc, precision_at_recall_80/90/95
      - savings_curve: list of (threshold, savings, norm_savings)
      - f_beta for beta in [1, 2, 5, 10]
      - break_even_fpr
    """
    ...

def compute_defense_metrics(
    attack_labels: np.ndarray,          # which rounds each client was attacking
    anomaly_scores: np.ndarray,         # per-client per-round anomaly scores
    detection_threshold: float = 0.5,
) -> dict:
    """
    Compute defense-specific metrics.

    Returns dict with:
      - honest_fpr (per-round, cumulative)
      - rounds_to_detection (per attack type)
      - flagging_layer (which layer flagged each attacker)
    """
    ...
```
