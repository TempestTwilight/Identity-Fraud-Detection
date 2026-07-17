# Peer Review Report

## Manuscript Information
- **Title**: Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework
- **Manuscript ID**: [Not provided]
- **Review Date**: 2026-07-11
- **Review Round**: Round 1 review

---

## Reviewer Information

### Reviewer Role *
**EIC (IEEE TIFS Associate Editor)**

### Reviewer Identity *
Associate Editor, IEEE Transactions on Information Forensics and Security. Expertise in adversarial machine learning, federated learning security, and applied cryptography.

### Review Focus *
Evaluating the paper's overall contribution, originality, and significance for IEEE TIFS; assessing whether a design-stage specification with zero experimental results meets the journal's standards for demonstrated contribution; determining fit between the paper's evidence level and the claims made; and judging novelty relative to the Byzantine-robust Federated Learning literature.

---

## Overall Assessment *

### Recommendation *
- [ ] **Accept** — Can be published directly, only minor formatting changes needed
- [ ] **Minor Revision** — Minor revisions needed, no re-review after revision
- [ ] **Major Revision** — Substantial revisions needed, re-review required after revision
- [x] **Reject** — Not suitable for publication in this journal

### Confidence Score *
**5** — Completely within my area of expertise, I am very confident in my assessment.

### Summary Assessment *
This manuscript presents a design-stage specification for a three-layer gated cascade defense framework for robust federated learning in credit card fraud detection. The paper identifies a genuine vulnerability — the "statelessness blind spot" of round-independent Byzantine-robust aggregators against temporally-adaptive poisoning — and proposes a layered defense combining norm/cosine filtering, spectral anomaly detection via PCA, and sliding-window reputation scoring. Formal analysis provides FPR bounds (~1.6%) under stationary covariance and characterizes drift-affected degradation via the Davis-Kahan sinΘ theorem.

The problem framing is sound, the threat taxonomy (six attack models A1–A6) is well-structured, and the paper demonstrates unusually thorough engagement with regulatory requirements (GDPR, SR-11-7, ECOA, AML/CFT). However, the manuscript contains **zero experimental results**. Every quantitative claim — every projected Attack Success Rate, every comparison to baselines, every ablation configuration's expected outcome — is a theoretical projection or architectural estimate. For IEEE TIFS, a top-tier transactions journal requiring demonstrated security contributions, a design-stage specification with no empirical validation does not meet the publication threshold. The paper is more akin to a detailed technical white paper or an extended systems-design abstract than a complete archival research article. I recommend **Reject** with strong encouragement to resubmit after experimental validation is completed and reported.

---

## Strengths *

### S1: Clear Problem Diagnosis: The Statelessness Blind Spot *
The paper identifies and formalizes a genuine limitation of existing Byzantine-robust aggregation methods (Krum, Median, Trimmed Mean, Bulyan, FLTrust, FoolsGold): they are stateless, evaluating each training round independently. The formal intuition on pp. 5–6 (Eq. 1 and surrounding text) clearly articulates how a temporally-adaptive attacker can alternate between malicious and benign updates to evade per-round defenses. This is a non-obvious observation that merits attention in the FL security community.

### S2: Comprehensive and Well-Structured Attack Taxonomy *
The specification of six attack models (A1–A6, Table 2, pp. 15–20) spanning naive model replacement through cascade-aware adaptive adversaries is thorough and principled. The A6 "operational envelope" framing (pp. 18–20) is intellectually honest — it explicitly scopes what the defense can and cannot detect, and formalizes the information-theoretic limitation (KL divergence bound, Eq. 10) rather than over-claiming universal robustness. This level of threat-modeling rigor is commendable.

### S3: Thorough Regulatory and Governance Analysis *
Sections VII (Regulatory and Ethical Considerations) and VIII (Discussion and Limitations) are unusually comprehensive for a computer science paper, mapping the framework to GDPR (Art. 22, 25, 28, 32), SR-11-7 model validation, ECOA/FCRA fairness obligations, AML/CFT override procedures, and cross-jurisdictional data governance (Schrems II implications, CLOUD Act, data localization). This demonstrates awareness that FL fraud detection is as much a regulatory challenge as a technical one.

