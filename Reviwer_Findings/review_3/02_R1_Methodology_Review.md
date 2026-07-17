# Peer Review Report — Methodology Review

## Reviewer Information
- **Role**: Peer Reviewer 1 (Methodology)
- **Identity**: Expert in robust federated learning aggregation, Byzantine fault tolerance, and adversarial ML experimental design. Published on robust aggregation, spectral defenses, and Byzantine-resilient optimization. Familiar with the literature on Krum, Trimmed Mean, Bulyan, FLTrust, FoolsGold, FLDetector, FLAME, and spectral PCA defenses.
- **Review Focus**: Design-soundness and feasibility assessment of the proposed gated cascade defense. I evaluate whether the formal analysis supports the claimed robustness, whether the planned experiments can rigorously validate the design, and whether the expected results are justifiable from the theoretical framework provided.

---

## Overall Assessment

### Recommendation: Major Revision
The architectural synthesis is promising and the formal analysis represents a serious attempt at theoretical grounding, but critical validity gaps and overclaimed expected results prevent acceptance in the current design-stage form.

### Confidence Score: 4

### Summary Assessment (198 words)

This design-stage paper proposes a gated cascade defense for robust FL in credit card fraud, combining norm/cosine filtering, spectral PCA, and EMA reputation with adaptive threshold escalation. The architectural concept is novel and well-motivated, and the planned experimental scaffolding (10 baselines, 5 attacks, 10 ablations) is comprehensive in scope. The formal analysis correctly derives an FPR bound (~1.6%) under stationary covariance and establishes convergence of the reputation dynamics. However, the paper suffers from three critical deficiencies. First, the formal analysis does *not* bound the primary objective — the attack success rate or model utility under the paper's own sophisticated threat models (A2–A4) — rendering the expected results in Table V entirely speculative. Second, the Stewart perturbation bound assumes gradient covariance stationarity, a premise directly contradicted by the temporal nature of fraud (concept drift), creating a major external validity threat. Third, the planned experiments cannot isolate the effect of tight hyperparameter tuning from genuine architectural robustness, and the design offers no formal resistance against adaptive adversaries aware of the cascade structure. Major revision is required to align claims with evidence.

---

## Strengths

### S1: Novel and Well-Motivated Architecture
The 3-layer gated cascade (norm/cosine → spectral PCA → EMA reputation with adaptive threshold escalation) is an original synthesis of heterogeneous robust FL techniques. The layered design is well-justified against the paper's diverse threat model, and the gating mechanism represents a principled approach to managing the robustness-participation trade-off.

### S2: Rigorous Formal Backbone
The application of Stewart's perturbation theory to bound the FPR of the spectral layer is technically correct and provides meaningful theoretical confidence in the defense's reliability against benign false dismissals. The fixed-point analysis of the adaptive threshold dynamics (Lipschitz constant L_h = 0.05 < 1) is elegant and establishes that the reputation system will converge under stationary assumptions.

### S3: Comprehensive Experimental Scaffolding
The planned experiments (10 baselines spanning classical aggregation, Byzantine-robust rules, reputation systems, and differential privacy), 5 threat models, and 10 ablation configurations (including the critical fixed-threshold C9 and oracle-threshold C10 controls) represent an extremely thorough evaluation structure. The use of two real-world financial datasets with explicit non-IID partitioning is appropriate for the domain.

### S4: Domain-Relevant Task Selection
Choosing credit card fraud detection with heavy imbalance (0.172% fraud rate) directly stresses defenses in a practically relevant scenario, going beyond standard image-based benchmarks. The non-IID splits (Dirichlet + geographic) appropriately reflect deployment conditions.

---

## Weaknesses

### W1: Formal Analysis Does Not Bound the Core Objective (Severity: Critical)
The Stewart bound addresses the false positive rate of the filter in benign settings. The Lipschitz analysis proves the reputation thresholds converge. Neither provides a bound on the *attack success rate* or the *model utility* under the paper's own threat models (A2–A4). Without a formal connection between the filter's behavior and the optimization error of the global model, the expected ASR of 0.25 (Table V) is entirely speculative and unsupported by the theory provided. The design's feasibility against its primary threat models is unvalidated.

### W2: Stationarity Assumption Contradicts the Core Claim of Temporal Awareness (Severity: Critical)
The Stewart perturbation bound relies on the assumption that the benign gradient covariance matrix Σ is stationary across rounds. The paper's title and motivation heavily emphasize temporal awareness, yet credit card fraud is notorious for concept drift (shifting spending patterns, emergent fraud strategies). If Σ shifts, the spectral PCA layer's decision boundary degrades without formal characterization. The formal analysis does not address the defense's reliability under the very temporal dynamics the paper claims as its contribution. This is a direct threat to both construct and external validity.

### W3: Undefended Against Adaptive Omniscient Adversaries (Severity: Major)
The attack models (A1–A5) evaluate specific poisoning strategies, but the paper does not model an *adaptive adversary* aware of the full cascade structure, its thresholds, and the reputation floor. An adversary could craft updates that linger just below the detection boundaries or slowly inflate their EMA reputation over multiple rounds. The "oracle" ablation (C10) tunes thresholds optimally, but it cannot distinguish between the defense logic being fundamentally sound vs. the thresholds being perfectly tuned. The formal analysis is entirely silent on adaptive adversary resilience.

### W4: Reputation Floor Does Not Account for Legitimate Non-IID Clients (Severity: Major)
The Reputation Floor Theorem (R_SS = 0.85) implicitly assumes honest clients exhibit consistent gradient patterns. In extreme label skew (e.g., a client seeing only fraud in a given round, or a new merchant category emerging), an honest client's gradients will deviate from the majority, triggering the norm/cosine filter and decaying their EMA reputation. The paper does not analyze the probability of an honest client being permanently excluded by the cascade, nor does it bound the cost of false positives on the model's generalization.

