# ADR-001: Gated Cascade vs. Fusion Ensemble

**Status:** Accepted

**Context:**

The defense framework must combine three detection layers — Norm/Cosine filtering (L1), Spectral anomaly detection (L2), and Temporal reputation scoring (L3) — each producing an `(anomaly_score, confidence)` pair per client per round. The core architectural question is *how* to combine these signals.

Two competing patterns exist in the literature:

1. **Fusion ensemble:** Each layer produces an independent score; scores are combined via a weighted sum (e.g., learned weights, fixed heuristics, or meta-classifier) into a single decision value. Used by FLDetector (Zhang et al. 2022) and most ensemble-based defenses.

2. **Gated cascade:** Layers are arranged in a decision pipeline. L1 (O(d)) resolves ~80% of updates confidently. Only uncertain cases (confidence ∈ [θ_low, θ_high]) escalate to L2 (O(Nd²)), and fewer still to L3 (O(1) per client). The orchestrator uses confidence to gate escalation, not to blend scores.

The fraud detection domain imposes hard constraints: a credit card transaction must be scored in milliseconds, and the FL server handles hundreds of clients per round. The defense cannot afford to run all three layers on every update in every round.

**Decision:**

We adopt the **gated cascade** architecture with confidence-based escalation, NOT a fusion ensemble.

The orchestrator (`AdaptiveThresholdEscalation`) implements a decision tree:

- **Accept zone** (anomaly_score ≥ θ_high, confidence high): update accepted immediately, no escalation.
- **Escalation zone** (θ_low ≤ anomaly_score ≤ θ_high): escalate to next layer.
- **Reject zone** (anomaly_score < θ_low, confidence high): update rejected outright.

Each layer computes two scalars per client: anomaly score (how honest the update looks, in [0,1]) and confidence (how certain the layer is, in [0,1]). The orchestrator routes based on confidence, not score. When L1 is highly confident (confidence > 0.9), its decision is trusted. When confidence is low, the case is escalated.

This contrasts with fusion, where all three scores would be multiplied/weighted into a single composite score. In cascade, L2 and L3 are invoked only on the subset of updates that L1 cannot confidently classify — typically 15–25% of updates per round.

**Consequences:**

*Positive:*

- **Computational efficiency:** L1 runs on all N updates (O(Nd)). L2 runs on ~0.2N updates (O(0.2N·d²)). L3 runs on ~0.05N updates (O(0.05N)). Total cost ≈ O(Nd + 0.2Nd²) vs. O(Nd² + N·T_L3) for fusion. For d=10⁶, this is a ~5× savings per round.
- **Interpretability:** Each decision is traceable to a specific layer. The `DefenseRecord.explain()` method shows exactly which layer flagged a client and why, aiding regulatory compliance (GDPR Art. 22, SR 11-7).
- **Graceful degradation:** If L2 encounters too few clients for SVD (N < 3), the orchestrator falls back to L1+L3 only. Fusion ensembles cannot degrade gracefully — they require all scores to compute.
- **Attack isolation:** The cascade prevents a single compromised layer from corrupting all decisions. An adversary that evades L1 must still face L2 and L3 independently.

*Negative:*

- **Information loss:** L2 and L3 do not see all updates. An attack that only manifests via L2's spectral signature across *all* clients (including those L1 accepted) could be missed. Mitigated by periodic full sweeps every W=50 rounds and by monitoring aggregate loss for attack alarms.
- **Ordering sensitivity:** The cascade is order-dependent. L1 runs first by design (cheapest), but if a hypothetical attack targets only L2's spectral view, the gating could filter out the very updates needed to detect it. The adaptive alarm signal (loss jump detection) catches this case.
- **Threshold tuning complexity:** Adds two decision thresholds (θ_low, θ_high) that must be calibrated jointly across layers. Calibration procedure in ADR-005.

*Migration/Tuning:*

To switch to fusion, replace the escalation logic in `AdaptiveThresholdEscalation.process_round()` with a weighted combination of the three anomaly scores. The layer interfaces (`score() -> (anomaly_score, confidence)`) remain unchanged. Fusion would require re-tuning all ablation configurations and likely increase compute cost without improving ASR (empirically verified in ablation study configs `ensemble_vs_cascade`).
