# Peer Review Report — Domain Review

## Reviewer Information
- **Role**: Peer Reviewer 2 (Domain)
- **Identity**: Senior fraud detection architect with 15+ years of experience designing and deploying AML and payment fraud models at top-tier financial institutions. Extensive experience with cross-institution consortium data initiatives (Early Warning Services, RTP networks), model risk management under SR 11-7, and fraud ring pattern analysis.
- **Review Focus**: Evaluating the operational feasibility, threat realism, and regulatory validity of the proposed gated cascade defense in the specific context of credit card fraud detection. Assessing whether the claimed gap between stateless defenses and temporally-adaptive poisoning is operationally significant and whether the design can survive real-world banking constraints.

---

## Overall Assessment

### Recommendation: Major Revision
### Confidence Score: 4 (High)

### Summary Assessment
This paper tackles a genuinely important problem: hardening federated learning (FL) against adaptive poisoning in the high-stakes domain of credit card fraud detection. The central concept of a "grinding attack"—a temporally-adaptive poisoning schedule designed to evade stateless defenses—is well-motivated and aligns with the structured, patient nature of sophisticated fraud rings. The proposed three-layer gated cascade (norm/cosine, spectral PCA, EMA reputation) offers a logically sound defense-in-depth architecture.

However, as a design-stage paper, significant gaps between the theoretical framework and operational reality must be addressed before this work is suitable for IEEE TIFS. The threat model relies on a strong Kerckhoffs assumption (adversary knows the full defense architecture but has gradient-only observation) that is difficult to justify in a real banking consortium setting. More critically, the evaluation datasets (IEEE-CIS 2019, ECC 2015) are chronologically mismatched to contemporary fraud patterns, rendering the validated attack surface anachronistic. The N=10 stable consortium assumption ignores the operational churn, latency constraints, and governance challenges that define real-world FL deployments in financial services. The regulatory mapping, while commendable in ambition, oversimplifies the legal weight of AML overrides and model auditability requirements under SR 11-7. A thorough grounding of the experimental design in operational banking constraints is required before publication.

---

## Strengths

1. **Operationally Important Problem Statement:** The intersection of FL security and payment fraud is a critical, underserved topic in the security literature. The core motivation—that fraud rings will actively poison a cross-institution FL model—is timely and well-justified.
2. **Well-Structured Attack Narrative (A2 Grinding Attack):** The four-phase attack schedule (burn-in, subliminal, active, cooldown) is a creative and highly plausible adversarial strategy that closely mirrors the patience and operational security observed in sophisticated fraud ring operations. The phase-specific metrics are well-chosen.
3. **Architectural Soundness of Defense Cascade:** The progression from vector-level (norm/cosine) to spectral (PCA) to temporal (EMA reputation) is logically coherent and represents a genuine defense-in-depth approach. The authors correctly recognize that a single static filter is trivially bypassed by a temporally-adaptive adversary.
4. **Commendable Regulatory Ambition:** The inclusion of GDPR (Art. 4, 5, 22, 28, 35, 44–49), SR 11-7 model validation, ECOA/FCRA fair lending, and AML/CFT shows a genuine attempt to bridge the gap between ML security research and the complex regulatory landscape in which these systems must operate.
5. **Clear and Explicit Assumptions:** The upfront listing of assumptions (N=10 stable banks, uncompromised server, regulated financial institutions, gradient-only observation) allows domain experts to precisely judge the scope and limitations of the claims being made.

---

## Weaknesses (with Severity)

1. **[High Severity] Insufficient Threat Model Realism — Intelligence Asymmetry:** The adversary is assumed to have perfect architectural knowledge of the defense (Kerckhoffs principle) yet is constrained to gradient-only observation. In a real consortium, a client with the sophistication to execute a meticulously scheduled four-phase poisoning attack across 120 rounds would almost certainly have broader intelligence—timing side channels on inference, knowledge of other consortium members, or access to broader system telemetry. The specific intelligence asymmetry (omniscient architecture, zero reconnaissance) is operationally implausible and must be justified or adjusted.

2. **[High Severity] Chronologically Mismatched Datasets:** IEEE-CIS (2019) and ECC (2015) are standard academic benchmarks but are functionally obsolete for validating a defense against *current* fraud tactics. The payment landscape was revolutionized by the COVID-era shift to digital/commerce (CNP explosion), the maturation of token-based transactions (EMV tokenization, network tokens), and the rise of AI-generated synthetic identities. A defense validated strictly on 5–10 year old data cannot credibly claim to address modern fraud patterns. The authors must either curate a contemporary dataset or provide a rigorous analytical argument for why the defense generalizes.

3. **[High Severity] Unrealistic Operational Scenario — Consortium Dynamics:** The N=10 stable bank consortium idealization ignores critical operational realities. Real-world fraud consortiums experience member churn, heterogeneous IT stacks and governance capabilities, political disputes over gradient contributions, and strict inference latency SLAs (often sub-100ms for real-time authorization). The three-stage cascade introduces non-trivial communication and computation overhead per round. The EMA reputation layer (L3) faces a severe cold-start problem for new members, and system convergence behavior under member dropout is unaddressed.

