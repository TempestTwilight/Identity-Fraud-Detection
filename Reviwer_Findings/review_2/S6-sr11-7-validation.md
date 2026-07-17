# S6: SR 11-7 Validation Cycle

**Issue:** The Domain Expert flagged that the paper entirely omits how SR 11-7 (and equivalent banking regulations: ECB Guide to ML, APRA CPG 234, PRA SS1/23) model validation applies to the proposed defense.
**Reviewers:** Domain (P2), Perspective
**Severity:** 🟡 Must Fix Before TIFS Submission

---

## 1. What SR 11-7 Requires

SR 11-7 (and its international equivalents) mandates three validation elements for any quantitative model used in regulated banking:

| Phase | Requirement | Our Response |
|-------|-------------|-------------|
| **Development** | Sound methodology, documented assumptions | ✅ Covered by paper |
| **Ongoing monitoring** | Continuous assessment of model performance, concept drift detection, benchmark comparison | ❌ **Missing** — the paper treats evaluation as one-time, not ongoing |
| **Outcomes analysis** | Compare predicted outcomes to actual outcomes at the individual transaction level | ❌ **Missing** — paper evaluates aggregate metrics (ASR, AUC) not per-transaction outcome analysis |

## 2. What We Need to Add

### 2.1 Ongoing Monitoring Protocol

A dedicated monitoring loop that runs alongside the FL training:

```
Each round t:
  1. Train FL round → new global model w_(t+1)
  2. Holdout validation: evaluate w_(t+1) on held-out validation set
  3. Concept drift detection: compare w_(t+1) to baseline model w_0
     - If ‖w_(t+1) - w_0‖ / ‖w_0‖ > δ → flag for review
  4. Benchmark comparison: compare w_(t+1) to best-known baseline
     - If ASR(w_(t+1)) > ASR(w_baseline) + ε → flag for review
  5. Defense calibration: check that threshold τ₁, τ₂ haven't drifted outside expected range
     - If any threshold has been at its min/max for > T max rounds → flag for calibration review
```

This monitoring loop can be implemented as a **cron job in production** that fires alerts rather than blocking training — minimal overhead.

### 2.2 Outcomes Analysis

When the defense flags a client as malicious:
1. **Retrospective analysis:** Were that client's previous 5 updates anomalous? (temporal pattern)
2. **Cross-reference:** Did other layers flag the same client? (cascade consistency)  
3. **False positive review:** If the flagged client was later confirmed honest, what triggered the false alarm? (root cause → threshold adjustment)

### 2.3 Governance Structure

Define a minimum governance framework:

| Role | Responsibility | Independence |
|------|---------------|-------------|
| **Model owner** | Runs FL training, configures defense parameters | Same institution as server operator |
| **Model validator** | SR 11-7 validation: monitors ongoing performance, conducts annual review | Independent from model owner (different team or external auditor) |
| **Consortium oversight** | Reviews flagged events, approves threshold changes, manages client exits/rejoin | Cross-institutional committee |

## 3. Why This is Addressed at Design Level (Not Implementation)

The paper is a design-stage chapter plan. The SR 11-7 validation structure is **documented as a governance framework** that implementing banks would follow. The design provides:

- Monitoring protocol ✅ (programmable)
- Outcomes analysis procedure ✅ (traceable)  
- Governance structure ✅ (definable)
- Threshold calibration rules ✅ (from S2 convergence bounds)

The actual implementation is the responsibility of the deploying institution's compliance team.

## 4. Paper Changes

| Change | Location |
|--------|----------|
| Add "Regulatory Validation" subsection | Paper §9 (Discussion) |
| Add monitoring protocol pseudocode | Paper §8 (Deployment) |
| Reference SR 11-7, ECB Guide, APRA CPG 234 | Paper §8-9 |
| Add governance role table | Paper §8 |
