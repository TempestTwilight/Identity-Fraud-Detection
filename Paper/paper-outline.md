# Phase 2: Structure & Evidence Map — Full Outline

> **Phase:** Structure Architect  
> **Source Materials:** Paper draft + revised-argument-flow + 10 spec docs + S1-S10 resolutions + 5 reviewer reports

---

## Paper Title
**Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework**

---

## Section-by-Section Outline

### §1 Introduction (1,000–1,200 words)

**Section Goal:** Frame the fraud-specific poisoning problem, identify the statelessness blind spot, state contribution.

| Paragraph | Claim | Evidence Source | Word Count |
|-----------|-------|----------------|------------|
| 1.1 Hook | Cross-silo FL for fraud detection is deployed — but vulnerable | Draft §1; Yang 2019, Abdul Salam 2024 | 100w |
| 1.2 Problem | Fraudsters have direct financial incentive to poison FL models; they operate adaptively, not one-shot | Draft §1.1 "Core Problem" | 150w |
| 1.3 Gap | Existing Byzantine-robust methods are stateless — they evaluate per-round, missing temporally-adaptive attackers | Draft §1.2 "Gap"; Revised argument flow §2 | 200w |
| 1.4 Key insight | Statelessness is the blind spot, not non-IID (corrected from earlier framing) | Revised argument flow "How Narrative Changes" | 100w |
| 1.5 Our approach | 3-layer gated cascade: Norm/Cosine → Spectral → Temporal, with adaptive threshold escalation | Draft §2.2; Revised §3; adaptive-threshold-escalation.md | 250w |
| 1.6 Contributions | (1) Temporal statelessness blind spot identification (2) Gated cascade design (3) Explicit operational envelope (A6 residual gap) (4) Formal analysis (FPR bound, threshold dynamics, fairness) (5) Cross-disciplinary regulatory compliance mapping | Verified resolution matrix | 150w |
| 1.7 Roadmap | Standard "§2 Related Work, §3 Threat Model…" | — | 50w |

**Supporting materials:** Draft §5.6 (original structure), revised-argument-flow (narrative reframe), R1 resolution (statelessness reframe)

**Key tension to avoid:** Per EIC, must state up front that results are **expected** (no experimental validation yet). "We present a design specification with formally-motivated expected results."

---

### §2 Related Work (1,200–1,500 words)

**Section Goal:** Position against three literatures — FL fraud detection, Byzantine-robust aggregation, adaptive attacks.

| Subsection | Content | Source | Impact |
|------------|---------|--------|--------|
| **2.1 FL for Fraud Detection** | Yang 2019 (FedAvg only), Abdul Salam 2024 (data balancing, no poisoning), Zheng 2025 (plain FL), Farrukh 2025 (identifies robustness gap) | Draft §5.5 gap table; Draft references | Shows **no existing fraud FL work evaluates poisoning** |
| **2.2 Byzantine-Robust Aggregation** | Krum, Median, Trimmed Mean, Bulyan, RFA, FLTrust, FoolsGold — strengths and why each breaks under non-IID + targeted evasion | Draft §2.2 table; adaptive-threshold-escalation §2 | Establishes existing methods are **stateless + non-IID-blind** |
| **2.3 Adaptive Adversarial Attacks** | Fang 2020 (adaptive attacks), Jagielski 2018 (gradient matching), Shejwalkar 2022 (manipulated FedAvg) | adaptive-threshold-escalation §2.2; S1-cascade-analysis §1 | Shows adaptive attacks exist — but none in **fraud-specific** setting |
| **2.4 Gap Synthesis** | Table mapping each existing work's blind spot against our coverage | Draft §5.5; reviewer C2 | Establishes **originality of intersection** |

**Note:** DA flagged "related work timeline is dated (2017-2020)." — Acknowledge but note our contribution is architectural, not a new aggregator. Reference FLAME, ShieldFL, FedDef briefly as orthogonal.

---

### §3 Threat Model (1,500–1,800 words)

**Section Goal:** Formalize adversary, attacks, and constraints — incorporating S3 (server compromise) and S8 (regulatory capture).

