# S7: Structural Fairness — Temporal Reputation Downward Spiral

**Issue:** The Perspective reviewer identified a structural fairness blind spot: the temporal reputation system (Layer 3) creates a feedback loop that can systematically penalize minority-serving banks, creating a "cold start → flagging → reputation drop → more flagging" spiral.
**Reviewers:** Perspective (primary), Domain (R10), Ethics
**Severity:** 🟡 Must Fix Before TIFS Submission

---

## 1. The Problem

The current reputation update (from `orchestration/`):

```
R_i(t+1) = (1 - α) · R_i(t) + α · s_i(t)
```

Where s_i(t) is the anomaly score for client i at round t. The problem:

1. **Cold start:** New clients start at R_i = 1.0 (perfect trust)
2. **First flag:** A minority bank with genuinely different data may trigger L1 or L2 → s_i(t) ≈ 0.3
3. **Reputation drop:** R_i drops from 1.0 → 0.937 after one low score (α=0.1)
4. **Lower reputation → greater suspicion:** s_i(t) includes R_i(t) in L3's scoring: a_3,i = R_i(t) · (update consistency)
5. **Self-reinforcing:** Lower R_i means even normal updates from this client get lower scores → further reputation drops
6. **Systematic exclusion:** After enough drops, R_i < θ_reject → client permanently excluded from aggregation

**This is a structural fairness failure, not a statistical anomaly.** It would disproportionately affect:
- Small banks with volatile transaction patterns (higher variance = more flags)
- Minority-serving banks with different fraud profiles (different fraud types = flag by L2)
- New entrants without historical data (cold start → immediate scrutiny)

## 2. Mitigation Design

### 2.1 Forgetting Mechanism (Old Penalty Decay)

Add a decay coefficient γ that gradually restores reputation from past low scores:

```
R_i(t+1) = R_i(t) + α · (s_i(t) - R_i(t)) + γ · (R_i_ss - R_i(t))
```

Where R_i_ss = 0.85 is a "steady-state" reputation that the system pulls toward. This means:
- A single bad round temporarily drops reputation by ~α·Δs
- Over subsequent normal rounds, reputation drifts back toward R_i_ss at rate γ
- Persistent bad behavior must outpace the upward drift to maintain low reputation

Default parameters: γ = 0.02 (≈ 50 rounds to recover from a 0.3-point drop)

### 2.2 Fairness Intervention Triggers

Monitor three fairness metrics in real-time:

| Metric | Threshold | Action |
|--------|-----------|--------|
| **Max FPR gap** across client <0,1,2> | max(FPR) - min(FPR) > 0.10 | Freeze reputation updates; flag for human review |
| **Correlation** between FPR and client size (transaction volume) | ρ(FPR, log(volume)) > 0.5 | Restrict L2's authority: L2 score can only demote to "suspicious", not "reject" |
| **Exclusion rate** per subgroup | Exclusion_Rate_minority / Exclusion_Rate_majority > 2 | Halt adaptive thresholds; use fixed thresholds until review |

### 2.3 Procedural Safeguard

Add a **due process** mechanism: any client whose reputation drops below θ_reject (permanent exclusion threshold) enters a probationary state rather than immediate rejection:

```
if R_i(t) < θ_reject:
    # Not immediately excluded — enter probation
    if probation_rounds[i] < PROBATION_LIMIT (≈ 10 rounds):
        # Down-weight but don't exclude
        w_i(t) = w_i(t) · 0.25  # 75% weight reduction instead of 100%
        probation_rounds[i] += 1
    else:
        Exclude client i from aggregation
        Flag for consortium human review
```

This prevents a single volatile round from permanently excluding a legitimate bank.

## 3. Code Changes

Add to the reputation update in `orchestration/`:

```python
def _update_reputations(self, scores, updates):
    ALPHA = 0.1   # EMA smoothing
    GAMMA = 0.02  # Forgetting/restoration rate
    R_SS = 0.85   # Steady-state reputation
    
    for i in range(len(scores)):
        # Standard EMA with forgetting term
        self.reputations[i] = (
            self.reputations[i] 
            + ALPHA * (scores[i] - self.reputations[i])
            + GAMMA * (R_SS - self.reputations[i])
        )
        self.reputations[i] = np.clip(self.reputations[i], 0.0, 1.0)
```

## 4. Paper Changes

| Change | Location | 
|--------|----------|
| Add fairness-forgetting mechanism to reputation update | Paper §6 (Proposed Framework) | 
| Add fairness intervention triggers | Paper §6 (Proposed Framework) |
| Add procedural safeguard (probation before exclusion) | Paper §6 (Proposed Framework) |
| Add fairness evaluation as a required metric | Paper §7 (Experimental Design) |
| Address structural fairness in discussion | Paper §9 (Discussion) |