### S4: Formal Analysis of FPR Bounds and Convergence *
The cascade error propagation bound (Theorem 1, pp. 23–24) using Stewart's perturbation theorem and the drift-affected FPR characterization via the Davis-Kahan sinΘ theorem (Corollary 1.1, pp. 24–25) provide a theoretically grounded FPR estimate (~1.6%) under stationary covariance. The convergence analysis of the adaptive threshold dynamics (pp. 25–27) as a two-timescale control system is a principled framing, even if the constants are not derived in closed form.

### S5: Explicit and Transparent Disclosure of Limitations *
The paper consistently flags what is known vs. projected vs. unknown: "This paper is a design-stage specification" appears in the abstract (p. 1), the introduction (p. 5), the experimental section (p. 21), and the conclusion (p. 35). The warm-up protocol disclosure (p. 14) explicitly states that σ_{R,i} was measured on a single toy simulation. This transparency is a model of research integrity.

---

## Weaknesses *

### W1: Zero Experimental Results — Insufficient Evidence for IEEE TIFS
**Problem**: The manuscript contains no experimental measurements whatsoever. Every quantitative claim — the projected ASR upper bounds in Table 7 (pp. 22–23), the ablation configuration outcomes in Table 6 (p. 21), the FPR bound of ~1.6%, the convergence neighborhood estimates — is a theoretical projection or architectural estimate explicitly stated as "not experimentally measured." The paper even provides a disclaimer in the main results table (Table 7, p. 22): "The numerical values below are theoretically projected from formal analysis and architectural reasoning, not experimentally measured."

**Why it matters**: IEEE TIFS is a top-tier archival journal (impact factor >6) that requires demonstrated technical contributions validated through rigorous experimentation. A paper whose central quantitative claims are entirely projected, with zero empirical evidence, does not satisfy the journal's minimum publishability threshold. The gap between "design-stage specification" and "archival journal publication" is fundamental. Without experiments, the reviewer (and reader) cannot assess whether the cascade actually works, whether the FPR bound holds in practice, whether the ASR projections are optimistic or pessimistic, or whether the approach outperforms the 14 baselines as claimed.

**Suggestion**: Complete the described experimental plan (50–100 GPU-hours, 10 independent trials, 15 ablation configurations, IEEE-CIS and European Credit Card datasets). Report actual measured ASR, FPR, and ablation results with variance across seeds. Resubmit as a full paper. Alternatively, target a venue that explicitly accepts design-stage or "big idea" papers (e.g., workshops, or journals with a systems/design focus) and restructure accordingly.

**Severity**: **Critical**

### W2: Claims of Novelty Are Overstated Relative to Prior Art
**Problem**: The paper claims (p. 5, Contributions; p. 6, Contribution 1) that existing Byzantine-robust methods are "stateless" and that this is an unaddressed vulnerability. However, the paper itself cites FLDetector (Zhang et al., 2022) which uses history-based anomaly detection, and temporally-aware defenses FLAME (Shejwalkar et al., 2023), ShieldFL (Wang et al., 2024), and FedDef (Zhang et al., 2024). These works are dismissed with the statement that they were "evaluated on image classification with random label-flipping, not tabular fraud data" (p. 4). This is a domain-application gap, not a fundamental algorithmic gap — the temporal-awareness concept is already established in the literature.

**Why it matters**: Overstating novelty weakens the paper's contribution claim. The core insight — that temporal context matters for poisoning detection — predates this work. The paper's actual novel contribution is the specific cascaded architecture and its application to the fraud domain, not the discovery of temporal awareness as a defense principle.

**Suggestion**: Significantly revise the novelty claims. Frame the contribution as: (a) a specific gated-cascade architecture combining three known detection principles for the FL fraud detection domain, (b) formal FPR analysis for this specific combination, and (c) a comprehensive threat taxonomy and regulatory mapping for FL fraud consortia. Remove or soften language suggesting that temporal awareness in FL defense is a new discovery (e.g., "identifies the statelessness blind spot" → "applies temporal-awareness principles to the underexplored domain of FL fraud detection").

