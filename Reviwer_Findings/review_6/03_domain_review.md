# Peer Review Report

## Manuscript Information
- **Title**: Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework
- **Manuscript ID**: [Not provided — design-stage specification]
- **Review Date**: 2026-07-11
- **Review Round**: R1

---

## Reviewer Information

### Reviewer Role *
Peer Reviewer 2 (Domain)

### Reviewer Identity *
Financial fraud detection ML practitioner with 10+ years of experience deploying production fraud models at tier-1 financial institutions, including cross-silo FL consortium design and regulatory model validation (SR 11-7, GDPR, ECOA/FCRA).

### Review Focus *
This review evaluates the attack model realism for real fraud rings, the completeness of baseline defenses against practical fraud-specific threats, the accuracy of the regulatory framework analysis (GDPR Art.22, SR 11-7, ECOA/FCRA), and the practical feasibility of deploying the proposed gated cascade in a regulated financial consortium. Because the paper is a design-stage specification without experimental results, the review focuses on whether the design choices are defensible and the planned experiments would validate the claims.

---

## Overall Assessment *

### Recommendation *
- [ ] **Accept** — Can be published directly, only minor formatting changes needed
- [ ] **Minor Revision** — Minor revisions needed, no re-review after revision
- [x] **Major Revision** — Substantial revisions needed, re-review required after revision
- [ ] **Reject** — Not suitable for publication in this journal

### Confidence Score *
**4** — Mostly within my area of expertise, high confidence.

### Summary Assessment *
This design-stage specification proposes a three-layer gated cascade defense (norm/cosine filtering, spectral PCA, temporal reputation scoring) for cross-silo FL fraud detection, targeting the "statelessness blind spot" of existing Byzantine-robust aggregators. The paper identifies a genuine and underexplored problem — temporally-adaptive fraud rings that grind defenses over multiple training rounds — and the cascade architecture is well-motivated with complementary detection principles. The regulatory analysis is admirably thorough for a design-stage paper, correctly addressing GDPR Art.22 training-vs-inference separation and SR 11-7 model risk management requirements.

However, the paper has several significant weaknesses that require major revision. The attack models, while thoughtfully structured, rely on rigid phase schedules and collusion thresholds (M ≥ 3) that do not reflect the opportunistic, adaptive behavior of real fraud rings. The planned evaluation on synthetic Gaussian data (d=50) cannot capture the feature complexity, class imbalance, and temporal dynamics of real credit card transactions (d=200–500, high-cardinality categoricals, 0.1–3.5% fraud rate). The 200-round warm-up period leaves a critical vulnerability window insufficiently addressed. And the baseline set omits several practical fraud-specific defenses (SignSGD, Zeno, trimmed-mean variants with momentum-based exclusion) that would strengthen the empirical claims. A major revision should address these issues before the experimental phase begins.

---

## Strengths *

### S1: Clear identification of the statelessness blind spot *
The paper formalizes (Section III-B, p. 3) a genuinely overlooked vulnerability: stateless per-round aggregators (Krum, Median, Trimmed Mean, Bulyan) are blind to temporally-corrupted update sequences. The formalization using detection indicator sequences f_t and memory-k statistics S_t (Equation 2) is clean and persuasive. This framing correctly identifies that fraud rings — unlike the random Byzantine faults studied in the robust FL literature — operate in campaigns with probe-adapt-retreat cycles that cannot be detected round-by-round. As a fraud practitioner, I confirm this aligns with observed organized fraud behavior: rings test limits, withdraw when detected, and re-emerge with modified tactics.

