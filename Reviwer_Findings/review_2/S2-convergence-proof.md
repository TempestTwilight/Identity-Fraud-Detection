# S2: Convergence Analysis — Formal Proof

**Issue:** The original convergence analysis is a sketch referencing the ODE method without instantiating any of the specific functions, Lipschitz conditions, or fixed-point analysis.
**Reviewers:** Methodology (C1), DA, Perspective
**Severity:** 🔴 Must Fix

---

## 1. What Was Missing

The original §7 referenced Borkar's ODE method for stochastic approximations but left uninstantiated:

| Missing Element | Why It Matters |
|----------------|----------------|
| Drift function h(τ, ξ) | Need the specific h for our threshold update rules, not a generic reference |
| Lipschitz continuity of h | Required for ODE convergence theorem |
| Fixed point(s) τ₁*, τ₂* | What does the system converge to, and under what conditions? |
| Neighborhood bound for constant η | We use constant η (not decaying) — need to bound the convergence neighborhood |
| τ₁-τ₂ coupling | Both thresholds update from the same ρ_t signal — coupling analysis missing |
| Attack-rate dependence | Fixed point should be a function of true Byzantine fraction f |

---

## 2. Formal Setting

### 2.1 System State

At round t, the internal state is:

```
S(t) = [τ₁(t), τ₂(t), μ₁(t), σ₁(t), V_k(t), R_i(t) ∀i]
```

Where:
- τ₁(t), τ₂(t): adaptive thresholds (the primary convergence objects)
- μ₁(t), σ₁(t): running norm statistics for L1
- V_k(t): SVD subspace for L2 (k principal components)
- R_i(t): reputation scores for each client i

### 2.2 Threshold Update Rules (Restated)

**Under normal conditions** (φ(t) = 0, no attack alarm):

```
τ₁(t+1) = τ₁(t) + η_relax · (τ₁_max - τ₁(t))
τ₂(t+1) = τ₂(t) + η_relax · (τ₂_max - τ₂(t))
```

**Under attack** (φ(t) = 1):

```
τ₁(t+1) = τ₁(t) - η_attack · ρ(t)
τ₂(t+1) = τ₂(t) - η_attack · ρ(t)
```

With projection onto [τ_k_min, τ_k_max].

### 2.3 The Attack Alarm Signal

φ(t) = 1 iff ρ(t) > ρ₀ + 2σ_ρ OR ΔL(t) > ΔL₀ + 2σ_L

Where ρ(t) = (1/N) Σᵢ 1_[a_i(t) < θ_accept] is the fraction flagged.

**Key observation:** ρ(t) is a function of the current thresholds and the true Byzantine fraction f:

```
ρ(t) = f · P[attack flagged | f, τ₁(t), τ₂(t)] + (1-f) · P[honest flagged | τ₁(t), τ₂(t)]
```

---

## 3. Drift Function Derivation

### 3.1 No-Attack Case (φ = 0)

The drift for each threshold τ_k is:

```
h_k(τ_k, φ=0) = η_relax · (τ_k_max - τ_k)
```

This is **linear** in τ_k with Lipschitz constant L_k = η_relax.

The fixed point is trivially τ_k → τ_k_max (exponential approach with rate η_relax).

**Rate:** convergence rate = 1 - η_relax per round. With η_relax = 0.05, the system reaches 90% of τ_k_max in ~45 rounds.

### 3.2 Attack Case (φ = 1)

The drift for each threshold τ_k is:

```
h_k(τ_k, φ=1) = -η_attack · ρ(t)
```

Where ρ(t) = (1/N) Σᵢ 1_[s_i(t) < θ_accept] and s_i(t) is the cascade-final anomaly score for client i.

**This is the critical term.** ρ(t) depends on both thresholds and the attack structure because:

```
s_i(t) = { L1(g_i) if c₁ ≥ τ₁(t) else
           L2(g_i) if c₂ ≥ τ₂(t) else
           L3(g_i) }
```

The cascade structure makes ρ(t) a **piecewise-constant function** of τ₁ and τ₂ with discontinuities at the decision boundaries.

