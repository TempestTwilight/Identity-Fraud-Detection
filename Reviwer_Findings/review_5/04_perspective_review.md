# Cross-Disciplinary Perspective Review Report

**Paper:** "Robust FL for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework" (Design-Stage Specification)
**Role:** Peer Reviewer 3 — Cross-Disciplinary Perspective (Privacy Engineering / RegTech)
**Expertise:** Privacy-enhancing technologies, TEE attestation architectures, GDPR/SR 11-7 compliance for regulated ML systems

---

## Executive Summary

This review evaluates the design-stage specification from the intersection of Privacy-Enhancing Technologies (PETs) and Financial Regulation Technology (RegTech). The regulatory mapping in §8 is a strong piece of survey work—consistent with the EIC's assessment—but the *architectural* execution of the proposed layered framework suffers from a fundamental internal contradiction that undermines its central privacy claims. The design relies on a single, fragile trust anchor (TEE attestation) without the cryptographic layering required to meet GDPR's "state of the art" security standard. It completely ignores cross-jurisdictional landmines (Schrems II → US CLOUD Act) that would invalidate its application for the exact cross-border banking scenarios it targets. The explainability framework is under-engineered for the adversarial regulatory environments (ECOA, GDPR Art. 22) it maps. While the problem is important and the survey is valuable, the current design is structurally inconsistent with its own stated regulatory requirements. Major architectural revisions are needed before this specification can move to validation.

---

## 1. Analysis of the Privacy-Robustness Tension

**Core Architectural Conflict:**
The framework attempts to reconcile two inherently conflicting requirements—robust detection (which needs raw gradient signal) and privacy preservation (which requires obfuscation). The design fails to resolve this tension transparently.

- **§8.2 vs. §7.4 (The Raw Gradient Contradiction — Critical):** The paper claims that L2 (Robust Detection) "operates on raw gradients before DP noise." Separately, §7.4 describes TEE-based SecAgg as a mechanism to protect gradient confidentiality. These two claims are logically incompatible. If the robust aggregation logic inside the TEE sees the *raw, un-noised* gradient, the architecture does *not* provide gradient confidentiality—it provides confidentiality *from external entities only*. The TEE operator, the entity that provisioned the enclave, or any attacker who breaches the TEE's attestation boundary sees everything.

- **Honesty of Trade-offs:** *Not fully honest.* The paper presents the layers as independent components of a unified defense. They are not. L4 (Privacy) is structurally subordinated to L2 (Detection)—the privacy guarantee only kicks in *after* detection has seen everything. The trade-off is that the system prioritizes attack detection accuracy over strong privacy guarantees, but this is framed as "layered" rather than "prioritized detection over privacy." The architectural selection (raw → detect → DP) must be explicitly acknowledged as a choice that narrows the privacy adversary model significantly.

- **Explainability Side-Channel (§8.7):** The surrogate SHAP model requires a "consent-authorized proxy dataset." This creates a secondary data store outside the main TEE training pipeline. If the proxy dataset is correlated with real training data, generating explanations on it could leak information about the real dataset. The paper does not model this privacy leakage path.

---

## 2. Regulatory Consistency Check

**GDPR Art. 25/32 — Data Protection by Design and Security of Processing:**
The design relies *exclusively* on TEE attestation as its primary privacy anchor. This is a **High-severity gap** from a regulatory perspective.

- **Art. 28 (Processor Guarantees):** A bank (Controller) engaging a tech firm (Processor) that operates TEEs must ensure sufficient guarantees. TEE attestation vouches for the *code* running, but does *not* prevent a malicious system administrator from conducting side-channel attacks (timing, power, cache) on the enclave. The design provides no mechanism for the bank to independently audit the Processor's TEE operational security.
- **Art. 32 (State of the Art):** Best practice for GDPR-compliant FL mandates *multiple*, *independent* layers of protection. Cryptographic SecAgg or DP-noise applied *before* the robust aggregation loop provides mathematical guarantees independent of hardware trust. The design offers no fallback if the TEE is compromised (e.g., Plundervolt, Foreshadow, SGAxe attacks). "State of the art" for regulated ML requires defense-in-depth—the current single-anchor design fails this standard.

**ECOA / Reg B & GDPR Art. 22 — Adverse Action Notices (§8.7):**
The R² ≥ 0.9 fidelity threshold for the surrogate SHAP model is **woefully insufficient** for regulatory compliance.

- **Local vs. Global Fidelity:** A global R² of 0.9 can mask subpopulations where local fidelity drops to 0.3. Credit denials contested under ECOA or GDPR Art. 22 require explanations that are accurate for the *specific individual*. A global R² threshold is not a valid audit metric for adverse-action compliance.
- **Proxy Dataset Governance:** The paper states this dataset must be "consent-authorized" and "proxy" but specifies **no details** on its size, sampling strategy, consent withdrawal policy, data retention, or audit trail. "Proxy" implies it is not the real data, which fundamentally limits its legal validity for explaining decisions made on *actual* applicant data. A proxy-based explanation for a denied credit line would not withstand regulatory scrutiny.

**SR 11-7 (Model Risk Management):**
- **Challengeability:** A model whose training logic runs entirely inside a sealed TEE is extremely difficult for a bank's internal audit and independent validation teams to examine. Regulators under SR 11-7 (OCC, Federal Reserve) expect banks to understand, challenge, and test their models. The design does not provide an interface for independent validation without breaking the TEE's security model.

---

## 3. Cross-Jurisdictional Analysis

**Critical Omission — The paper contains no analysis of cross-border legal conflicts.** For a paper targeting "cross-border banking," this is fatal.

