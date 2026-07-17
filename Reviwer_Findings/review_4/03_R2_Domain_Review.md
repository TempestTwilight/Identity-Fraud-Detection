# Peer Review Report — R2 (Domain)
**Paper ID:** TIFS-2026-XXXX
**Title:** "Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework"
**Reviewer:** Peer Reviewer 2 (Domain — Financial Fraud Detection & Federated Learning Systems)

---

**Recommendation: Major Revision**

**Summary:** This paper proposes a design-stage specification for a Byzantine-robust FL framework intended for a small banking consortium (N=10) to collaboratively detect fraud. The topic is timely and relevant to IEEE TIFS, bridging distributed ML security with heavily regulated financial infrastructure. However, the specification over-indexes on generic FL security literature while under-serving the operational, legal, and data-ecology realities of a real-world banking consortium.

---

### 1. Literature Review Completeness

**Strength:** The coverage of Byzantine-robust aggregation methods (Krum, Bulyan, Trimmed Mean) and generic FL privacy attacks is competent.

**Critical Gaps:**
- **Finance-specific FL deployments are absent.** The paper fails to engage with the FATE framework (the dominant open-source FL framework in Asian banking consortiums) or NVIDIA FLARE (used in European pilot deployments). Industry whitepapers from JPMorgan (Onyx) and the Monetary Authority of Singapore (Project Ubin) document precisely the operational hurdles this specification claims to address.
- **Fraud-specific adversarial ML literature is missing.** The paper treats adversarial threats (A2, A6) through the lens of image-domain attacks, but fraud detection is overwhelmingly tabular. Key works on adversarial robustness for deep tabular networks (TabNet, FT-Transformer) and the unique vulnerability of fraud models to *minority-class-targeted* gradient poisoning are not cited.
- **System-level FL fraud surveys are overlooked.** Shen et al. (2021, *A Survey of FL for Fraud Detection*) and FedFraud architectures are missing from the related work comparison.

### 2. Threat Model Realism

**Strength:** The inclusion of a cascade-aware adaptive attack (A6) shows awareness of sophisticated adversaries that is rare in the FL literature.

**Critical Weaknesses:**
- **Sybil Attack (A4) is a non-threat in this context.** In a KYC'd, AML-cleared consortium of N=10, every participant is a legally liable entity. A Sybil attack (spawning fake nodes) is operationally implausible. The paper imports this threat from anonymous P2P FL without adapting it to the banking governance layer. The specification should replace A4 with *Insider Collusion* (e.g., two compromised banks submitting poisoned updates) or *Aggregator Compromise*.
- **Missing threat: Privacy Poisoning (A7).** In a fraud consortium, an adversary can inject clean transaction data that is *uniquely identifying* (PII-rich, synthetic identities), forcing the model to memorize individuals and enabling later membership inference attacks. This is a known threat in financial FL.
- **Free-rider (A1) lacks competitive grounding.** The paper assumes altruistic participation. In practice, a bank with significant fraud market share may have little incentive to share. The specification does not model *valid free-riding* (a bank legitimately lacks a fraud typology) vs. *adversarial free-riding* (shirking contribution). A Shapley-value or reputation-based contribution mechanism is required.

### 3. Practicality of the Framework

**Strength:** The N=10 assumption is a defensible lower bound for a consortium pilot.

**Critical Weaknesses:**
- **Governance vacuum.** The paper names a "trusted aggregator" but specifies no legal structure—entity formation, model ownership, liability for erroneous decisions, exit/onboarding rights for members. In financial services, these *are* the primary obstacles to deployment, not the Byzantine aggregation logic. A consortium agreement structure must be part of a design specification.
- **Compute and latency heterogeneity is ignored.** Fraud detection demands sub-100ms inference. A Tier 1 bank has GPU clusters; a community bank runs on a single server. The specification assumes all nodes train and serve the same model. A practical spec must address model compression, personalization (e.g., FedMD, DS-FL), and a tiered compute requirement standard.
- **Incentive mechanism is absent.** How do you measure contribution in an N=10 consortium? The paper has no contribution scoring or compensation scheme. Without this, free-riding (A1) is a guaranteed failure mode, not just a threat.