4. **[Medium Severity] Regulatory Oversimplification — AML/CFT SAR Override:** The concept of an "EMA reputation score overriding a Suspicious Activity Report (SAR)" is legally unsound and operationally dangerous. Filing a SAR is a statutory obligation under the Bank Secrecy Act; an automated decision based on a sliding-window reputation score cannot legally override this requirement. The framework must be explicitly positioned as a *risk-scoring input* for a human-in-the-loop decision, with a full audit trail satisfying SR 11-7's documentation requirements.

5. **[Medium Severity] Neglect of Downstream Operational Impact Metrics:** The proposed evaluation metrics (Success Rate, Gradient Cosine Similarity, Update Norm) are purely ML-space features. In production fraud detection, the primary operational cost is False Positive Rate (FPR). An attack that increases FPR from 2% to 3% on a 590K transaction volume translates to tens of thousands of blocked legitimate transactions and massive manual review expense. A design-stage paper must commit to evaluating end-to-end business impact (precision, recall at operational thresholds, FPR delta) to demonstrate practical relevance.

---

## Detailed Comments

**Introduction (Gap Claim):** The gap claim is well-motivated but requires sharper positioning. The assertion that "stateless defenses miss temporally-adaptive attacks" is partially true, but several robust FL defenses (FoolsGold, RFA, FLAME, FANG defense variants) incorporate stateful or momentum-based reasoning. The specific gap is more nuanced: *temporally-structured stealthy poisoning designed to exploit batch-based gradient defenses in the credit card fraud detection domain.* The authors should more clearly differentiate from general adaptive FL attacks (model replacement, distributed backdoor attacks) and explicitly position relative to the most closely related work.

**Threat Model:** This is the paper's weakest link from a domain perspective. The adversary is assumed to be a *single* compromised client with no Sybil capability. Modern fraud rings operate by establishing dozens of synthetic identities simultaneously. Furthermore, the 120-round grinding schedule assumes static membership. A practical fraud ring would accelerate, decelerate, or switch attack vectors based on observed transaction outcomes (a feedback loop). The adversary model should account for this adaptive evolution.

**Related Work (FL Fraud Detection):** This section is too thin on practical industry applications. The paper must discuss and differentiate from existing industry consortium models: Early Warning Services (Zelle network fraud detection), FICO Falcon Consortium (collaborative fraud rules), SWIFT SIAC (cross-institution AML intelligence). These represent the current operational baseline for how cross-institution fraud intelligence is shared.

**Regulatory Sections:**
- *GDPR Art. 22 (Automated Decision-Making):* A cascaded defense relying on an opaque temporal sliding window (EMA) directly triggers the right to manual review and explanation. The paper must address how the framework supports the right to explanation for a decision made by a multi-layer stateful defense.
- *SR 11-7 (Model Risk Management):* The spectral PCA layer assumes a fixed subspace. How is this subspace validated and recalibrated over time without leaking gradient information or exposing the system to covariate shift?
- *ECOA/FCRA (Fair Lending):* An EMA reputation layer based on gradient history may inadvertently introduce a disparate impact against low-income or transient populations who have naturally less banking history or more volatile transaction patterns.

**Discussion:** Must be substantially expanded with a candid assessment of (1) the threat model's narrow scope, (2) the dataset era limitations, (3) the operational simplifications, and (4) the regulatory frictions identified above.

---

## Questions for Authors

1. **Threat Model Intelligence Asymmetry:** Can you provide a single realistic operational scenario where a fraud ring possesses perfect architectural knowledge of your cascade defense (including the EMA rounding threshold and spectral PCA subspace) but is strictly constrained to gradient-only observation and cannot Sybil the system?

2. **Dataset Generalization:** Given the median age of your evaluation data (5–10 years old), how do you argue your defense generalizes to modern fraud patterns such as token-based CNP attacks, real-time authentication bypass, digital wallet manipulation, and AI-driven synthetic identity injection?

3. **Operational Churn and Latency:** Your design assumes 10 static banks. In practice, consortiums experience member churn. How does the EMA reputation layer (L3) handle the cold-start problem for a new bank joining the federation? What is the estimated latency overhead of your three-stage cascade, and how does that align with the real-time (<100ms authorization) constraints of credit card processing?

4. **Legal Mechanism for EMA "Override":** Could you clarify the intended legal mechanism for your EMA reputation-based "SAR override"? Is this intended to be a binding decision to suppress a regulatory filing, or is it a prioritization score for a human analyst? How would the automated decision be audited under SR 11-7 and BSA requirements for human-in-the-loop documentation?

---

## Dimension Scores

| Dimension | Weight | Score | Weighted Score | Notes |
|---|---|---|---|---|
| **Originality** | 20% | 70 | 14.00 | Grinding attack novel; cascaded defense for fraud domain is a new synthesis. |
| **Methodological Rigor** | 25% | 45 | 11.25 | Design logical but assumptions far from operational reality; consortium dynamics unaddressed. |
| **Evidence Sufficiency** | 25% | 30 | 7.50 | Reliance on 5–10 year old datasets without plan to address modern fraud fronts is critical gap. |
| **Argument Coherence** | 15% | 75 | 11.25 | Coherent narrative from attack motivation through design; regulatory section oversimplified but shows awareness. |
| **Writing Quality** | 15% | 80 | 12.00 | Clear, well-structured, professionally written with effective use of diagrams and tables. |
| **Weighted Average** | **100%** | | **56.00** | |