| Subsection | Content | Source |
|------------|---------|--------|
| **3.1 System Model** | Cross-silo FL, N banks, non-IID P_i, trusted server | Revised §3.1; privacy-model §2 |
| **3.2 Adversarial Objectives** | Targeted evasion ≠ model collapse; incentive-driven; accuracy-preserving | Revised §3.1; Draft §3.2 |
| **3.3 Adversarial Capabilities** | Kerckhoffs's principle; controls m clients; ❌ does NOT control server (bounded); does NOT control other clients | Revised §3.1; **S3-server-compromise §2** (explicit trust boundary) |
| **3.4 Attack Taxonomy (6 types)** | A1-A6 with layer mapping table | Revised §3.3 table; §3.4 attack definition updated |
| **3.5 Why Stateless Defenses Fail** | Grinding attack formal intuition + Bernoulli vs. sequence-game comparison | Revised §3.2; S1-cascade-analysis §3 |
| **3.6 Assumptions & Scope** | Explicit list: no server compromise, no synthetic identity injection, no regulatory capture arbitrage | S3-server-compromise §3; Domain P1; **S8-regulatory-corrections §4** |

**Key contribution over draft:** §3.6 is new — explicitly lists what's OUT of scope (per Domain reviewer P1). Also adds "trusted consortium server" assumption with governance justification (S3).

---

### §4 Proposed Framework (2,500–3,000 words) — Core Contribution

**Section Goal:** Full architectural specification — the gated cascade, each layer, the adaptive threshold.

| Subsection | Content | Source |
|------------|---------|--------|
| **4.1 Architecture Overview** | Gated cascade diagram; escalation policy (3 confidence thresholds → which layer handles); confusion matrix definitions (TP, TN, FP, FN) | adaptive-threshold-escalation §3-4; S1-cascade-analysis §2 |
| **4.2 Layer 1: Norm & Cosine Filtering** | L2 norm + cosine similarity to mean; θ_low=0.21 confidence-calibrated rejection linking τ_norm to FPR₁ | adaptive-threshold-escalation §3.1 |
| **4.3 Layer 2: Spectral Anomaly Detection** | PCA on client update matrix; residual-based scoring; spectral separation of collusive attacks | Revised §3.4; adaptive-threshold-escalation §3.2; R1 resolution |
| **4.4 Layer 3: Temporal Reputation Scoring** | Sliding window W=50 reputation score R_i; steady-state floor R_SS=0.85; probation mechanism | adaptive-threshold-escalation §3.3; **S7-fairness-blind-spot §3-4** |
| **4.5 Reputation Forgetting + Adaptive Thresholds** | EMA reputation recovery; threshold dynamics (η_attack, η_relax); temperature schedule α_t | adaptive-threshold-escalation §4-5; **S2-convergence-proof** |
| **4.6 Combined Aggregation** | Adaptive trimmed mean with reputation weights; convergence via EMA control system | adaptive-threshold-escalation §6; **S2-convergence-proof §3-6** |
| **4.7 Baseline Estimation (EWMA)** | Continuously-evolving baseline via λ=0.995 EWMA; bootstrap safeguards (TEE, robust estimator, blinding); replaces one-shot warm-up | **DA-C2/M4 resolution; §IV-H** |
| **4.8 Formal Analysis** | Cascade error propagation bound (Stewart, ~1.6% FPR); interpretation note on confident-rejection vs raw-flag FPR; threshold dynamics; fairness guarantee | **S1-cascade-analysis**; **S2-convergence-proof** |

**Key improvements over draft:**
- Reframed from "fusion ensemble" to **gated cascade** (per Methodology C2)
- Added formal analysis subsection (§4.8) — addresses DA core argument
- Added confusion matrix definitions (§4.1) — addresses DA-C2 clarity
- Added EWMA baseline + bootstrap safeguards (§4.7) — addresses M4 staleness gap
- Added fairness forgetting mechanism (§4.4) — addresses Perspective S7
- Added convergence analysis (§4.6) — addresses Methodology C1

---

### §5 Attack Models (1,000–1,200 words)

**Section Goal:** Formal definitions of A1-A6, implementation notes, and expected evasion difficulty.

