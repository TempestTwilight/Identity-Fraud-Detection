## Methodology Review Report

**Paper:** Design-stage Specification for Robust Federated Learning via Two-Timescale SA
**Reviewer Role:** Peer Reviewer 1 — Methodology (Robust FL / Optimization)
**Review Type:** Design Soundness and Feasibility Evaluation

---

### 1. Summary

This design-stage proposal outlines a Byzantine-resilient federated learning framework that leverages two-timescale Stochastic Approximation (SA) for dynamic thresholding against temporal fraud patterns. The formal backbone comprises a Stewart-based FPR bound (≤1.6%), a Davis-Kahan eigenvector correction, a drift-affected FPR expression, and a convergence neighborhood bound. The review finds the theoretical framing ambitious and domain-relevant, but identifies critical issues in the assumption stack regarding stationarity of Σ, the validity of the SA contraction argument under state-dependent noise, and a significant internal validity gap where the experimental plan cannot distinguish attacks from benign distribution shifts.

---

### 2. Design Soundness Assessment

**Strengths:**
- The two-timescale SA architecture is well-motivated for separating fast threshold dynamics from slow model convergence, directly targeting temporal attack patterns often neglected in the literature.
- Derivation of a closed-form, domain-specific FPR bound attempts to provide design-stage guarantees rare in robust FL papers.
- The use of eigenvector perturbation theory (Davis-Kahan) for subspace drift detection is technically appropriate.

**Critical Weaknesses:**
- **Assumption–Domain Mismatch:** The bounded perturbation assumption (δ ≤ 0.15) and stationary covariance Σ exclude the most dangerous classes of temporal fraud (low-frequency high-magnitude injections, adversarial data that alters the correlation structure). The design is sound *within* this regime, but the regime excludes the motivating problem's hardest instances.
- **Coupling of Timescales:** During transient fraud spikes, the gradient norm explodes, coupling the fast and slow timescales. The standard Borkar separation theorem requires the fast dynamic to be contractive uniformly in the slow state, an assumption likely violated during detection phases.

**Verdict:** The skeleton is sound under its self-declared idealizations, but the boundary conditions of these idealizations are not rigorously justified against the intended fraud domain.

---

### 3. Formal Analysis Evaluation

**3.1 Stewart Bound (FPR ≤ 1.6%, Eq. 8)**
The bound is mathematically standard for a singleton outlier test under Gaussian null statistics. The derivation is consistent. However, FL update vectors are aggregates; dependency introduced by client sampling and non-IID data weakens the bound. The text should explicitly state the dependency on the eigen-gap, as the 1.6% figure holds only if the gap is sufficiently large.
**Severity:** Medium

**3.2 Two-Timescale SA Contraction Argument**
The weight-dependence of the Lipschitz constant for the fast threshold update is the most fragile theoretical link. If the Lipschitz constant of the fast ODE depends on the gradient norm of the slow state, the uniform contraction required by Borkar's theorem does not hold globally. A justification via "quasi-stationarity" or a newly derived state-dependent noise SA result is required; without it, the convergence argument is not proven during transient phases.
**Severity: HIGH** (Soundness)

**3.3 Davis-Kahan Correction and Drift-Affected FPR**
The removal of the k-in-numerator error is a meaningful improvement backed by non-asymptotic sin(θ) bounds. The corrected bound is likely correctly stated. The drift-affected FPR expresses degradation as a function of drift magnitude but relies on nuisance parameters (eigen-gap, noise variance). It provides qualitative theoretical confirmation of the trade-off curve but is not "actionable" as a closed-form threshold for practitioners.
**Severity:** Low

**3.4 Convergence Neighborhood Bound**
Standard SA theory yields an asymptotic neighborhood bound of the form `limsup E[||θ_t − θ*||] ≤ C * (step-size ratio)`. If the text frames this as a finite-sample guarantee, it is misleading. The review assumes proper caveating given the design-stage context, but the phrasing must be strictly as an order-of-magnitude estimate of the convergence radius, not a proven tight guarantee.
**Severity:** Medium (risk of future misinterpretation)

---

### 4. Experimental Plan Critique

**4.1 Self-Consistency of Assumptions**
The evaluation plan must include a *controlled validation* scenario where Σ is exactly stationary and δ ≤ 0.15 to verify the core FPR bound. It *must also* stress-test the method by violating both assumptions (non-stationary Σ, δ unconstrained). Without both, the evaluation cannot prove the claimed hypothesis that the defense works under the specified theoretical conditions *and* generalizes beyond them.

