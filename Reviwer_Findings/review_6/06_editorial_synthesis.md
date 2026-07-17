# Editorial Synthesis & Prioritized Issue List

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework  
**Venue:** IEEE TIFS (design-stage specification)  
**Review Round:** 6 | **Synthesis Date:** 2026-07-11

---

## Consolidated Reviewer Verdicts

| Reviewer | Recommendation | Score | Confidence |
|----------|---------------|-------|------------|
| **EIC** | Reject | 42/100 | 4/5 |
| **R1 (Methodology)** | Major Revision | 62/100 | 5/5 |
| **R2 (Domain)** | Major Revision | 58/100 | 4/5 |
| **R3 (Perspective)** | Major Revision | 55/100 | 5/5 |
| **DA (Devil's Advocate)** | — (issue list) | — | 5/5 |

**Editorial Verdict: Major Revision — Two substantive fixes required**

The EIC recommends Reject, driven by the absence of experimental validation at a top archival venue. However, the three peer reviewers and DA all identify **fixable design-stage issues** — and several of the DA's CRITICAL issues are already honestly addressed by the paper's own text. The editorial synthesis below filters the reviewer findings through the current paper to isolate genuinely unresolved gaps from criticisms the paper already acknowledges.

**Key correction versus the raw reviewer reports:** Three issues flagged as "not addressed" by reviewers are in fact already handled by the paper's explicit text — C3 (DP→SNR deferred to planned experiment, §VI-C), C4 (FPR→ASR disclaimed at §VII-A-1), and DA-C1 (bootstrap vulnerability described as open problem with three mitigations, §IV-H). These are **honest design-stage scoping**, not bugs.

**Decision: Major Revision** conditioned on resolving the **two genuinely open mathematical issues** (DA-C2's FPR constants and M4's baseline staleness) plus addressing the remaining MAJOR concerns (more baselines, experiments, disclosure). If DA-C2 cannot be resolved (FPR₁=0.003 is inconsistent with τ_norm=1.5σ), the paper's headline 1.6% bound is unsupported — downgrade to Reject. All other issues are reasonable scope-appropriate asks.

---

## Consensus Map (Corrected for Paper's Existing Text)

### Already Handled by Paper (not bugs — honest design-stage disclosure)

| Issue | Raised By | Paper's Position | Verdict |
|-------|-----------|-----------------|---------|
| DP→SNR degradation unquantified | R3(W1), DA, R1, R2 | Planned experiment (§VI-C: ε_local sweep); tradeoff disclosed (§VIII-B) | **Addressed: future work, not a paper bug** |
| FPR→ASR mismatch | R1(W1), EIC | §VII-A-1 explicitly disclaims: "FPR bound does not directly bound ASR" | **Addressed: disclaimer exists** |
| Bootstrap circularity | DA(C1), R2(W4), R3(W4) | §IV-H: three mitigations listed + "an open problem" statement | **Addressed: honest open-problem disclosure** |

### Full Agreement — Genuinely Unresolved (5/5 reviewers)

| Issue | Raised By | Type |
|-------|-----------|------|
| Stationary-Σ assumption contradicts real fraud drift | R1(W3), DA(M1) | **Consensus: major limitation** |
| A6 operational envelope framing contested | R3(W5), DA(C3), EIC | **Partially mitigated by Kerckhoffs (§III-C); numeric threshold publication is separate concern** |
| Undocumented FPR constants (0.003, 0.012, 0.001) inconsistent with τ_norm=1.5σ | R1(W2), DA(C2) | **Consensus: mathematical error — must fix** |

### Strong Agreement (4/5)

| Issue | Raised By | Verdict |
|-------|-----------|---------|
| d=50 synthetic data inadequate for spectral validation | R1(W5), R2(W3), EIC | Reasonable experiment-expansion ask |
| Underpowered trial protocol | R1(W4), DA(m1), EIC | Reasonable ask (increase N or add power analysis) |

### Divided Opinion

| Issue | Positions |
|-------|-----------|
| **Is IEEE TIFS the right venue?** | EIC says Reject (no experiments); R1/R2/R3/DA say Major Revision (design-stage acceptable). **Editorial: fits scope but needs 'Design-Stage Specification' header.** |
| **TEE adequacy for GDPR cross-border** | R3(W3) flags Schrems II as CRITICAL; R2 calls it "most comprehensive seen." **Editorial: R3's technical concern is valid but not CRITICAL — most papers at this stage cite policy intent, not deployed attestation infrastructure. Keep as MAJOR.** |

---

## Devil's Advocate CRITICAL Issues — Corrected Assessment

The three DA CRITICAL issues split into: (1) one genuine math error that must be fixed, (2) two that the paper already honestly addresses.

### DA-C2: Undocumented FPR Constants **⚠️ GENUINE MATH ERROR — MUST FIX**
**Severity: CRITICAL — Consensus (R1 + DA)**
**Status: Unresolved — FPR₁=0.003 is inconsistent with stated τ_norm=1.5σ**

The per-layer FPR values (FPR₁ ≤ 0.003, FPR₂ ≤ 0.012, FPR₃ ≤ 0.001) appear without derivation. The Stewart's theorem-based Eq. 69 contains unspecified constants C and σ. A Gaussian tail bound P(‖g‖ > 1.5σ) ≈ 0.003 is inconsistent with standard Gaussian quantiles (~0.067 for 1.5σ) and Chebyshev (~0.44). The 0.003 value would require τ_norm ≈ 3σ, contradicting the stated τ_norm = 1.5σ (line 203).

**Resolution required:** (1) Derive each constant explicitly from the stated thresholds, (2) cite the specific tail bound theorem used, and (3) replace undocumented values with parameterized expressions. If the values are illustrative, label them as such. The headline 1.6% bound depends on these numbers — they must be verifiable.

### DA-C1: Bootstrap Circularity ✓ **ALREADY ADDRESSED**
**Severity downgraded: CRITICAL → MAJOR (acknowledged open problem)**
**Status: Honest design-stage disclosure exists**

The paper's §IV-H provides three mitigations (base-rate test over sliding window, paired-client correlation, Shapley validation on held-out data) and explicitly states "these safeguards reduce but do not eliminate the bootstrap vulnerability" — directly acknowledging it as an open problem. For a design-stage specification, this is appropriate disclosure. No formal solution exists, but the paper does not pretend one does.

**Resolution:** Keep the disclosure; add a bound on warm-up threshold error under bounded attack rate, even if approximate. Remains a credible threat to the FPR guarantee in deployment.

### DA-C3: A6 Operational Envelope as Evasion Recipe ✓ **PARTIALLY ADDRESSED**
**Severity downgraded: CRITICAL → MAJOR (Kerckhoffs mitigates; numeric thresholds are separate)**
**Status: Partially addressed, residual concern**

The paper invokes Kerckhoffs's Principle (§III-C: "the adversary knows the system") — standard in security papers. Given this assumption, publishing the architecture and thresholds is not a vulnerability; the paper's contribution is designing a system secure under that assumption. However, the DA's concern about exact numeric thresholds (τ_norm=1.5σ, τ_cos=0.5, τ_Δ=5) being published alongside the envelope is a separate point from just assuming the attacker knows the design. Publishing precise calibration values does make it easier for a real attacker to estimate the detection gap.

**Resolution:** Either (a) add a sensitivity analysis showing that knowledge of exact thresholds only modestly reduces the detection gap, or (b) calibrate thresholds to a secret entropy source (within the TEE) and bound worst-case leakage. Most papers survive with option (a) — an analysis argument.

---

## Prioritized Issue List (Corrected)

### CRITICAL (2 issues — genuine math/design gaps)

| # | Issue | Lead Reviewer | Section | Proposed Fix |
|---|-------|--------------|---------|-------------|
| **C1** | **FPR constants (FPR₁≤0.003, FPR₂≤0.012, FPR₃≤0.001) undocumented; FPR₁=0.003 inconsistent with stated τ_norm=1.5σ** | DA(C2) + R1(W2) | §6.1, Eq. 69 | Derive from stated thresholds or replace with verifiable parameterized bounds. Gaussian tail at 1.5σ ≈ 0.067, not 0.003 — if the values are illustrative, say so explicitly. The headline 1.6% bound rests on these numbers |
| **C2** | **M4: Baseline R̄_i and σ_{R,i} computed once over warm-up (Eq. 13–14), not sliding — a round-1 attacker inflates their baseline permanently** | DA(M2) → corrected to **M4** | §4.8 (Eq. 13–14) | Either (a) make the baseline continuously rolling (exponentially weighted or recomputed on a sliding window), or (b) prove that drift-triggered recalibration (§IX-B) fires fast enough to bound the inflation. Current design: a round-1 attacker's inflated baseline persists until the next recalibration trigger |

### MAJOR (7 issues — address during revision)

| # | Issue | Lead Reviewer | Section | Proposed Fix |
|---|-------|--------------|---------|-------------|
| **M1** | Bootstrap circularity — already honestly disclosed (§IV-H); add a bound on warm-up threshold error under bounded attack rate | DA(C1) downgraded | §4.8 | Paper honestly calls this an open problem. For revision: add approximate worst-case bound on how much an ε-bounded attacker can shift the calibrated thresholds during W_h=200 warm-up |
| **M2** | A6 envelope + exact numeric thresholds published — Kerckhoffs mitigates architecture knowledge, but precise values help attackers estimate the detection gap | DA(C3) downgraded | §5.7, §3.3 | Add sensitivity analysis: does knowing exact thresholds (vs. knowing the architecture alone) materially change the attacker's optimal strategy? |
| **M3** | d=50 synthetic data inadequate for spectral detection validation | R1(W5) + R2(W3) | §7.4 | Add scaling argument linking d=50 gap structure to operational d≈40K; or acknowledge as limitation and specify real-data plan |
| **M4** | M≥3 collusion threshold leaves 1-2 attacker scenarios with zero L2 protection | R2(W2) | §5.2, §7.2 | Project ASR for 1-2 malicious clients relying on L1+L3 only. If single-attacker ASR > 0.5, state as deployment constraint |
| **M5** | Gate vs. ensemble FPR independence: Eq. 20 assumes independent per-layer FPR/TPR, but L3's d_grad shares info with L1's cosine check, and thresholds are jointly adaptive | DA(M3) → m6 promoted | §4.1, Eq. 20 | Verify or qualify the independence assumption. If violated, the cascade FPR may be higher than Eq. 20 predicts |
| **M6** | Stationary-Σ assumption contradicts fraud's temporal drift | R1(W3) + DA(M1) | §6.1 | Qualify as explicit assumption with a theorem-statement caveat. The drift-affected analysis (Cor. 1.1) should be labeled "heuristic," not "bound" |
| **M7** | Underpowered trial protocol: N=10 trials, 3 independent randomness sources | R1(W4) + DA(m1) | §7.4 | Increase to ≥30 or add power analysis justifying N=10 for 5-10pp distinctions |

### MINOR (5 issues — fix in final version)

| # | Issue | Lead Reviewer | Section |
|---|-------|--------------|---------|
| **m1** | Baseline set omits Zeno, SignSGD, momentum-based trimming | R2(W5) | §7.1 |
| **m2** | A2 4-phase schedule too rigid (implied, not a real calendar) | R2(W1) | §5.2 |
| **m3** | Auditability regress: who audits the auditor? | R3(W2) | §8.4 |
| **m4** | Schrems II / CLOUD Act: attestation key jurisdiction unspecified | R3(W3) | §8.5 |
| **m5** | 200-round warm-up (~7 months) vulnerability window — can mitigate with faster recalibration trigger analysis | R2(W4) | §4.8 |

---

## Editorial Decision Letter (Design-Stage Specification)

Dear Authors,

Thank you for submitting your design-stage specification to IEEE TIFS. The reviewers and I have carefully evaluated the paper's architectural design, formal analysis, and experimental plan.

**Overall assessment:** The paper addresses a genuine and underexplored vulnerability — the statelessness blind spot of Byzantine-robust FL aggregators — and proposes a well-motivated three-layer cascade architecture. The threat taxonomy (A1-A6), regulatory framework engagement (GDPR, SR 11-7, ECOA/FCRA), and honest disclosure of limitations are strengths for a design-stage specification.

**However, two issues must be fixed for the paper's core claim to stand:**

1. **FPR constants (C1).** The headline 1.6% FPR bound rests on per-layer values (FPR₁≤0.003, FPR₂≤0.012, FPR₃≤0.001) that are inconsistent with the stated thresholds. Gaussian tail at τ_norm=1.5σ gives ~0.067, not 0.003. These must be derived transparently or replaced with verifiable parameterized bounds.

2. **Baseline staleness (C2).** The per-client reputation baseline (R̄_i, σ_{R,i}) is computed once over W_h=200 warm-up rounds, not on a sliding window. A round-1 attacker can inflate their own baseline indefinitely (§IV-H, Eq. 13–14). The paper's drift-triggered recalibration (§IX-B) may not fire fast enough.

**Issues already handled by the paper** that reviewers flagged as "not addressed": (a) DP→SNR deferred to planned experiment (§VI-C), (b) FPR→ASR disclaimer exists (§VII-A-1), (c) bootstrap circularity disclosed with three mitigations (§IV-H). These are honest design-stage scoping, not bugs.

**The remaining MAJOR and MINOR issues** (d=50 synthetic data, M≥3 collusion gap, underpowered trials, baseline omissions, gate-vs-ensemble independence) are reasonable scope-appropriate asks for a revision.

**Decision: MAJOR REVISION** — Conditioned on resolving C1 (FPR constants) and C2 (baseline staleness). If the FPR constants cannot be derived consistently from the stated thresholds, the 1.6% bound is unsupported → downgrade to Reject. All other issues are standard revision scope.

Sincerely,
Editor-in-Chief (IEEE TIFS — simulated)

---

## Cross-Reviewer Issue Traceability Matrix (Corrected)

| Issue | EIC | R1 | R2 | R3 | DA | Recommended Priority |
|-------|-----|----|----|----|----|--------------------|
| FPR constants | — | W2 | — | — | C2 | **CRITICAL** |
| Baseline staleness | — | — | — | — | M2 | **CRITICAL** |
| Bootstrap circularity | * | — | W4 | W4 | C1† | MAJOR |
| A6 envelope + thresholds | * | — | — | W5 | C3† | MAJOR |
| d=50 inadequate | * | W5 | W3 | — | — | MAJOR |
| M≥3 collusion gap | — | — | W2 | — | — | MAJOR |
| Gate vs ensemble independence | — | — | — | — | M3 | MAJOR |
| Stationary Σ | — | W3 | — | — | M1 | MAJOR |
| Underpowered trials | — | W4 | — | — | m1 | MAJOR |
| Baseline omissions | — | — | W5 | — | — | MINOR |
| A2 schedule too rigid | — | — | W1 | — | — | MINOR |
| Auditability regress | — | — | — | W2 | — | MINOR |
| Schrems II vulnerability | — | — | — | W3 | — | MINOR |
| 200-round warm-up window | — | — | W4 | — | — | MINOR |

*EIC noted in general assessment. †Rescored: paper's existing text mitigates.

---

## Files

| File | Content |
|------|---------|
| `01_eic_review.md` | EIC review report — Reject (42/100) |
| `02_methodology_review.md` | R1 methodology review — Major Revision (62/100) |
| `03_domain_review.md` | R2 domain review — Major Revision (58/100) |
| `04_perspective_review.md` | R3 perspective review — Major Revision (55/100) |
| `05_devils_advocate.md` | Devil's Advocate report — 3 CRITICAL issues |
| `06_editorial_synthesis.md` | This file — consolidated decision + prioritized issue list |
