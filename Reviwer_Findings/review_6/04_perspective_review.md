# Peer Review Report

## Manuscript Information
- **Title**: Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework
- **Manuscript ID**: [Not available — design-stage specification]
- **Review Date**: 2026-07-11
- **Review Round**: Round 1

---

## Reviewer Information

### Reviewer Role *
Peer Reviewer 3 (Perspective)

### Reviewer Identity *
Cross-disciplinary privacy-preserving ML systems researcher with expertise in differential privacy, trusted execution environments, and the privacy-utility tension in regulated ML deployments. Background spans cryptographic protocol design, GDPR/Schrems II compliance for cross-border data processing architectures, and spectral anomaly detection in high-dimensional settings.

### Review Focus *
This review evaluates three cross-disciplinary tensions at the intersection of privacy, security, and regulation that the other reviewers' domain-specific lenses may underweight: (1) the compatibility of local DP noise with spectral detection SNR in Layer 2, (2) the auditability and cross-border adequacy of the TEE attestation architecture under Schrems II, and (3) whether the claimed third contribution (A6 operational envelope) is a genuine theoretical contribution or a relabeled limitation.

---

## Overall Assessment *

### Recommendation *
- [ ] **Accept**
- [ ] **Minor Revision**
- [x] **Major Revision**
- [ ] **Reject**

### Confidence Score *
**5** — Completely within my area of expertise; I am very confident in my assessment.

### Summary Assessment *
This paper targets an important and genuinely underexplored problem: temporally-adaptive poisoning in cross-silo FL for credit card fraud detection. The gated cascade architecture (norm/cosine + spectral + temporal reputation) is architecturally well-motivated, and the formalization of the statelessness blind spot is a useful conceptual contribution. The paper is unusually thorough in its regulatory mappings (GDPR, SR 11-7, ECOA), which is praiseworthy for a systems paper. However, from a cross-disciplinary privacy-preserving ML systems perspective, the paper exhibits critical gaps in three areas that undermine its central design claims. First, the TEE+DP pipeline (local DP before spectral detection) is presented as a resolved design tension, but no quantitative analysis exists showing that spectral SNR survives DP noise at any practically meaningful ε_local — the paper's own disclosure (§IV-D) that "detection power may degrade unacceptably" is effectively an admission that the architecture may be internally inconsistent. Second, the auditability architecture suffers from a regress problem: the independent auditor is a consortium appointee whose attestation reports are published to a consortium-controlled log, with no mechanism for genuine third-party verification. Under Schrems II, the TEE's US-managed attestation keys create a cross-border transfer vulnerability that the paper's mitigations (sovereign attestation services) acknowledge but do not design for. Third, the A6 operational envelope is presented as Contribution 3, but it is substantially a relabeled impossibility result — the information-theoretic detection bound (§V-A) is correct but well-understood in the anomaly detection literature, and its packaging as a "contribution" conflates identifying a limitation with solving one. The design-stage status amplifies these concerns: each requires either theoretical analysis or experimental evidence that is absent. I recommend Major Revision conditional on the authors providing substantive analysis of the DP→SNR degradation, a resolvable auditability architecture, and clearer positioning of what the operational envelope contributes beyond what is already known from detection theory.

---

## Strengths *

### S1: Statelessness Blind Spot Formalization *
The paper provides a clean formalization of the statelessness blind spot (p. 4, §I-C): showing that any stateless aggregation rule produces an independent detection sequence $\{f_t\}$ that a temporally-adaptive attacker can probe and bypass. The contrast with the stateful cascade's memory-$k$ detection statistic $S_t = \sum_{i=t-k+1}^t w_i f_i$ is clearly articulated and genuinely novel. This is a non-trivial observation that the Byzantine-robust FL literature has overlooked, and it grounds the cascade design in a well-defined failure mode.

