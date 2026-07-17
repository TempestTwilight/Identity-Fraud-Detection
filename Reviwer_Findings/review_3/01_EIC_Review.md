# EIC Peer Review Report

## Manuscript Information
- **Title**: Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework
- **Review Date**: 2026-07-06
- **Review Round**: Round 1

## Reviewer Information
- **Role**: Editor-in-Chief / Senior Area Editor
- **Identity**: IEEE Transactions on Information Forensics and Security (IEEE TIFS), specializing in secure machine learning systems and adversarial ML
- **Review Focus**: Journal fit, originality, significance, overall quality, feasibility

## Overall Assessment

### Recommendation: **Reject for TIFS**
### Confidence Score: **5** (Very High)

### Summary Assessment
This manuscript presents a design-stage specification for a temporally-aware gated cascade defense framework targeting robust federated learning in credit card identity fraud detection. The central insight—that existing FL defenses overlook the stateless, dynamically-shifting nature of streaming fraud transactions—is genuinely perceptive and well-motivated. The three-layer architecture (norm/cosine filtering, PCA spectral anomaly detection, EMA reputation scoring) is logically structured, and the inclusion of formal bounds (FPR via Stewart's perturbation theorem, fairness floor via R_SS=0.85) reflects theoretical ambition. The paper is clearly written and well-organized.

However, the manuscript is fundamentally incomplete for IEEE TIFS. TIFS is a premier archival journal that requires rigorous empirical validation; a "design-stage specification" that explicitly states "experimental validation is in progress" does not meet this bar. The threat model is preliminary (no adaptive adversaries), the manuscript length (~7 pages) is well below TIFS expectations for a full paper, and the core adaptive threshold mechanism remains underspecified. While I strongly believe the direction is promising, a design-stage paper without experimental results cannot be accepted for publication at TIFS. I recommend rejection, with the strongest encouragement to complete the experiments and resubmit a full-length version, or alternatively to target a workshop venue for early feedback.

---

## Strengths (4)

### S1: Timely and Relevant Problem Identification
The paper correctly identifies a critical blind spot in existing FL defenses: the assumption of client statefulness in a problem domain—real-time credit card fraud detection—where transaction streams are inherently stateless and temporally nonstationary (§3). This framing is compelling and demonstrates deep domain awareness.

### S2: Systematically Designed Layered Defense
The gated cascade architecture (L1: norm/cosine filtering, L2: PCA spectral anomaly detection, L3: EMA reputation scoring) is well-structured and shows careful reasoning about composability (§4). The gate decision logic and the rationale for ordering layers are clearly articulated.

### S3: Formal Theoretical Analysis
The use of Stewart's perturbation theorem to bound honest-client FPR (≈1.6%) and the fixed-point convergence analysis for reputation scoring represent genuine theoretical contributions for a design-stage work (§7). The fairness guarantee via reputation floor R_SS=0.85 shows awareness of regulatory constraints.

### S4: Comprehensive Evaluation Planning
The specification of 5 attack models (A1–A5), 10 baselines (B1–B10), and 10 ablation configurations (C1–C10) demonstrates methodological thoroughness in the experimental design (§6). The plan, if executed, would provide strong evidence for the framework's efficacy.

---

## Weaknesses (5)

### W1: Fundamental Absence of Empirical Results
**Problem**: The manuscript is explicitly a "design-stage specification." No experimental results are provided. Section 6 states "Experimental validation is in progress on cloud infrastructure."
**Why it matters**: TIFS is an archival journal requiring definitive evidence of performance, robustness, and practical feasibility. A design document without validation cannot support the claims made about security guarantees, FPR bounds, or attack mitigation.
**Suggestion**: Complete the empirical evaluation and resubmit a full paper with comprehensive results.
**Severity**: Critical

### W2: Under-Developed Threat Model (No Adaptive Adversary)
**Problem**: The five attack models (A1–A5) represent static, well-known attack vectors (label flip, backdoor, etc.) but do not consider an adaptive adversary who observes and actively bypasses the layered defense (§3, §5).
**Why it matters**: The entire premise of a "robust" defense is its resilience against worst-case, adaptive threats. Without analyzing adaptive attacks engineered to evade L2 spectral detection or L3 reputation scoring, the claimed robustness is unsupported.
**Suggestion**: Implement an adaptive adversary that crafts attacks specifically targeting the cascade's weakest layer.
**Severity**: Major

### W3: Insufficient Length and Technical Depth for TIFS
**Problem**: The manuscript is approximately 7 pages and 6,500 words. TIFS full papers typically run 12–16 pages with exhaustive technical development, extended related work discussion, and complete experimental appendices.
**Why it matters**: The formalism in the threat model, threshold adaptation policy, and treatment of non-IID data is truncated. The paper reads more like an extended abstract or workshop paper than a TIFS submission.
**Suggestion**: Expand the formal analysis (especially the adaptive threshold escalation mechanism), deepen the related work engagement, and provide full empirical appendices.
**Severity**: Critical

### W4: Opaque Adaptive Threshold Escalation Policy
**Problem**: Section 4.4 describes an "adaptive threshold escalation policy" that adjusts layer sensitivity over time, but the specific mechanism (how thresholds evolve, what signals trigger escalation/de-escalation, convergence properties) is presented only in abstract terms.
**Why it matters**: The adaptive threshold is a core design component distinguishing this work from static defenses. Without formalization or empirical characterization, the reader cannot evaluate its stability or security properties.
**Suggestion**: Formalize the threshold dynamics (e.g., as a control system or Markov process) and analyze its convergence and sensitivity.
**Severity**: Major

### W5: Shallow Regulatory and Deployment Analysis
**Problem**: The mapping to GDPR, SR 11-7, ECOA, and AML/CFT is listed (Section 9) but not deeply analyzed. Practical tensions (e.g., right to explanation vs. spectral black-box detection, fairness guarantees across demographic subgroups) are acknowledged but unaddressed.
**Why it matters**: TIFS values practical impact and deployment realism. A "temporally-aware" financial system must explicitly address regulatory compliance challenges for real-world adoption.
**Suggestion**: Provide a deeper analysis of at least one regulatory tension (e.g., ECOA adverse action requirements and the L2 spectral module).
**Severity**: Minor

---

## Detailed Comments by Section

### Title & Abstract
The title accurately reflects the content. The abstract clearly states the design-stage nature of the work, which is honest but immediately flags the mismatch with TIFS requirements. The abstract could better highlight the novelty of the statelessness blind spot.

### Introduction
Strong motivation. The critique of stateful assumptions in FL defenses for fraud detection is well-argued and original. The paper correctly distinguishes itself from conference-scale works. The explicit "design-stage specification" framing limits the paper's force and signals incompleteness.

### Related Work (Section 2)
Adequate coverage of FL defense families (norm-based, clipping, aggregation robust). However, misses recent work on temporally-aware defenses (e.g., online FL, streaming anomaly detection) and does not deeply engage with adaptive attack literature. The paper would benefit from a clearer taxonomic positioning of where L1, L2, and L3 fit relative to existing approaches.

### Threat Model (Section 3)
The stateless client model is the paper's strongest contribution. The threat model for attackers is weak: all 5 attacks are specified at the data modification level without modeling adaptive behavior or collusion strategies. The threat model should include an adversary that sees the defense layers and optimizes against them.

### Framework (Section 4)
The cascade logic is the paper's architectural strength. L1 filtering is standard. L2 (PCA spectral anomaly) is a strong choice that exploits structure in the gradient space. L3 (EMA reputation) is a well-motivated temporal component. The gating logic ("pass to next layer" vs. "reject immediately") is sensible.

**Key missing detail**: How does the gate handle cascading false positives from L1 inflating L2/L3 load? The adaptive threshold policy lacks formal specification. Under what conditions are thresholds tightened or loosened?

### Attacks (Section 5)
A1–A5 are standard (label flip, backdoor, gradient scaling, etc.). Missing: (a) adaptive attacks targeting the spectral filter specifically; (b) multi-round reputation manipulation attacks; (c) collusion scenarios. The design-stage framing makes this less critical, but the lack of adaptive attacks is a major weakness.

### Experimental Design (Section 6)
"Experimental validation is in progress on cloud infrastructure." This is insufficient for TIFS. The planned comparisons (10 baselines, 10 ablations) are thorough, but no data, results, or analysis are presented. For a design-stage paper in a journal that requires validation, this section is effectively empty.

### Formal Analysis (Section 7)
This is the strongest technical section. The FPR bound derivation using Stewart's perturbation theorem is conceptually sound and well-presented. The fixed-point analysis of reputation scoring convergence is a nice touch. The fairness guarantee (R_SS=0.85) is well-motivated.

**Concerns**: The ~1.6% FPR bound depends on assumptions about spectral perturbation norms. Are these assumptions satisfied under realistic non-IID fraud distributions? How tight is the bound for worst-case versus average-case attacks?

### Regulatory Compliance (Section 9)
A worthy inclusion. The mapping to GDPR, SR 11-7, ECOA, and AML/CFT demonstrates awareness of deployment constraints. However, the analysis is shallow—it catalogs requirements without analyzing design tensions (e.g., how does a spectral anomaly detector meet the explainability requirements of ECOA?).

### Discussion & Conclusion
Appropriate for a design-stage paper. The limitations are acknowledged. The conclusion rightly emphasizes the open problems.

---

## Questions for Authors (4)

1. **Experimental Roadmap**: The paper states "Experimental validation is in progress on cloud infrastructure." What specific experimental results are currently available (if any), and what is the concrete timeline for completion? Would the authors be willing to provide preliminary results (e.g., on a single dataset) for an invited revision?

2. **Adaptive Adversary Modeling**: The threat model evaluates five static attack vectors (A1–A5). How robust is the L1/L2/L3 cascade against an *adaptive adversary* who observes the defense's behavior and crafts poison updates specifically to evade the spectral filter (L2) while maintaining a high reputation score (L3)? This is the most challenging threat for a layered defense and is currently unaddressed.

3. **Threshold Escalation Dynamics**: The adaptive threshold escalation policy is a key innovation but is presented abstractly. How is the policy parameterized? Is there a formal convergence guarantee for the adaptive thresholds, and how do they interact with the fixed-point convergence of the EMA reputation scores?

4. **Regulatory Tensions**: The paper maps regulatory requirements (GDPR, ECOA) but does not resolve tensions (e.g., ECOA's adverse action notification vs. the black-box nature of PCA spectral anomaly detection). How would the authors reconcile the need for per-instance explainable decisions in credit denial with the use of a high-dimensional spectral filter that resists straightforward interpretation?

---

## Dimension Scores

| Dimension | Weight | Score | Weighted Score | Notes |
|---|---|---|---|---|
| **Originality** | 20% | 70 | 14.00 | Statelessness blind spot is novel and well-identified. Framework layers are individually known but the cascade and temporal awareness are new. |
| **Methodological Rigor** | 25% | 35 | 8.75 | Design logic is sound, but the threat model is underdeveloped (no adaptive adversary), and the core adaptive threshold mechanism is underspecified. |
| **Evidence Sufficiency** | 25% | 5 | 1.25 | **No experimental results.** The paper explicitly relies on "expected results" and validation "in progress," which is insufficient for TIFS acceptance. |
| **Argument Coherence** | 15% | 78 | 11.70 | Clear, well-structured narrative. The motivation, design, and evaluation plan flow logically. |
| **Writing Quality** | 15% | 85 | 12.75 | Well-written. Technical concepts are presented clearly. The abstract and introduction are strong. |
| **Weighted Average** | 100% | — | **48.45** | |

---

## Editorial Decision Rationale

The proposed framework addresses a genuine gap in the robust FL literature. The statelessness critique, the layered cascade design, and the formal analysis (Stewart's theorem FPR bound, fixed-point convergence, fairness floor) represent solid theoretical groundwork. The topic is well-aligned with TIFS scope.

However, the fundamental barrier is the absence of empirical validation. TIFS is not a venue for design-stage proposals. A paper without experimental results—where the core contribution hinges on demonstrated robustness, FPR, and attack mitigation—cannot be published. Additionally, the manuscript length (~7 pages) and the underdeveloped threat model (no adaptive adversary, opaque threshold dynamics) limit the paper's readiness even for a major revision path.

**Recommendation**: **Reject for TIFS**

The authors are strongly encouraged to:
1. Complete the planned experimental validation.
2. Incorporate adaptive adversaries into the threat model.
3. Formalize the adaptive threshold escalation policy.
4. Expand the paper to full TIFS length (12–15 pages).

An invited resubmission of the completed work would be welcome, or the authors may consider targeting a workshop (e.g., ACM AISec, ICML FL Workshop) for earlier dissemination of the design ideas.
