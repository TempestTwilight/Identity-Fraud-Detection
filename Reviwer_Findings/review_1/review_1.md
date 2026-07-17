# Editorial Decision — Synthesis & Revision Roadmap

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Stage:** Chapter Plan / Design Verification  
**Date:** 2026-07-06

---

## All 5 Reviews Received

| Reviewer | Score | Recommendation | 
|----------|-------|---------------|
| EIC (Zhao) | 65/100 contribution | **Major Revision** |
| Methodology (Tanaka) | 3.2/5 | **Minor Revision** |
| Domain (Mitchell) | 68/100 | **P1-P5 priority fixes** |
| Perspective (Chen) | 58/100 | **Significant cross-disciplinary revision** |
| Devil's Advocate | — | **Do not pass** |

---

## Editorial Decision: MAJOR REVISION

**Decision rationale:** The paper identifies a genuine gap and the 3-layer defense has sound individual components. However, **no reviewer believes the paper is ready for TIFS submission in its current state.** The DA's "do not pass" verdict cannot be ignored — but it identifies fixable issues, not fatal ones.

**Verdict structure:** Major Revision with staged tasks. After all tasks complete, re-review before submission.

---

## 1. Verified Strengths (No Changes Needed)

| Claim | Supporting Evidence | Reviewers |
|-------|-------------------|-----------|
| Gap identification | Four-argument gap analysis is sharp, novel, well-supported | EIC, Domain, DA |
| Dataset choices | IEEE-CIS + ECC with Dirichlet + geographic splits is appropriate | Domain, Methodology |
| Modular codebase | All three layers implemented and importable | Methodology |
| Fraud-specific metrics | Savings curves, ASR, Honest FPR, AUASR are right | EIC, Methodology, DA |
| Training/inference separation | Explainability argument is correct | Perspective, Domain |

---

## 2. Remaining Issues (Revised Priority)

### Tier 1: Must Fix Before Any Resubmission (4 items)

These are the issues multiple reviewers independently flagged as foundational.

| ID | Issue | Source | Action |
|----|-------|--------|--------|
| **S1** | **Joint cascade analysis missing** | DA (core argument), Methodology (C2) | Prove or bound the error propagation probability of the cascade. Show that Pr(miss at L1) × Pr(contaminated SVD | miss) × Pr(unfair reputation | contaminated) is bounded. Without this, "3 layers > 1" is an article of faith |
| **S2** | **Convergence proof is insufficient** | Methodology (C1), DA, Perspective | Formalize τ dynamics, resolve constant-η vs decaying-η tension, or honestly reframe as empirical control system with convergence bounds |
| **S3** | **Threat model incomplete — server compromise** | Domain (P1), Perspective, DA | The most realistic attack in banking FL is server manipulation, not client-side poisoning. Must address or explicitly bound out |
| **S4** | **Ablation controls incomplete** | Methodology (C5, C6), DA | Add `cascade_fixed` (adaptive threshold replaced by fixed 2σ threshold) and `cascade_oracle` (optimal per-round threshold from oracle knowledge) to isolate adaptive threshold novelty from cascade structure |

### Tier 2: Must Fix Before TIFS Submission (6 items)

These are blocking for TIFS acceptance but not for the design validity.

| ID | Issue | Source | Action |
|----|-------|--------|--------|
| **S5** | **Privacy model not ready for TIFS** | Perspective, Domain (P3) | Either strengthen the trusted server justification (TEE integration details, formal DP analysis, concrete leakage bounds) or accept SecAgg → drop L2 framing |
| **S6** | **SR 11-7 validation cycle absent** | Domain (P2), Perspective | Add ongoing monitoring, concept drift, outcomes analysis, governance structure |
| **S7** | **Structural fairness blind spot** | Perspective (ethical), Domain (R10) | Temporal reputation creates a downward spiral for minority banks. Add decay mechanism for old penalties, fairness intervention triggers |
| **S8** | **Regulatory overconfidence** | Perspective, Domain | Correct GDPR compliance mapping (DPIA is mandatory, gradients = personal data). Add AML/CFT override obligation. Address cross-jurisdictional conflicts |
| **S9** | **A2-Grinding underspecified** | Methodology (C3) | Add reactive (defense-aware) variant with explicit λ_max bounds per attack phase |
| **S10** | **Honest FPR evaluation incomplete** | Methodology (C4) | Add max-consecutive-false-flags metric, "benign outlier" scenario for honest non-IID banks |

### Tier 3: Strongly Recommended Before Submission (4 items)

These would significantly strengthen the paper but are not blocking.

| ID | Issue | Source | Action |
|----|-------|--------|--------|
| **S11** | **Missing temporal metrics** | Methodology (C7) | Add Time to Reject / Detection Window / per-layer resolution rate |
| **S12** | **L1 acceptance threshold unvalidated** | Methodology (C8) | Validate 80% L1 acceptance rate under Dirichlet α=0.1 extreme skew |
| **S13** | **Synthetic identity injection attack** | Domain, DA | Add A6 to the threat model (most FL-relevant fraud type) |
| **S14** | **Consumer protection obligations** | Perspective | Address FCRA, ECOA, CCPA/CPRA, EU AI Act implications for the deployed system |

---

## 3. Revised Assessment

| Dimension | Original Score (R1-R10) | Post-Review Score | Gap |
|-----------|------------------------|-------------------|-----|
| Contribution significance | 7/10 (70%) | 5/10 (50%) | Cascade-independent convergence needed |
| Methodological rigor | 7/10 (70%) | 5/10 (50%) | Joint cascade analysis + proof |
| Domain realism | 7/10 (70%) | 6/10 (60%) | Server compromise, regulatory depth |
| Privacy/ethics | 5/10 (50%) | 4/10 (40%) | Privacy model insufficient for TIFS |
| Evaluation design | 8/10 (80%) | 7/10 (70%) | Ablation controls, temporal metrics |

**Overall: ~55/100** (down from our self-assessment of 80/100). This is honest — the 10 issue resolutions addressed the *original* review but did not anticipate the deeper concerns this round uncovered.

---

## 4. Path to TIFS Submission

```
Round 1 (R1-R10) → Round 2 (S1-S14) → Experimental validation → Paper writing → Re-review → Submission
        ✅                  🔲 Pending         🔲 Pending       🔲 Pending     🔲 Pending    🔲
```

**Estimated work for S1-S14:**
- Tier 1 (S1-S4): ~3-5 days of analysis + code changes
- Tier 2 (S5-S10): ~2-3 days of document + code changes  
- Tier 3 (S11-S14): ~1-2 days of document changes
- Experimental validation: ~2-5 days on suitable hardware
- Paper writing: ~1-2 weeks

**Estimated total: 3-5 weeks to TIFS-ready submission.**

Hardware constraint (Ryzen 3 3250U, 8GB RAM) blocks experimental validation. Recommend cloud compute (AWS p3.2xlarge, ~$3-5/hour, 50-100 hours = $150-500) or using a lab's GPU server for the experiments.