### S2: Regulatory Mapping Completeness *
The paper's treatment of GDPR (Art. 4(1) gradient-as-personal-data, Art. 22 automated decision-making, Art. 28/32 technical measures, Art. 44–49 cross-border transfers), SR 11-7 model risk management, ECOA/FCRA fairness, and AML/CFT obligations (pp. 25–31, §VII) is unusually comprehensive for a systems paper. The explicit mapping of SR 11-7 requirements to specific framework components (Table IX), the disclosure of the gradient-as-personal-data legal theory under *Nowak* (C-434/16), and the acknowledgment of the *Schrems II* cross-border tension (§VII-G) demonstrate a level of regulatory awareness that significantly elevates the paper's practical relevance.

### S3: Explicit Disclosure of Bootstrap and Envelope Vulnerabilities *
The paper is commendably transparent about its own limitations: the $W_h = 200$ warm-up vulnerability window (p. 15, §III-D2), the "circular bootstrap" problem (p. 16, §III-D2 item 3), the A6 operational envelope's admission that adversaries within the typical set are undetectable (§V-A), and the DP-SNR degradation being an open question (§IV-D). This candor is rare and valuable. However, as discussed in the weaknesses below, candor about a gap does not constitute evidence that the gap is bridged.

### S4: Gated Cascade as an Architectural Pattern *
The division-of-labor design principle (L1 for trivial attacks, L2 for coordinated collusion, L3 for slow adaptive poisoning) with confidence-based gating (Algorithm 1) is a clean architectural contribution that avoids the selection-bias problem of fused ensemble methods. The dual-threshold architecture (Table III) distinguishing reputation threshold $T_i$ from RCC deviation threshold $\tau_{\Delta,i}$ is a thoughtful design detail for non-IID settings.

---

## Weaknesses *

### W1: Unquantified DP→SNR Degradation — The Central TEE+DP Tension
**Problem**: The paper proposes a processing pipeline where local DP noise ($\varepsilon_{\text{local}}$) is applied to gradients *before* they enter the spectral detection cascade (p. 24, §IV-D1). This means Layers 2 and 3 operate on DP-noised gradients. The paper candidly acknowledges that "DP noise reduces L2/L3 detection SNR" and that degradation "must be characterized empirically" (p. 24, §IV-D1), yet provides no quantitative analysis — theoretical or experimental — of what DP noise level preserves sufficient spectral separability for the cascade to function. The experimental plan (§VI-C) lists a "DP-SNR degradation" experiment but only at $\varepsilon_{\text{local}} \in \{10, 5, 2, 1\}$, on $d=50$ synthetic data. This is insufficient in two respects. First, the PCA reconstruction error threshold $\tau_2$ is calibrated under clean gradients; adding DP noise inflates the residual variance by $\sigma_{\text{DP}}^2 = O(d \cdot \Delta_f^2 / \varepsilon_{\text{local}}^2)$ (via the Gaussian mechanism), which directly increases the honest reconstruction error $e_i$ and thus the FPR. Second, for $d \approx 434$ (IEEE-CIS) or higher, the curse of dimensionality means that even modest DP perturbation can collapse the spectral gap that L2 relies on — the eigenvalue gap $\lambda_k - \lambda_{k+1}$ may not survive additive noise whose variance scales with $d$.

**Why it matters**: The paper's core architectural claim is that the TEE enables spectral detection that pure DP would preclude. But if $\varepsilon_{\text{local}}$ must be large enough (e.g., $\varepsilon_{\text{local}} > 10$) for L2 to function, then the "cryptographic" privacy guarantee that the paper claims is independent of TEE trust is vacuous at operationally meaningful privacy levels. Conversely, if $\varepsilon_{\text{local}}$ is set to a GDPR-compliant value (say $\varepsilon_{\text{local}} \leq 5$), L2 may be blind. This is not a minor parameter-tuning issue — it is an architectural contradiction that the paper identifies but does not resolve. The paper's fallback position ("prioritized detection over privacy under audited TEE" — p. 24) is an honest concession but undermines the claimed contribution of a cryptographically-guaranteed privacy layer.