### S2: Well-motivated cascade architecture with complementary detection principles *
The division-of-labor design (Section IV-A, pp. 5–6) is sound. Layer 1 (norm/cosine) for trivial-attack rejection, Layer 2 (spectral PCA) for coordinated collusion, and Layer 3 (sliding-window reputation) for slow adaptive poisoning — each addresses a distinct threat class that the others miss. The gating mechanism (Algorithm 1, p. 9) avoids the selection-bias problem of ensemble fusion. The reputation forgetting mechanism with steady-state floor R_SS = 0.85 (Section VI-D, p. 19) is an operationally essential feature that prevents permanent exclusion of honest banks after transient anomalies — a practical concern that many academic papers miss entirely.

### S3: Theoretically rigorous FPR bound under stationary covariance *
The cascade FPR bound of ~1.6% (Theorem 1, Section VI-A, pp. 15–16) derived via Stewart's perturbation theorem and the Davis-Kahan sinΘ characterization of drift-affected degradation (Corollary 1.1) provides a theoretically grounded operating envelope. The eigenvalue-gap-dependent drift bound (ε_drift / gap) and the practical recommendation P ≤ gap / ε_drift for PCA recomputation interval give actionable design guidance. This level of formal analysis is rare in design-stage papers and strengthens confidence that the cascade would not produce excessive false declines in deployment.

### S4: Sophisticated regulatory framework analysis *
The regulatory mapping (Section VII, pp. 20–26) is the most comprehensive I have seen in an FL fraud detection paper. Key strengths: (a) correct identification of the GDPR Art.22 training-vs-inference separation; (b) the SR 11-7 mapping table (Table 8, p. 22) with specific monitoring metrics (FPR autocorrelation, MCFF, reputation distribution); (c) the cross-jurisdictional analysis of TEE key management geography and the CLOUD Act / Schrems II tension (Section VII-G, p. 24); (d) the practical ECOA adverse-action mitigation via surrogate SHAP with local fidelity audit (Section VII-I, p. 24). The paper correctly recognizes that proxy-based explanations are "estimates, not legally binding explanations" — a necessary caveat that shows regulatory maturity.

### S5: Transparent disclosure of limitations and bootstrap vulnerabilities *
The paper explicitly acknowledges the warm-up vulnerability (Section IV-B-4, p. 11: "The window W_h = 200 rounds remains a vulnerable period") instead of glossing over it. The circular bootstrap resolution (TEE, geometric median robust estimator, blinding noise) is well-specified even if not fully satisfactory. The red-team assessment table (Table 10, p. 23) with residual risks is a welcome feature. The honest disclosure that the cascade "cannot detect adversaries who constrain perturbations strictly within [the envelope]" (Section V-F, p. 13) and the reframing as an "early-warning alarm for high-magnitude or structurally anomalous updates" (Section V-G, p. 14) shows intellectual honesty.

---

## Weaknesses *

### W1: Attack models lack the opportunistic, adaptive behavior of real fraud rings
**Problem**: The A2 Gradient Grinding attack (Section V-B, pp. 12–13) uses a rigid 4-phase schedule (Burn-in rounds 1–19, Subliminal 20–59, Active 60–99, Cooldown 100–120) with deterministic transitions. Real fraud rings do not follow fixed-duration campaign schedules — they adapt in real time based on detection feedback, changing tactics within 2–3 rounds of sensing resistance. The paper's own A6 cascade-aware adversary (Section V-F) acknowledges this but treats A6 as the "operational envelope" rather than the primary attack model. The fixed schedule means the experiments would evaluate the cascade against a predictable opponent, not a realistic one.

**Why it matters**: A fraud ring that shortens or extends phases based on real-time probing (e.g., aborting an attack after 2 rounds if the defense tightens) would present a harder detection problem than the fixed-schedule A2. The paper's projected ASR bounds (Table 6, p. 15) may significantly underestimate real-world attack success.

**Suggestion**: (1) Make A6 (the adaptive adversary) the primary attack model rather than a separate threat — reframe A2 as a simplified special case of A6. (2) Replace the fixed 4-phase schedule with a Markov decision process model where the attacker's phase transitions depend on observed defense state (θ_high, θ_low, R_i). (3) Add an experiment where the attacker shortens the active phase in response to reputation drops.

