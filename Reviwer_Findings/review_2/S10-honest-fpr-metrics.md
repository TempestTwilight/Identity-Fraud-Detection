# S10: Honest FPR Evaluation — Temporal and Outlier Metrics

**Issue:** The current honest FPR metric reports per-round false positive rate averaged across all rounds. This misses temporal patterns (consecutive false flags that compound reputation damage) and fails to cover the "benign outlier" scenario.
**Reviewers:** Methodology (C4)
**Severity:** 🟢 Strongly Recommended

---

## 1. Missing Metrics

### 1.1 Max Consecutive False Flags (MCFF)

The number of consecutive rounds an honest client is falsely flagged. This captures the **reputation damage** from a false positive burst:

```
For each honest client i:
  consecutive_flags[i] = 0
  for round t:
    if flagged(i, t) then consecutive_flags[i] += 1
    else reset: consecutive_flags[i] = 0

MCFF = max over all honest clients of consecutive_flags[i]
```

If MCFF > 5 (the probation threshold from S7), a single false-positive burst could trigger the procedural safeguard and permanently damage reputation — even if the average FPR is small.

### 1.2 Detection Window (DW)

The number of rounds from defense deployment to first false flag. Measures the cold-start robustness of the temporal reputation system:

```
DW = min over honest clients of (first round t where flagged(i, t) = True)
```

Small DW means the defense starts flagging honest clients immediately — dangerous for new consortium members.

### 1.3 Per-Layer Resolution Rate

For each false flag, which layer triggered it? This helps identify the primary fairness risk:

```
For each false flag event:
  Determine the escalation layer [L1, L2, L3] that made the final decision
  Increment that layer's false flag counter
```

If Layer 2 is responsible for > 50% of false flags, the SVD subspace is the primary fairness risk (confirming S7's analysis).

## 2. Benign Outlier Scenario

Current evaluation assumes honest clients are statistically "normal" (within the distribution). In real banking:
- A community bank serving recent immigrants may have a transaction profile that looks anomalous to the consortium
- A credit union specializing in small-business lending has a different fraud distribution than consumer-focused retail banks

**New scenario:** Create a "benign outlier" client with:
- Transaction distribution drawn from a different Dirichlet parameter than the majority (α_benign = 0.3 vs α_majority = 0.5)
- Fraud rate that is higher but legitimate (4% vs 2% consortium average)
- Update norm that is systematically 1.5σ above the mean (realistic for high-volume business banking)

**Expected outcome:** The defense should flag this client initially (L1/L2 see the statistical difference) but clear it after enough rounds when the temporal reputation system learns its pattern. If the defense permanently penalizes this client, it has a structural fairness problem.

## 3. Code Changes

Add metrics to `ifd_fintech/experiment/metrics.py`:

```python
def compute_temporal_fpr(flag_history: np.ndarray) -> dict:
    """Compute temporal FPR metrics from per-round flag matrix.
    
    Args:
        flag_history: (T, N) boolean matrix of flag status per round per client
        
    Returns:
        dict with MCFF, DetectionWindow, per-layer resolution
    """
    N_clients = flag_history.shape[1]
    
    mcff = max(_longest_consecutive_streak(flag_history[:, i]) 
               for i in range(N_clients))
    
    first_flags = [np.argmax(flag_history[:, i]) 
                   for i in range(N_clients)]
    detection_window = min(first_flags) if any(f == True for f in first_flags) else 0
    
    return {"MCFF": mcff, "detection_window": detection_window}
```

## 4. Paper Changes

| Change | Location |
|--------|----------|
| Add temporal FPR metrics (MCFF, DW) to evaluation section | Paper §7 (Experimental Design) |
| Add benign outlier scenario | Paper §7 (Experimental Design — non-IID splits) |
| Add per-layer false flag analysis | Paper §7 (Results) |