**Suggestion**: Provide a theoretical bound on the SNR degradation: let $\tilde{e}_i = \| (r_i + \xi_i) - (r_i + \xi_i) U_k U_k^T \|_2$ where $\xi_i \sim \mathcal{N}(0, \sigma_{\text{DP}}^2 I_d)$. Derive the distribution of $\tilde{e}_i$ as a function of $\varepsilon_{\text{local}}$, $d$, and the eigenvalue spectrum of $\Sigma$. At minimum, compute for the IEEE-CIS feature dimensionality ($d=434$) the $\varepsilon_{\text{local}}$ threshold below which the spectral gap collapses. Without this, the TEE+DP architecture is an assertion, not a design.

**Severity**: Critical

### W2: The Auditability Regress Problem — Who Audits the Auditor?
**Problem**: The attestation design (p. 24, §IV-D2) specifies a "neutral entity (Big 4 firm, industry body, or separate legal entity)" as Layer 1 independent auditor. This entity runs attestation daily and publishes signed reports to a "consortium-accessible audit log." The paper does not address the fundamental auditability regress: on what basis does any consortium member (or external regulator) verify that (a) the auditor's own infrastructure is uncompromised, (b) the auditor's signed attestation report corresponds to the enclave that actually processed their gradients (not a benign-but-different fork), and (c) the audit log itself has not been tampered with by the consortium's server operator? The paper states that "any consortium member can independently attest the enclave" (Layer 2, client opt-in), but this requires the member to possess the enclave's public verification key and expected measurement hash — which are "published in the consortium agreement." This creates a circular trust chain: the consortium agreement (written by the members, including potentially adversarial ones) defines the reference measurements against which attestation is judged. An attacker who controls a majority of consortium members (or who has compromised the consortium governance process) can define a malicious measurement hash as canonical.

**Why it matters**: The paper's regulatory compliance claims (GDPR Art. 28/32, SR 11-7 monitoring) rest critically on this auditability architecture. Under GDPR Art. 5(2) (accountability), the data controller must demonstrate compliance — not merely assert it. A circular trust chain in which the auditor is appointed by the consortium and reports to a consortium-controlled log does not satisfy this burden. Similarly, under SR 11-7, model risk management requires independent validation; an auditor who is economically dependent on the consortium cannot provide this. The paper's TEE risk register (Table VIII) enumerates side-channel and key-compromise threats but does not even list "collusion between auditor and consortium" as a threat vector.

**Suggestion**: Address the regress problem explicitly. Three concrete paths: (1) Specify a verifiable transparency log (e.g., Certificate Transparency-style or blockchain-based) where attestation digests are published in an append-only, publicly-verifiable store independent of the consortium. (2) Specify the legal/contractual separation between the consortium and the auditor — e.g., the auditor reports to a financial regulator (central bank), not to the consortium board. (3) Replace or supplement procedural attestation with a cryptographic mechanism: each client can non-interactively verify that the aggregated output $\theta_{\text{agg}}^{(t)}$ is a deterministic function of the attested code and the inputs, using something like a TEE-produced zero-knowledge proof of correct execution. Absent one of these, the auditability architecture is security theatre.

**Severity**: Critical

### W3: Schrems II Adequacy and the CLOUD Act Problem
**Problem**: The paper acknowledges (p. 28, §VII-G) that Intel SGX/TDX and AMD SEV-SNP attestation keys are managed by US-headquartered companies, creating a *Schrems II* vulnerability: under the US CLOUD Act (2018), a US law enforcement agency can compel these companies to assist in subverting the enclave. The proposed mitigations (sovereign attestation services, geographic residency requirements, hybrid DP+TEE) are listed at a conceptual level with no architectural specification. Specifically, (1) "sovereign attestation services using non-US key hierarchies" — what existing technology provides this? Open RISC-V TEEs are mentioned but are not production-ready for the financial sector. (2) "Geographic residency requirements for attestation key management" — this is a policy preference, not a technical design. (3) "The hybrid DP + TEE architecture ensures the formal privacy guarantee does not depend on TEE trust" — but W1 above shows this guarantee may be vacuous at privacy levels that survive spectral detection. The paper cannot simultaneously rely on the DP layer to salvage the TEE's cross-border inadequacy (against *Schrems II*) while admitting the DP layer may be unusable at meaningful $\varepsilon$ values (against the SNR requirement).

