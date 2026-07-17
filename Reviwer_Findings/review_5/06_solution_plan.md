# Comprehensive Solution Plan — Review 5

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework
**Date:** 2026-07-11
**Based on:** 5 independent reviews (EIC, R1 Methodology, R2 Domain, R3 Perspective, Devil's Advocate)
**Feasibility Decision:** RETHINK

---

## Structure

Five phases ordered by dependency. **Phase 1** (Framing) must be completed before any other work begins — these are conceptual corrections that change how the paper is understood. **Phase 2** (Architecture) and **Phase 3** (Formal Analysis) can be developed in parallel once Phase 1 is settled. **Phase 4** (Experimental Campaign) depends on Phase 1 framing to define what success means. **Phase 5** (Missing Perspectives) is independent and can proceed in parallel with 2–4.

| Phase | Focus | Priority | Dependency |
|-------|-------|----------|------------|
| **1** | Framing Corrections | Must resolve first | None |
| **2** | Architectural Specifications | Parallel with Phase 3 | Phase 1 |
| **3** | Formal Analysis Resolutions | Parallel with Phase 2 | Phase 1 |
| **4** | Experimental Campaign Plan | After Phase 1 | Phase 1 |
| **5** | Missing Perspectives | Independent | None |

---

# Phase 1 — Framing Corrections (PREREQUISITE)

*Resolve the 3 Critical contradictions before any other work. These define what the paper actually claims.*

---

## P1.1 — Reframe the Contribution Claim

**Reviewers:** DA (#3 CRITICAL), EIC, R1

**Problem:** The paper frames the cascade as closing the "statelessness blind spot" in general. Section 5.6 then admits the adaptive adversary (A6) operates indefinitely below threshold. This is a logical contradiction in the central claim.

**Solution — Three-tier contribution reframing:**

Replace the current single claim with a layered, honest decomposition:

> **Contribution 1 (Detection Primitive):** We identify and formalize the *statelessness blind spot* — the vulnerability of round-independent robust aggregators to temporally-corrupted update sequences. We show that any stateless aggregation rule (Krum, Median, Trimmed Mean) can be bypassed by a sustained sequence of bounded-perturbation updates, even if each individual update passes round-level checks.

> **Contribution 2 (Stateful Cascade Design):** We design a three-layer gated cascade (L1 norm/cosine → L2 spectral PCA → L3 EMA reputation with per-client baseline) that introduces state into the aggregation pipeline. We prove FPR bounds under stationary benign gradient covariance Σ (Stewart's theorem) and characterize drift-affected FPR degradation via Davis-Kahan sinΘ (Eq. 14).

> **Contribution 3 (Attack Taxonomy):** We contribute six fraud-specific attack models (A1–A6) spanning the adversarial capability spectrum, including the cascade-aware adaptive adversary (A6) which defines the operational envelope within which the cascade can detect attacks.

**Key reframing rule:** The cascade detects *unbounded* or *spectrally-correlated* attacks and sustains detection under *bounded drift*. The adaptive adversary (A6) who constrains perturbations below each layer's threshold is explicitly scoped as an *open problem* — the cascade detects attacks that exceed its calibrated envelope, not attacks that operate within it. The defense is an *early-warning alarm for high-magnitude or structurally anomalous updates*, not a general adversary-proof aggregator.

**Affected sections:** §2.2 (Central Claim), §5.6 (A6), Abstract, §9 (Discussion)

---

## P1.2 — Narrow the Literature Gap Claim

**Reviewer:** R2 (Critical, D1)

**Problem:** Claiming "no existing FL fraud study evaluates robust aggregation" is factually overreaching. Work exists (FedML Financial benchmark, FLTrust, FoolsGold, Krum/Median/Trimmed Mean on IEEE-CIS).

**Solution:** Replace with the narrower, defensible gap:

> **Authentic Gap:** While robust aggregation methods have been evaluated on financial FL tasks (FedML Financial, IEEE-CIS benchmarks), **no existing study evaluates their vulnerability to temporally-adaptive adversaries under the operational constraints of a regulated financial consortium**: (i) non-stationary concept drift from fraud evolution, (ii) multi-round attack scheduling across retraining cycles, (iii) regulatory requirements for auditability and explainability that preclude black-box aggregation, and (iv) the specific incentive structure of a small-N consortium (10 institutions) where membership is known and exclusion is costly.

**Change:** Acknowledge the foundation work explicitly in §3 with citations. The contribution is *an evaluation gap*, not a *literature void*.

**Affected sections:** §3 (Related Work), §2.3 (Gap Synthesis)

---

## P1.3 — Resolve the Stationary Σ Contradiction

**Reviewers:** DA (#2 CRITICAL), R1 (HIGH, M-2), R3, R2 (D6), EIC

**Problem:** The FPR bound (≤1.6%) and Borkar convergence proof assume stationary Σ. The paper's motivation is non-stationary fraud data. The proofs are valid in a regime that excludes the domain.

**Solution — Multi-tier resolution:**

**Tier A — Narrow the formal guarantee (mandatory):**

Restate the FPR bound (Theorem 1 / Eq. 8) with an explicit stationarity qualifier:

> **Theorem 1 (Cascade FPR under stationary Σ).** Assume the benign gradient covariance Σ is stationary over the evaluation window W. Under the statistical model of Section 3.2 (zero-mean update residuals, i.i.d. across rounds), the cascade FPR is bounded as...
>
> **Corollary 1.1 (Drift-affected FPR).** When Σ is non-stationary with bounded drift rate ‖ΔΣ‖_2 ≤ ε_drift, the FPR bound degrades by at most:
>
> ```FPR₂(ε_drift) ≤ P( e_i > τ₂ − ε_drift / gap | honest )```
>
> where ε_drift = max over windows ‖Σ_t − Σ_0‖_2, gap is the eigen-gap separating the signal and noise subspaces of Σ₀, and e_i is the PCA reconstruction error of client i's update residual under Σ₀. This is a *tail probability*, not a closed-form operating point — numerical FPR claims require empirical ε_drift measurement. The ε_drift / gap form (first power) follows from the Davis–Kahan sinΘ theorem and matches the paper's existing Eq. 14 (verified in §VII-B).

This is already partially present in the paper (Eq. 14) but was buried. It must be elevated to a first-class result with explicit limitations.

**Tier B — Add benign-drift baseline to experimental plan (mandatory):**

The experimental campaign must include a *benign drift control*: a non-stationary but non-adversarial distribution shift of comparable magnitude to the attack. This tests whether the cascade can distinguish attack from drift — the core operational requirement.

**Tier C — Discuss concept drift management (recommended):**

Add a paragraph in §7 (Discussion) on how the framework can be extended to handle concept drift:
- Periodic baseline recalibration (triggered by global model loss plateau)
- Separate drift detection (e.g., monitoring the reconstruction error of the PCA subspace)
- Drift-resilient estimator: use a sliding-window PCA rather than cumulative PCA

**Affected sections:** §6.1 (Formal Analysis), §5.2 (L2 Design), §7 (Discussion), §9 (Limitations)

---

## P1.4 — Resolve the A6 Framing (Operational Envelope)

**Reviewer:** DA (#3 CRITICAL), EIC

**Problem:** A6 is simultaneously the paper's most sophisticated adversary and its most damning limitation. The cascade cannot detect an adaptive attacker who stays below each layer's threshold.

**Solution — Reframe as an operational envelope, not a limitation:**

Replace the current "Detection Limitation" paragraph (§5.6) with an explicit **Operational Envelope** definition:

> **Definition 1 (Cascade Operational Envelope).** The gated cascade guarantees detection of any adversary whose update sequence violates at least one of the following conditions over any sliding window of length W:
> - **L1 envelope:** ‖g_i‖_2 > τ_norm (magnitude bound) — per-round quantity compared to per-round threshold ✓
> - **L1 envelope:** cos(g_i, μ) < τ_cos (directional bound) — per-round quantity compared to per-round threshold ✓
> - **L2 envelope:** PCA reconstruction error > τ_2 (spectral bound) — per-round quantity compared to per-round threshold ✓
> - **L3 envelope:** R_i < T_i (reputation below per-client threshold) — windowed reputation R_i compared to windowed threshold T_i, both on the same RCC-normalized scale ✓
>
> An adversary who constrains their updates to stay strictly within all four envelopes simultaneously can operate indefinitely. This is not a design flaw — it is a fundamental consequence of the information-theoretic gap between benign and adversarial update distributions (see §X — Information-Theoretic Limits).

**Add a new subsection (§X — Information-Theoretic Limits of Gradient-Based Detection)** that formally discusses why no gradient-based detector can distinguish attack from drift when the adversary's updates lie within the typical set of the benign distribution. This directly addresses the DA's strongest counter-argument (KL divergence bound) and turns it from a liability into an honest foundational contribution.

**Affected sections:** §5.6, new subsection after §5

---

# Phase 2 — Architectural Specifications

*Detailed design decisions that reviewers flagged as underspecified. Implement after Phase 1 framing is settled.*

---

## P2.1 — TEE Architecture with Cryptographic Layering

**Reviewers:** R2 (Critical, D2), R3 (High, C-1, H-2), DA (#5 Major), EIC

**Problem:** Three distinct sub-issues:
1. L2 operates on *raw* gradients before DP — the privacy claim is inconsistent with the architecture (R3 C-1)
2. Single-anchor TEE fails GDPR Art. 25/32 "state of the art" — cryptographic layering required (R3 H-2)
3. No TEE risk register, no audit architecture (R3 H-3)

**Solution — Revised TEE architecture with three mandatory changes:**

### P2.1a — DP applied before gradient enters detection logic

Restructure the processing pipeline from:

```
[Raw gradient] → L1 → L2 (raw) → L3 (raw) → DP noise → Secure Aggregation
```

to:

```
[Raw gradient] → Local DP noise (ε_local) → L1 → L2 (DP-noised) → L3 (DP-noised) → Secure Aggregation (ε_global)
```

**Consequence:** L2/L3 operate on locally DP-noised gradients. This means:
- The privacy guarantee is cryptographic, not hardware-attested — satisfies GDPR Art. 25/32 (R3)
- L2 spectral detection and L3 deviation detection work on DP-noised gradients — this reduces detection SNR but provides a mathematical privacy bound independent of TEE trust
- The TEE becomes a *defense-in-depth layer* (protecting the aggregation logic and DP accounting) rather than the *sole privacy anchor*

**Trade-off disclosure:** DP noise reduces L2/L3 detection power. The paper must characterize this degradation empirically (added to experimental plan). If detection power degrades unacceptably, the alternative is to frame the architecture honestly as "prioritized detection over privacy under audited TEE."

### P2.1b — Add TEE risk register

New subsection "TEE Risk Register and Graceful Degradation" documenting:

| Threat | Severity | Known Attack | Mitigation in Design | Graceful Degradation |
|--------|----------|-------------|---------------------|---------------------|
| Side-channel (timing/power/cache) | High | Plundervolt, ZombieLoad, CacheOut, SGAxe | Constant-time attestation, memory encryption | Fall back to cryptographic SecAgg-only mode |
| Attestation key compromise | High | Intel ME vulnerability | Dual-layer attestation (auditor + client), key rotation schedule | Consortium governance emergency key refresh |
| Rollback attack | Medium | TEE rollback to previous enclave state | Monotonic counter via TPM or blockchain-anchored state | Detect via chain-of-hash on published digest; halt and audit |
| Supply chain | Low | Hardware backdoor | Open-source firmware audit, TPM-measured boot | — |
| SGX deprecation | Medium | Intel ending SGX on consumer CPUs | Design is abstraction-layer over DCAP/TDX/SEV-SNP | Use AMD SEV-SNP or NVIDIA CC as alternative |

### P2.1c — Add audit architecture (IETF RATS)

New subsection "Regulator Audit Pathway for TEE Operations":

- Map the architecture to IETF Remote Attestation Procedures (RATS) reference model: Verifier (independent auditor), Relying Party (consortium members), Attester (the TEE enclave)
- Specify the evidence collection pipeline: attestation evidence (Quote), appraisal policy (code hash, measurement register), attestation result (signed token shared with regulators)
- Describe regulator access: quarterly code review against verified enclave hash, independent verifier node operated by the national banking supervisor

### P2.1d — Add SMPC/DP/TEE comparison table

| Dimension | Pure SMPC | DP-only | TEE-only (current) | TEE + DP (proposed) |
|-----------|-----------|---------|-------------------|---------------------|
| Privacy guarantee | Cryptographic | Differential privacy (ε) | Hardware attestation | DP (ε_local + ε_global) + HW attestation |
| Auditability | High (protocol public) | Medium (noise accounting) | Low (black box) | Medium (attested code + DP accounting) |
| Computational cost | Very high (O(d²) communication) | Low | Medium | Medium |
| Robust aggregation | Limited (# parties matters) | Compatible | Fully compatible | Fully compatible |
| GDPR Art. 25 compliance | High | High | Low (unless crypto layered) | High |

**Affected sections:** §4.1 (Architecture), §7.4 (Privacy-Robustness Tension), new subsections in §4

---

## P2.2 — Per-Client Baseline Measurement Protocol

**Reviewers:** R2 (High, D3), DA (Minor, #6), EIC

**Problem:** The per-client detection threshold is the key innovation replacing global τ_R, but the measurement of the baseline and per-client statistics is unspecified. Claims about Dirichlet α=0.5 and measured values are grounded in a single simulation.

**Solution — New explicit subsection "Baseline Measurement Protocol":**

### Dual-threshold architecture

Two distinct per-client thresholds serve complementary purposes:

| Threshold | Symbol | Formula | Purpose |
|-----------|--------|---------|---------|
| **Reputation threshold** (`R_i` scale) | `T_i` | `T_i = R̄_i − τ_Δ · σ_{R,i}` | Flags when EMA reputation `R_i` drops below `T_i`. `σ_{R,i}` = std(`R_i`) — the standard deviation of the *windowed reputation score* itself. (Paper's existing rule, verified. `τ_Δ = 5`, `σ_{R,i} ≈ 0.015`.) |
| **RCC deviation threshold** (ΔRCC scale) | `τ_{Δ,i}` | `τ_{Δ,i} = RCC_i^{(base)} + k · σ_{||r||,i} / √W` | Flags when short-window RCC deviates from calibrated baseline. `σ_{||r||,i}` = std(‖r_i^(s)‖) — the standard deviation of the *per-round residual norm*. The `/√W` term is the standard error of the mean (correctly shrinks a per-round std to bound a windowed average). |

Both thresholds are calibrated during warm-up but govern different flagging conditions in the cascade. They use distinct statistics (`σ_{R,i}` vs `σ_{||r||,i}`) and should never be conflated.

### Phase 1 — Warm-up calibration (W_hist = 200 rounds)

During an initial trusted calibration period, each client participates in standard FedAvg with all-reduce averaging. For each client i and each round s = 1..W_hist, record:

```
g_i^(s) — client's gradient update
μ^(s) = (1/N) Σ_j g_j^(s) — peer mean
r_i^(s) = g_i^(s) − μ^(s) — residual
R_i^(s) — client i's reputation score at round s (per-round value before EMA smoothing)
```

### Baseline estimation

Compute per-client reference statistics:

```
μ_i_ref = (1/W_hist) Σ_s g_i^(s)               — reference gradient
Σ_i = Cov(g_i^(1), ..., g_i^(W_hist))           — local gradient covariance (d×d)
R̄_i = (1/W_hist) Σ_s R_i^(s)                   — mean reputation score
σ_{R,i} = std({R_i^(s)} over s=1..W_hist)       — std of reputation score       (≈0.015, paper)
RCC_i^(base) = ‖(1/W_hist) Σ_s r_i^(s)‖ / ( (1/W_hist) Σ_s ‖r_i^(s)‖ )
σ_{||r||,i} = std(‖r_i^(s)‖ over s=1..W_hist)  — std of residual vector norm    (new)
```

**Disclosures:**
- The reported σ_{R,i} ≈ 0.015 was measured on the windowed reputation score R_i in a single toy logistic regression simulation (d=100, N=10, Dirichlet α=0.5). This is a preliminary observation, not a design principle.
- σ_{||r||,i} was not reported in the paper's original simulation — it is an open parameter that must be measured empirically on each dataset. Its value depends on gradient dimensionality d and SGD batch size in ways σ_{R,i} does not.
- The Dirichlet α=0.5 observation for RCC_i^(base) is also a single-simulation datapoint — the α sweep (Phase 4) will establish whether the per-client baseline approach generalizes.

Empirical validation on real financial data must verify:
1. Whether both σ_{R,i} and σ_{||r||,i} vary significantly across clients with different data volumes and non-IID degree
2. Whether both statistics are stable across retraining cycles
3. Whether the measurement procedure is robust when some warm-up rounds are corrupted

### Threshold selection

```
T_i = R̄_i − τ_Δ · σ_{R,i}                         (τ_Δ = 5 — paper's existing rule)
τ_{Δ,i} = RCC_i^(base) + k · σ_{||r||,i} / √W     (k = 3 — new RCC deviation rule)
```

where k=3 approximates a 3-sigma bound on RCC fluctuations under stationary Σ. The Dirichlet α sweep (α ∈ {0.1, 0.3, 0.5, 1.0, 5.0}) will test how both T_i and τ_{Δ,i} must vary with non-IID degree. Note: the `/√W` correction applies only to τ_{Δ,i} because it uses a per-round std (`σ_{||r||,i}`) to bound a windowed statistic (RCC_i). The T_i formula involves `σ_{R,i}`, which is already on the windowed reputation scale, so no `/√W` correction is needed.

### Circular bootstrap resolution (DA CRITICAL #1)

The warm-up phase vulnerability (no defense during W_hist rounds) is addressed via:

1. **Initial trusted hardware:** The calibration runs inside a TEE with code signed by the consortium's independent auditor. All W_hist rounds are attested and logged.
2. **Alternate robust estimator:** If trusted warm-up is infeasible, use the *geometric median* of residuals as a robust baseline estimate instead of the mean — this tolerates up to 50% corrupted rounds.
3. **Security implication:** If an adversary controls a client during warm-up, the baseline for that client is corrupted, but the *difference* ΔRCC_i will still detect abrupt changes in their behavior pattern. Explicit acknowledgment: bootstrap vulnerability is reduced, not eliminated.

**Affected sections:** §4.3 (L3 Reputation Scoring), §5 (Implementation), new measurement protocol subsection

---

## P2.3 — Cross-Jurisdictional Analysis Section

**Reviewer:** R3 (Critical, C-2)

**Problem:** The paper targets cross-border banking but contains no analysis of cross-jurisdictional legal conflicts (Schrems II, US CLOUD Act, data localization).

**Solution — New dedicated subsection "Cross-Jurisdictional and Sovereign Trust Considerations":**

### Key threats to address:

1. **TEE key management geography.** Intel SGX/TDX and AMD SEV-SNP attestation keys are managed by US-headquartered companies. Under the US CLOUD Act, a US law enforcement agency can compel these companies to assist in subverting the enclave. For an EU bank processing EU citizens' data in a TEE whose trust anchor is a US company, this creates a *Schrems II violation* — the data does not receive "essentially equivalent" protection.

2. **Mitigations proposed:**
   - Sovereign attestation services using non-US key hierarchies (e.g., EU TEEs with European key management, or open-source RISC-V TEEs with independent certification)
   - Geographic residency requirements for attestation key management
   - Hybrid architecture: cryptographic DP guarantees the privacy bound; TEE provides operational security. The privacy guarantee does not depend on TEE trust — it is mathematical (DP).

3. **Data localization vs. AML record retention.** EU banking secrecy laws (e.g., German §24c KWG, French Monetary and Financial Code) require data to remain within the jurisdiction. The architecture's DP-based privacy guarantee must be reconciled with the fact that fraud detection data may be exempt from right-to-erasure under GDPR Art. 23. The design should specify a data retention policy that respects both obligations.

4. **Cross-jurisdiction compliance mismatch.** GDPR's right to erasure conflicts with FINMA's 10-year record retention requirement. The architecture should separate the *training data* (subject to DP/right-to-erasure) from the *fraud detection model* and *audit log* (subject to AML retention). This is a legal design decision that must be specified.

**Affected sections:** New subsection in §8 (Regulatory) after §8.2

---

## P2.4 — Explainability Framework Rewrite

**Reviewer:** R3 (High, H-1)

**Problem:** The surrogate SHAP model with global R² ≥ 0.9 meets neither ECOA nor GDPR Art. 22 requirements. Proxy dataset governance is unspecified.

**Solution — Replace with local fidelity framework:**

### Abandon global R² threshold

Replace "R² ≥ 0.9" with a *local fidelity audit*:

> **Local fidelity requirement:** For each decile of the applicant score distribution, the surrogate SHAP model must achieve:
> - Weighted local R² ≥ 0.85 within each decile
> - Maximum individual-level absolute SHAP error ≤ 0.15 (relative to true model output delta)
> - Audit flag: if local fidelity drops below threshold for any decile, that decile's explanations are marked "estimated — contact [regulatory authority name] for individualized explanation"

### Proxy dataset governance specification

Define:

| Parameter | Specification |
|-----------|--------------|
| Size | N_proxy ≥ 10,000 (or 5% of training set, whichever larger) |
| Sampling | Stratified by outcome class (fraud/non-fraud) and by membership institution |
| Consent | Explicit opt-in with right-to-withdrawal; proxy data cannot contain PII |
| Retention | Tied to model lifecycle, with automatic deletion 90 days after model decommissioning |
| Audit trail | SHA-256 hash of proxy dataset published to consortium blockchain at train start |
| Legal validity | Explicit caveat: proxy-based explanations are *estimates*, not legally binding explanations under ECOA §615 or GDPR Art. 22. Institutions must maintain their own individualized explanation capability for adverse actions. |

**Affected sections:** §8.7 (Explainability), rewrite in full

---

# Phase 3 — Formal Analysis Resolutions

*Mathematical and theoretical fixes. Can proceed in parallel with Phase 2 once Phase 1 framing is settled.*

---

## P3.1 — Two-Timescale SA Coupling Justification

**Reviewer:** R1 (HIGH, M-1)

**Problem:** The Borkar two-timescale SA convergence argument requires the fast-timescale update to be uniformly contractive in the slow state. During attack detection phases, the Lipschitz constant of the threshold dynamics may depend on the gradient norm, potentially violating the uniform contraction requirement.

**Solution — Three options (pick one):**

**Option A (Preferred — Explicit coupling analysis):** Derive a modified Borkar condition for the cascade's specific update structure. Show that the fast threshold update L = λ max is:

```
λ_max^(t+1) = λ_max^(t) + γ_t · (σ_R,i − λ_max^(t))
```

which is a linear contraction with rate (1 − γ_t) independent of the gradient. The contraction depends only on σ_{R,i} (the per-client reference gradient norm), not on the gradient itself. Since σ_{R,i} is a constant estimated from warm-up data, the uniform contraction holds *even during attack phases*.

**Option B (Fallback — Quasi-stationarity argument):** If coupling cannot be fully resolved, provide a quasi-stationarity argument: between attack detection events, the slow model converges at rate O(a_t) and the fast threshold at rate O(b_t) with a_t/b_t → 0. Attack events are transient and bounded in magnitude, so the slow variable is effectively frozen on the fast threshold's timescale.

**Option C (Narrower claim):** If no analytical justification is possible, explicitly state: "The convergence argument applies under the assumption that ‖g_i‖_2 remains O(1) on the slow timescale. Transient attack phases may violate this assumption; Section 5.6 characterizes the resulting operational envelope (see Definition 1)."

**Affected sections:** §6.1 (Formal Analysis — Borkar framework), new appendix with detailed coupling analysis

---

## P3.2 — Benign-Drift Control Experiment and FPR Validation

**Reviewer:** R1 (HIGH, M-2), R2 (D6), DA (#2)

**Problem:** The FPR bound is untested under non-stationary Σ. The experimental plan must include a benign-drift control.

**Solution — Add to experimental plan:**

### Benign-drift control condition

- **Simulated drift type 1 (gradual):** Rotate the benign gradient distribution by θ degrees per round over 50 rounds (θ ∈ {1°, 2°, 5°}) — models product rollout
- **Simulated drift type 2 (abrupt):** Shift the mean of benign distribution by δ at a single round (δ ∈ {0.5σ, 1σ, 2σ}) — models holiday spike
- **Simulated drift type 3 (oscillatory):** Weekly seasonality pattern with period 7 — models weekend vs weekday fraud patterns

### Measurements

1. **Cascade FPR under each drift type** — reported separately from attack-detection results
2. **FPR bound tightness:** Compare measured FPR to theoretical bound (1.6% + drift term). Report gap as fraction of bound.
3. **Distinguishability metric:** For each drift-attack pair of equal magnitude, compare the cascade's response distributions. Report overlap coefficient (OVL) — the fraction of drift events misclassified as attacks. If OVL > 0.2, the defense cannot distinguish drift from attack at that regime.

**Success criterion:** FPR ≤ 5% under all three drift types, AND distinguishability OVL ≤ 0.2 for drift-attack pairs of equal magnitude.

**Affected sections:** §7 (Experimental Design), new subsection "Benign-Drift Control"

---

## P3.3 — Circular Bootstrap Resolution (Formal)

**Reviewer:** DA (CRITICAL, #1), R2 (D3)

**Problem:** The defense needs a secure starting state to calibrate baselines but exists to create that secure state. Circular dependency.

**Solution — Formal bootstrap specification:**

### Three-pronged bootstrap architecture

1. **Trusted execution environment (hardware root):** The warm-up phase (W_hist = 200 rounds) runs inside a TEE with code signed by the consortium's independent auditor. The TEE provides:
   - Integrity: all code and data in the calibration protocol are attested and logged
   - Confidentiality: gradient baselines are computed inside the enclave, never exposed to the aggregator outside
   - Audit trail: the full calibration transcript is sealed and published to the consortium blockchain

2. **Robust preliminary estimator (statistical root):** If TEE trust is unavailable, the baseline is computed using the *geometric median* of all clients' residuals across all W_hist rounds:
   ```
   r_GM = argmin_r Σ_i Σ_s ‖r_i^(s) − r‖_2
   ```
   The geometric median tolerates up to 50% corrupted clients, so even if some warm-up rounds are malicious, the baseline initialization is not catastrophically biased.

3. **Blinding during calibration (adversarial root):** During W_hist, each client's gradient is individually noise-masked before the aggregation: g_i' = g_i + η_i where η_i ~ N(0, σ_blind²) and σ_blind is a minimum-entropy noise guarantee. The noise is removed only inside the TEE after the baseline is computed. This prevents an adversary from knowing whether they are in the warm-up period.

**Explicit disclosure:** The bootstrap window W_hist = 200 rounds (approximately 1–2 weeks of daily training) is a vulnerable period. The three safeguards above reduce but do not eliminate this vulnerability. Fully eliminating the bootstrap dependency remains an open problem.

**Affected sections:** New subsection "Bootstrap and Initialization Protocol" after §4.3

---

# Phase 4 — Experimental Campaign Plan

*Complete experimental specification as required by all 5 reviewers. Depends on Phase 1 framing to define metrics and success criteria.*

---

## P4.1 — Datasets

| Dataset | Size | Fraud Rate | Type | Role |
|---------|------|------------|------|------|
| IEEE-CIS Fraud Detection (Kaggle) | 590K transactions | 3.5% | Credit card + identity | Primary benchmark |
| European Credit Card (ULB) | 284K transactions | 0.172% | PCA-transformed features | Sensitivity check (extreme imbalance) |
| Synthetic (Generate) | 200K transactions | Variable (0.1–5%) | Known ground-truth drift | Benign-drift control experiments |

**Data partitioning:** Dirichlet α ∈ {0.1, 0.3, 0.5, 1.0, 5.0} with N=10 clients. 10 independent partition seeds per α value.

---

## P4.2 — Baseline Methods

**Alignment note:** This table uses the paper's verified Table III as the canonical list (B1–B14, matching §VII-A exactly). The solution plan previously proposed a different set under the same IDs — reconciled below. FLAME (requested by reviewers) is added as B15.

| ID | Baseline | Category | Rationale |
|----|----------|----------|-----------|
| B1 | FedAvg (no defense) | Vanilla | Lower bound on robustness |
| B2 | Krum (1 outlier) | Stateless robust | Canonical defense, R1 request |
| B3 | Median | Stateless robust | Non-parametric, R1 request |
| B4 | Trimmed Mean (20% trim) | Stateless robust | Non-parametric, R1 request |
| B5 | Bulyan | Stateless robust | Cascade defense variant |
| B6 | FLTrust | Stateful (trust) | Direct competitor (trust score) |
| B7 | FoolsGold | Stateful (reputation) | Direct competitor (sybil defense) |
| B8 | RFA (Robust Federated Aggregation) | Stateless robust | Geometric median baseline |
| B9 | DP-FL (ε=8) | Privacy-only | Privacy baseline (low noise) |
| B10 | FLDetector | Stateful (consistency) | Temporal anomaly detection baseline |
| B11 | DP-FedAvg (ε=4) | Privacy-only | Privacy baseline (moderate noise) |
| B12 | DP-FedAvg (ε=1) | Privacy-only | Strong privacy baseline |
| B13 | Clipped Median | Robust + private | Combined baseline |
| B14 | Multi-Krum + Trimmed Mean | Hybrid | Cascade-like but stateless |
| B15 | **FLAME** | **Stateful (dynamic threshold)** | **Added per review — most relevant stateful competitor** |

All 15 baselines evaluated under the same 10-trial, 3-seed protocol.

---

## P4.3 — Evaluation Metrics (per R2 D5)

| Metric | Definition | Primary / Secondary |
|--------|-----------|-------------------|
| **Fraud Recall at FPR=0.1%** | Recall_T = TP / (TP + FN) when specific FPR=0.1% | Primary — domain-critical |
| **Attack Success Rate (ASR)** | Fraction of adversarial rounds where malicious update passes all layers | Primary — defense effectiveness |
| **AUC-ROC** | Area under ROC curve | Secondary |
| **FDR (False Discovery Rate)** | FP / (FP + TP) among flagged updates | Secondary — fairness for honest clients |
| **MCC** | Matthews Correlation Coefficient | Secondary — balanced measure |
| **Benign-Drift Overlap Coefficient** | OVL = overlap coefficient of cascade response distribution between drift and attack | Domain-specific — distinguishability |
| **Parameter Sensitivity** | ASR variance over ±20% τ_norm, τ_cos, W, τ_Δ | Robustness — DA #7 |

**Cost-sensitive framing (recommended):** Define a cost model where each missed fraud costs $c_m and each false positive (honest client incorrectly flagged) costs $c_f. Report total societal cost C = c_m·FN + c_f·FP. This aligns with R2's operational requirement.

---

## P4.4 — Benign-Drift Control (expanded from P3.2)

| Experiment | Drift Type | Parameters | Measurement |
|------------|-----------|------------|-------------|
| E1 | Gradual rotation | θ ∈ {1°, 2°, 5°}, 50 rounds | FPR, ASR, OVL |
| E2 | Abrupt shift | δ ∈ {0.5σ, 1σ, 2σ}, single round | FPR, ASR, OVL |
| E3 | Oscillatory | Period=7 rounds, amplitude=1σ | FPR, ASR, OVL |
| E4 | Combined drift-attack | Equal-magnitude drift + A2 attack | OVL, confusion matrix |

**Success criteria:**
- FPR ≤ 5% under all drift types (relaxed from 1.6% stationary bound)
- OVL ≤ 0.2 between drift and attack distributions of equal magnitude
- ASR improvement over FedAvg with statistical significance (p < 0.05, paired t-test over 10 trials)

---

## P4.5 — Attack Models (expanded)

**Alignment note:** This table preserves the paper's verified Table II as the canonical ID set (A1–A6). Additions (Eavesdrop, Label Flip) are marked with variant IDs and cross-referenced to the paper's taxonomy. When this table is merged into the paper, every existing reference to A1–A6 in §V, §VII, and the ASR bounds table will continue to point at the same attack as before.

| ID | Attack | Paper ID | Description | Tempo | Realism (R2) | Treatment |
|----|--------|----------|-------------|-------|--------------|-----------|
| A0 | Eavesdrop (passive) | — *(new, control)* | Observe model update only, no modification | Per-round | Low | Control condition; not an attack |
| **A1** | **Naive Model Replacement** | **A1 (unchanged)** | **Replace local model entirely** | **1 round** | **Medium** | **Full evaluation — canonical paper baseline** |
| **A2** | **Gradient Grinding** | **A2 (unchanged)** | **Slow gradient pull over 120 rounds** | **5 days** | **Low (academic)** | **Deprioritized per R2; one condition only** |
| **A3** | **Spectral-Matching Collusion** | **A3 (unchanged)** | **Match malicious to benign PCA subspace** | **Multi-round** | **Medium** | **Full evaluation — targets L2** |
| A3' | Adversarial Label Flip | — *(data-level variant)* | Immediate label corruption before local training | 1 round | Medium | Full evaluation; supplements A3 (same gradient effect class) |
| **A4'** | **Insider Collusion** | **A4 split (elevated)** | **Compromised employee at member institution** | **Multi-round** | **High** | **Primary attack model per R2** |
| **A4''** | **Aggregator Compromise** | **A4 split** | **Compromise the TEE aggregator** | **Single-shot** | **Medium** | **Conditionally evaluated (TEE security)** |
| **A5** | **Data Feature Poisoning** | **A5 (unchanged)** | **Inject synthetic fraud accounts into training** | **Multi-round** | **High** | **Full evaluation** |
| **A6** | **Cascade-Aware Adaptive** | **A6 (unchanged)** | **Probe thresholds, stay below each layer** | **Indefinite** | **High** | **Scoped as open problem** (see P1.4) |

**Attack prioritization change per R2:** A4' (Insider Collusion) becomes the primary attack scenario. A2 (Grinding) is reduced to a single experimental condition with explicit caveat about operational tempo mismatch. A5 (Feature Poisoning) added as a primary threat. Bold rows = paper's canonical IDs preserved (no semantic drift).

---

## P4.6 — Sensitivity Analysis (per DA #7)

Systematic sweep over the five key hyperparameters:

| Parameter | Range | Grid | Rationale |
|-----------|-------|------|-----------|
| τ_norm (L1 norm threshold) | [1.5, 4.0] mean grad norm | 6 points | Magnitude envelope |
| τ_cos (L1 cosine threshold) | [0.3, 0.8] | 6 points | Direction envelope |
| W (RCC window size) | [10, 100] | 6 points | Temporal memory |
| τ_Δ (RCC deviation threshold) | [1.5σ, 6.5σ] | 8 points, includes τ_Δ=5 (paper's design choice) | Sensitivity to drift |
| N_clients | {5, 10, 20} | 3 points | Consortium size |

Report ASR heatmaps and FPR heatmaps for each (parameter pair). Identify plateau regions vs. cliff edges.

---

# Phase 5 — Missing Perspectives

*Independent of other phases. Can be drafted immediately.*

---

## P5.1 — Information-Theoretic Limits Section (New)

**Reviewer:** DA (Strongest Counter-Argument)

Add a new section after §3 (Related Work) or as a standalone §X:

> **Section X: Fundamental Limits of Gradient-Based Detection**
>
> Any defense operating on gradient updates is bounded by the Kullback-Leibler divergence between the benign and malicious update distributions. If an adversary constrains their updates to lie within the typical set of the benign distribution:
>
> `D_KL(P_benign ‖ P_adversary) → 0 ⟹ error → 1/2`
>
> No aggregation mechanism — stateless or stateful — can distinguish attack from benign drift in this regime. The gated cascade's operational envelope (Definition 1) is a consequence of this fundamental limit, not a design shortcoming.
>
> The paper's contribution is not *eliminating* this limit, but *characterizing* it for the specific case of temporal attacks on stateless robust aggregators, and *extending* the detectable envelope to include spectrally-correlated and high-magnitude temporal attack sequences.

This section transforms the DA's strongest criticism into a foundational contribution and reframes the A6 limitation as a necessary consequence of information theory.

**Affected sections:** New section, referenced in Abstract, §2, §5.6

---

## P5.2 — Incentive Alignment and Contribution Modeling

**Reviewers:** R2 (D7), R3 (missing economic perspective)

**Solution — New subsection "Consortium Incentive Design":**

Address the fundamental consortium problem: why would a large bank contribute high-quality gradient data when smaller members benefit equally?

1. **Shapley-value contribution scoring (already in §4.7):** Truncated Monte Carlo Shapley (K=100, P=50 rounds) computes each member's marginal contribution to model accuracy. Members with higher Shapley values receive:
   - Lower membership fees
   - Higher voting weight in consortium governance decisions
   - Priority access to model explanations (SHAP reports)

2. **Privacy budget as token:** Each client's local DP budget ε is a scarce resource. Clients who contribute more data receive a larger collective ε budget for their institution's queries.

3. **Reputation-to-stake conversion:** The L3 reputation score R_i is backed by a financial stake (smart contract escrow). If R_i drops below a threshold, the stake is partially slashed — creating an economic disincentive for malicious behavior that supplements the technical detection.

**Affected sections:** New subsection after §8.6 (Governance)

---

## P5.3 — Missing Stakeholder Perspectives

**Reviewer:** DA (Missing Stakeholder Perspectives)

### Regulator perspective — Model risk management (SR 11-7)

The TEE-based aggregation is a "black box" from the regulator's viewpoint. Add a section on how regulators can exercise their SR 11-7 responsibilities:
- Right to inspect the attested code hash before deployment
- Quarterly independent review of the enclave's measurement register against the published specification
- Authority to trigger a cryptographic attestation re-key (forcing the consortium to re-attest all enclaves)
- Escrow access to training logs (post-hoc, not real-time)

### Bank / Financial Institution — Operational cost assessment

Estimate the incremental infrastructure cost of the cascade design:
- TEE compute overhead: ~5–15% latency increase per round (paper's verified estimate, §VII-D)
- PCA on d-dimensional gradients: O(Nd²) per round — dominated by gradient computation
- SMART overhead: O(NKW) per contribution scoring round
- Total estimated compute: within 2× of plain FedAvg for N=10, d=500

Compare to the cost of a single undetected fraud campaign (estimated $1–10M for a mid-size institution).

### Honest Client — False positive recovery path

Define a "right to appeal" for honest clients whose reputation decays due to benign drift:
- Automatic reputation freeze if ΔRCC exceeds τ_Δ but subsequent rounds show reversion to baseline
- Manual review by consortium ethics committee if reputation falls below R_min
- Reputation reset at the beginning of each retraining cycle
- Explicit caveat: these mechanisms are governance-level, not cryptographic, and their efficacy depends on consortium member behavior.

**Affected sections:** Scattered throughout §8 (Regulatory) and §9 (Discussion)

---

## P5.4 — TEE Side-Channel Risk Register

**Reviewer:** R3 (M-2), R2 (D2)

Already specified in P2.1b above. Elevate to a standalone appendix for completeness.

**Affected sections:** Appendix A: TEE Security Considerations

---

# Summary: Resolution Mapping

| Reviewer Issue | Severity | Solution ID | Effort | Dependencies |
|---------------|----------|-------------|--------|-------------|
| DA #3 / EIC — A6 contradiction | CRITICAL | P1.1 (reframe), P1.4 (envelope) | Low (editing) | None |
| R2 D1 — Literature gap overreach | CRITICAL | P1.2 | Low (editing) | None |
| DA #2 / R1 M-2 — Stationary Σ | CRITICAL | P1.3, P3.2, P4.4 | Medium (analysis + experiment) | P1.1 |
| DA #1 — Circular bootstrap | CRITICAL | P2.2 (warm-up), P3.3 | Medium (spec + protocol) | P1.1 |
| R1 M-1 — SA coupling | HIGH | P3.1 | Medium (analysis) | P1.1 |
| R2 D2 / R3 C-1 / H-2 — TEE | CRITICAL | P2.1 (a–d) | Medium (arch specification) | P1.1 |
| R2 D3 / DA #6 — Per-client baseline | HIGH | P2.2 | Low (specification) | P1.1 |
| R3 C-2 — Cross-jurisdictional | CRITICAL | P2.3 | Low (research + writing) | None |
| R3 H-1 — Explainability framework | HIGH | P2.4 | Medium (rewrite) | None |
| R2 D4 / DA #4 — Attack tempo mismatch | HIGH | P4.5 (reprioritize) | Low (editing) | P1.1 |
| R2 D5 — Metrics undefined | HIGH | P4.3 | Low (specification) | P1.1 |
| DA #7 — Parameter sensitivity | MINOR | P4.6 | Medium (experiment) | P4.1–4.3 |
| R3 M-1 — SHAP side-channel | MEDIUM | P5.1 (info-theoretic) | Low (section) | P1.1 |
| R2 D7 — Incentive alignment | MEDIUM | P5.2 | Low (section) | None |
| DA — Missing stakeholder perspectives | MAJOR | P5.3 | Low (sections) | None |
| R3 M-2 — TEE risk register | MEDIUM | P5.4 | Low (appendix) | P2.1b |

**Total estimated effort:** ~60–80 hours of analytical/editing work + 100–150 GPU-hours for experimental campaign.

---

# Recommended Publication Roadmap

| Milestone | Content | Target | Timeline |
|-----------|---------|--------|----------|
| **M1: arXiv + Workshop (current form)** | Design-stage specification with Phase 1 framing corrections + Phase 5 perspectives | arXiv + AISec/FL@FM | 0–2 weeks |
| **M2: Revised arXiv (Phase 1–3)** | Framing corrections + architectural specs + formal analysis fixes | arXiv v2 | 2–6 weeks |
| **M3: Full Validation (Phase 4)** | Complete experimental campaign + sensitivity analysis | arXiv v3 | 6–14 weeks |
| **M4: TIFS Submission** | Full validated research article | IEEE TIFS | 14–18 weeks |

**Parallel workstreams:** Phase 5 (Missing Perspectives) can be drafted immediately. Phase 2 (Architecture) and Phase 3 (Formal Analysis) can proceed in parallel once Phase 1 framing is settled.
