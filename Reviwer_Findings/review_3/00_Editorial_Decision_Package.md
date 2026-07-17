# Editorial Decision Package

## A Temporally-Aware Layered Defense Framework for Robust FL Fraud Detection
### IEEE TIFS Design-Stage Specification

**Date**: 2026-07-06
**Editor**: Hermes Academic Paper Reviewer — Simulation

---

## 1. Review Summary

### 1.1 Reviewer Consensus Matrix

| Reviewer | Recommendation | Score | Confidence | Core Verdict |
|----------|---------------|-------|------------|--------------|
| 🏛️ **EIC** | Reject for TIFS | 48.5 | 5/5 | Design-stage without experiments doesn't meet TIFS bar; invited resubmission welcome |
| 🔬 **R1 (Methodology)** | Major Revision | 59.8 | 4/5 | Formal analysis doesn't bound ASR; stationarity assumption contradicts temporality |
| 🏦 **R2 (Domain)** | Major Revision | 56.0 | 4/5 | Threat model unrealistic; datasets anachronistic; consortium dynamics ignored |
| ⚖️ **R3 (Perspective)** | Major Revision | 67.5 | 4/5 | Privacy-robustness contradiction unresolved; regulatory mapping overreaches |
| 😈 **Devil's Advocate** | Critical Issues | — | — | EMA accommodates rather than detects grinding; reputation floor is revolving door; bootstrap window is free attack phase |

### 1.2 Aggregate Dimension Scores

| Dimension | Weight | EIC | R1 | R2 | R3 | **Avg** | **Wtd** |
|-----------|--------|-----|-----|-----|-----|---------|---------|
| Originality | 20% | 70 | 75 | 70 | 85 | **75.0** | 15.00 |
| Methodological Rigor | 25% | 35 | 55 | 45 | 62 | **49.3** | 12.31 |
| Evidence Sufficiency | 25% | 5 | 25 | 30 | 50 | **27.5** | 6.88 |
| Argument Coherence | 15% | 78 | 80 | 75 | 68 | **75.3** | 11.29 |
| Writing Quality | 15% | 85 | 85 | 80 | 82 | **83.0** | 12.45 |
| **Weighted Average** | **100%** | 48.5 | 59.8 | 56.0 | 67.5 | **—** | **57.93** |

---

## 2. Editorial Decision

### Verdict: **MAJOR REVISION**

