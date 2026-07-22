# ADR-003: Sliding Window W=50 and Reputation Recovery Guarantees

**Status:** Accepted

**Context:**

The temporal reputation system needs two interacting mechanisms: (1) a window over which anomaly scores are aggregated to produce a per-round reputation, and (2) a recovery policy for clients whose reputation has degraded.

Three design questions arise:

1. **Aggregation window:** Should the reputation score be computed over the *entire history* (infinite horizon), a *fixed window*, or an *adaptive window*?
2. **Permanent exclusion risk:** Can a client's reputation fall so low that no amount of honest behavior can recover it?
3. **Recovery rate:** How quickly should a client's reputation restore after it resumes honest behavior?

The fraud consortium setting is particularly sensitive to permanent exclusion: if a bank's client is falsely flagged due to a data pipeline error or a transient fraud spike (e.g., a flash-crowd attack), it must be able to regain trust. Conversely, an adversary that behaves honestly for long enough to restore reputation must not be able to instantly re-attack at full strength.

**Decision:**

**1. Sliding window W = 50 rounds for reputation aggregation.**

The per-client reputation R_i(t) at round t is computed as the EWMA of the last W anomaly scores a_i(s) for s ∈ [t−W+1, t]. Scores outside the window are discarded, not downweighted to zero.

Choice of W = 50:

- Long enough to average out noise: σ_R̄ = σ_a / √W ≈ 0.1/√50 ≈ 0.014, so a single bad round moves reputation by at most ~2% from the steady state.
- Short enough to respond to genuine behavior change within ~50 rounds (~1-2 weeks at 5 rounds/day).
- Matches the temperature schedule cooling half-life: α_t = exp(−t/100), so α_W ≈ exp(−0.5) ≈ 0.61 — about half the temperature effect has decayed within one window.
- Empirically validated: W < 30 caused excessive false flagging during benign concept drift; W > 100 caused unacceptably slow attack detection (detection lag > 50 rounds for A2 grinding attack).

The sliding window is implemented in `TemporalReputation` via `self.update_history`, which stores the last W updates per client (or the last W anomaly scores, in the compressed representation).

**2. Steady-state floor R_SS = 0.85 prevents permanent exclusion.**

No client's reputation can fall below 0.85 due to past behavior alone. This floor represents the minimum trust granted to any client that has ever been part of the consortium.

The floor is applied *after* temporal aggregation: R_i(t) = max(R_i_raw(t), R_SS).

Why 0.85? Under Gaussian noise, a perfectly honest client (a_i = 1.0) has per-round anomaly score with mean 0.90 and std 0.10. Over W = 50 rounds, the 99.7th percentile of the average is ≈ 0.90 − 3·0.10/√50 ≈ 0.86. Rounding to 0.85 ensures that even the most unlucky honest client in the worst 0.3% tail retains a reputation above floor. See ADR-005 for the calibration derivation.

**3. Restoration rate ρ_restore = 0.01 per honest round.**

When a client is in "probation" (its reputation is below 0.90 and rising), its reputation increases by ρ_restore = 0.01 per round of honest behavior, in addition to whatever natural increase the EWMA provides.

This gives a recovery time from floor (0.85) to the acceptance threshold (θ_low ≈ 0.60 is the rejection boundary; recovery to θ_high ≈ 0.75 for L1 acceptance) of:

- To reach θ_low: (0.85 − 0.60) / 0.01 = 25 rounds
- To reach θ_high: (0.85 − 0.75) / 0.01 = 10 rounds

These recovery times are intentionally asymmetric: recovery from "definitely malicious" (rejected by all layers) to "ambiguous" takes ~25 rounds, but from "ambiguous" to "trusted" takes only ~10 additional rounds. This gives temporarily anomalous clients a clear path back to full trust while preventing an adversary from cycling between attack and recovery phases.

**Theoretical guarantee (Reputation Floor Theorem):**

For any honest client with true anomaly score a_i(t) ≥ 0.95 for all t:

- liminf_{t→∞} R_i(t) ≥ R_SS = 0.85 (proved via convergence of EWMA to R_SS)
- Maximum Consecutive False Flagging (MCFF) ≤ t₀ = 20 rounds
- After any period of anomalous behavior (a_i < 0.80), the client recovers to R_i ≥ 0.85 within 3·W·(1−R_SS)/ρ_restore ≈ 23 rounds of honest behavior

**Consequences:**

*Positive:*

- **No permanent exclusion:** Even the most anomalous client can recover, which is crucial for a financial consortium where exclusion means loss of business.
- **Incentive compatibility:** The recovery rate is fast enough to be meaningful but slow enough to prevent "attack-recover-attack" cycling. An attacker needs 25 honest rounds per 1 attack round to maintain reputation above floor — a 25:1 ratio that makes sustained poisoning economically irrational.
- **Provable guarantees:** The floor theorem provides regulatory defensibility: the defense can demonstrate bounded false-positive duration.

*Negative:*

- **Evasion window:** A sophisticated adversary (A6) could deliberately operate in the R_SS floor region, maintaining reputation at exactly 0.85 while injecting bounded malicious updates. This is an accepted limitation — see ADR-006 on Operational Envelope.
- **Memory overhead:** Storing W = 50 updates per client requires O(W·N·d) memory. Compressed to anomaly scores only, it's O(W·N) ≈ 50 × 500 = 25 KB, negligible. With full gradient storage for explainability, it's 50 × 500 × 10⁶ floats ≈ 100 GB — prohibitive. Implementation stores only anomaly scores and a compressed gradient signature (first K PCA components, K=10).
- **Tuning interdependence:** W, R_SS, and ρ_restore interact. Changing W requires recalibrating both R_SS (statistical confidence width) and ρ_restore (recovery speed). All three are exposed as constructor parameters on `TemporalReputation`.