### 4. Dataset Selection Appropriateness

The use of IEEE-CIS and European Credit Card datasets is standard for academic ML but insufficient for a design specification:

- PaySim / ECC is static synthetic — it does not model concept drift, modern fraud typologies (Authorized Push Payment fraud, Account Takeover, Synthetic Identity), or the severe non-IID *domain shift* between institutions.
- The paper simulates non-IID splits via Dirichlet allocation, which is artificial. Real banking fraud distributions are not Dirichlet-sampled; they reflect fundamentally different customer demographics, merchant portfolios, and fraud environments.
- A specification must justify its dataset choice against real-world consortium data characteristics, or propose a synthetic benchmark that models label distribution skew and feature drift to properly stress-test the robustness claims.

### 5. Regulatory Mapping

**Strength:** This is the strongest contribution of the paper. The mapping of GDPR Art. 22 (automated decision-making), SR 11-7 (model risk management), ECOA (adverse action), and AML obligations is careful and demonstrates genuine subject matter expertise.

**Critical Weaknesses:**
- **GDPR explainability requires a technical solution, not just a flag.** The paper correctly notes the tension between FL and the "right to explanation" (Art. 15, 22), but a design specification must propose a mechanism (e.g., a globally agreed-upon SHAP/LIME surrogate, or a local distilled interpretable model). A regulator will not accept "we identify this as a challenge" as a spec.
- **Data retention and auditability are unaddressed.** SR 11-7 requires robust model validation trails. FL minimizes raw data retention, but what about gradient updates and model snapshots? These must be stored for regulatory audits, creating a massive GDPR Art. 5(1)(e) (data minimization) exposure. The specification is silent on retention and purging policies.
- **AML timeliness.** AML SARs have strict legal deadlines (often 30 days from suspicion). An FL model updated daily or weekly may violate the regulatory requirement for *timely* monitoring of fast-moving fraud typologies. The specification needs to address the update cycle latency vs. fraud velocity trade-off.

### 6. Operational Considerations (Omissions)

Several critical operational details are missing from a baseline design specification:

- **Concept drift and model staleness.** Fraudsters adapt daily. How does the global model handle high-velocity attacks within the FL update window? Is there a local fallback mechanism?
- **Incident response.** If the aggregator detects a poisoning attack, what is the rollback protocol? Mean Time to Detect (MTTD) is not bounded.
- **Auditor access.** How does an external regulator audit the FL system without violating participant privacy? This requires specific technical proposals (e.g., verifiable audit trails via zk-proofs or a Trusted Execution Environment for the aggregator).
- **Model update frequency.** How often does the model retrain? What happens during the gap between fraud campaigns and model updates?

### 7. Positioning Against Existing Literature

The paper claims novelty as the first integrated *Byzantine-robust + Regulatory-compliant* FL specification for finance. It does not compare itself against existing deployed systems (FATE, FLARE, IBM FL for finance) or parallel academic system designs (e.g., *FedFraud: A System for Financial FL*, IEEE BigData 2022). The paper would benefit from a dedicated "Comparison with Existing FL System Designs for Finance" table to sharpen its contribution.

---

## Recommendation: Major Revision

The paper has a strong core concept and the regulatory analysis is genuinely valuable. However, it reads more like a well-structured concept paper than a rigorous design specification for TIFS. To meet the standard of IEEE TIFS, the authors must:

1. **Ground the threat model** in real banking operations (replace Sybil with Collusion; add Privacy Poisoning; model incentive structures).
2. **Add a legal governance layer** (entity structure, model ownership, liability, exit rights) and an **incentive contribution mechanism** (e.g., Shapley-based valuation).
3. **Replace or augment static datasets** with a synthetic non-IID benchmark that models domain shift, concept drift, and label skew between consortium members.
4. **Provide technical solutions** for Explainability (local surrogates), Auditability (verifiable trails), and Data Retention (purging policies), rather than merely flagging them as open challenges.
5. **Include a dedicated comparison table** differentiating this work from FATE, FLARE, and existing financial FL system papers.

**Confidence:** High.
**Practical Impact:** Potentially high if the governance and operational gaps are closed in revision.