**Severity**: **Major**

### W3: Component-Wise Novelty Is Incremental — Each Layer Uses Known Techniques
**Problem**: Each of the three detection layers uses well-established techniques:
- Layer 1: Norm/cosine filtering — standard gradient clipping and directional filtering used in many robust aggregation schemes.
- Layer 2: PCA-based spectral anomaly detection — a textbook outlier detection method widely used in network intrusion detection, sensor networks, and ML security (e.g., outlier detection in gradient space has been explored).
- Layer 3: Sliding-window reputation scoring — a standard temporal memory mechanism used in reputation systems, federated learning (FoolsGold uses a related principle), and distributed systems.

The novel contribution is the *cascaded composition* and the *specific domain application*, not any new detection primitive.

**Why it matters**: IEEE TIFS expects security contributions that advance the state of the art. A combination of known techniques applied to a new domain, without experimental validation demonstrating that the combination yields emergent benefits, constitutes an incremental contribution. The paper needs experiments to show that the cascade's performance is superadditive (i.e., better than any single layer or two-layer combination) to justify the architectural complexity.

**Suggestion**: After completing experimental validation, demonstrate through rigorous ablation that the three-layer cascade provides non-linear improvements over individual layers and two-layer combinations. Show that the gating policy (adaptive escalation) yields measurable benefits over fixed-threshold alternatives (C9 in the ablation). Without this evidence, the contribution is primarily architectural/domain engineering rather than a security research advance.

**Severity**: **Major**

### W4: Projected ASR Values Appear Speculative and May Mislead Readers
**Problem**: Table 7 (p. 22) provides projected ASR upper bounds for 5 attack types across 6 defenses and the full cascade. For example, Krum's projected ASR against A2 (Gradient Grinding) is ≤0.70, and Trimmed Mean's against A2 is ≤0.60. These are not derived from the formal analysis — they are architectural estimates stated without derivation. The formal analysis (Section VI) provides an FPR bound (~1.6%) but explicitly does not provide ASR bounds (p. 24, end of §VI.A: "Formal ASR bounds require empirical measurement of per-layer true positive rates"). The ASR projections therefore sit in an evidential gap: they are neither formally derived nor empirically measured.

**Why it matters**: A reader — especially a practitioner or regulator — may treat the ASR values in Table 7 as validated results despite the disclaimers. The projection that the "Full Defense" achieves ASR ≤0.35 across attacks appears to be a design target, not a conclusion supported by analysis or evidence. Publishing such speculative values in a top-tier archival journal is problematic.

**Suggestion**: Remove the ASR projections from the main paper, or move them to a clearly marked "Design Targets" appendix. Replace the main experimental section with the experimental design (which is well-specified) and report actual results once obtained. A journal paper about a system that hasn't been built or tested is inherently preliminary.

**Severity**: **Major**

### W5: Paper Reads as a System Design Document Rather Than an Archival Research Article
**Problem**: The manuscript devotes substantial space to operational details that are more appropriate for a technical report or systems specification than an IEEE TIFS research paper — e.g., consortium governance structure (Table 9, p. 30), TEE risk register with specific threat mitigations (Table 8, p. 28), detailed SHAP explanation fidelity thresholds (pp. 31–32), and multi-paragraph stakeholder incentive analysis (pp. 32–33). These are valuable for a deployment specification but dilute the research contribution.

**Why it matters**: An IEEE TIFS paper should advance the state of knowledge in information forensics and security. The primary contributions should be technical novelty and validated security guarantees. The extensive governance, legal, and operational coverage — while evidence of thorough thinking — makes the paper 36 pages long while still lacking the core experimental evidence expected by the venue.

**Suggestion**: Significantly compress the regulatory and governance discussion (Sections VII and parts of VIII) to 2–3 pages focusing on how the technical design is affected by regulatory constraints. Move the consortium governance framework and detailed TEE risk register to a technical report or supplementary material. Focus the camera-ready version on: (a) the technical problem, (b) the proposed algorithm, (c) formal guarantees, and (d) experimental validation.

**Severity**: **Major**

---

## Detailed Comments *