### W5: Expected Results Overclaim Relative to Formal Analysis (Severity: Minor)
Table V presents projected results (Full Defense ASR = 0.25, FedAvg ASR = 0.92) with an implied degree of certainty not afforded by the theoretical framework. The formal bounds only cover FPR and reputation convergence; they do not chain to produce an ASR guarantee. The paper must explicitly frame Table V as hypotheses suggested by the theory, not as validated outcomes. For a design-stage paper at a venue like IEEE TIFS, this distinction is critical.

---

## Detailed Comments

### Methodology
The cascade approach is conceptually sound, but the sequencing of the filters lacks formal justification. Why is spectral PCA applied after norm/cosine filtering? The truncation induced by the first layer modifies the covariance structure observed by the PCA, potentially discarding honest high-loss clients before they can be vetted by the reputation system. The gating also introduces non-convexity into the training process; this is acknowledged but not formally addressed. A cost model or a formal property gained by the specific sequencing would strengthen the design argument.

### Experimental Design
The planned experiments are state-of-the-art in scope but have critical gaps:
1. **No sensitivity analysis over cascade hyperparameters.** The ablation study includes C9 (fixed) and C10 (oracle), but it does not include a systematic grid search over τ_l1, τ_l2, ρ, or the EMA window. If expected results degrade sharply under reasonable threshold variations, the *tuning* is doing the work rather than the *architecture*. This is an unaddressed internal validity threat.
2. **No streaming / temporal cross-validation split.** Given the paper's emphasis on temporal awareness, evaluating on a static random train/test split is a misalignment with the core claim. A time-series expanding window or iterated split is necessary to test robustness to concept drift.
3. **Missing temporally-aware model baseline.** The model is a 3-layer MLP. Is temporal information only in the defense (EMA), or is it also in the model features (lags, rolling statistics)? An ablation removing temporal features from the model is needed to evaluate the "temporally-aware" claim comprehensively.

### Formal Analysis
The formal analysis is the paper's strongest section but remains critically incomplete:
- **Lemma 1 (Stewart Bound):** Correctly derived but holds only under stationary Σ. A bound under bounded drift (∥Σ_t − Σ_{t-1}∥ ≤ ε) is necessary to bridge the gap between the theory and the application domain. Alternatively, the paper must explicitly acknowledge this assumption and restrict its claims.
- **Lemma 2 (Lipschitz Convergence):** Proves the gating threshold converges. This does *not* prove the global model converges to a low-loss solution under attack, which is the paper's core goal.
- **Theorem 3 (Reputation Floor):** Does not account for colluding adversaries (A3) who can simultaneously mimic the spectral signature and slowly inflate reputation. A coalition of adversaries controlling multiple clients could collectively raise the floor, or force honest clients below it. The analysis must bound the effect of collusion on the floor.

### Results Section
Table V presents expected results that are not derivable from the provided formal bounds. The paper must:
1. Explicitly state which cells in Table V are direct consequences of the formal analysis (e.g., FPR ≤ 1.6%).
2. Explicitly label remaining cells (ASR values) as speculative hypotheses to be tested.
3. Include error bars or expected variance in the projected numbers. The current table reads as a completed experimental result, which is misleading for a design-stage paper.

---

## Questions for Authors

1. **Stationarity vs. Temporal Drift:** The Stewart perturbation bound assumes stationary benign gradient covariance. Credit card fraud is characterized by concept drift. Can the authors provide a formal bound on the FPR or model degradation when ∥Σ_t − Σ_{t-1}∥ > 0? Without this, how can the "temporally-aware" claim be evaluated?

2. **Adaptive Adversary Resilience:** How does the cascade perform against an omniscient adversary aware of all three gates and the reputation floor? Could such an adversary craft updates that slowly ramp up their perturbation while staying within the detection bounds? What formal guarantee prevents this slow-ramp attack?

3. **Honest Client Exclusion:** In a highly non-IID fraud scenario, a legitimate client with a sudden change in behavior (new merchant, new region) may trigger the norm/cosine filter and see their reputation decay. Does the Reputation Floor of 0.85 hold for such clients? How does the cascade recover from a false dismissal of an honest client?

4. **Hyperparameter Sensitivity:** The ablation study has C9 (fixed thresholds) and C10 (oracle thresholds), but it does not include a sensitivity analysis across reasonable threshold values. How sensitive are the expected results to the exact choice of τ_l1, τ_l2, ρ, and the EMA window? Can the authors provide a formal robustness guarantee over threshold choice, or a planned experiment to isolate this effect?

---

## Dimension Scores

| Dimension | Weight | Score | Weighted Score | Notes |
|---|---|---|---|---|
| **Originality** | 20% | 75 | 15.00 | Layered cascade architecture is a novel synthesis; grinding attack is well-conceptualized. |
| **Methodological Rigor** | 25% | 55 | 13.75 | Formal analysis is sound but incomplete; stationarity assumption contradicts core claims. |
| **Evidence Sufficiency** | 25% | 25 | 6.25 | No empirical results; Table V speculative; no hyperparameter sensitivity analysis planned. |
| **Argument Coherence** | 15% | 80 | 12.00 | Clear narrative flow from motivation through design to evaluation plan. |
| **Writing Quality** | 15% | 85 | 12.75 | Well-structured; technical concepts clearly presented. |
| **Weighted Average** | **100%** | | **59.75** | |
