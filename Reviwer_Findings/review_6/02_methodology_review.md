# Peer Review Report

## Manuscript Information
- **Title**: Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework
- **Manuscript ID**: N/A (design-stage specification)
- **Review Date**: 2026-07-11
- **Review Round**: Round 1

---

## Reviewer Information

### Reviewer Role *
**Peer Reviewer 1 (Methodology)**

### Reviewer Identity *
Statistical learning theory researcher specializing in high-dimensional inference, robust statistics, and spectral methods for anomaly detection. Research interests include perturbation bounds for PCA-based detectors, concentration inequalities for FL gradient distributions, and the statistical foundations of Byzantine-robust aggregation.

### Review Focus *
Evaluation of formal analysis rigor (Theorem 1, Stewart's perturbation theorem application, Davis-Kahan sinΘ derivation, and the relationship between theoretical bounds and projected numerical values); experimental design validity (baseline selection, ablation architecture, synthetic data adequacy); and statistical sufficiency of the planned evaluation protocol (trial counts, power, metric appropriateness). Particular attention is paid to the gap between what the theory actually bounds (FPR under stationarity) and what the projected Table III claims (ASR across six attack models).

---

## Overall Assessment *

### Recommendation *
- [ ] **Accept** — Can be published directly, only minor formatting changes needed
- [ ] **Minor Revision** — Minor revisions needed, no re-review after revision
- [x] **Major Revision** — Substantial revisions needed, re-review required after revision
- [ ] **Reject** — Not suitable for publication in this journal

### Confidence Score *
**4** — Mostly within my area of expertise, high confidence

### Summary Assessment *
This paper identifies a genuine blind spot in Byzantine-robust FL—statelessness against temporally-adaptive adversaries—and proposes an elaborate three-layer gated cascade defense for cross-silo fraud detection. The core observation (that per-round defenses fail against alternating attack/benign schedules) is well-motivated and practically relevant. However, the paper is submitted as a "design-stage specification" with zero experimental results, and the formal analysis contains several critical gaps that undermine the projected quantitative claims. The claimed ~1.6% honest FPR bound depends on numeric constants (FPR₁ ≤ 0.003, FPR₂ ≤ 0.012, FPR₃ ≤ 0.001) that appear without derivation, and the transition from Stewart's perturbation theorem to Eq. (69) lacks an explicit chain of inequalities. The Davis-Kahan sinΘ bound is correctly cited, but its connection to the drift-affected FPR (Corollary 1.1) is a heuristic tail-probability statement, not a rigorous bound. Most concerningly, the projected ASR upper bounds in Table III are labeled as "theoretically projected from formal analysis" (line 671), yet the formal analysis explicitly bounds only FPR, not ASR (lines 739–741 state "Formal ASR bounds require empirical measurement"). This creates a fundamental mismatch between what the theory supports and what is claimed. The experimental design (14 baselines, 15 ablations) is comprehensive in scope, but 10 independent trials with three independently varying sources of randomness is underpowered for the intended inference; the synthetic Gaussian experiment (d=50, N=10, 20 trials) is reasonable as a sensitivity check but too low-dimensional to validate spectral detection claims. Major revisions are required to either (a) provide full derivations for all claimed numeric bounds, (b) clearly delimit what the theory actually proves versus what is conjectured, and (c) either commit to running the planned experiments before publication or restructure the paper as a pure design proposal without quantitative projections.

---

## Strengths *

### S1: Identification of the Statelessness Blind Spot
The paper convincingly argues (Section II) that existing Byzantine-robust aggregators—Krum, Median, Trimmed Mean, Bulyan, FLTrust, FoolsGold, FLDetector—are all stateless and thus vulnerable to temporally-corrupted update sequences. The formalization of the grinding attack (Section IV-A2) with a 4-phase schedule (burn-in, subliminal, active, cooldown) is concrete and domain-relevant. This is a genuine gap in the literature that the paper correctly identifies.

### S2: Comprehensive Attack Taxonomy (A1–A6)
The six attack models span a well-reasoned adversarial capability spectrum, from naive model replacement (A1) through to the cascade-aware adaptive adversary (A6). The explicit definition of an "operational envelope" (Section IV-F) — delineating what the defense can and cannot detect — is an intellectually honest framing that many robustness papers avoid. The information-theoretic limits discussion (Section IV-G) using KL divergence to bound detectable perturbations is appropriate framing.

### S3: Detailed Ablation Architecture (15 Configurations)
The ablation design (Table VI, C1–C15) is thorough, systematically isolating each layer's individual contribution (C2–C4), pairwise combinations (C5–C7), the role of adaptive thresholds (C9 vs. C8), and several sensitivity dimensions (C11–C15). The hyperparameter sensitivity grid (τ_norm, τ_cos, τ_Δ, W_h, W) covers the main knobs. The planned 2D heatmap (C12: W × τ_Δ) is particularly valuable for understanding the reputation window trade-off.

### S4: Regulatory Compliance Mapping
The detailed treatment of GDPR (Art. 4(1), 22, 25, 28, 32), SR 11-7, ECOA/FCRA, and AML/CFT obligations (Sections VII–VIII) goes well beyond what is typical for an FL robustness paper. The dual-layer TEE attestation design, the DP-before-detection pipeline restructuring, and the surrogate SHAP explainability protocol demonstrate awareness that fraud detection operates under legal constraints that shape architectural choices.

---

## Weaknesses *

### W1: Critical Disconnect Between Formal Bounds and Projected Numerical Values
**Problem**: The projected ASR upper bounds in Table III (e.g., Full Defense ≤ 0.10 for A1, ≤ 0.35 for A2) are labeled as "theoretically projected from formal analysis" (line 671). However, the formal analysis in Section VI explicitly bounds only the honest FPR, not the ASR. Lines 739–741 state: "Formal ASR bounds require empirical measurement of per-layer true positive rates (TPR_k)… Quantitative ASR bounds are deferred to the expanded version with cloud-based experiments." The ASR column for each attack in Table III is therefore not derived from Theorem 1, Corollary 1.1, or any other mathematical result in Section VI. The projected values are architectural conjectures presented alongside formal analysis, creating an appearance of theoretical support where none exists. Furthermore, the full defense column in Table III shows ≤ 0.50 for A4'' (Aggregator Compromise), yet Section IV-D explicitly states the TEE limits this attack vector and the value "reflects service-disruption ceiling, not model poisoning" — further evidence the projections are not theory-derived.

**Why it matters**: If the paper presents itself as a design-stage specification with projected values "informed by theory" (Table III header), readers and reviewers must be able to trace each projection back to a specific theoretical result. Currently, no such trace exists for ASR. The only formally bounded quantity is FPR, which is a secondary metric. This disconnect undermines the paper's credibility: either the theory supports the ASR claims (in which case the derivation must be shown) or it does not (in which case the projections must be clearly labeled as conjectures, not "projected upper bounds informed by theory").

**Suggestion**: Two options, presented in order of preference:
1. **Restructure the paper as a pure design proposal**: Remove all projected numerical values (Table III, Table VI expected ASR columns) and replace them with qualitative expectations ("L3 is expected to contribute the largest marginal improvement against A2"). Add a sentence: "Quantitative performance characterization requires experimental validation, which is in progress." This would make the paper exactly what it claims to be: a design-stage specification.
2. **Provide a rigorous derivation chain**: For each ASR projection, show how it follows from the formal analysis — e.g., "Under attack A1, the norm bound δ ≤ 0.15 implies L1 catches with probability ≥ p₁(δ); given L1 FPR ≤ 0.003 and assuming independence, ASR ≤ (1 − p₁(δ)) × (1 − TPR_remaining_layers)." This requires deriving TPR bounds from the theory, which the paper currently does not attempt.

**Severity**: Critical

### W2: Undocumented Constants in the FPR Bound Derivation
**Problem**: The cascade FPR bound (Section VI-A) claims FPR₁ ≤ 0.003, FPR₂ ≤ 0.012, and FPR₃ ≤ 0.001, producing the headline 1.6% bound. However, no derivation is provided for these three specific numbers. Eq. (69) gives 𝕻[e_i > τ₂ | honest] ≤ 2·exp(−(τ₂ − δC)²/(2σ²)) with τ₂ = 0.4, δ ≤ 0.15. To arrive at 0.012, the values C and σ must be specified—but they are not. Is C a constant from Stewart's theorem? If so, which constant (the spectral norm of the perturbation matrix? the Davis-Kahan multiplicative constant?). Is σ the standard deviation of reconstruction errors under honest behavior? What is its assumed or estimated value? Similarly, FPR₁ ≤ 0.003: the L1 thresholds (τ_norm = 1.5σ_max, τ_cos = 0.5) are given, but under what distributional assumptions on honest gradient norms does P(‖g_i‖₂ > 1.5σ_max) ≤ 0.003? If Gaussian, the tail probability at 1.5σ for a one-sided test is ~0.067, not 0.003. If Chebyshev, 1/(1.5²) ≈ 0.44. The claimed 0.003 requires an assumption (e.g., sub-Gaussian with known variance factor) that is not stated.

**Why it matters**: The 1.6% cascade FPR is the paper's central quantitative claim—it appears in the abstract, the conclusion, and the ethical justification (Section VIII-G). If the per-layer FPR numbers are assumed rather than derived, the entire bound collapses to a tautology: "If each layer has FPR ≤ x, then the cascade has FPR ≤ f(x)." The interesting part—proving that each layer actually achieves its claimed FPR under stated assumptions—is missing.

**Suggestion**: Provide a complete derivation for each per-layer FPR bound:
- For L1: State the distributional assumption on honest gradient norms (e.g., "honest gradient norms ‖g_i‖₂ are σ-sub-Gaussian"). Derive P(‖g_i‖₂ > τ_norm) ≤ exp(−τ_norm²/(2σ²)) via Hoeffding-type inequality. Plug in τ_norm = 1.5σ_max where σ_max = max_i σ_i.
- For L2: Provide the full Stewart's theorem bound: state the perturbation model, identify the constant C (likely ‖Σ₀⁻¹‖₂ · ‖Δ‖₂ or similar), specify σ² as the variance of the reconstruction error under the null, and show the computation step-by-step.
- For L3: Derive the reputation score bound under the assumption of i.i.d. anomaly scores with sub-Gaussian tails.

**Severity**: Critical

### W3: The Drift-Affected FPR Bound (Corollary 1.1) is a Heuristic, Not a Bound
**Problem**: Corollary 1.1 states FPR₂(ε_drift) ≤ 𝕻(e_i > τ₂ − ε_drift/gap | honest). This is not a bound—it is a restatement of the detection threshold shifting problem. The Davis-Kahan sinΘ theorem correctly bounds the subspace perturbation: ‖sinΘ(U, V)‖ ≤ ‖Σ₁ − Σ₂‖ / gap. From this, one can bound the change in reconstruction error for a fixed vector x: |‖x − UUᵀx‖ − ‖x − VVᵀx‖| ≤ ‖UUᵀ − VVᵀ‖ ≤ ‖sinΘ‖. However, the shift in FPR depends on the quantile function of the honest reconstruction error distribution, which is unknown and distribution-dependent. Replacing the detection threshold τ₂ with τ₂ − ε_drift/gap and then writing a tail probability is a heuristic approximation—it assumes the distribution of reconstruction errors under the drifted covariance is identical to the stationary distribution, merely shifted. This is unsubstantiated: a perturbation to the principal subspace also changes the reconstruction error variance, not just the mean.

**Why it matters**: The paper states the 1.6% FPR bound as a formal guarantee but acknowledges that concept drift degrades it. The drift degradation analysis (lines 733–738 and 798–805) gives the impression of a rigorous characterization, but the claimed threshold shift ε_drift/gap is a first-order approximation. The resulting "approximate rule: if ε_drift/gap ≤ 0.05, FPR increase < 1%" has no theoretical justification—it assumes a specific quantile function shape. This is not a bound; it is an engineering heuristic that would require empirical validation.

**Suggestion**: Either:
- State explicitly that the drift analysis is heuristic: "Under the first-order approximation that the reconstruction error distribution shifts by at most ε_drift/gap, we estimate FPR degradation by..."
- Or derive a rigorous bound using a uniform deviation inequality: P(e_i^{(drift)} > τ₂) ≤ P(e_i^{(stat)} > τ₂ − ε_drift/gap) + δ, where δ accounts for the distributional change and is bounded via, e.g., a transportation inequality or Wasserstein stability bound.

**Severity**: Major

### W4: Insufficient Statistical Power for the Planned Trial Protocol
**Problem**: The trial protocol (Section V-F) specifies 10 independent trials (seeds 0–9) with three sources of randomness varied independently: (i) 3 non-IID Dirichlet α values × 5 seeds each = 15 partition configurations, (ii) client sampling order per round, (iii) 4 attack starting rounds. With 5 attacks (A1–A5, plus 2 variants A4', A4''), 14 baselines, and 15 ablation configurations, the full experiment comprises ~5 × (14 + 15) × 10 = ~1,450 experimental conditions, each run for 200 rounds. With 10 trials, each condition receives exactly 10 replications. For binary outcome metrics (ASR: did the attack succeed or not?), 10 trials yield a standard error of at most √(0.5 × 0.5 / 10) ≈ 0.158 — far too wide to meaningfully distinguish projected ASR differences of 0.05–0.10 (e.g., C8 vs. C9: ≤ 0.35 vs. ≤ 0.40). For the FPR metric, where the claimed bound is 0.016, 10 trials provide a 95% CI width of ~±0.025 (using Wilson interval), which cannot reliably detect FPR differences below ~5 percentage points. Moreover, with three independent sources of randomness, 10 trials cannot disentangle variance components — e.g., is the ASR variation driven by the non-IID seed or the attack starting round? A proper variance decomposition requires at least a partially crossed design with multiple replicates per factor level.

**Why it matters**: The paper's projected findings include distinctions on the order of 5–10 percentage points (e.g., C8 vs. C9: "adaptive threshold is projected to add ~7 pp"). An experiment with 10 trials cannot statistically support such fine-grained comparisons. Furthermore, the FPR bound (1.6%) is presented as a key design guarantee, but with N=10 trials, a 95% confidence interval for the true FPR could easily span 0–5%, making the bound unfalsifiable in practice.

**Suggestion**: 
- Increase trials to at least 30–50 per condition for primary comparisons (full defense vs. baselines, C8 vs. C9). If computational cost is prohibitive (50–100 GPU-hours), prioritize: run 50 trials for the key causal contrasts (C8 vs. baselines, C8 vs. C5/C6/C9) and 10–15 trials for the full ablation sweep.
- Report effect sizes with confidence intervals and explicitly state the minimum detectable effect given the trial count.
- Use a nested ANOVA or mixed-effects model to partition variance across the three randomization sources, demonstrating that the trial count is adequate for the intended inference.

**Severity**: Major

### W5: Synthetic Gaussian Experiment (d=50) is Insufficient for Spectral Detection Validation
**Problem**: The synthetic Gaussian experiment (lines 599–600) uses d=50 dimensions, N=10 clients, and 20 trials to "establish the operating envelope." However, the spectral detection layer (L2) relies on PCA reconstruction error in a d-dimensional gradient space. Real gradients for fraud detection models (3-layer MLP with 256→128→64→1 units) have approximately 256×128 + 128×64 + 64×1 = 41,024 parameters. A d=50 Gaussian provides an extremely poor proxy for this setting for several reasons: (i) the eigenvalue spectrum of a 50-dimensional random matrix concentrates much more tightly than that of a 40,000-dimensional one under realistic covariance structures (Marchenko-Pastur vs. spiked covariance models); (ii) the Davis-Kahan sinΘ bound's gap λ_k − λ_{k+1} is fundamentally different in low vs. high dimensions — in high dimensions, even the top eigenvalues of a sample covariance are biased upward; (iii) the detection of m=3 colluding clients via spectral separation depends on the signal-to-noise ratio in the residual subspace, which scales with d. The synthetic d=50 experiment can establish basic feasibility but cannot validate the spectral detection bounds claimed in Section VI.

**Why it matters**: The paper's formal analysis relies on PCA reconstruction error bounds (Stewart, Davis-Kahan) that are dimension-dependent. Validating these bounds at d=50 provides no evidence that they hold at the operational d≈41,000. The L2 layer's detection guarantees for m≥3 colluding attackers are conditional on the eigenvalue gap being sufficiently large — a condition that must be verified empirically at the correct dimensionality.

**Suggestion**: 
- Add a higher-dimensional synthetic experiment (d=500 or d=1,000) with a spiked covariance structure that better approximates real gradient distributions. Use the Marchenko-Pastur spiked model to control the eigenvalue gap explicitly.
- Alternatively, use the IEEE-CIS dataset (434 features, which after the MLP embedding becomes 41,024-dimensional) to run a small-scale validation of the spectral detection mechanism even before the full experiment.
- Acknowledge the d=50 limitation explicitly in the experimental design section and characterize how the gap and detection SNR scale with dimensionality.

**Severity**: Major

### W6: Threshold Adaptation Dynamics Analysis is Incomplete
**Problem**: The convergence analysis for the adaptive thresholds (Section VI-B) provides a Lipschitz condition L_h ≈ 0.05 < 1 and a tracking error bound O(ησ_ρ/(1−L_h)), but makes three critical concessions that together amount to stating the problem rather than solving it. First, the Lipschitz constant depends on ∂ρ/∂θ, which the paper calls "an order-of-magnitude estimate" requiring "measurement from deployment data" (line 753). Second, the tracking error bound is O(·) with an "attractor geometry" constant "not derived here" (line 762). Third, the two-timescale analysis (line 764) is described as establishing "the framework" with "the constant derivation left as future work." The transient coupling analysis (Eq. (72)) introduces a free parameter β that is set to β ≤ 10⁻⁴ to guarantee L_h(t) < 1, but the bound depends on 0.3 · 2.0 / 0.015 · β = 40β, so β ≤ 10⁻⁴ gives 0.004 — yet the base L_h,0 = 0.05, so L_h(t) ≤ 0.054 < 1 regardless of β. The β parameter appears tunable to make the inequality hold trivially.

**Why it matters**: The adaptive threshold escalation policy (Algorithm 1, Eqs. (5)–(8)) is a core architectural contribution. If its convergence properties cannot be established analytically and rely on unspecified measurement data and free parameters, the paper should state this honestly rather than presenting an incomplete analysis that gives the impression of rigor.

**Suggestion**: Either provide a complete Lyapunov-style convergence proof for the piecewise-linear threshold dynamics (possibly under simplifying assumptions, e.g., ρ(θ) is monotone in θ), or state clearly: "The following is a heuristic control-systems analysis framework; formal convergence guarantees require empirical characterization of the attack-rate response function and are deferred to experimental validation."

**Severity**: Minor (as a design-stage paper, incomplete convergence analysis is acceptable if honestly labeled — but the current framing oversells the result)

---

## Detailed Comments *

### Title & Abstract
The abstract accurately summarizes the contribution and correctly flags the design-stage status. However, the claim of "establishing a ~1.6% honest FPR bound" (line 31) in the abstract is stronger than what the analysis supports given the undocumented constants (W2). Suggest adding a qualifier: "under stated distributional assumptions on gradient norms and residual covariance."

### Introduction
- The statelessness blind spot is well-motivated. The formal intuition (lines 57 and 166) contrasting 𝔼[f_t | θ, g_adv] = h(g_adv) for stateless vs. S_t = Σ w_i f_i for stateful is crisp and effective.
- Section I-C (Contributions) lists three contributions. Contribution 2 bundles the cascade design, FPR bounds, drift analysis, reputation floor, and A6 envelope into a single item — this is four contributions, not one. Consider disaggregating.
- Line 72: "Experimental validation is in progress on cloud infrastructure" — this should appear earlier/more prominently for transparency.

### Threat Model (Section III)
- Clear and appropriately scoped. The distinction between targeted evasion (accuracy-preserving) and untargeted Byzantine faults is well-drawn.
- The Kerckhoffs's principle assumptions (Section III-C) are reasonable. The trust boundary discussion (line 160) citing Visa B2B Connect and Fnality provides concrete grounding.
- Line 170: Out-of-scope items are listed appropriately. However, "reputation identity cycling" being described as "operational" rather than an architectural concern undersells the severity: if an adversary can cycle Sybil identities at cost γ_syb (as assumed in Section III-C), the probation period P=10 rounds and initial reputation R=0.50 may be insufficient deterrent. Suggest adding a quantitative analysis of the cost to cycle vs. expected benefit.

### Proposed Framework (Section IV)
- The cascade architecture is well-structured and the design principle of "division of labor" is sound.
- The sliding-window PCA with recomputation interval P is a reasonable approach to concept drift. However, the claim that the sliding window "discards stale gradient statistics" (line 1036) requires that the window length P captures the drift timescale — if concept drift occurs faster than P rounds, the stale statistics remain. This circular dependency (P ≤ gap/ε_drift) requires knowing ε_drift a priori.
- The per-client baseline measurement protocol (Section IV-G) is thorough and the dual-threshold architecture (Table IV) is an important design detail. The disclosures (lines 382–386) that the σ_{R,i} ≈ 0.015 measurement came from "a single toy logistic regression simulation (d=100, N=10, Dirichlet α=0.5)" are commendably transparent but also reveal how thin the empirical basis is for the claimed numbers.
- Lines 264–265: The probation mechanism (P=10 rounds at 50% weight) and cold-start bootstrap (Section IV-E last paragraph) are sensible but the 10-round probation window seems short relative to the W_h=200 warm-up. Justification would strengthen this.

### Attack Models (Section V)
- The 4-phase grinding attack schedule (A2) is well-specified. However, the fixed schedule assumes the attacker does not adapt during the attack — as A6 acknowledges, a real adaptive adversary would adjust phases based on observed detection outcomes. The paper correctly addresses this via A6.
- Table V attack taxonomy: A4'' (Aggregator Compromise) has ASR(UB) ≤ 0.50 "reflects service-disruption ceiling, not model poisoning" — this should be in a separate category from the model-poisoning attacks since the mechanism is fundamentally different.
- A6 operational envelope (Section V-F): This is the paper's most intellectually honest contribution. The framing that the cascade is "an early-warning alarm for out-of-distribution updates, not a general adversary-proof aggregator" (line 518) correctly sets expectations. The four envelope conditions (L1 magnitude, L1 direction, L2 spectral, L3 reputation) are clearly stated.

### Experimental Design (Section V continued)
- **Baselines (14)**: The set covers the main families of robust aggregators. However:
  - DP-FedAvg at ε ∈ {1, 4, 8} (B9, B11, B12) is a privacy mechanism, not a poisoning defense. Including it as a baseline against A1–A5 is appropriate for completeness, but it should be noted that DP provides no formal robustness guarantees against targeted gradient poisoning. The projected ASRs should reflect this.
  - B13 (Clipped Median) and B14 (Multi-Krum + Trimmed Mean) are "engineering variants" without citations (line 559). For reproducibility, either provide a clear algorithmic specification or cite a source.
  - The computational complexity table (Table IV) is useful. The claim that the full defense takes ≤ 0.8s with PCA O(Nd²) for N=10, d=100K gives O(10 × 10¹⁰) = O(10¹¹) operations — this is 0.8s only with aggressive optimization (efficient eigendecomposition, possibly randomized PCA). Clarify the PCA implementation (full SVD? randomized? power iteration?) and whether this estimate includes the warm-start overhead.
- **Benign-drift control experiment** (Section V-C): The drift injection methodology (Phase 2: Σ_t = Σ_0 + δ_t · E, ‖E‖₂ = 1) is reasonable. However, the measurement protocol (lines 593–598) mentions three quantities but the connection to the theoretical gap ε_drift/gap is not explicitly operationalized. How is ε_drift measured from data? How is gap estimated?
- **Ablation analysis** (Section V-D): 15 configurations provide good coverage. The key control pair C9 (Cascade Fixed) vs. C8 (Full Defense) correctly isolates the adaptive threshold contribution. However, C10 (Cascade Oracle) involves "grid-searched τ" — this requires defining a search space and an optimization criterion. The projected ≤ 0.35 matching C8 is suspicious: if oracle-tuned thresholds match the adaptive thresholds, the adaptive mechanism adds no value (contradicting the ~7 pp claim). Clarify the oracle specification.
- **Temporal cross-validation split** (line 616–617): The expanding-window design is appropriate for the temporally-aware claim. Good.
- **Evaluation metrics** (Section V-E): MCC is appropriate for imbalanced fraud settings. FDR is a practical metric. The list is complete. However, note that ASR is the primary metric, yet the paper's only formal bound is on FPR — this asymmetry should be explicitly flagged.

### Formal Analysis (Section VI)
- **Theorem 1 (Cascade FPR)** : The cascade FPR formula (Eq. (10)–(11)) is a standard serial-system false-positive composition. The contribution is in bounding each term. As discussed in W2, the per-layer bounds lack derivations. The Stewart's theorem reference (line 714) is appropriate in principle but the connection is incomplete: Stewart's theorem (1973) bounds the perturbation of invariant subspaces under additive perturbations, but Eq. (69) uses an exponential tail bound (Chernoff-style) that is not from Stewart. The derivation chain should be: (a) model honest residuals as sub-Gaussian, (b) reconstruction error is a quadratic form, (c) apply a concentration inequality (e.g., Laurent-Massart for χ²), (d) bound the perturbation of the projection matrix using Stewart's sinΘ theorem, (e) combine via union bound. Currently the paper jumps from Stewart to the exponential bound without intermediate steps.
- **Corollary 1.1 (Drift-affected FPR)** : As discussed in W3, the form FPR₂(ε_drift) ≤ 𝕻(e_i > τ₂ − ε_drift/gap | honest) is a heuristic. The Davis-Kahan sinΘ bound (Eq. (14)) is correctly stated, and the reconstruction error perturbation (Eq. (15)) is correct for the norm. The leap to the FPR bound is where rigor breaks down. The "approximate rule" (lines 737, 805) giving specific FPR percentages (1%, 10–50%) for specific ε_drift/gap ratios (0.05, 0.167) is presented without derivation of the honest reconstruction error quantile function — it appears to assume a particular distribution (perhaps Gaussian with known quantiles), which is not stated.
- **Reputation Floor (Theorem 1, p. 809)**: This is a definitional consequence, not a theorem. If R_SS = 0.85 is a hard floor applied after window computation (line 814), then by construction R ≥ 0.85 for all clients. The theorem's condition ("average anomaly score ≥ 0.95 over any W-round window") is not actually needed — the floor is applied unconditionally. Similarly, Corollary 1 (MCFF ≤ t₀ = 10) is just a restatement of the hard-reset-on-violation mechanism (line 259: "If a client is flagged for F_max = 3 consecutive rounds..."). These are design specifications, not analytical results, and labeling them as theorems/corollaries inflates the paper's perceived formality.
- **Convergence analysis** (Section VI-B): Discussed in W6. The two-timescale reference to Borkar (1997) is appropriate for the framework, but without specific constants it remains a sketch.

### Discussion and Limitations (Section VIII)
- The counter-arguments table (Table X, "Red-Team Assessment") is a useful self-critique exercise. However, the response "S5: 1.6% honest FPR bound" for the FPR accumulation concern is tautological — the bound is the claim being challenged. A stronger response would acknowledge that the bound's dependence on δ ≤ 0.15 means FPR could exceed 1.6% if perturbations exceed this bound.
- Limitations (Section VIII-E) are honestly acknowledged. The disclosure that "W=50 is a design heuristic without formal optimality characterization" (line 1094) is appropriate. The EMA-to-sliding-window change is noted but not justified in terms of the EMA half-life sensitivity — providing the reasoning would strengthen the design narrative.

### References
- The citation coverage is appropriate and current. The use of standard FL and Byzantine robustness references is adequate.

---

## Questions for Authors *

1. **Derivation of per-layer FPR constants**: What distributional assumptions on honest gradient statistics (norms, residuals, reputation scores) lead to the specific values FPR₁ ≤ 0.003, FPR₂ ≤ 0.012, and FPR₃ ≤ 0.001? Please provide the full chain of inequalities, specifying the concentration inequality used, the sub-Gaussian/sub-exponential parameter values, and how Stewart's theorem's constants (C in Eq. (69)) are determined. Without this, the 1.6% cascade FPR bound is an assumed number, not a derived one.

2. **ASR projections vs. formal analysis**: Table III labels ASR upper bounds as "theoretically projected from formal analysis (§VI)." Yet §VI explicitly bounds only FPR, not ASR. How are the ASR values (e.g., Full Defense ≤ 0.35 for A2) derived from the formal analysis? If they cannot be traced to specific theoretical results, can the paper restructure to present these as architectural conjectures rather than theory-informed projections?

3. **Statistical power and trial count**: With N=10 trials and three independently varied sources of randomness, what is the minimum detectable effect size for the primary contrast (C8 vs. baselines, or C8 vs. C9) at α = 0.05 and 80% power? If the minimum detectable effect exceeds the projected 5–10 pp differences, how will the paper avoid inconclusive results? Is there a plan to increase trial count for key comparisons or to use variance-reduction techniques (e.g., common random numbers, paired design)?

4. **Drift-affected FPR analysis**: The "approximate rule" (ε_drift/gap ≤ 0.05 → FPR increase < 1%) in Corollary 1.1 appears to assume a specific quantile function for honest reconstruction errors. What is this assumed distribution, and how sensitive is the rule to misspecification? If the reconstruction errors are heavier-tailed than assumed (e.g., Cauchy-like tails from non-IID gradient heterogeneity), could the FPR degradation be substantially worse?

---

## Minor Issues

### Language / Grammar
- Line 249, Eq. (12): "where a_i^{(s)} ∈ [0,1] is the per-round anomaly score" — missing closing line break after the equation, the text runs into the equation display.
- Line 408: The Shapley equation number is \label{eq:shapley} but the text at line 409 reads "where K=100 random permutations..." — the placement of this text between the table (dual-threshold) and the equation reference is confusing. The paragraph beginning "where K=100..." seems to be a continuation of the Shapley discussion from Section IV-F, but it appears after Section IV-G on baseline measurement. Consider restructuring so that the Shapley computation and the dual-threshold protocol are in separate subsections.
- Line 793: "Note the absence of k in the numerator" — this sentence refers to Eq. (16) but the notation is not fully explained. Clarify that UUᵀ − VVᵀ has spectral norm bounded by ‖sinΘ‖, which does not explicitly involve k (k appears only in the gap denominator).

### Technical Corrections
- **Eq. (69)**: The expression (τ₂ − δC)²/(2σ²) — is σ² the variance of the reconstruction error? If so, state this explicitly. If C is a constant from Stewart's theorem, give its definition.
- **Eq. (4), line 306**: The relaxation update (Eq. (8)) uses θ_low^{(t+1)} = θ_low^{(t)} − η_relax (ρ₀ − ρ^{(t)}) · 1_{ρ^{(t)} < ρ₀}. Since (ρ₀ − ρ^{(t)}) > 0 when ρ^{(t)} < ρ₀, this subtracts a positive quantity, decreasing θ_low — which widens the rejection region. Is this the intended behavior? Normally during relaxation one would increase θ_low to reduce rejection sensitivity. Please verify the sign.
- **Line 764**: "Borkar, 1997; Borkar & Meyn, 2000" — these are standard references for two-timescale SA but should be in the bibliography, not inline.
- **Line 814**: "The R_SS floor applies after the window computation as a hard lower bound" — if the floor is applied as a clamp after the window average, then R_i ≥ 0.85 always, making the theorem's condition unnecessary. If the floor applies only to the reputation score before windowing, clarify the precedence.

### Figures and Tables
- Table III (Projected ASR UB): The row for FedAvg shows "≤ 0.99" for all attacks. Label this as "≤ 1.0" or explain why the bound is 0.99 rather than 1.0 (is 0.99 a reflection that the attack may fail with probability 0.01 even under undefended FedAvg?).
- Table VI (Ablation): C11–C15 show "See text" for expected ASR. For a design-stage paper, providing point estimates (even speculative) would make the table self-contained. If estimates are infeasible, consider replacing "See text" with qualitative labels ("Expected: moderate degradation," "Expected: minimal effect").
- Table IV (Baselines): B14 "Multi-Krum + Trimmed Mean" — is this a cascaded defense (Krum first, then Trimmed Mean on survivors)? Specify the combination order.

---

## Dimension Scores *

| Dimension | Score (0-100) | Descriptor | Notes |
|-----------|--------------|------------|-------|
| Originality (20%) | 75 | Strong | The statelessness blind spot is a genuine contribution, and the cascade-aware adaptive adversary (A6) operational envelope is a novel framing. However, individual components (spectral detection, temporal reputation, threshold adaptation) are well-studied in isolation — the originality is in the combination and domain application. |
| Methodological Rigor (25%) | 55 | Weak | The formal analysis is incomplete: per-layer FPR bounds are stated without derivation, the drift-affected FPR analysis is heuristic rather than rigorous, and the threshold convergence analysis relies on unspecified constants. The experimental design (trial count, synthetic dims) is underpowered for the intended claims. The gap between what the theory bounds (FPR) and what is claimed (ASR) is a critical rigor concern. |
| Evidence Sufficiency (25%) | 45 | Weak | As a design-stage specification with zero experimental results, the paper provides no empirical evidence for its claims. The projected numerical values are architectural conjectures. The single data point supporting σ_{R,i} ≈ 0.015 is from a toy simulation (d=100, N=10, one seed). The rubrics (25–40 sources, 70%+ peer-reviewed) are not satisfied in the evidence dimension because the paper lacks experimental validation entirely — this is inherent to the design-stage framing but must be reflected in scoring. |
| Argument Coherence (15%) | 70 | Adequate | The paper flows logically from problem identification → threat model → design → analysis → limitations. However, the mismatch between the formal analysis (which bounds FPR) and the projected results (which claim ASR) creates a coherence gap: the reader expects the analysis to support the projections, but the connection is absent. The narrative would be more coherent if contextualized as a pure design specification. |
| Writing Quality (15%) | 75 | Strong | Professional academic writing with precise terminology. The paper is well-structured and the cascade architecture is clearly described. Some equations lack annotation, and the placement of the Shapley continuation after the baseline protocol section is confusing. Minor grammatical issues noted above. |
| **Weighted Average** | **62.25** | **Major Revision** | |

**Calculation**: (75 × 0.20) + (55 × 0.25) + (45 × 0.25) + (70 × 0.15) + (75 × 0.15) = 15.0 + 13.75 + 11.25 + 10.5 + 11.25 = 61.75 (correcting: 15+13.75=28.75, +11.25=40, +10.5=50.5, +11.25=61.75). The weighted score of ~62 falls in the Major Revision band (50–64).

---

## Summary for Authors

Thank you for submitting this design-stage specification. The paper identifies a genuinely important vulnerability in FL fraud detection — the statelessness blind spot — and proposes a well-structured cascade defense with thoughtful consideration of regulatory and operational constraints. However, as a methodology reviewer, I have serious concerns about the rigor of the formal analysis and the disconnect between the theoretical bounds and the projected numerical claims. Specifically:

1. **The headline 1.6% FPR bound is stated without derivation.** The per-layer FPR values (0.003, 0.012, 0.001) appear as numeric claims without justification. Please provide the complete chain of inequalities from distributional assumptions to these values.

2. **The projected ASR upper bounds (Table III) are not supported by the formal analysis.** The analysis bounds only FPR, yet ASR claims are presented as "theoretically projected." Either derive ASR bounds from theory or clearly label these as architectural conjectures.

3. **The drift degradation analysis is heuristic, not a bound.** Corollary 1.1's threshold-shift approximation lacks distributional justification. Please either provide a rigorous bound or label as an engineering heuristic.

4. **The trial count (N=10) is underpowered** for the 5–10 pp differences the paper aims to detect. Please either increase trials or explicitly state the minimum detectable effect.

5. **The synthetic Gaussian experiment (d=50) is too low-dimensional** to validate spectral detection claims at the operational dimensionality (~41,000).

I recommend Major Revision. The core architectural contribution is sound and the problem is well-motivated. The paper needs either (a) full derivations for all claimed bounds and a clearer separation of proven results from conjectures, or (b) a restructured presentation as a pure design proposal without quantitative projections. I look forward to seeing the experimental results in a future version.