### Title & Abstract
- The title is accurate and appropriately descriptive, though long (18 words).
- The abstract clearly signals the design-stage status ("This paper is the design-stage specification; experimental validation is in progress"), which is transparent but immediately signals the paper's fundamental limitation.
- The abstract summarizes contributions effectively but overclaims novelty (e.g., "identifies the statelessness blind spot" — this blind spot has been partially addressed in prior temporally-aware defenses).

### Introduction
- The research motivation (fraud losses >$28B/year, FL as a solution, poisoning as a threat) is well-established and persuasive.
- The "statelessness blind spot" framing (pp. 3–4) is the paper's strongest conceptual contribution — clearly explained with formal intuition.
- The contributions list (p. 4) is well-structured but overreaches: Contribution 1 (detection primitive) overstates novelty; Contribution 3 (operational envelope) is genuinely novel in its honest framing of limitations.

### Literature Review / Related Work
- Literature coverage is adequate but not exhaustive. The paper correctly identifies that no prior work evaluates Byzantine-robust aggregation specifically for fraud FL. However, the dismissal of FLAME, ShieldFL, and FedDef as "evaluated on image classification" (p. 4) is a weak argument — the temporal-awareness mechanism is general, and the domain gap does not negate their prior existence.
- The gap analysis (Table 1, p. 5) is useful and clearly positioned.

### Methodology / Research Design
- The gated cascade architecture (Section IV) is well-specified with clear design principles, formal definitions, and algorithmic pseudocode (Algorithm 1).
- The per-client baseline measurement protocol (pp. 13–15) is detailed and addresses a genuine challenge (non-IID client behavior in FL consortia). The dual-threshold architecture is appropriately conservative.
- The attack models (Section V) are the paper's strongest contribution — well-structured, grounded in realistic threat assumptions, and spanning a useful capability spectrum.
- **However**: The methodology section describes a *design*, not a *validated system*. There is no implementation, no dataset results, no convergence traces, no runtime measurements from actual deployment.

### Results / Findings
- There are no results. Section VI (Experimental Design and Expected Results, pp. 20–23) describes the planned experimental protocol in detail but reports only "projected" values with explicit disclaimers that they are not experimentally measured.
- Table 7 (Projected ASR Upper Bounds) is the paper's central quantitative exhibit and is entirely speculative. For a top-journal submission, this is fundamentally insufficient.
- The ablation table (Table 6) is well-designed and would be valuable if filled with real measurements.

### Discussion
- The Discussion section (Section VIII) is thorough and self-critical. The red-team assessment (Table 10) and stakeholder analysis (pp. 32–33) demonstrate careful thinking about deployment challenges.
- However, the discussion of "Experimental Validation Status" (p. 28) is a single sentence acknowledging the work is not done. The limitations section (pp. 33–34) is honest but its existence does not compensate for the absence of results.

### Conclusion
- The conclusion accurately recaps the contributions but restates the central problem: "Expected results project 0.25 ASR... Experimental validation is planned." A conclusion that looks to future validation rather than summarizing completed work is appropriate for a project proposal, not a journal paper.

### References
- Citation format is consistent with IEEEtran style.
- The reference list appears current and relevant, covering FL fundamentals, Byzantine robustness, and domain-specific fraud detection work. The reference to "Schrems II" (2020) shows awareness of legal developments.

---

## Questions for Authors *

1. **What would change your projected ASR values?** The paper projects specific numerical ASR upper bounds for each attack and baseline combination (Table 7). Since these are stated as theoretical projections, what specific experimental outcome would confirm vs. refute each projection? In other words, what would constitute a falsification of the design's expected performance?

2. **What is the minimal experimental validation you would accept as sufficient for a journal publication?** You have designed an extensive experimental plan (14 baselines, 15 ablations, 10 seeds, 2 datasets). Which subset of experiments would you consider necessary to establish that the cascade works as designed, and which could be deferred to an extended version?

3. **Is the cascaded architecture strictly necessary, or would a simpler ensemble suffice?** The paper emphasizes "gating, not fusion" as a design principle (p. 7). What inherent advantage does the cascade's sequential gating provide over a parallel ensemble that scores all clients on all three dimensions simultaneously? Can you sketch a scenario where the cascade succeeds but a parallel ensemble fails?

