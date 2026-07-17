# Peer Review Report — Perspective Review

## Reviewer Information
- **Role**: Peer Reviewer 3 (Perspective)
- **Identity**: Expert in AI regulation and data privacy law (GDPR, CCPA, EU AI Act), financial model risk management (SR 11-7, OCC 2011-12), fair lending compliance (ECOA, FCRA, UDAAP), and AML/CFT governance frameworks. Primary research focuses on the cross-disciplinary gap between ML system design and regulatory feasibility in regulated financial services.
- **Review Focus**: Cross-disciplinary coherence of the proposed framework; accuracy of regulatory mapping claims (GDPR, SR 11-7, ECOA/FCRA, AML/CFT); identification of contradictions between technical architecture and legal/ethical constraints; feasibility of stated privacy and fairness guarantees for a consortium deployment.

---

## Overall Assessment

### Recommendation: Major Revision
### Confidence Score: 4 (Out of 5)

### Summary Assessment
This paper tackles a genuinely important problem—designing a federated learning system for credit card fraud detection that respects the complex web of financial regulation. The gated cascade architecture is creative, and the effort to map regulatory requirements (GDPR, SR 11-7, ECOA/FCRA, AML/CFT) onto specific technical behaviors is ambitious and overdue. However, the paper suffers from a critical, unresolved contradiction at its core: it claims to be privacy-preserving through DP-FL while requiring raw gradient access for its signature Spectral Anomaly Detection layer. This is not a minor implementation detail—it is a design flaw that voids both claims simultaneously unless a secure execution environment is specified and demonstrated. The regulatory mapping, while well-structured, overreaches: the reputation floor (R_SS=0.85) is presented as a fairness guarantee when it is likely an inference-time band-aid that could create its own disparate impact; the Art. 22 analysis conflates training/inference separation with exemption from automated decision-making rules; and the SR 11-7 mapping describes functional equivalents, not the governance and oversight posture the regulation demands. Competitive intelligence leakage, listed as a limitation, is arguably the single greatest governance barrier to consortium adoption and receives no structural mitigation. The paper is too advanced for rejection—the problem it addresses is vital—but it requires a major revision to resolve these cross-disciplinary contradictions before the design can be considered defensible for its intended deployment.

---

## Strengths

1. **Timely and High-Impact Problem Domain.** The intersection of FL, real-time fraud detection, and strict multi-jurisdictional financial regulation is critically underserved. The paper identifies a genuine barrier to industry adoption and attempts to bridge it.

2. **Structured Regulatory Mapping (Table VII and §VIII).** The systematic mapping of SR 11-7 requirements (governance, out-of-tolerance, concept drift, override processes) to specific technical components is a concrete contribution that other researchers can build upon or critique.

3. **Honest Limitations Section and Self-Awareness of Tradeoffs.** The paper explicitly acknowledges SecAgg incompatibility, cold-start challenges, competitive intelligence leakage, and the degrading effect of DP noise on Layer 2 detection. This transparency is commendable and builds trust.

4. **Proactive Engagement with Fairness and Ethics.** Explicitly identifying three fairness risks and proposing a specific mitigation (reputation floor, SAR_override flags, per-subgroup FPR monitoring) demonstrates a level of ethical awareness that remains rare in systems papers.

---

## Weaknesses (with Severity)

1. **[High Severity] Unresolved Privacy-Robustness Contradiction.** The paper's central architectural claim—that it is privacy-preserving via DP-FL (ε=8)—is fundamentally incompatible with the requirement that Layer 2 (Spectral Anomaly Detection) operate on raw gradient updates. If DP noise is applied *before* Layer 2, the paper's own analysis concedes that L2 detection precision degrades. If Layer 2 accesses raw updates *before* DP noise, the privacy guarantee is voided for that pathway. The paper hand-waves this as future work with TEEs/SMPC, but for a design-stage paper claiming feasibility, this is the central architectural contradiction that must be resolved, not deferred.

2. **[High Severity] Oversimplification of Fairness Guarantees (R_SS = 0.85).** The reputation floor is framed affirmatively as a fairness guarantee. This is legally and technically insufficient. A *uniform* floor applied to populations with *differential* false positive rates does not remedy disparate impact under ECOA—it merely shifts the threshold at which the impact manifests. Groups with higher volatility or lower initial reputation will oscillate around this floor, suffering a different but equally problematic pattern of harm. The ECOA analysis requires *training-time* fairness constraints (adversarial debiasing, group reweighing, or equalized odds regularization on the FL aggregation), not an inference-time clip.

3. **[Medium-High Severity] Insufficient GDPR Art. 22 and Joint Controller Analysis.** The paper asserts that separating training from inference sidesteps Art. 22 (automated decision-making). This is legally weak. The learned profiles *are* the mechanism for the profiling that Art. 22(1) regulates. Training/inference separation is an implementation detail, not a compliance strategy. Furthermore, the Art. 28 "joint controller" analysis is mislabeled (Art. 28 governs processors; Art. 26 governs joint controllers). A 50+ bank consortium creates contested joint controllership, and the paper provides no framework for allocating liability for a defective decision.

4. **[Medium Severity] Overstated SR 11-7 Compliance.** Table VII maps SR 11-7 requirements to specific code modules, which is a good start. However, SR 11-7 is fundamentally a *model risk management* and *governance* framework. It demands independent validation, stakeholder challenge, and an audit trail documenting the model's limitations. An automated "SAR_override flag" and a "concept drift threshold" are functional features, not governance structures. A design-stage paper must clearly distinguish between *mapping* and *satisfying*, and outline the governance infrastructure that sits *around* the technical system.