**Severity**: Major

### W2: Collusion threshold M ≥ 3 for A3 is too high; no treatment of 1–2 attacker scenarios
**Problem**: The A3 Spectral-Matching Collusion requires M ≥ 3 malicious clients (Section V-C, p. 13) because the spectral layer uses k=3 principal components. The paper states "For m ≥ 3, this component becomes detectable in the residual of the k=3 subspace" — but this explicitly means attacks with 1–2 colluding banks go undetected by L2. In a 10-bank consortium, a single compromised bank (e.g., a community bank with weak security that a fraud ring takes over) is the most plausible attack scenario, not 3+ banks. The A4' bound m ≤ ⌊N/3⌋ (p. 13) is justified as "unlikely under regulatory oversight" but regulatory oversight (KYC, AML, ongoing due diligence) primarily catches money laundering, not gradient manipulation by insiders.

**Why it matters**: The paper's projected ASR bounds assume that L2 handles A3 and A4', but if the most realistic attack is a single compromised bank, L2 provides zero protection for that scenario. The overall defense then collapses to L1 + L3, which the paper projects at ASR ≤ 0.45 (C6, Table 5, p. 14) — significantly weaker than the full defense's ≤ 0.35.

**Suggestion**: (1) Add explicit analysis of 1–2 attacker scenarios and project which layers detect them. (2) Justify the M ≥ 3 threshold with empirical evidence (or planned experiments) showing that spectral detection fails for m=1,2. (3) Revise the A4' bound: cite specific KYC regulatory requirements (e.g., 31 CFR 1020.220 Customer Due Diligence, FATF Recommendation 10) that would make ≥3 insider collusion detectable, rather than the vague "unlikely under regulatory oversight."

**Severity**: Critical

### W3: Synthetic Gaussian data (d=50) is fundamentally inadequate for validating fraud-specific claims
**Problem**: Section VI-C (p. 17) specifies that the benign-drift control experiment and formal bound validation use "synthetic Gaussian data (d=50, N=10, 20 independent trials)." Real credit card fraud transaction data has: dimensionality d=200–500 (IEEE-CIS has 434 features after encoding), severe class imbalance (0.1–3.5% fraud rate), high-cardinality categoricals (merchant IDs, MCC codes, ZIP+4 codes with 10,000+ levels), heavy-tailed feature distributions, temporal autocorrelation (fraud surges follow data breach announcements), and non-Gaussian feature correlations (e.g., transaction amount × merchant category interactions). None of these properties are captured by d=50 Gaussian data.

**Why it matters**: The paper's theoretical FPR bound (Section VI-A) assumes Gaussian-distributed gradient residuals. Real gradient distributions from tabular fraud data on neural networks are not Gaussian — they have heavier tails, non-zero skew, and feature-specific variance structures that would invalidate the Stewart bound's concentration inequality (Equation 24). The claim "σ_R,i ≈ 0.015" was measured on a "single toy logistic regression simulation (d=100)" (Section IV-B-3, p. 10) — this is one data point from a toy model, not a reliable design principle.

**Suggestion**: (1) Run ALL experiments on IEEE-CIS (d=434) and European Credit Card (d=30 PCA) as primary datasets — not just the main evaluation but also the bound validation. (2) If synthetic data is necessary for computational tractability, use a more realistic generative model (e.g., CTGAN or DoppelGANger trained on real fraud data) rather than isotropic Gaussians. (3) At minimum, concede that the d=50 Gaussian results are purely illustrative and should not be interpreted as validation of real-world FPR bounds. (4) Report the gradient covariance eigenvalue spectrum from the IEEE-CIS experiments to validate the "gap" assumptions in the Davis-Kahan bound.

**Severity**: Critical