4. **How does the warm-up vulnerability interact with the practical deployment timeline?** The paper acknowledges (p. 15) that the 200-round warm-up period (1–2 weeks) is a vulnerable window. For a real consortium deploying this defense, what operational safeguards (beyond TEE blinding) would you recommend during this window? Could an adversary simply wait through warm-up and then attack?

---

## Minor Issues

### Language / Grammar
- The paper is generally well-written with clear technical exposition.
- Minor: The abstract uses bold for key terms extensively (~15 bold phrases), which is unusual for IEEE TIFS style. Consider reducing bold emphasis.
- p. 4, line 87: Double backslash in LaTeX citation `\\\\textit` appears to be a formatting artifact.

### Citation Format
- Some citations use `\\cite` with extra backslashes (LaTeX artifact).
- p. 5, Table 1 citations: Consider ensuring all entries reference specific papers rather than survey-level citations where possible.

### Figures and Tables
- The paper contains 14 tables, which is excessive for a 36-page article. Several (especially the governance structure Table 9, TEE risk register Table 8, privacy technology comparison Table 11) could be moved to supplementary material.
- Figure quality is not applicable (no figures in current draft beyond algorithm pseudocode).

### Layout
- The paper is 36 pages (IEEEtran format), which is within journal page limits but dense. The heavy use of `\resizebox{\columnwidth}{!}` for tables may produce illegible font sizes in the printed journal.

---

## Dimension Scores *

| Dimension | Score (0-100) | Descriptor | Notes |
|-----------|--------------|------------|-------|
| Originality (20%) | 50 | Adequate | The "statelessness blind spot" framing has merit, but temporal-awareness in FL defense predates this work. Core novelty is in the specific domain application and cascaded architecture, not new detection primitives. |
| Methodological Rigor (25%) | 30 | Weak | The theoretical analysis (FPR bounds, convergence) is well-executed, but there is zero experimental validation. A paper whose central claims are entirely unvalidated cannot score above Weak on methodological rigor. |
| Evidence Sufficiency (25%) | 10 | Insufficient | No experimental evidence exists. Every quantitative claim is projected, not measured. This is the paper's fatal flaw for IEEE TIFS. |
| Argument Coherence (15%) | 70 | Strong | The paper is logically structured, clearly written, and the arguments flow consistently from problem identification to proposed solution to limitations. The threat model and design rationale are well-articulated. |
| Writing Quality (15%) | 75 | Strong | Well-written with clear technical exposition, appropriate formality, and honest self-assessment. Minor issues with bold overuse and table density. |
| **Weighted Average** | **42** | **Reject** | The paper scores poorly on the two highest-weighted dimensions (Methodological Rigor and Evidence Sufficiency) due to the complete absence of experimental validation. For IEEE TIFS, this is a fatal gap. |

---

## Summary for Editorial Office

This manuscript is a design-stage specification for a three-layer gated cascade defense against poisoning attacks in cross-silo Federated Learning for credit card fraud detection. The paper is unusually well-structured and intellectually honest — it clearly identifies a genuine limitation of stateless Byzantine-robust aggregators, provides formal FPR bounds and convergence analysis, specifies a comprehensive threat taxonomy with six attack models, and engages thoroughly with regulatory requirements (GDPR, SR-11-7, ECOA, AML/CFT). However, the manuscript contains **no experimental results whatsoever**. Every quantitative claim — every projected Attack Success Rate, every comparison against 14 baselines, every ablation outcome — is a theoretical projection explicitly stated as not experimentally measured.

For IEEE TIFS, a top-tier archival journal with an impact factor >6, a design-stage specification without empirical validation does not meet the minimum publishability standard. The paper would be suitable for a systems-design venue, a workshop, or — after completing the described experiments (50–100 GPU-hours, 10 trials, 15 ablations) — as a full paper for TIFS. I recommend **Reject** with strong encouragement to resubmit after experimental validation is completed. The paper demonstrates the authors have done the design and analysis work; what remains is the essential step of demonstrating that the design actually works.