- **Schrems II & the CLOUD Act:** Modern TEEs rely on attestation keys managed by US-headquartered companies (Intel for SGX/TDX, AMD for SEV-SNP, NVIDIA for Confidential Computing). Under the US CLOUD Act, a US law enforcement agency can compel these companies to hand over attestation keys or cooperate in subverting the enclave. An EU bank processing EU citizens' gradient data in a TEE whose trust anchor is a US company fails the "essentially equivalent" standard set by *Schrems II*. The paper does not even identify this risk, let alone propose a mitigant (e.g., sovereign attestation services, open-source TEEs, geographic residency requirements for key management).

- **Data Localization vs. AML/KYC Retention:** EU banking secrecy laws (e.g., German §24c KWG), combined with local data localization mandates, conflict with the architecture's DP-based privacy guarantees. Fraud detection is exempt from some GDPR provisions (Art. 23), but the paper does not map its design to this balancing test or discuss data retention obligations that would override the DP guarantee.

- **Regulatory Cross-Jurisdiction Mismatch:** The paper cites a mix of GDPR, US regulations, and Basel standards without acknowledging that compliance with one regime may constitute a violation of another (e.g., GDPR "right to deletion" vs. FINMA "record retention" for 10 years). The design does not address this conflict.

---

## 4. Missing Perspectives

- **Audit & Standards Framework:** The paper lacks an audit architecture for regulators. How does a national banking supervisor verify the code running inside the TEE is the code described in the paper? The IETF's RATS (Remote Attestation Procedures) standard is a relevant framework that is entirely absent. A reference architecture without an audit framework is incomplete.

- **Risk Register for TEE Vulnerabilities:** The paper treats the TEE as a perfect security assumption. The literature on practical TEE attacks (Plundervolt, Foreshadow, CacheOut, SGAxe) is extensive. A design-stage specification must include a dedicated risk assessment of TEE failure modes and the system's graceful degradation path when the TEE is compromised.

- **Economic / Trade-Off Modeling:** The paper does not compare the cost-benefit of its TEE architecture vs. pure cryptographic approaches (e.g., fully homomorphic encryption, secure multiparty computation). Is the TEE providing a net improvement in privacy for the added complexity, or is it simply shifting the trust boundary? A cross-disciplinary design should justify this architectural choice quantitatively.

- **Informed Consent & Transparency:** The paper discusses consent-authorized proxy datasets but never addresses informed consent for the *primary* data. Are users aware their data is processed in a TEE-based FL system? What happens if a user withdraws consent? How is the model retrained?

---

## 5. Specific Issues with Severity

| ID | Severity | Issue | Section |
|---|---|---|---|
| **C-1** | **Critical** | L2 operates on raw gradients before DP noise, violating the TEE's stated confidentiality goal. The privacy model is incorrectly scoped. | §8.2 / §7.4 |
| **C-2** | **Critical** | Completely absent cross-jurisdictional analysis (Schrems II, CLOUD Act, banking secrecy/data localization). The international framing is regulatory naive. | §1 (Implicit) |
| **H-1** | **High** | Surrogate SHAP model meets neither ECOA nor GDPR Art. 22 compliance. Global R² threshold is inappropriate. Proxy dataset governance completely unspecified. | §8.7 |
| **H-2** | **High** | Single-anchor TEE reliance fails GDPR Art. 25/32 "state of the art" standard. No mandatory cryptographic layering hedge (e.g., pre-detection DP). | §7.4 |
| **H-3** | **High** | No audit framework or standards mapping (e.g., IETF RATS) for regulator verification of TEE operations. | §7.4 / §9 |
| **M-1** | **Medium** | Privacy leakage path from surrogate SHAP proxy dataset to primary training data not modeled. | §8.7 |
| **M-2** | **Medium** | Side-channel and microarchitectural attacks on TEEs not listed in risk register. No graceful degradation path specified. | §7.4 |

---

## 6. Recommendation

**Decision: Reject in current form. Major architectural revisions required for re-evaluation.**

The paper has a strong foundation in its regulatory survey but fails dramatically in design execution from a cross-disciplinary PET/RegTech perspective. The framework is architecturally conflicted (C-1) and geographically naive (C-2).

**Mandatory Revisions for Re-Submission:**

1. **Resolve C-1 — Realign Architecture with Privacy Claims.** Explicitly define the adversary model. Either operate robust detection on DP-noised gradients (accepting lower detection accuracy) or honestly state that the robust aggregation entity is a fully trusted insider with access to raw data. Remove the claim of "gradient confidentiality" unless cryptographic measures (e.g., SecAgg) are applied as a mandatory layer before detection.

2. **Address C-2 — Full Cross-Jurisdictional Architecture Section.** Add a dedicated section analyzing TEE key management geography, CLOUD Act implications, Schrems II impact, and data localization conflicts. Propose mitigations (sovereign clouds, open-source TEEs with non-US attestation keys).

3. **Fix H-1 — Strengthen Explainability Framework.** Replace the global R² threshold with a local fidelity requirement (e.g., weighted local fidelity for each decile of applicants). Define the proxy dataset size, sampling strategy, consent governance, retention policy, and audit trail. Acknowledge the legal limitations of "proxy-based" explanations.

4. **Fix H-2 / H-3 — Cryptographic Layering & Audit Architecture.** Mandate DP-noise applied *before* the gradient enters the detection logic (or a post-detection math guarantee). Add an audit architecture section mapping how regulators can independently verify the enclave's code and data handling (e.g., IETF RATS, TPM-based supply chain).

The paper is a valuable problem statement and regulatory survey. With these revisions, it could become a landmark design-stage framework for navigating the tension between robust FL, privacy, and financial regulation. In its current form, the structural inconsistencies render it unsuitable for the venue.
