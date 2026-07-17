# S9: A2-Grinding Reactive Variant

**Issue:** The Gradient Grinding attack (A2) uses a fixed 4-phase schedule (burn-in → subliminal → active → cooldown) that does not react to defense feedback.
**Reviewers:** Methodology (C3)
**Severity:** 🟢 Strongly Recommended

---

## 1. Current Design (Fixed Schedule)

```
Phase 1 (rounds 1-15):  Burn-in — honest behavior, norm=1.0× mean
Phase 2 (rounds 16-25): Subliminal drift — norm=1.02× mean, drift=0.01× grad per round
Phase 3 (rounds 26-50): Active — norm=1.1× mean, drift=0.05× grad per round
Phase 4 (rounds 51-200): Cooldown — drift halts, norm returns to 1.0× mean
```

The problem: the attacker doesn't adjust strategy based on whether the defense detects them. A real adversary would.

## 2. Reactive Variant (A2-Adaptive)

Add a defense-aware policy that adjusts the attack in response to detection signals:

```
def reactive_step(state, defense_feedback):
    """
    Args:
        state: current attack phase + round + drift parameters
        defense_feedback: {flagged: bool, anomaly_score: float, confidence: float}
    """
    if defense_feedback['flagged']:
        # Detected — pull back
        state.phase = 'cooldown'
        state.drift_rate *= 0.5  # Reduce aggression
        state.cooldown_rounds = 5
    elif state.phase == 'cooldown' and not defense_feedback['flagged']:
        state.cooldown_rounds -= 1
        if state.cooldown_rounds <= 0:
            # Resume attack with slightly lower aggression
            state.phase = 'subliminal'
            state.drift_rate *= 0.8
    else:
        # Not detected — increase aggression
        state.drift_rate *= 1.02
        state.drift_rate = min(state.drift_rate, state.MAX_DRIFT_RATE)
    
    return state
```

## 3. λ_max Bounding

The fixed drift rate λ_max (maximum per-round gradient drift) is currently underspecified. For the reactive variant:

| Phase | λ_max | Rationale |
|-------|-------|-----------|
| Burn-in | 0.0 | No poisoning |
| Subliminal | 0.01 × ‖g‖ | Below L1's 3σ threshold for norm change |
| Active | 0.03 × ‖g‖ | Below SVD detectable threshold (Stewart bound: < 2/(0.3√N)) |
| Cooldown | 0.005 × ‖g‖ | Below L3 EMA detection threshold |

## 4. Implementation

Add `ifd_fintech/attacks/a2_grinding_adaptive.py` extending the base A2 with reactive policy and defense feedback loop. The FL simulator passes each client's anomaly score and flag status back to the attacker module each round.