### W4: 200-round warm-up period creates an operationally unacceptable vulnerability window
**Problem**: The per-client baselines (R̄_i, σ_R,i, RCC_i^(base)) are calibrated during an initial W_h = 200-round "trusted" warm-up period (Section IV-B-4, pp. 10–11) during which the defense is not operational. The paper acknowledges this is "approximately 1–2 weeks of daily training" — but in production, many fraud detection models retrain daily or even intra-day (streaming updates). At daily retraining, 200 rounds = ~7 months. A fraud ring that compromises a bank during the first 7 months of consortium operation can poison the baseline and evade L3 detection indefinitely.

**Why it matters**: The mitigations (TEE with signed code, geometric median robust estimator, blinding noise) do not solve the root problem: they reduce the risk of baseline poisoning but do not eliminate it. A determined adversary who controls even one client during the warm-up can inflate their baseline perturbation before the attack begins. The geometric median estimator tolerates "up to 50% corrupted rounds" — but one compromised bank in a 10-bank consortium is 10%, well within that tolerance, meaning a single attacker can still bias the baseline.

**Suggestion**: (1) Add a warm-up-free alternative: use population-level statistics (median of medians across clients, cross-validated outlier detection on initial rounds) that do not require a trusted calibration period. (2) Report the minimum safe warm-up length under realistic attack probabilities — 200 rounds is stated as a default but never justified. (3) Add a zero-day attack experiment where the attacker is present from round 1 and measure the resulting ASR inflation.

**Severity**: Critical

### W5: Baseline set omits practical fraud-specific defenses
**Problem**: The fourteen baselines (Table 3, pp. 13–14) cover the standard Byzantine-robust FL literature but omit several defenses relevant to fraud detection: (1) SignSGD / majority vote — simple binary aggregation that trivially defeats gradient-magnitude attacks; (2) Zeno / Zeno++ (Xie et al., 2019) — client selection via stochastic validation checks that is naturally stateful because it tracks per-client historical scores; (3) Momentum-based trimming (e.g., coordinate-wise trimmed mean with exponential moving average of recent gradients) — a natural stateful extension of Trimmed Mean; (4) RSA (Byzantine-Robust SGD, Data & Diggavi, 2019) — uses coding-theoretic redundancy sharing.

**Why it matters**: The paper claims that "no existing study evaluates robust aggregation or poisoning defenses in the fraud detection context" (p. 2) and that existing methods are stateless. Including Zeno (which uses a historical scoring mechanism) or momentum-based trimming would test whether simple stateful extensions of existing methods approach the cascade's performance at lower complexity. Without these, the paper overclaims the novelty of "statefulness."

**Suggestion**: (1) Add Zeno (or Zeno++) and momentum-based Trimmed Mean as baselines B15 and B16. (2) Include SignSGD as a lower-complexity alternative to L1 — if it performs comparably, the cascade may be over-engineered. (3) Clarify the distinction between "stateful-by-design" (FLDetector tracks history) and "stateful-only-with-hacks" (Krum cannot be made stateful).

**Severity**: Major

---

## Detailed Comments *

