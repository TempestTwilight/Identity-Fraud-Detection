# ADR-008: Fraud-Specific Evaluation Metrics

**Status:** Accepted

**Context:**

Standard FL defense evaluation uses metrics like accuracy, AUC-ROC, and robust accuracy under attack. These are insufficient for a credit card fraud detection system. The fraud domain has a unique cost structure and operational constraints that generic metrics fail to capture:

- **Cost asymmetry:** A false negative (missed fraud) costs ~$450 (average fraud loss per transaction), while a false positive costs ~$5 (manual review). This 90:1 cost ratio means the evaluation must be cost-sensitive.
- **Savings curve:** The key business metric is *total fraud savings* — not accuracy on a held-out set. A model with 99% accuracy could be worthless if the 1% of errors cover all high-value fraud.
- **Attack success criteria:** An attack "succeeds" if it causes the global model to misclassify specific fraud patterns. Standard robust accuracy measures whether the model's overall accuracy degrades — which is less relevant.
- **Operational constraints:** Regulators (FATF Recommendation 15) require explainable decisions and bounded detection lag. The evaluation must measure both.

**Decision:**

**We adopt a fraud-specific metrics suite in place of (or supplementing) generic accuracy/robustness metrics.**

The metrics suite, implemented in `experiment/metrics.py`, comprises five categories:

**1. Attack Success Rate (ASR) and AUASR**

ASR measures the fraction of attack rounds in which the adversary achieves its objective (e.g., misclassifying a backdoor trigger sample). Unlike robust accuracy (which measures global model quality), ASR directly measures attack effectiveness:

```
ASR = (attacks reaching objective) / (total attack rounds)
```

We also define **Area Under ASR Curve (AUASR)**, integrating ASR over the attack intensity parameter λ (for grinding attack A2) or perturbation budget δ (for A1). AUASR gives a threshold-agnostic summary of defense robustness. Lower is better.

Honest accuracy is tracked in parallel to ensure ASR improvement does not come at the cost of model utility.

**2. Precision@Recall (P@R80, P@R90, P@R95)**

Standard Precision-Recall AUC is insufficient because the operating point matters. A fraud detection system must operate at a specific recall target (e.g., catch 90% of fraud). Precision@Recall measures the precision achieved when recall is fixed at R%.

We report P@R80, P@R90, and P@R95 corresponding to typical regulatory targets (FATF guidelines recommend ≥90% fraud detection rate for institutional controls).

**3. Savings Curve and Total Fraud Savings**

The business metric: given a cost-per-FP (c_FP = $5) and average fraud loss per FN (c_FN = $450), compute total savings relative to a no-model baseline:

```
Savings(model) = Total_Fraud_Loss − FP_Cost − FN_Cost − Model_Cost
              = N_fraud·avg_loss − FP·c_FP − FN·c_FN − C_model
```

The savings curve plots savings as a function of the decision threshold. The maximum savings point is the optimal operating threshold for deployment.

Savings is reported as a percentage of theoretical maximum savings (perfect detection).

**4. Cost-Sensitive Fβ (β ∈ {1, 2, 5, 10})**

Standard F1 (β=1) weights precision and recall equally. In fraud detection, recall is more important: missing a fraud is 90× worse than a false alarm. The cost-sensitive Fβ with β = c_FN / c_FP ≈ 90 would be extreme; we instead report:

- F1 (β=1): equal weighting
- F2 (β=2): recall twice as important
- F5 (β=5): recall five times as important
- F10 (β=10): recall ten times as important

The sequence F1 → F10 shows how the defense performs as the operating point shifts toward recall prioritization. A good defense maintains high Fβ across all β; a defense that achieves good F1 by being conservative degrades sharply at F5 and F10.

**5. Cumulative Detection Lag and Honest FPR**

**Detection lag:** The mean and median number of rounds between the start of an attack and the first round where the defense consistently (≥3 out of 5 rounds) flags the attacking clients. Reported per attack type (A1, A2, A3).

**Detection lag breakdown by attack phase:** For A2 (grinding, 4-phase), lag is reported separately for each phase (burn-in, subliminal, active, cooldown). This reveals whether the defense detects the attack during the active phase or only after.

**Honest FPR:** The fraction of non-attacking client-rounds in which an honest client is flagged. This is the primary cost metric: each false flag costs c_FP = $5 in review overhead.

**6. Fairness Metrics (cross-reference ADR-NNN)**

Separately implemented in `experiment/fairness.py`, we measure per-subgroup honest FPR across four client profiles:

- Majority banks (large, diverse transaction portfolios)
- Minority-serving banks (focused on underrepresented communities)
- Small banks (limited transaction volume)
- New entrants (limited history)

The fairness gap is the maximum absolute difference in honest FPR between any two profiles. We require fairness gap ≤ 0.01 (1 percentage point) for deployment acceptance.

**Why NOT generic metrics alone:**

| Metric | What it measures | Fraud domain limitation |
|---|---|---|
| Accuracy | Overall correctness | Misleading: 99.9% accuracy if fraud is 0.1% rate |
| AUC-ROC | Rank ordering | Doesn't capture cost ratio |
| Robust accuracy | Accuracy under attack | Doesn't say if attack succeeded |
| Model utility | Model quality | Doesn't capture operational constraints |

**Consequences:**

*Positive:*

- **Directly measures what matters:** The savings curve tells the consortium how much money the defense saves. ASR tells them how well it resists attacks. These are boardroom-ready metrics, not just research numbers.
- **Attack-specific insights:** Detection lag per attack phase for A2 reveals whether the defense catches attacks early (during subliminal phase) or late (only during active phase). The ablation study shows that L3 (temporal) reduces detection lag for A2 by 40 rounds compared to L1+L2 only.
- **Fairness accountability:** The fairness gap requirement prevents the defense from achieving good aggregate metrics by sacrificing minority-serving banks — a real concern in financial ML.
- **Regulatory alignment:** P@R90, detection lag, and explainability trace directly to FATF guidelines and SR 11-7 model risk management requirements.

*Negative:*

- **Metrics proliferation:** 15+ metrics makes it hard to compare defenses with a single number. The paper uses a **composite score**: Savings × (1 − ASR) × (1 − Fairness_Gap), normalized to [0, 1]. At the reviewer's request, individual metrics are also reported in the appendix.
- **Threshold dependence:** Many metrics (P@R, savings, Fβ) depend on the decision threshold. We fix the threshold at the point maximizing the savings curve on a validation set for all baseline comparisons, ensuring fair comparison.
- **Computation overhead:** Computing the full metrics suite requires running the defense across multiple attack intensities and checking detection lag per phase. Total experiment time is ~2× longer than with accuracy-only evaluation. Parallelized across 4 GPUs, this is acceptable (≈6 hours per full experiment run).

*Implementation:*

All metrics are computed by `compute_metrics()` in `experiment/metrics.py`. The function accepts `y_true`, `y_pred`, `y_scores`, and optional `fraud_amounts` arrays. The savings curve is computed via `compute_savings_curve()` which sweeps 100 threshold values and reports the maximum savings point.

The `FairnessEvaluator` class in `experiment/fairness.py` computes per-subgroup metrics and the fairness gap. Results are reported in both the paper's main table (composite score, ASR, P@R90, savings) and appendix (all 15+ metrics, per-attack breakdowns).
