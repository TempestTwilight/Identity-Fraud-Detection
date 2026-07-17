# S8: Regulatory Overconfidence — Correction Document

**Issue:** The Perspective reviewer flagged that the paper's GDPR and banking regulation compliance mapping is overconfident and incomplete.
**Reviewers:** Perspective (primary), Domain
**Severity:** 🟡 Must Fix Before TIFS Submission

---

## 1. Specific Corrections

### 1.1 GDPR: Gradients = Personal Data

**Current claim:** Gradient leakage is unlikely because "batch-size arguments and tabular data reduce reconstruction risk."
**Correction:** Under GDPR Art. 4(1), a gradient is personal data if it relates to an identifiable natural person. The CJEU's *Nowak* decision (2017) established that exam answers are personal data even without names — gradients similarly encode transaction-level information.

**Required change:** Acknowledge that gradients are personal data. The paper's privacy argument should not minimize this but instead explain why the *processing* (FL training with honest server) satisfies GDPR Art. 6(1)(f) legitimate interest basis.

### 1.2 GDPR: DPIA is Mandatory

**Current claim:** DPIA as "future work."
**Correction:** GDPR Art. 35 requires a DPIA for processing that "is likely to result in high risk to the rights and freedoms of natural persons" — which fraud detection definitively does (Art. 35(3)(a) systematic evaluation of personal aspects; Art. 35(3)(b) processing on a large scale).

**Required change:** DPIA is not optional. The paper should either (a) provide a DPIA framework, or (b) acknowledge this is a deployment-stage requirement and provide the structure in an appendix.

### 1.3 AML/CFT Override

**Most critical regulatory gap:** No fraud detection system can guarantee 100% detection. When the system fails to flag a fraudulent transaction, the bank may still have a **mandatory Suspicious Activity Report (SAR) filing obligation** under the Bank Secrecy Act / AML Directive.

**Required change:** Add a subsection acknowledging that our defense does not eliminate SAR obligations — it merely reduces the frequency of missed detections. The defense should be positioned as a *risk reduction tool* within the existing AML compliance framework, not a replacement for it.

### 1.4 Cross-Jurisdictional Compliance

**Current claim:** References GDPR and SR 11-7 as if they coexist harmoniously.
**Correction:** GDPR's data minimization (Art. 5(1)(c)) can conflict with SR 11-7's model validation data retention requirements. A bank operating in the EU (GDPR) and US (GLBA/SR 11-7) faces conflicting obligations.

**Required change:** Acknowledge this tension and flag it as a deployment consideration.

## 2. Summary Table of Corrections

| Regulation | Previous Claim | Corrected Claim |
|-----------|---------------|-----------------|
| GDPR Art. 4(1) | Gradients are not personal data | Gradients are personal data; processing is Art. 6(1)(f) legitimate interest |
| GDPR Art. 35 | DPIA is optional future work | DPIA is mandatory; framework provided in appendix |
| AML/BSA | (missing) | SAR obligations remain; defense reduces false negative rate but does not eliminate reporting duty |
| SR 11-7 | Validation is one-time | Validation is ongoing (S6) |
| Cross-jurisdiction | (assumed compatible) | GDPR-GLBA-APRA tensions acknowledged |
| Consumer protection (FCRA, ECOA) | (missing) | Adverse action notice requirements when bank uses model output to deny service |