### Title & Abstract
- The title is accurate but verbose. Consider "A Temporally-Aware Gated Cascade Defense for Federated Fraud Detection" — shorter and captures the contribution.
- The abstract correctly identifies the statelessness blind spot and summarizes the three-layer architecture. However, it is too dense with formal references (Stewart's theorem, Davis-Kahan sinΘ, fixed-point analysis) for a domain audience. Consider deferring technical machinery to the body and keeping the abstract at the architectural level.

### Introduction
- The fraud-specific poisoning threat description (Section I-A, p. 2) is excellent and correctly identifies the incentive-driven, accuracy-preserving nature of fraud attacks vs. untargeted Byzantine faults.
- The statelessness blind spot formalization (Section I-B) is clear and persuasive.
- Missing: a concrete example or case study of a real fraud ring operating across institutional boundaries (e.g., the 2014–2015 Carbanak group that compromised 100+ banks). This would strengthen the motivation significantly.

### Literature Review / Related Work
- The gap synthesis table (Table 1, p. 4) is useful but oversimplifies — e.g., FoolsGold was specifically designed for collusion detection in FL and has a similarity-based mechanism that is not purely "stateless" as defined (it aggregates historical gradient similarity).
- The claim that methods "inspecting per-client gradients (FLTrust, FoolsGold, FLDetector) are incompatible with Secure Aggregation" (p. 4) is correct but worth noting that FoolsGold operates on cosine similarity which can be computed under SecAgg via MPC in principle (at high cost).
- Missing reference to Chen et al. (2023) "DEFL: Defending against Collusion Attacks in Federated Learning" which explicitly addresses collusive fraud with temporal analysis.

### Attack Models (Primary concern for R2)
- See W1 and W2 above. The attack taxonomy is well-structured but the implementation details need fundamental revision.
- The A4' insider collusion bound m ≤ ⌊N/3⌋ needs stronger justification. The paper says "a consortium of 10 banks with ≥4 colluding members is unlikely under regulatory oversight" — but the US OCC's "Risk Management of Outsourcing" bulletin and the EBA's outsourcing guidelines focus on operational risk, not collusion detection. Collusion among 3 banks in a 10-bank consortium is a realistic threat (e.g., regional banks in the same geographic area facing similar fraud patterns).
- The information-theoretic limits discussion (Section V-G, pp. 14–15) is welcome but the KL divergence bound (Equation 14) assumes the adversary knows P_honest exactly. In practice, the adversary has only empirical estimates and samples, which broadens the typical set and makes detection possible even for bounded perturbations. This caveat should be stated.

### Proposed Framework
- The cascade design is well-architected. The L2 spectral PCA for coordinated attacks (Section IV-C) is the most novel contribution and is well-motivated.
- The L3 reputation anomaly score combines three signals with fixed weights 0.4/0.4/0.2 (Equation 11). In practice, these weights would need to be calibrated per consortium and would drift over time. The paper should address whether the weights are learned or fixed.
- The sliding-window PCA recomputation every P rounds (Section IV-C, p. 7) is sensible but the drift bound P ≤ gap / ε_drift is circular: you need to know ε_drift to set P, but ε_drift is what you're trying to bound. Recommend an adaptive recomputation trigger instead (e.g., recompute when the reconstruction error of the median update exceeds 1.5× its running mean).
- The Shapley contribution scoring (Section IV-F, pp. 11–12) is computationally expensive (1,000 forward passes every 50 rounds) and its benefit over simple reputation weighting is unclear. The paper should either justify the added complexity with a concrete failure case of reputation-only weighting, or move it to "future work."

### Experimental Design (Design-stage, but critical for planning)
- See W3 and W4. The experimental design is thorough in ablation configurations (15 configurations, Table 5) but relies on the wrong data.
- The temporal cross-validation split (expanding-window, Section VI-D, p. 14) is appropriate for the temporally-aware claim. Good.
- The trial protocol (10 independent seeds, three sources of randomness) is statistically sound. Good.
- However, the 50–100 GPU-hour estimate for d=434, N=10, 3-layer MLP suggests either a massive hyperparameter sweep or very inefficient implementation. For context: one training run (200 rounds × 10 clients × 5 epochs × ~600K transactions) on a single RTX 4090 takes ~4 hours. With 10 seeds × 14 baselines × 15 ablations = ~2,900 runs, that would be ~12,000 GPU-hours, not 50–100. The authors should re-estimate their compute budget.

### Regulatory Framework
- See S4. The regulatory analysis is generally excellent and thorough.
- One omission: SR 11-7 §III.C requires model validation to be performed by a "qualified party independent of model development." The paper maps monitoring and governance requirements but does not address who validates the cascade itself or how the validation is structured. This is a significant gap for a system that would be deployed in US-regulated banks.
- The ECOA adverse-action discussion (Section VII-D, p. 22) is correct but incomplete: ECOA §615(a) requires the creditor to provide "specific reasons" for a decline, not just a score or flag. A SHAP-based explanation showing which features drove the decline may satisfy this, but the paper should cite the Interagency Fair Lending Examination Procedures and discuss how the surrogate model's fidelity is validated for fair lending compliance.
- The GDPR Art.25 (data protection by design) mapping (Section VII-A, p. 21) correctly identifies the TEE + DP architecture. However, Art.25 requires data minimization — the paper does not address whether processing gradients for all clients (rather than a sampled subset) violates this principle.

### Discussion & Limitations
- The stakeholder analysis (Section VIII-D, pp. 23–24) is one of the paper's strongest sections, correctly identifying incentive misalignments between regulators, member banks, and customers.
- The limitations section (Section VIII-E, p. 24) is comprehensive and honest.
- Missing: discussion of latency constraints. Real-time credit card authorization decisions require sub-100ms inference. While the paper focuses on training (not inference), the cascade's per-round latency (Table 4 estimates ≤0.8s for full defense) could become a bottleneck if the training cadence is intra-day or the consortium scales beyond N=10.

---

## Questions for Authors *

1. **Single-attacker scenarios**: Your spectral layer (L2) uses k=3 PCA components and requires M ≥ 3 colluding attackers for detection. What is the projected ASR of a single compromised bank running A2 (grinding) with an adaptive schedule, relying only on L1 + L3? This is the most realistic attack scenario in a regulated consortium. Do your projected bounds account for this gap?

2. **Warm-up vulnerability quantification**: You acknowledge that W_h = 200 rounds "remains a vulnerable period" (p. 11). Can you quantify the probability that a single attacker present during warm-up can inflate their baseline sufficiently to evade L3 detection indefinitely? What is the minimum W_h such that the geometric median robust estimator provides 95% confidence in baseline integrity under a 10% attack rate?

3. **Gaussian data limitation**: Your formal FPR bound and drift characterization rely on synthetic Gaussian data (d=50). Are you confident that the eigenvalue gap (gap = λ_k − λ_{k+1}) assumptions hold for the IEEE-CIS dataset's gradient covariance? Will you validate the Davis-Kahan sinΘ bound empirically on IEEE-CIS before claiming the 1.6% FPR bound applies to real fraud data?

4. **SR 11-7 independent validation**: Who will perform the independent model validation of the cascade itself? An SR 11-7-compliant bank requires the model validation function to be structurally independent from the model development function. Does your governance framework (Section VII-F) address this, or is the cascade intended to be deployed without the independent validation that regulated entities require?

---

## Minor Issues

### Language / Grammar
- p. 2, Section I-B: "the attacker can probe thresholds by observing f_t directly across rounds" — this assumes the attacker can observe f_t, but per-round detection results may not be observable if the server does not broadcast them. Clarify the information asymmetry.
- p. 7, Equation 14: "D_KL(P_adv ∥ P_honest)" — the KL divergence is not symmetric and the direction matters. Using P_adv as the first argument suggests the "forward" KL, but the detection bound (Equation 14) is typically stated with P_honest as the reference. Verify the direction.

### Citation Format
- Several citations use \textit vs \emph inconsistently (e.g., \textit{et~al.} in Section II-A vs. \emph in Section II-B).
- The Schrems II citation (Schrems II, p. 21) should include the full case reference: Judgment of the Court of Justice of the European Union, Case C-311/18, July 16, 2020.
- Missing citation for the Nilson Report (reference [1]): include report number and date.

### Figures and Tables
- Table 6 (Expected ASR bounds, p. 15) has a prominent disclaimer row that breaks the table layout. Consider adding the disclaimer as a footnote rather than a table row.
- Table 4 (complexity, p. 14) estimates "≤0.8s" for the full defense at d=100K parameters. For the planned model (3-layer MLP 256→128→64→1, ~33K parameters), the PCA cost O(Nd²) would be ~10× lower. Clarify whether d refers to features or model parameters and report the expected latency at the actual model size.
- The algorithm float (Algorithm 1) appears before its caption reference in the PDF layout. Add a placement constraint.

### Layout
- The paper uses \resizebox{\columnwidth}{!} for all tables, which on IEEEtran two-column format makes small-font tables. Several tables (Tables 2, 3, 5, 6) would benefit from manual column width optimization to improve readability at the journal's print size.
- Equation 24 (Stewart bound, p. 15) references "δC" but C is not defined in surrounding text. Define C as the condition number or Stewart's constant.

---

## Dimension Scores *

| Dimension | Score (0-100) | Descriptor | Notes |
|-----------|--------------|------------|-------|
| Originality (20%) | 80 | Strong | The statelessness blind spot is a genuinely novel observation for fraud FL. The cascade architecture, while combining known primitives, does so in a novel configuration with formal guarantees. |
| Methodological Rigor (25%) | 55 | Adequate | Strong theoretical analysis (FPR bounds, convergence neighborhoods, Davis-Kahan) but the proposed experiments have critical weaknesses: Gaussian d=50 data cannot validate real-world claims, the attack models are too rigid, and the warm-up vulnerability is not adequately bounded. |
| Evidence Sufficiency (25%) | 30 | Weak | By admission, this is a design-stage paper with no experimental results. Acceptable for a design specification, but the projected ASR bounds (Table 6) are presented with far more precision than the evidence supports. The single datapoint (σ_R,i ≈ 0.015 from one toy simulation) is not evidence. |
| Argument Coherence (15%) | 75 | Strong | The paper is well-structured, the problem-motivation-solution chain is clear, and the formal claims are connected to the architecture. The operational envelope framing (A6) is coherent. |
| Writing Quality (15%) | 70 | Strong | Generally clear and well-organized. Occasionally dense with formal references in non-technical sections. The abstract tries to cover too much ground. |
| Literature Integration (optional) | 65 | Adequate | Good coverage of Byzantine-robust FL and adaptive attacks. Notable omissions: fraud-specific poisoning defenses (Zeno, SignSGD), Chen et al. (2023) on collusive fraud FL, practical fraud consortium case studies. |
| **Weighted Average** | **58** | **Major Revision** | The design concept and theoretical foundations are strong, but the experimental plan has critical flaws (data, attacks, warm-up) that must be addressed before the validation phase. The paper should be revised substantially before the experiments begin to ensure the experiments test realistic scenarios. |

---

## Summary for Authors

This is a bold and intellectually honest design-stage specification that tackles a genuine and underexplored problem: temporally-adaptive fraud rings in cross-silo FL. The cascade architecture is well-motivated, the formal FPR analysis is rigorous, and the regulatory analysis is the most thorough I have seen in this space. The paper's strengths — clear problem identification, complementary layer design, honest limitation disclosure — make it a valuable contribution to the literature.

However, the paper cannot proceed to experimental validation in its current form. Three critical issues must be resolved before the experimental phase:

1. **Attack realism**: The fixed 4-phase schedule (A2) must be replaced with an adaptive adversary (A6 as primary). The M ≥ 3 collusion threshold must be justified or the 1–2 attacker gap explicitly bounded.

2. **Data adequacy**: The synthetic Gaussian d=50 experiments cannot validate real-world claims. The planned experiments must use IEEE-CIS (d=434) as the primary evaluation dataset, with the Gaussian data relegated to illustrative sanity checks only.

3. **Warm-up vulnerability**: The 200-round vulnerability window must be addressed with either a warm-up-free alternative calibration or a quantitative bound on baseline poisoning risk. A zero-day attack experiment is essential.

I look forward to seeing the revised specification and, eventually, the experimental validation on cloud infrastructure.