**Why it matters**: For a paper targeting "cross-border banking" (p. 28, §VII-G), the TEE's susceptibility to CLOUD Act compulsion is a first-order architectural problem, not a footnote. An EU bank processing EU citizens' payment data through a US-attested enclave would face a Data Protection Authority finding that the transfer lacks "essentially equivalent" protection under *Schrems II* — regardless of the consortium's contractual safeguards. The paper's mitigations are not implementable as specified.

**Suggestion**: Either (a) commit to a specific sovereign attestation technology (e.g., AWS Nitro Enclaves in EU regions with EU-key-attested firmware, or a specific open-source TEE with independent hardware certification) and describe its architecture, OR (b) restructure the architecture so that the Schrems II-relevant data never enters an enclave at all (i.e., commit fully to DP-only detection with the TEE providing defense-in-depth rather than the primary privacy anchor). The current half-measure — where the paper points to both options without designing either — is insufficient.

**Severity**: Critical

### W4: SR 11-7 Internal Consistency — Calibration on Potentially Poisoned Warm-Up Data
**Problem**: The cascade's thresholds ($\tau_{\text{norm}}$, $\tau_{\text{cos}}$, $\tau_\Delta$, $W_h$) are calibrated during a $W_h = 200$ round warm-up period (p. 15, §III-D2). The paper acknowledges this bootstrap vulnerability (p. 16: "the window $W_h = 200$ rounds remains a vulnerable period") and proposes three safeguards: TEE-attested execution, a robust geometric median estimator tolerating 50% corruption, and noise blinding during calibration. However, from an SR 11-7 model risk perspective (the paper's own chosen regulatory framework), this creates an internal inconsistency. SR 11-7 (§III.B, monitoring; §IV, governance) requires independent validation of model inputs and ongoing monitoring for data quality issues. If the warm-up data used to calibrate the per-client thresholds $T_i = \bar{R}_i - \tau_\Delta \cdot \sigma_{R,i}$ is itself poisoned — even partially — then the baselines $\bar{R}_i$ and $\sigma_{R,i}$ are corrupted, and the entire detection regime that follows is operating on a corrupted reference distribution. The geometric median estimator tolerates up to 50% corruption under the assumption that corrupt updates are symmetrically distributed, but a coordinated poisoning campaign during warm-up (e.g., $m$ insiders shifting all their gradients in a common direction) would bias the geometric median arbitrarily. The paper's own attack model A4$'$ (insider collusion, §V-C) describes exactly this scenario but does not analyze its effect on warm-up calibration.

**Why it matters**: A financial institution deploying this framework under SR 11-7 would need to demonstrate to examiners that the model's risk controls are not circular — i.e., that the defense thresholds are not themselves compromised by the very attacks they are meant to detect. The paper's robust estimator safeguard (geometric median) is presented without analyzing its breakdown point under correlated (not just symmetric) corruption. The TEE blinding safeguard prevents the attacker from knowing they are in the warm-up period, but does not prevent the attacker from poisoning their updates during that period — the noise masking only hides the existence of warm-up, not the ability to submit malicious gradients.

**Suggestion**: Perform a formal analysis of the geometric median estimator's breakdown point under the specific correlated corruption model of A4$'$ (insider collusion). Alternatively, adopt a robust estimation procedure with proven breakdown under correlated corruption, such as the coordinate-wise median of residuals (which has a 50% breakdown point even under adversarial correlation). Disclose the residual risk transparently in the SR 11-7 mapping: the calibration procedure is conditionally valid assuming the warm-up period is attack-free, and this assumption must be verified through independent onboarding audits (contractual, not technical).