5. **[Medium Severity] Underdeveloped Treatment of Competitive Intelligence Leakage.** Listed as a limitation, this is arguably the most significant practical and regulatory barrier to a bank consortium adopting FL for fraud. Gradient updates from competing institutions can leak proprietary risk postures, merchant vulnerabilities, and detection strategies. The paper provides no structural mitigation (split learning, functional encryption, secure enclaves, or blinding), and the deferral to future work weakens the overall feasibility claim.

---

## Detailed Comments

### Privacy-Robustness Tension (§VII-D)
This is the paper's critical vulnerability. The gated cascade is the paper's core contribution, yet the foundational architectural assumption of the cascade is in direct conflict with the paper's privacy-preserving claim.

The paper states Layer 2 (Spectral Anomaly Detection) "operates on raw gradient updates to detect coordinated adversarial attacks" and "maintains high precision because it does not suffer from post-processing noise degradation." At the same time, §VII-D acknowledges DP noise degrades L2 detection and calls DP a "nontrivial tradeoff." The paper attempts to resolve this by proposing Layer 2 run "either before DP noise is applied to the update, or within a trusted execution environment."

This is insufficient for a design-stage feasibility claim. The authors must commit:
- If Layer 2 runs *before* DP noise, the system is not end-to-end privacy-preserving. The DP budget for Layer 2's access must be explicitly accounted for.
- If Layer 2 runs *within a TEE*, the authors must provide an architecture sketch, discuss whether TEE integrity satisfies GDPR Art. 32, and address the performance implications of real-time spectral analysis inside an enclave.
- If neither is viable, the paper must drop one of its claims (either "privacy-preserving" or "high-precision anomaly detection") and revise the design accordingly.

### Regulatory (§VIII)
**GDPR (§VIII-A):** The Nowak (C-434/16) argument that gradient updates are personal data under Art. 4(1) is defensible. However, the analysis fails to distinguish between the cardholder (whose transaction generates the gradient) and the institution (that holds the gradient). The Art. 22 analysis (training vs. inference) is the weakest legal argument in the paper—calling it "inference" does not exempt the system from the regulation.

**ECOA/FCRA (§VIII-B):** The solution (R_SS = 0.85) is disproportionate to the stated risks. The analysis must proceed to a *disparate impact* analysis: What is the adverse impact ratio for each subgroup before and after the floor? Is there a less discriminatory alternative (e.g., subgroup-specific thresholds, training-time fairness regularization)?

**SR 11-7 (§VIII-C):** A design paper claiming to map to SR 11-7 should include: (1) the governance feedback loop, (2) the independent validation dataset and holdout strategy, (3) the performance monitoring charter. Without these, the claim that the framework "satisfies" SR 11-7 is overreach.

### Ethical Implications (§IX-D)
**Competitive Intelligence Leakage:** This is the paper's most significant practical governance omission. In a consortium of 50+ competing banks, the risk that an adversary can infer a competitor's exposure to a specific merchant compromise, seasonal fraud patterns, or risk tolerance threshold is a reason for the consortium to never form. Split learning, vertical FL, or a masked aggregation protocol with certified differential privacy *between* institutions should be proposed as a concrete architectural change.

---

## Questions for Authors

1. **The Central Architectural Contradiction:** You claim the system is privacy-preserving via DP-FL (ε=8) while simultaneously requiring Layer 2 to operate on raw gradient updates. How is this contradiction resolved in your proposed design? Please specify the exact data access pattern, the threat model for the Layer 2 pathway, and the aggregate privacy guarantee for the complete system.

2. **Fairness Rigor under ECOA:** The reputation floor (R_SS = 0.85) is presented as a fairness remedy. Can you provide a simulation or formal proof that this floor does not create a *new* form of disparate impact on the most volatile subgroup members? What is the adverse impact ratio for each subgroup *before* and *after* the floor is applied?

3. **GDPR Joint Controllership:** You reference "Art. 28 Joint Controller" (§VIII-A), but Art. 28 addresses *processors*, while Art. 26 governs joint *controllers*. In a consortium of 50+ banks, how is liability for an erroneous fraud decision allocated? Does your technical framework provide the transparency required by Art. 26(2) to determine each controller's responsibilities?

4. **Competitive Intelligence as a Governance Barrier:** Given that this is a design-stage paper, please propose a concrete cryptographic or architectural path—specific to your gated cascade—that prevents a malicious consortium member from inferring a competitor's risk posture. Without this, what makes the framework feasible for adoption by competing regulated entities?

---

## Dimension Scores

| Dimension | Weight | Score | Weighted Score | Notes |
|---|---|---|---|---|
| **Originality** | 20% | 85 | 17.00 | Critical gap well-identified; layered design with regulatory mapping is genuinely novel. |
| **Methodological Rigor** | 25% | 62 | 15.50 | Design logic sound, but unresolved privacy-robustness contradiction weakens feasibility. |
| **Evidence Sufficiency** | 25% | 50 | 12.50 | Regulatory mapping accurate in scope but lacks depth; governance infrastructure unaddressed. |
| **Argument Coherence** | 15% | 68 | 10.20 | Tension between privacy and detection claims is acknowledged but not resolved. |
| **Writing Quality** | 15% | 82 | 12.30 | Well-structured; legal arguments clearly presented. |
| **Significance & Impact** | (bonus) | 85 | — | High practical significance for the FL + financial regulation intersection. |
| **Weighted Average** | **100%** | | **67.50** | |