**4.2 Baseline Completeness**
The claim of 14 baselines is strong. However, the following are notably absent from standard robust FL evaluation suites:
- **Krum / Multi-Krum** (canonical stateless defense)
- **Trimmed Mean** and **Median** (non-parametric baselines of exceptional importance for comparison)
- **FLAME** (a recent stateful defense with dynamic thresholding—directly relevant competitor)
- **DPSGD** (to contextualize utility–privacy–robustness trade-offs)

Without these, the evaluation body is incomplete. An ablation showing *where* the proposed method improves upon or degrades relative to Median is essential.
**Severity: MEDIUM**

---

### 5. Internal Validity Threats

**Critical Threat: The Signal–Drift Confound**
This is the highest-severity internal validity issue and *cannot be addressed by any standard experiment included in a plan based on the current assumptions.*

- **Mechanism:** The defense flags deviations in the empirical eigenstructure. A benign concept drift (e.g., user behavior during a holiday, weekend pattern, seasonality) produces deviations indistinguishable from an adversarial injection.
- **Why Bounds Fail:** The FPR bound assumes the null hypothesis (i.i.d. benign updates) is true. A benign distribution shift *violates that null*. The bounded false alarm rate is therefore meaningless against non-stationary data.
- **Mitigation Required:** The plan must introduce a *benign drift baseline*—a control experiment where a non-stationary but non-adversarial distribution shift of equal magnitude to the attack is applied. Without this, the defense cannot claim to distinguish attack from drift, which is the central design requirement of a temporal fraud detector.

**Additional Threats:**
- **Parameter Sensitivity:** With 4+ free parameters (two step sizes, eigen-window, threshold prior), an exhaustive sweep is required. Single pareto-optimal curves are insufficient.
- **Non-IID Quantification:** The Dirichlet α parameter controlling data skew must be rigorously varied, and the evaluation must include extreme skew settings (α < 0.1) to match domain realism.

**Severity: HIGH**

---

### 6. Specific Issues with Severity

| ID | Issue | Severity | Section |
|---|---|---|---|
| M-1 | Weight-dependence of Lipschitz constant invalidates Borkar contraction argument during transient attack phases. Proof of quasi-stationarity or alternative coupling analysis required. | **HIGH** (Soundness) | 3.2 |
| M-2 | Stationarity of Σ is assumed but violated by temporal fraud domain. No experimental design can distinguish attack from benign drift under current assumptions. | **HIGH** (Internal Validity) | 2, 3.1, 5 |
| M-3 | Missing baselines: Krum, Trimmed Mean, Median, FLAME, DP-SGD. | **MEDIUM** (Experimental Plan) | 4.2 |
| M-4 | Convergence neighborhood bound risks misinterpretation as a finite-sample guarantee rather than asymptotic order-of-magnitude estimate. | **MEDIUM** (Formal Analysis) | 3.4 |
| M-5 | Drift-affected FPR is qualitatively useful but not actionable without explicit noise models. | **LOW** (Formal Analysis) | 3.3 |

---

### 7. Recommendation

**MAJOR REVISIONS REQUIRED FOR DESIGN VALIDATION**

The two-timescale SA framework targets an important underexplored problem. The theoretical mathematics (FPR bounds, subspace perturbation) are competently handled. However, two HIGH-severity issues must be resolved before the design can be considered executable:

**Primary Required Revisions (Address M-1 and M-2):**
1. **Formalize the coupling of timescales.** Provide a theoretical justification for the SA contraction argument when the Lipschitz constant of the fast update depends on the slow state. This may require a modified update rule, an explicit noise model, or a proof of exponential mixing under state-dependent noise.
2. **Repair the stationarity assumption gap.** Explicitly analyze the defense's behavior under non-stationary Σ (benign drift). Introduce a *benign drift baseline* into the experimental plan. This is essential to test the central claim of distinguishing temporal attack from benign temporal variance.

**Secondary Required Revisions (Address M-3 and M-4):**
3. Augment the baseline suite with Krum, Trimmed Mean, Median, FLAME, and DP-SGD.
4. Rephrase the convergence neighborhood bound strictly as an asymptotic neighborhood radius, not a finite-sample guarantee.

**Resubmission Status:** Resubmission for design validation is strongly encouraged provided the high-severity issues are convincingly addressed—either by extending the theoretical analysis or by explicitly narrowing the applicability domain to attacks occurring *without* confounding benign drift.