**Severity**: Major

### W5: A6 Operational Envelope — Genuine Contribution or Relabeled Limitation?
**Problem**: The paper claims three contributions (p. 3, §I-C): (1) identification of the statelessness blind spot, (2) stateful cascade design with formal FPR bounds, and (3) the "attack taxonomy and operational envelope." Contribution 3 is flagged as the focus of this concern. The A6 operational envelope (§V-A) states: the cascade guarantees detection when an adversary exceeds per-layer calibrated bounds, but cannot detect adversaries who constrain updates within those bounds. This is presented as a "fundamental consequence of the information-theoretic gap between benign and adversarial gradient distributions" (p. 18). The formalization via KL divergence (Eq. 13) restates a well-known result in hypothesis testing (Chernoff-Stein lemma): when $D_{\text{KL}}(\mathcal{P}_{\text{adv}} \| \mathcal{P}_{\text{honest}}) \to 0$, any detector satisfies $\beta \le \alpha$. This is a textbook result in detection theory (e.g., Cover & Thomas, Elements of Information Theory, Ch. 11). Its application to the FL poisoning context is a reasonable observation, but packaging it as a "contribution" (especially co-equal with the cascade design itself) overstates its novelty. The operational envelope is a limitation — "we cannot detect adversaries who stay within the benign typical set" — expressed in formal language. The paper's reframing ("this transforms the known limitation into an honest foundational claim," p. 3) is rhetorically clever but analytically thin.

**Why it matters**: The paper's contribution claims should accurately reflect what is new. Information-theoretic limits on gradient-based detection are well-studied in the adversarial ML literature (e.g., the "no-free-lunch" results in Gilmer et al., 2018; the fundamental trade-offs in Fawzi et al., 2015). Restating the KL divergence bound in the context of spectral FL defenses is an expository contribution, not a novel theoretical result. The A6 attack model itself (cascade-aware adversary with threshold probing and reputation inflation) is a useful adversarial modeling contribution, but this should be attributed to the attack taxonomy, not to the operational envelope framing.

**Suggestion**: Restructure the contribution claims. Contributions 1 and 2 are well-supported architectural contributions; Contribution 3 should be split into: (3a) A6 attack model as part of the taxonomy (a useful adversary specification), and (3b) operational envelope as an honest limitation analysis (valuable for deployers but not a novel theoretical result). The KL divergence analysis should be moved to §VIII (Limitations) or §VI (Formal Analysis) as a characterization of the defense's fundamental constraints, not positioned as a co-equal contribution.

**Severity**: Major

---

## Detailed Comments *

### Title & Abstract
The title accurately reflects the paper's content. The abstract is well-structured and clearly communicates the design-stage status. However, the abstract's final sentence — "The framework is evaluated against six fraud-specific attack models across fourteen baselines and fifteen ablation configurations" — is misleading in its passive implication of completed evaluation. The paper explicitly states this evaluation is projected/theoretical. The abstract should use "is projected to be evaluated" or similar language to align with §VI-E's disclaimer.

### Introduction
The motivation is well-constructed, and the statelessness blind spot (§I-B) is clearly articulated with strong formal intuition. The contribution list (p. 3) is admirably specific. However, Contribution 3 (operational envelope) should be toned down as discussed in W5.

### Literature Review / Theoretical Framework
The literature gap analysis (Table I) is useful but omits several works on information-theoretic limits of gradient-based detection that are directly relevant to the operational envelope claim (see W5). The paper should cite Gilmer et al. (2018, "Motivating the Rules of the Game for Adversarial Example Research") and Goldwasser et al. (2022, "Planting Undetectable Backdoors in Machine Learning Models") which establish similar information-theoretic impossibility results in adjacent contexts.

