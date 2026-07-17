# Regulatory Explainability

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Issue:** R9 — Address regulatory explainability  
**Date:** 2026-07-06

---

## 1. The Challenge

The Devil's Advocate review asked: *"How does a bank explain the denial of a credit card transaction when the model was trained with spectral filtering?"*

The Domain Expert (R2) added: *"Regulatory scrutability. How does a bank justify denial from a black-box neural net? GDPR Article 22 says citizens can contest decisions based solely on automated processing."*

This is a real compliance requirement.

---

## 2. Key Insight: Spectral Filtering ≠ Spectral Decisions

The confusion comes from conflating:

| Process | Spectral? | What Happens |
|---------|-----------|-------------|
| **Training-time detection** (Layer 2) | ✅ Yes | SVD filters malicious gradient updates during FL training |
| **Inference-time decision** (bank's model) | ❌ No | The trained model is a standard neural network — it makes predictions normally |

The SVD operates on *gradients during training*, not on *transactions during inference*. A bank deploying the trained model can explain each decision exactly as they would with any other neural net:

- SHAP/LIME on the frozen model
- Gradient-based attribution (Integrated Gradients)
- Counterfactual explanations
- Rule extraction (decision trees approximating the network)

### 2.1 Why This Matters for the Paper

> *"Our defense operates exclusively at training time. The output is a standard neural network identical in architecture to FedAvg or any other FL baseline. The bank's explainability obligations are the same regardless of whether the training used spectral filtering, robust aggregation, or simple averaging."*

This parallel is drawn to Krum, Trimmed Mean, or any robust aggregation method — none of them require special explainability procedures at inference time.

---

## 3. Regulatory Framework

### 3.1 GDPR Article 22 — Automated Decision-Making

**Right:** data subjects have the right not to be subject to decisions based solely on automated processing that produce legal effects.

**Our response:**

| GDPR Requirement | How Our System Meets It |
|-----------------|------------------------|
| **Meaningful information** about logic | The inference model is explainable via SHAP/LIME/Integrated Gradients. Defense layers are *training-time* only |
| **Significance and consequences** | Banks provide standard Fraud Alerts — our process doesn't change this |
| **Right to contest** | The final model's predictions can be contested via standard appeal process |
| **Human review** | The Adaptive Threshold Escalation alarm (§R2) triggers human review, satisfying Art. 22(2)(b) |

### 3.2 Banking Supervision (ECB, OCC, APRA)

| Requirement | Compliance |
|------------|-----------|
| **Model risk management** (SR 11-7) | Ablation study (§R8) validates each layer's contribution. DP ablation (§R3) quantifies privacy-utility trade-off |
| **Audit trail** | Every detection decision (which clients flagged, which layer, what threshold) is logged. Immutable blockchain audit trail proposed |
| **Fair lending** | Fairness analysis (§R10) ensures minority-serving banks aren't disproportionately flagged |
| **Explainability** | Final model is standard NN. Gradient-level spectral operations are training-only |

### 3.3 FATF (Financial Action Task Force) Guidance

FATF Recommendation 15 requires financial institutions to understand and document their AML/CFT systems. Our defense is *more* transparent than standard black-box FL because:

1. **Each layer's scoring rule is mathematically specified** (norm/cosine, SVD, EMA)
2. **The adaptive threshold is interpretable** — a $2\sigma$ alarm is a well-understood statistical concept
3. **All anomaly scores are logged** — an auditor can inspect why any specific update was flagged

---

## 4. Explainability Architecture

```
                        ┌─────────────────────────────┐
                        │   Trained Global Model       │
                        │   (standard NN, no spectral) │
                        └──────────┬──────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
    ┌─────────┴─────────┐                    ┌──────────┴──────────┐
    │ SHAP/LIME          │                    │ Adaptive Threshold │
    │ (transaction-level)│                    │ Escalation Log     │
    │                    │                    │ (defense audit)     │
    └───────────────────┘                    └─────────────────────┘
              │                                         │
              │                                         │
    ┌─────────┴─────────────────────────────────────────┴──────────┐
    │                    Bank's Explanation Engine                   │
    │                                                                 │
    │  "Transaction #48291 was flagged because:                       │
    │   • Risk score > threshold (SHAP: amount + location + velocity) │
    │   • Fraud probability: 92%                                      │
    │   • Training defense active: all layers passed audit check"     │
    └─────────────────────────────────────────────────────────────────┘
```

---

## 5. Practical Explanation Flow

### Scenario: Transaction denied for customer

```
Customer: "Why was my card declined?"

Bank:
Step 1 — Model explanation (same as any fraud detection):
  "The transaction was flagged because:
   - Amount ($950) is 3× your typical transaction
   - Merchant category (electronics) is unusual for you
   - Location (Country Y) is outside your travel pattern
   These factors contributed to a fraud probability of 92%."

Step 2 — Defense explanation (only if customer asks about training):
  "The model was trained collaboratively across 20 banks using
  a federated learning system with active defense against data
  poisoning. Your transaction's decision is based on the final
  trained model — the defense only affects how the model was
  built, not how it evaluates your transaction."
```

**Key:** The bank never needs to mention spectral decomposition or SVD to the customer. The defense is an infrastructure detail, like the choice of optimizer or regularization.

---

## 6. Implementation: Explanation Module

```python
class DefenseExplainer:
    """Generates human-readable explanations of defense decisions.

    Used for regulatory audit, not for customer-facing explanations.
    """

    def __init__(self, history: DefenseHistory):
        self.history = history

    def explain_flagging(self, client_id: int, round_t: int) -> str:
        """Explain why a specific client was flagged at a specific round."""
        record = self.history.get(client_id, round_t)
        if record is None:
            return f"Client {client_id} was not flagged at round {round_t}."

        parts = []
        if record.get("layer1_anomaly", 1.0) < 0.3:
            parts.append(
                f"• Layer 1 (Norm/Cosine): gradient norm {record['norm']:.2f} "
                f"exceeds the 2σ bound [{record['norm_lower']:.2f}, {record['norm_upper']:.2f}]"
            )
        if record.get("layer2_anomaly", 1.0) < 0.3:
            parts.append(
                f"• Layer 2 (Spectral): update has {record['nullspace_ratio']:.1%} "
                f"energy in the nullspace of honest updates"
            )
        if record.get("layer3_anomaly", 1.0) < 0.3:
            parts.append(
                f"• Layer 3 (Temporal): EMA reputation dropped "
                f"from {record['prev_reputation']:.3f} to {record['reputation']:.3f}"
            )

        return f"Client {client_id} flagged at round {round_t}:\n" + "\n".join(parts)

    def audit_trail(self, start_round: int, end_round: int) -> str:
        """Generate a regulatory audit report for a round range."""
        return self.history.to_dataframe(start_round, end_round).to_csv()
```

---

## 7. Paper Text

> **Regulatory Compliance.** Our defense layers operate exclusively during FL training. The final global model is a standard neural network, structurally identical to those produced by FedAvg or any other aggregation method. Banks deploying this model face no additional explainability burdens beyond standard neural network interpretation (SHAP, Integrated Gradients, counterfactual explanations). The defense's audit log (§...) provides regulators with a complete, immutable record of all detection decisions, satisfying model risk management requirements (SR 11-7, FATF Rec. 15).
>
> The Adaptive Threshold Escalation mechanism (§...) triggers human review during training when anomalous activity is detected, providing the meaningful human oversight required by GDPR Article 22(2)(b). Individual transaction decisions are contestable through standard bank appeals processes — the defense does not alter inference-time behavior.