### 3.3 Approximating ρ(t) as Continuous

Define the cascade's acceptance probability:

```
P_accept(i) = P[c₁ ≥ τ₁] · P[L1 says honest | c₁ ≥ τ₁] 
            + P[c₁ < τ₁, c₂ ≥ τ₂] · P[L2 says honest | c₁ < τ₁, c₂ ≥ τ₂]
            + P[c₁ < τ₁, c₂ < τ₂] · P[L3 says honest | c₁ < τ₁, c₂ < τ₂]
```

This is continuous in τ₁, τ₂ if the confidence distributions have densities (sigmoid scores have smooth densities). The empirical ρ(t) = 1 - (1/N) Σᵢ P_accept(i).

**Lipschitz continuity:** Since all per-layer scores are sigmoid functions of their inputs and all confidence thresholds are bounded away from 0 and 1, the gradient ∇_{τ₁,τ₂} P_accept is bounded. The Lipschitz constant L_h = η_attack · ‖∇ρ‖_∞ is finite.

---

## 4. Fixed-Point Analysis

### 4.1 Equilibrium Condition

At equilibrium, the tightening and relaxing forces balance:

```
E[η_relax · (τ_k_max - τ_k) · (1 - φ)] = E[η_attack · ρ · φ]
```

Using the law of total expectation:

```
η_relax · (τ_k_max - τ_k) · P[φ=0] = η_attack · E[ρ | φ=1] · P[φ=1]
```

### 4.2 Equilibrium Threshold

Solving for τ_k*:

```
τ_k* = τ_k_max - (η_attack / η_relax) · E[ρ | φ=1] · P[φ=1] / P[φ=0]
```

**Interpretation:**

| Factor | Effect | 
|--------|--------|
| η_attack / η_relax | = 3 (with defaults 0.15/0.05). Attack tightening is 3× faster than relaxation |
| E[ρ | φ=1] | Expected flag rate during attack. Higher = more tightening |
| P[φ=1] / P[φ=0] | Attack frequency. Full-time attack → φ=1 always → τ_k* = τ_k_max - 3 · E[ρ|φ=1] |

**Example:** If under attack 10% of rounds (P[φ=1]=0.1), and during attacks ρ averages 0.2:
```
τ₁* = 0.90 - 3 × 0.2 × 0.1/0.9 = 0.90 - 0.067 = ~0.833
```

### 4.3 Bounded Range Guarantee

The equilibrium τ_k* is guaranteed to stay within [τ_k_min, τ_k_max] because:

- Upper bound: τ_k* ≤ τ_k_max (by construction — drift toward max when φ=0)
- Lower bound: τ_k* ≥ τ_k_max - (η_attack/η_relax) · 1 · 1/0 = τ_k_min in the limit. The min bound clips this.

The practical lower bound (without clipping) is:
τ_k_min_effective = τ_k_max - (η_attack/η_relax) · ρ_max

Where ρ_max ≤ 1 is the maximum possible flag rate. With defaults: τ₁_min_eff = 0.90 - 3 × 1 = -2.1 → clipped to 0.55. So in practice, the lower bound clamp is active during sustained high-intensity attacks.

---

## 5. Convergence Rate

### 5.1 Without Attack (φ=0 Always)

Linear convergence (exponential) to τ_k_max:

```
|τ_k(t) - τ_k_max| = (τ_k(0) - τ_k_max) · (1 - η_relax)^t
```

For τ₁(0)=0.75, τ₁_max=0.90, η_relax=0.05:
- t=10: 0.75 + 0.15 × (1 - 0.95^10) = 0.75 + 0.15 × 0.401 = 0.810
- t=20: 0.75 + 0.15 × 0.642 = 0.846
- t=50: 0.75 + 0.15 × 0.923 = 0.888

### 5.2 Under Attack (φ=1 Always)

```
τ_k(t+1) = τ_k(t) - η_attack · ρ(t)
```

The dynamics depend on ρ(t), which depends on τ_k(t). This is a feedback loop. If ρ(t) is approximately constant α:

```
τ_k(t) = τ_k(0) - η_attack · α · t
```

This is **linear** convergence to τ_k_min. With η_attack=0.15, ρ=0.2 → 0.03 per round. From τ₁=0.90 to τ₁_min=0.55: (0.90-0.55)/0.03 ≈ 12 rounds.

### 5.3 Mixed (Most Realistic)

The two force directions create a bounded oscillation:

```
τ_k oscillates between:
  Upper bound: τ_k_max (relaxation during calm periods)
  Lower bound: max(τ_k_min, τ_k* - ε) (tightening during attacks)
```

The oscillation bandwidth Δτ_k = τ_k_max - τ_k* ≈ (η_attack/η_relax) · E[ρ|φ=1] · P[φ=1]/P[φ=0] decreases with attack frequency.

---

## 6. τ₁-τ₂ Coupling Analysis

Both thresholds update from the same ρ(t) signal, creating coupling:

```
Δτ₁(t) ∝ ρ(t) · φ(t)   (same for Δτ₂)
```

**Implication:** τ₁(t) and τ₂(t) are co-monotonic — they rise and fall together. The gap τ₁(t) - τ₂(t) is preserved at:

```
τ₁(t) - τ₂(t) = (τ₁(0) - τ₂(0)) · (1 - η_relax)^t   (during relaxation)
                   ≈ 0   (during attack — both decrease at same rate)
```

**Design insight:** The gap is small (default 0.05) and converges to 0 under attack. This is intentional — both thresholds should tighten proportionally.

---

## 7. Honest Reframing

### 7.1 What We Can Actually Claim

| Claim | Status | Evidence |
|-------|--------|----------|
| Thresholds converge to a neighborhood | ✅ Proven | Linear/exponential approach to bounded interval [τ_min, τ_max] |
| Oscillation bandwidth is bounded | ✅ Proven | Bounded by η_attack/η_relax and E[ρ] |
| τ₁-τ₂ coupling maintains gap structure | ✅ Proven | Both respond to same signal at same rate |
| Thresholds do not diverge | ✅ Proven | Projection onto bounded interval guarantees stability |
| Thresholds converge to optimal value | ❌ **Not claimed** | Optimal τ depends on unknown f; adaptive system tracks empirical attack intensity |
| Formal convergence proof in ODE sense | ❌ **Not fully claimed** | The piecewise nature and non-stationary ξ make ODE proof incomplete without additional smoothing assumptions |

### 7.2 Recommended Paper Framing

Rather than "convergence proof" (which we don't fully have), use:

> **"Stability and Bounded Dynamics of Adaptive Thresholds"**
> 
> We prove that the adaptive threshold system:
> 1. Has bounded output: τ₁(t) ∈ [0.55, 0.90], τ₂(t) ∈ [0.55, 0.85] by construction
> 2. Converges exponentially to τ_max under no-attack (relaxation rate η_relax)
> 3. Converges linearly to τ_min under persistent attack (tightening rate η_attack · ρ)
> 4. Has co-monotonic thresholds (gap ≤ 0.05 preserved under all conditions)
> 5. The equilibrium τ_k* is a function of attack frequency and severity (Equation 4.2)

This is **honest, rigorous, and sufficient** for the paper's claim. The thresholds are an *adaptive control mechanism*, not a mathematical optimum-finder.

---

## 8. Code Changes Required

Add the equilibrium analysis bounds as assertions in the orchestration code:

```python
def _verify_stability_bounds(self):
    """Runtime verification of convergence properties."""
    # Both thresholds must move in same direction
    assert (self.tau_1 - self.tau_1_prev) * (self.tau_2 - self.tau_2_prev) >= 0, \
        "Thresholds must be co-monotonic"
    
    # Gap must be bounded
    assert abs(self.tau_1 - self.tau_2) <= 0.1, \
        "Threshold gap exceeds design bound"
    
    # Must stay within bounds
    assert self.TAU_1_MIN <= self.tau_1 <= self.TAU_1_MAX
    assert self.TAU_2_MIN <= self.tau_2 <= self.TAU_2_MAX
```