### Methodology / Research Design
The gated cascade architecture is well-specified with clear design rationale. However, the TEE+DP pipeline (§IV-D) lacks the quantitative rigor that the rest of the methodology demonstrates. The paper describes what the pipeline is, but not why it works at any specific $\varepsilon_{\text{local}}$ value (see W1). The temperature of analysis drops markedly between §VI (detailed formal analysis of FPR bounds, Davis-Kahan, convergence) and §IV-D (qualitative discussion of DP, no SNR analysis). This asymmetry is concerning given that the DP+SNR tension is arguably the most critical architectural constraint.

### Results / Findings
As a design-stage specification, the paper has no experimental results. The projected ASR table (Table VII) is clearly disclaimed as theoretical. This is acceptable given the paper's stated scope, but the authors should consider whether the TEE+DP SNR tension (W1) and the auditability regress (W2) are resolvable via theoretical analysis alone — if not, the paper's claims cannot be validated without experimental evidence that the paper explicitly states is absent.

### Discussion
The red-team assessment (Table X) is useful but does not include the TEE+DP tension or the auditability regress as listed concerns. Given that these are first-order architectural issues (not parameter tuning), their omission from the self-critique is noticeable. The limitation discussion (§VIII-G) lists many valid limitations but does not directly address the circular bootstrap problem in the context of SR 11-7 consistency (see W4).

### Conclusion
The conclusion accurately summarizes the paper's contributions but overstates the third contribution by declaring it co-equal with the first two. The projected ASR numbers in the conclusion (p. 31: "0.25 ASR for the full defense vs. 0.92 for undefended FedAvg") should include a parenthetical noting these are theoretical projections, as done in §VI-E.

### References
The reference list is current and relevant. However, the paper should cite (a) works on information-theoretic detection limits (see above), (b) the *Schrems II* judgment (C-311/18) explicitly rather than a secondary source, and (c) recent work on TEE side-channel attacks (e.g., Van Bulck et al. on SGX vulnerabilities) given the paper's reliance on enclave security.

---

## Questions for Authors *

1. **Quantitative DP→SNR analysis**: At what $\varepsilon_{\text{local}}$ value does the PCA reconstruction error gap $\tau_2 - \mathbb{E}[e_i]$ collapse to zero for the IEEE-CIS feature dimensionality ($d=434$)? Can you provide a theoretical bound of the form $\varepsilon_{\text{local, min}} \ge f(\lambda_k, \lambda_{k+1}, d, \tau_2)$? Without this, how can a deployer determine whether the TEE+DP pipeline is consistent or contradictory?

2. **Auditability regress resolution**: The attestation architecture relies on an independent auditor whose reports are published to a consortium-accessible log. Who verifies the auditor's own infrastructure, and on what basis can a member bank (or regulator) verify that the enclave actually processing their gradients is the attested code rather than a malicious fork? Can you specify a concrete mechanism (e.g., verifiable transparency log with independent witnesses, or non-interactive TEE proofs of correct execution) that breaks the circular trust chain?

3. **Schrems II and the CLOUD Act**: The paper acknowledges that Intel/AMD attestation keys are US-managed and thus susceptible to CLOUD Act compulsion, creating a *Schrems II* violation for EU-consortium data. Your proposed mitigations are listed at a policy-desiderata level. Which specific technology (e.g., AWS Nitro in EU regions with sovereign key hierarchy, a specific open RISC-V TEE implementation) do you propose to use, and what is the deployment timeline? Alternatively, if the DP layer is the primary privacy guarantee, can you provide evidence that $\varepsilon_{\text{local}}$ can be set low enough for GDPR compliance without destroying L2 SNR (linking to Question 1)?