| Attack | Description | Formalization | Expected ASR (full defense) | Source |
|--------|-------------|---------------|---------------------------|--------|
| **A1: Naive Model Replacement** | Extreme gradient | ‖g_adv‖₂ > τ_high | 0.05 | attacker-design §2 |
| **A2: Gradient Grinding** | Adaptive drift; 4-phase schedule; λ_max=0.15 | g_adv = g_honest + λ·δ, λ∈[0,λ_max] | 0.25 | attacker-design §3; **S9-a2-adaptive** |
| **A3: Spectral-Matching** | Colluding m≥3 clients with correlated gradients | g_adv,j ∼ N(μ_adv, Σ_adv) ∀j | 0.30 | attacker-design §4 |
| **A4: Collusive Grinding** | A2 + A3 combined | Both temporal + spectral coordination | 0.45 | attacker-design §5 |
| **A5: Data Feature Poisoning** | Local data corruption | Shift in P_i(X,y) via injected transactions | 0.35 | attacker-design §6; Domain P1 |
| **A6: Cascade-Aware Adaptive** | Full knowledge of defense; each update within perturbation envelope | ‖g‖₂ ≤ τ_norm, cos(g,μ) ≥ τ_cos, per-update ‖Δ‖ ≤ δ | 0.15 | **DA-C3 / information-theoretic bound** |

**Note:** A6 is the operational envelope — attacks strictly within the defense's perturbation bounds are information-theoretically indistinguishable from honest high-variance non-IID updates.

---

### §6 Experiments & Expected Results (1,500–2,000 words)

**Section Goal:** Experimental protocol with expected results tables. Candid about "expected" nature.

| Subsection | Content | Source |
|------------|---------|--------|
| **6.1 Setup** | IEEE-CIS (primary), ECC (secondary); Dirichlet α∈{0.1, 0.5, 1.0} + geographic splits; 10 clients, 200 rounds | noniid-splits.md |
| **6.2 Baselines** | 14 baselines: FedAvg, Krum, Median, TrimmedMean, Bulyan, FLTrust, FoolsGold, RFA, DP-FL (ε=8), FLDetector, DP-FedAvg (ε=4,1), Clipped Median, Multi-Krum+TrimmedMean | baselines.md |
| **6.3 Ablation Configurations** | 15 configs: single-layer, pairs, full, none, cascade_fixed, oracle, τ_Δ sweep, W×τ_Δ heatmap, warm-up skip, empty pool, RCC | ablation-study.md; **S4** |
| **6.4 Metrics** | ASR, Savings curves (FN:FP 10:1–100:1), Precision@Recall 80/90/95, Honest FPR, Detection Lag, FPR_autocor, MCFF, AUASR | fraud-metrics.md; **S10-honest-fpr-metrics** |
| **6.5 Expected Results** | Table 1: ASR per defense × attack × α; Table 2: Ablation breakdown; Table 3: Savings at 100:1 cost ratio | ablation-study expected-tables; estimated from design reasoning |
| **6.6 Statistical Plan** | 5 seeds per config; 95% CI reporting; paired t-tests vs best baseline | fraud-metrics §4 |

**⚠️ Candid note:** These results are **expected based on design reasoning** from the cascading error analysis (S1 convergence bound). Experimental validation is required and planned on cloud infrastructure.

---

### §7 Analysis & Formal Guarantees (1,000–1,500 words)

**Section Goal:** The formal results that support the design — cascade bound, convergence neighborhood, fairness floor.

| Subsection | Content | Source |
|------------|---------|--------|
| **7.1 Cascade Error Propagation** | Stewart perturbation theorem bound; gated FPR accumulation ≤ 1.6%; interpretation note on confident-rejection vs raw-flag FPR | S1-cascade-analysis §3-5 |
| **7.2 Convergence of τ Dynamics** | Fixed-point analysis; Lipschitz continuity L < 1 for convergence; neighborhood size O(η·σ_attack) | S2-convergence-proof §3-6 |
| **7.3 Fairness Guarantee** | Reputation steady-state floor R_SS = 0.85; restoration rate 0.01; max consecutive flags bounded by γ | S7-fairness-blind-spot §3-4; **S10-honest-fpr-metrics** |
| **7.4 Privacy-Robustness Tension** | CAP framework (confidentiality, availability, privacy) 3-layer trust; DP ablation at ε∈{∞,8,4,1} | **S5-privacy-model-strengthen** |

**Note:** These are design-stage formal analyses — bounding arguments, not full proofs. Honest about what's proven vs. heuristic.

---

### §8 Regulatory & Ethical Considerations (1,000–1,500 words)

**Section Goal:** Address the cross-disciplinary gaps identified by Perspective and Domain reviewers.