The paper is **NOT ACCEPTABLE** in its current design-stage form. However, the core problem—hardening FL fraud detection against temporally-adaptive poisoning—is genuine and timely. The gated cascade architecture represents a novel synthesis, and the formal analysis (Stewart's perturbation theorem, fixed-point convergence, reputation floor) provides credible theoretical grounding. All reviewers acknowledge the paper's ambition as its primary strength.

**Why Major Revision rather than Reject:**
- The statelessness blind spot is a genuine gap in existing FL fraud detection work, as reviewers R1–R3 and DA agree
- The architectural concept (gated cascade with complementary detection principles) is sound and practically motivated
- The formal analysis, though incomplete, represents meaningful theoretical progress
- The experimental scaffolding (10 baselines, 5 attacks, 10 ablations) demonstrates methodological thoroughness
- The limitations section shows self-awareness; most weaknesses are identified and actionable

**Why not Accept:**
- No experimental results whatsoever — expected results in Table V are speculative
- Three CRITICAL issues identified by the Devil's Advocate (EMA/grinding mismatch, reputation start-up paradox, bootstrap window exploit) that directly threaten the paper's core thesis
- Unresolved architectural contradiction: L2 spectral detection requires raw gradients; DP-FL claim requires noise
- Regulatory mapping overreaches — functional equivalence ≠ regulatory compliance
- Core parameterization (anomaly score weights, EMA decay) is underspecified

---

## 3. Prioritized Revision Issues (Must-Address High to Low)

### Tier 1 — Critical (Blocking Issues)

| ID | Issue | Source | Section |
|----|-------|--------|---------|
| C1 | **EMA accommodates rather than detects grinding attacks.** γ=0.02 EMA half-life (~35 rounds) means the defense normalizes the slow drift of A2's subliminal phase rather than penalizing it. The EMA forgets the burn-in evidence by the time the active phase begins. | DA, R1 | §IV-D, §V-B |
| C2 | **Reputation start-up paradox.** New clients enter at R=0.85 (the floor). An adversary can cycle Sybil identities — enter at floor, attack within probation window at 50% weight, depart before EMA penalty accumulates. The temporal persistence requirement contradicts the transient identity model inherent to fraud. | DA, R2 | §IV-C, §IV-D |
| C3 | **Bootstrap window is a free attack phase.** Cold-start t₀=20 rounds aligns perfectly with A2's 19-round burn-in. L3 operates at reduced confidence during this window. The attacker seeds the EMA with poisoned history before full detection kicks in. | DA | §IV-D, §V-B |
| C4 | **Missing experimental results.** No validation data supports any claim about ASR, FPR, or robustness. Expected results (Table V) are purely speculative. | EIC, R1 | §VI |
| C5 | **Privacy-robustness contradiction unresolved.** DP-FL (ε=8) and L2 spectral anomaly detection on raw gradients cannot coexist without a specified TEE or SMPC architecture. The paper holds both claims without demonstrating compatibility. | R3 | §VII-D, §IV-C |

### Tier 2 — Major (Required for Revision)

| ID | Issue | Source | Section |
|----|-------|--------|---------|
| M1 | **Formal analysis doesn't bound the core objective.** Stewart's theorem bounds FPR, not ASR or model utility under attack. The connection between filter behavior and global model quality is unformalized. | R1, DA | §VII-A |
| M2 | **Stationarity assumption contradicts temporality claim.** Stewart bound assumes stationary gradient covariance Σ. Credit card fraud exhibits concept drift. If Σ shifts, the spectral PCA layer degrades without characterization. | R1 | §VII-A |
| M3 | **No adaptive adversary model.** Attack models are static (A1–A5). No adversary that observes the defense and optimizes against it is considered. | EIC, R1, DA | §III, §V |
| M4 | **Threat model intelligence asymmetry is implausible.** Kerckhoffs principle (perfect architectural knowledge) has gradient-only observation — contradicts sophistication needed for multi-phase attacks. Sybil capability is not considered. | R2 | §III-C |
| M5 | **Datasets anachronistic.** IEEE-CIS (2019), ECC (2015) — pre-COVID, pre-CNP explosion, pre-AI synthetic identity. Not representative of current fraud tactics. | R2 | §VI-A |
| M6 | **Consortium dynamics unrealistic.** N=10 static banks; no churn, no latency constraints, no governance. Real FL consortia face member churn, heterogeneous GPU/compute, sub-100ms SLAs. | R2 | §III-A, §IV |
| M7 | **R_SS=0.85 is not a fairness guarantee.** Uniform floor on differential FPR subgroups does not satisfy ECOA disparate impact analysis. May mask rather than remedy harm. | R3, R1 | §VII-C |

### Tier 3 — Important (Strongly Recommended)

| ID | Issue | Source | Section |
|----|-------|--------|---------|
| I1 | **No hyperparameter sensitivity analysis planned.** Ablations C9/C10 isolate threshold effects, but no grid over τ_l1, τ_l2, ρ, EMA window. Cannot distinguish architecture effect from tuning effect. | R1 | §VI-C |
| I2 | **GDPR Art. 22 analysis legally weak.** Training/inference separation does not exempt profiling from Art. 22. Art. 28 "joint controller" mislabel should be Art. 26. | R3 | §VIII-A |
| I3 | **SR 11-7 mapping confuses function with governance.** Table VII maps code modules to requirements, but SR 11-7 demands independent validation, documentation, and audit trails — not built into any flag or detector. | R3, R2 | §VIII-B |
| I4 | **Anomaly score weights unspecified.** a_i^{(t)} combines three signals but weights omitted "for brevity." The design is not reproducible; the 0.25 expected ASR is unsupported. | DA, R1 | §IV-C |
| I5 | **Competitive intelligence leakage has no structural mitigation.** Listed as limitation but no cryptographic or architectural solution proposed. May be the biggest adoption barrier. | R3 | §IX-B |
| I6 | **No temporal cross-validation.** Static train/test split misaligns with "temporally-aware" claim. Requires expanding window or iterated time-series split. | R1 | §VI-A |

### Tier 4 — Minor (Suggested)

| ID | Issue | Source | Section |
|----|-------|--------|---------|
| m1 | Expected results (Table V) should be explicitly labeled as hypotheses, not presented as validated outcomes. | R1 | §VI-D |
| m2 | Paper length (~7 pp, 6,500 words) is well below TIFS standard (12–16 pp). | EIC | — |
| m3 | EMA concept drift threshold and autocorrelation monitoring unaddressed. | R2 | §IV-C |
| m4 | Adaptive threshold policy lacks formal specification. | EIC | §IV-E |
| m5 | False decline harm treated as post-hoc risk rather than design constraint. | R3 | §IX-D |
| m6 | AMC/SAR override concept legally unsound as binding decision. | R2 | §VIII-D |

---

## 4. Revision Roadmap

The editorial board recommends the following sequential revision plan:

### Phase 1 — Resolve Foundational Contradictions
1. **Privacy-Robustness**: Choose one path — (a) specify TEE/SMPC architecture with formal privacy budget accounting, OR (b) drop DP-FL claim and acknowledge privacy limitation, OR (c) drop raw-gradient L2 and redesign the spectral layer for noisy inputs.
2. **EMA vs. Grinding**: Analyze the γ=0.02 / A2 schedule mismatch. Either revise parameters (shorter half-life), adopt sliding window with hard reset, or provide formal boundary conditions where the defense holds against the grinding attack.
3. **Cold-Start Bootstrap**: Quantify the attack surface during t₀=20 rounds. Either shorten the window, provide early detection mechanisms, or formally bound worst-case damage.

### Phase 2 — Execute Experiments
4. **Core validation**: Run 10 baselines × 5 attacks × 10 ablations on at least one dataset.
5. **Sensitivity analysis**: Grid search over τ_l1, τ_l2, ρ, EMA window. Report ASR variance.
6. **Adaptive adversary**: Implement at least one adversary that sees the defense layers and optimizes against them (e.g., gradient matching + EMA targeting).
7. **Temporal cross-validation**: Evaluate on time-series expanding window split.
8. **High-churn scenario**: Simulate membership churn with Sybil identity cycling.

### Phase 3 — Deepen Analysis
9. Extend Stewart bound to non-stationary Σ (bounded drift ∥Σ_t − Σ_{t-1}∥ ≤ ε).
10. Provide ASR or utility bound under attack (not just FPR bound).
11. Fault-tree analysis of cascade dependency (how failures propagate).
12. ECOA disparate impact analysis with subgroup-specific FPR ratios.

### Phase 4 — Regulatory & Deployment Rigor
13. Correct GDPR Art. 26/28 joint controller analysis.
14. Differentiate SR 11-7 mapping from satisfying.
15. Propose concrete mitigation for competitive intelligence leakage (split learning, functional encryption).

---

## 5. Files

All five review reports saved to `Reviwer_Findings/`:
| File | Contents |
|------|----------|
| `01_EIC_Review.md` | Editor-in-Chief: journal fit, originality, publishability |
| `02_R1_Methodology_Review.md` | Methodology: formal analysis, experimental design, baselines |
| `03_R2_Domain_Review.md` | Domain expert: threat realism, deployment feasibility |
| `04_R3_Perspective_Review.md` | Regulation/ethics: privacy, fairness, regulatory compliance |
| `05_Devils_Advocate_Report.md` | Stress-test: foundational contradictions, parameter mismatches |

---

*Editorial simulation generated by Hermes Agent — Academic Paper Reviewer v1.10.0*
