# Peer Review Report — R3 (Perspective/Holistic)
**Paper ID:** TIFS-2026-XXXX
**Title:** "Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework"
**Reviewer:** Peer Reviewer 3 (Perspective/Holistic Reviewer — meta-level evaluation)

---

**Score: 30/100 | Recommendation: Reject**

---

### 1. Summary

This design-stage specification proposes a reputation-gated cascade defense for FL-based fraud detection, targeting the underexplored interaction between temporal non-stationarity and poisoning resilience. While the problem framing is well-motivated and the architectural ambition is apparent, the paper as submitted is not acceptable for IEEE TIFS. The Batch 1 reviews collectively surface three critical categories of concern: fatal formal proof gaps (R1), domain realism failures (R2), and premature evidential status (EIC). My holistic review adjudicates these, identifies additional issues missed by both batch reviewers, and assesses the viability of the proposed path forward.

### 2. Adjudication of Batch 1 Findings

**R1 vs. R2 — Proof Rigor vs. Domain Governance**

The most critical tension lies between these two reviews. R1 demonstrates that Theorem 1 (Reputation Floor) is not resistant to a scaling attack, that the Lipschitz convergence proof assumes independence between reputation weights and model parameters that is violated by design, and that the Stewart bound requires IID data the paper explicitly claims to transcend. R2 argues the threat model is misaligned (Sybil vs. Insider Collusion), the governance structure is underspecified, and the validation plan neglects regulatory realities.

I adjudicate firmly in favor of **R1's critique as the binding constraint**. R2's concerns about consortium governance, incentive design, and regulatory compliance are significant for eventual deployment but are *implementation barriers*. R1's critique strikes at the *mathematical foundation* of the defense. If the reputation filter can be bypassed by a multiplicative scaling factor, the entire "layered defense" collapses into a single brittle filter with a known bypass. No amount of legal structure or AML narrative can rescue a paper claiming formal guarantees that do not hold. R2's governance critique complements R1: an architecture with a "trusted aggregator" inspecting raw gradients *must* be irrefutably provable, because it has already sacrificed the privacy guarantee that motivated FL in the first place. If the proofs are broken, the trust/privacy trade-off becomes indefensible.

**EIC's 40/100 and the "Resubmit Experiments" Path**

The EIC's characterization — "beautiful blueprint, not archival contribution" — is accurate in spirit but risks being overly optimistic in its prescription. Running experiments on static synthetic datasets will not resolve the non-stationarity contradiction the EIC themselves identified. Furthermore, experiments cannot patch a broken proof. The path forward must therefore prioritize theoretical repair over empirical volume. The projected ASR (0.25) flagged by R1 remains irreconcilable with the formal claim of full attacker exclusion, and this inconsistency must be resolved *before* any experimental campaign.

### 3. Missed Issues — What No Batch Reviewer Raised

Three meta-level issues cut across the entire submission and were not adequately addressed by Batch 1:

**A. The Trust-Privacy Paradox**

None of the reviewers fully articulated that a "trusted aggregator" inspecting raw gradients eliminates the primary privacy justification for FL. In a consortium of N=10 KYC'd institutions, the system is functionally equivalent to sharing raw transaction data with a central processor, which likely violates the same data-sharing regulations (GDPR, GLBA) the FL approach was intended to avoid. For IEEE TIFS — a venue fundamentally concerned with security and privacy — the paper must explicitly justify why this architecture is preferable to a centralized log analyzer with differential privacy. The current submission reads as FL-in-name-only.

**B. The Non-Stationarity Contradiction**

The paper's motivation rests on temporal concept drift. The central Stewart bound assumes stationary covariance. The validation plan relies on static datasets with no drift component. The entire contribution travels from a non-stationary premise, through a stationary proof, to a stationary evaluation. This is not merely an empirical gap — it is a conceptual inconsistency that must be resolved in the formalism itself. No Batch 1 reviewer adequately connected these three dots.

**C. Defense Depth — One Filter is Not a Layer**

The architecture is termed a "multi-layer defense," but functionally it consists of a single real-time reputation filter (cosine similarity to peer mean) with a fallback to empty-client-pool. The latter is mentioned but not analyzed. A genuine layered defense would operate on orthogonal principles (e.g., geometric median + trimmed mean + reputation), providing coverage when one filter fails. The current stack has no defense-in-depth against the scaling attack R1 identified: if the reputation filter is bypassed, the aggregator has no second line of defense. The paper misnames its architecture, inflating the contribution.

**D. Real-Time Feasibility Gap**

Millions of credit card transactions per hour require inference and scoring at sub-second latency. Gradient computation, cosine comparison across N clients, and median estimation impose O(N²·d) overhead per round. No discussion of computational budget exists. For a paper targeting a real-time fraud setting, this omission is critical.

### 4. Evaluation of the Design-Stage Framing

IEEE TIFS does not have an established "design-stage specification" track. The paper is being reviewed under standard criteria requiring completed, validated contributions. A design-stage framing can be appropriate if the paper delivers a complete, self-contained theoretical core (e.g., a new cryptographic protocol with formal proofs). The present paper attempts this, but the proofs contain unfixable-in-minor-revision gaps (scaling attack on Theorem 1, Lipschitz interdependence).

For the framing to work, the formal analysis must be *airtight*, and the empirical plan must address the core theoretical assumptions. The paper currently fails both tests. It occupies an uncomfortable middle ground: too technically incomplete for journal acceptance, yet too ambitious in its claims for a workshop.

### 5. Recommendation and Path Forward

**Score: 30/100. Reject.**

This paper cannot be published in its current form. The formal guarantees are unsupported (R1), the architecture sacrifices FL's privacy promise without commensurate theoretical rigor (R3), and the validation plan contradicts the motivating problem (EIC/R2).

**Appropriate Path Forward:**

1. **Fix the formal core first.** Theorem 1 must be proven against the scaling attack, or the claims must be explicitly weakened to provably correct bounds. The Lipschitz convergence proof must model the mutual dependence between reputation weights and gradient parameters.

2. **Resolve the trust model.** Either (a) adopt SecAgg-compatible reputation (e.g., encrypted similarity protocols) and prove the system still works, or (b) explicitly frame the contribution as a *centralized* robust aggregation defense and abandon the privacy framing.

3. **Align validation with motivation.** Replace or supplement PaySim with a dataset that exhibits temporal drift (e.g., real credit card transaction streams with timestamps, or a generative temporal simulator). The Stewart bound must be adapted to non-stationary covariance, or the paper must abandon the stationarity assumption.

4. **Adopt R2's threat model recommendations.** Replace Sybil attacks with Insider Collusion and Aggregator Compromise, which are realistic for a KYC'd N=10 consortium.

Without addressing the proof gaps, any number of experimental trials will fail to establish the intended contribution. The authors are advised to pause empirical work and invest heavily in repairing the theoretical architecture. The current submission represents a promising *problem formulation* but not a defensible *solution contribution*.