| Subsection | Content | Source |
|------------|---------|--------|
| **8.1 GDPR Compliance** | Gradient-as-personal-data (Nowak decision); DPIA mandatory; Art.22 automated decisions; joint-controller vs. processor | S8-regulatory-corrections §2; Perspective report §2.1 |
| **8.2 SR 11-7 Model Validation** | Ongoing monitoring cycle; governance triggers; concept drift detection; out-of-tolerance thresholds | **S6-sr11-7-validation**; Domain P2 |
| **8.3 Fairness Regulation** | ECOA, FCRA compliance; per-subgroup honest FPR monitoring; FPR_autocor as fairness signal | fairness-analysis.md; S7-fairness-blind-spot; S10 |
| **8.4 AML/CFT Override** | SAR filing obligations when defense fails; SAR_override config flag | S8-regulatory-corrections §3 |
| **8.5 Cross-Jurisdictional Conflict** | GDPR ↔ GLBA ↔ APRA tension; Schrems II transfer impact assessments | S8-regulatory-corrections §4; Perspective §2.2 |
| **8.6 Operational Considerations** | Override process; consortium governance; false-positive appeal path; cold-start protocol | Domain P2; S6-sr11-7-validation §5 |

**Key improvement:** This entire section is new — requested by Perspective/DA reviewers and absent from original draft.

---

### §9 Discussion & Limitations (800–1,000 words)

| Content | Source |
|---------|--------|
| Experimental validation pending (design-stage — honest admission) | EIC report |
| Server compromise as future work (TEE path) | S3-server-compromise |
| Cold-start vulnerability window | Domain P1; Methodology C4 |
| Synthetic identity fraud not addressed | Domain P1 |
| Reputation window tuning required | Methodology C3 |
| SecAgg incompatibility acknowledged | privacy-model §5; Perspective §1.2 |
| Updated related work needed (2023-2025) | DA minor issues |
| Scalability analysis pending (30-50 clients) | DA minor issues |

---

### §10 Conclusion (300–400 words)

Standard restatement. Focus: **statelessness is the blind spot, gated cascade is the solution, experimental validation is next.**

---

## Overall Structure

| Section | Words | Est. Pages (TIFS 2-col) | Source Documents Mapped |
|---------|-------|------------------------|----------------------|
| §1 Introduction | 1,000 | 1.0 | Draft + revised-argument-flow |
| §2 Related Work | 1,200 | 1.2 | baselines.md, Draft §5.5 |
| §3 Threat Model | 1,500 | 1.5 | Revised §3 + S3 + S8 |
| §4 Proposed Framework | 3,000 | 3.0 | 10 spec docs + S1 + S2 + S7 |
| §5 Attack Models | 1,000 | 1.0 | attacker-design + S9 |
| **§6 Experimental Design** | 2,000 | 2.0 | ablation + fraud-metrics + noniid + S4 + S10 (14 baselines, 15 ablations) |
| §7 Analysis & Guarantees | 1,500 | 1.5 | S1 + S2 + S5 + S7 |
| §8 Regulatory & Ethics | 1,500 | 1.5 | S5 + S6 + S7 + S8 |
| §9 Discussion | 1,000 | 1.0 | 5 reviewer reports |
| §10 Conclusion | 400 | 0.5 | — |
| **Total** | **12,100** | **~12-14pp** | **21 spec docs** |

---

## Evidence Map: Which Doc → Which Section

| Source Document | Contributes To |
|----------------|---------------|
| Draft (original) | §1, §2, §3, §5 |
| Revised argument flow | §1, §3 |
| R1: spectral/non-IID reframe | §1, §4.3 |
| R2: adaptive threshold spec | §4.5 |
| R3: privacy model | §7.4, §8.1 |
| R4: attacker design | §3.4, §5 |
| R5: fraud metrics | §6.4 |
| R6: baselines | §6.2 |
| R7: non-IID splits | §6.1 |
| R8: ablation study | §6.3, §6.5 |
| R9: explainability | §8.2, §8.3 |
| R10: fairness analysis | §8.3 |
| S1: cascade analysis | §4.8, §7.1 |
| S2: convergence proof | §4.6, §7.2 |
| EWMA baseline specification | §4.7 |
| S3: server compromise | §3.3, §3.6, §9 |
| S4: ablation controls | §6.3 |
| S5: privacy model strengthen | §7.4, §8.1 |
| S6: SR 11-7 validation | §8.2 |
| S7: fairness blind spot | §4.4, §7.3, §8.3 |
| S8: regulatory corrections | §8.1, §8.4, §8.5 |
| S9: A2-adaptive | §5 (future) |
| S10: honest FPR metrics | §6.4, §7.3 |

Ready for user confirmation before Phase 3 (Argumentation).