4. **SR 11-7 circular calibration**: The per-client thresholds are calibrated during a warm-up period that may itself be poisoned by insider collusion (A4$'$). Your proposed safeguard (geometric median estimator) has an unanalyzed breakdown point under correlated corruption. What is the formal breakdown point of the geometric median under the A4$'$ attack model? If it is less than 50% under correlated corruption, what alternative robust estimator do you propose?

---

## Minor Issues

### Language / Grammar
- p. 24, §IV-D1: "satisfies GDPR Art.~25 (data protection by design) and Art.~32 (state of the art)" — the citation should also reference Art. 25's requirement for data protection *by default*, which has distinct implications for the DP parameter choice.
- p. 28, §VII-G: "essentially equivalent" should be quoted or cited to the *Schrems II* judgment (C-311/18, para. 94).
- p. 17, §V-A: The operational envelope bullet list repeatedly says "per-round to per-round, constant scale" — this phrasing is unclear on first reading and could be simplified.

### Citation Format
- Reference to *Schrems II* (C-311/18) should use the official ECLI identifier (ECLI:EU:C:2020:559) for precision.
- The *Nowak* case (C-434/16) should similarly use ECLI:EU:C:2017:994.
- Missing citations for several foundational detection theory results referenced in §V-A (Cover & Thomas, 2006; Gilmer et al., 2018).

### Figures and Tables
- Table II (attacks): The distinction between A4$'$ and A4$''$ using prime notation is confusing. Rename to A4a and A4b or "Insider Collusion" and "Aggregator Compromise" for clarity.
- Table VIII (TEE risk register): Add a row for "Auditor-consortium collusion" and "CLOUD Act compulsion of attestation key holder" as identified threats.
- The KL divergence equation (Eq. 13, p. 17) should include the standard hypothesis testing inequality for completeness: $\beta \le \min(1, \alpha \cdot e^{D_{\text{KL}}(\mathcal{P}_{\text{adv}}\|\mathcal{P}_{\text{honest}})})$ from Stein's lemma.

### Layout
- Consider moving the information-theoretic limits section (§V-A) to §VI (Formal Analysis) or §VIII (Limitations), as it is a negative result characterizing a constraint rather than a positive attack model.

---

## Dimension Scores *

| Dimension | Score (0-100) | Descriptor | Notes |
|-----------|--------------|------------|-------|
| Originality (20%) | 68 | Adequate | Stateful cascade and statelessness blind spot are genuinely novel; operational envelope contribution is overclaimed. |
| Methodological Rigor (25%) | 50 | Weak | Strong on FPR bounds and convergence analysis; critically weak on DP→SNR quantification, auditability architecture, and calibration robustness. The analysis quality is uneven — excellent in some dimensions (§VI), absent in others (§IV-D). |
| Evidence Sufficiency (25%) | 30 | Weak | Design-stage paper with no experimental evidence. Acceptable given stated scope, but the TEE+DP tension cannot be resolved without either theoretical bounds or experiments — both absent. |
| Argument Coherence (15%) | 65 | Adequate | Main argument (statelessness → stateful cascade) is clear and well-supported. Third contribution is overstated relative to its analytical depth. The TEE+DP discussion is internally contradictory (claims cryptographic privacy while admitting SNR may force it to TEE-only). |
| Writing Quality (15%) | 72 | Strong | Generally clear, well-organized, and professional. Occasionally verbose in technical sections. |
| Significance & Impact (optional) | 55 | Weak | Important problem, well-motivated. However, the practical impact of the architecture is contingent on resolving the TEE+DP tension and auditability regress — which the paper does not accomplish. Impact is conditional on future work. |
| **Weighted Average** | **55.0** | **Major Revision** | Calculation: 68×0.20 + 50×0.25 + 30×0.25 + 65×0.15 + 72×0.15 = 13.6 + 12.5 + 7.5 + 9.75 + 10.8 = 54.15 → rounds to 55. Major Revision is appropriate, but note that two Critical and two Major weaknesses (W1, W2, W3, W4) touch foundational architectural assumptions. If the authors cannot provide substantial theoretical analysis (W1, W4) or a fundamental architectural redesign (W2, W3), the score would drop below 50 (Reject). |
