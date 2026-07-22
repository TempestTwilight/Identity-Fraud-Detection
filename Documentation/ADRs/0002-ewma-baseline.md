# ADR-002: EWMA Baseline (not static warm-up)

**Status:** Accepted

**Context:**

Traditionally, Byzantine-robust defenses establish a "normal" baseline using a static warm-up phase: collect t₀ rounds of known-honest updates, estimate mean and variance, and use these fixed statistics for all subsequent rounds. This one-shot approach has three fatal flaws in the fraud detection setting:

1. **Concept drift:** Credit card fraud patterns evolve. A baseline frozen at round 20 becomes stale by round 200 as the honest client distribution shifts.
2. **Poisoning vulnerability (Lai et al. 2024):** An adversary that remains dormant during warm-up can launch attacks immediately afterward, evading a static baseline that has no memory of post-warm-up behavior.
3. **No forgetting:** A client falsely flagged at round 50 carries that stain forever if the baseline never updates.

The alternative is a dynamic baseline that continuously evolves, weighting recent observations more heavily while retaining long-term structure.

**Decision:**

Each client's reputation baseline evolves via **Exponentially Weighted Moving Average (EWMA)**, not a static warm-up.

**The update equations:**

- Mean reputation:  R̄_i(t+1) = λ·R̄_i(t) + (1−λ)·R_i(t+1)
- Std deviation:    σ_R,i(t+1) = √(λ·[σ_R,i(t)]² + (1−λ)·(R_i(t+1) − R̄_i(t+1))²)

**Parameters:**

- Smoothing factor λ = 0.995
- Effective memory W_h = 1/(1−λ) = 200 rounds
- Bootstrap: TEE (Trusted Execution Environment) for first t₀ = 20 rounds
- Post-bootstrap: robust initial estimator using median-of-means

**Why λ = 0.995?**

With W_h = 200 rounds, the baseline retains signal from roughly the last 200 rounds but gracefully forgets older history. This matches the time scale of realistic fraud pattern shifts (seasonal cycles ~90 days, retraining cadence ~weekly, so ~200 FL rounds at 10 rounds/day). A smaller λ (e.g., 0.99, W_h = 100) forgets too quickly, making the defense vulnerable to "grinding" attacks that drift the baseline. A larger λ (0.999, W_h = 1000) is too slow to adapt to genuine concept drift.

**Bootstrap safeguards:**

- **TEE phase (rounds 0–20):** All updates processed inside a trusted execution environment with known-honest initial seeds. No baseline adaptation occurs; instead, a robust initial estimator is computed from all 20 rounds using median-of-means (dividing 20 rounds into 4 groups of 5, taking mean of each group, then median of the 4 means).
- **Blinding:** During bootstrap, the adversary does not know which rounds are warm-up. The orchestrator randomly samples 20 rounds from the first 30 as the effective bootstrap set, with the remaining 10 rounds serving as validation.

**Consequences:**

*Positive:*

- **Concept drift adaptation:** The baseline tracks slow changes in honest client behavior (e.g., seasonal fraud pattern evolution, new merchant category codes).
- **Automatic forgetting:** A client with a temporarily anomalous period (e.g., a bank's internal system migration) recovers naturally as old low-reputation observations are exponentially downweighted.
- **Grinding attack resistance:** An adversary that injects +0.01 anomaly per round for 100 rounds would need to inject a total drift of ~1.0 to meaningfully shift the baseline, but by round 50 the early injections have λ^50 ≈ 0.78 weight remaining — the baseline partially forgets the earliest poison.
- **Provable convergence:** For honest clients (a_i ≥ 0.95), liminf R_i ≥ R_SS = 0.85. Formal proof in ADR-007.

*Negative:*

- **Statefulness:** Each client requires persistent state (R̄_i, σ_R,i, rounds_seen). For 500 clients, this is ~4 KB — negligible.
- **Cold start:** New clients have no history. The defense uses a conservative initial reputation R̄_i(0) = 1.0 with high initial uncertainty σ_R,i(0) = 0.3, ensuring new clients are escalated to L2 by default for the first 10 rounds.
- **Parameter sensitivity:** λ must be tuned to the FL round cadence. If rounds happen hourly instead of daily, W_h should be adjusted. Configurable via `TemporalReputation.alpha = 1 - λ`.

*Implementation:*

The EWMA baseline lives in `TemporalReputation` (layer3_temporal.py). Each client's EMA update vector (`self.ema_updates[client_id]`) tracks the expected update direction. The anomaly score is computed as cosine similarity between the client's current update and its EMA-predicted update, normalized by the EMA standard deviation.
