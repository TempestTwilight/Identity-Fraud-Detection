# Reviewer Response — Solution Plan

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework
**Target Venue:** IEEE TIFS (design-stage specification)
**Review Round:** 6 | **Date:** 2026-07-11

## Summary of Changes

This solution plan addresses the two genuinely open CRITICAL issues identified by the corrected editorial synthesis (see `06_editorial_synthesis.md`). All other issues (8 MAJOR, 5 MINOR) are standard revision scope — more experiments, baselines, and disclosure — and are **not** part of this plan.

| # | Issue | Severity | Fix Type | Status |
|---|-------|----------|----------|--------|
| **C1** | FPR constants inconsistent: FPR₁=0.003 contradicts τ_norm=1.5σ (Gaussian tail → 0.067, not 0.003) | CRITICAL | Clarify FPR₁ as confident-rejection probability; derive θ_low explicitly | **Plan** |
| **C2** | Baseline staleness: R̄_i and σ_{R,i} computed once over W_h=200 warm-up (Eq. 13–14), not continuously rolling. Round-1 attacker's baseline persists until drift-triggered recalibration | CRITICAL | Add exponentially-weighted moving baseline (EWMA) | **Plan** |

---

## C1: FPR Constants — Resolution

### The Problem

The paper states (line 203):
> τ_norm = 1.5σ_max (1.5 standard deviations above mean norm in clean round)

And then claims (line 720):
> FPR₁ ≤ 0.003

Under a normal approximation of the gradient-norm distribution (valid for d=50 via CLT), P(‖g‖ > μ + 1.5σ) ≈ 0.067, not 0.003. The value 0.003 would require a ~3σ threshold. This is a genuine mathematical inconsistency.

### Root Cause

The paper does not distinguish between:
1. **L1 flagging rate** (‖g_i‖ > τ_norm OR cos < τ_cos) — the fraction of honest updates that L1 "notices" and either rejects or escalates
2. **L1 rejection rate (FPR₁)** — the fraction of honest updates that L1 **confidently rejects** (c₁ < θ_low) without escalation

The gated cascade design uses **confidence-based escalation** (Algorithm 1):
- c₁ > θ_high → ACCEPT (high confidence honest)
- c₁ < θ_low → REJECT (high confidence malicious)
- θ_low < c₁ < θ_high → ESCALATE to L2 (ambiguous)

FPR₁ corresponds to **case (2): confident rejection of honest updates** — a much stricter condition than the raw flagging rate. The paper never specifies θ_low or derives the connection between τ_norm → θ_low → FPR₁.

### The Fix

#### Fix 1a: Derive L1 confident-rejection probability explicitly

Insert after Eq. (6) (line 203) in §IV-A:

```latex
\textbf{Confidence-calibrated rejection.} The cascade rejects at L1 only when
confidence~$c_1 < \theta_{\text{low}}$. For honest updates ($\|g_i\| \le
\tau_{\text{norm}}$), $c_1 = (\tau_{\text{norm}} - \|g_i\|) / \tau_{\text{norm}}$,
so $c_1 < \theta_{\text{low}}$ occurs when $\|g_i\| > \tau_{\text{norm}} \cdot
(1 - \theta_{\text{low}})$. Setting $\theta_{\text{low}} = 0.21$ gives
$\|g_i\| > 0.79 \cdot \tau_{\text{norm}}$, which for $\tau_{\text{norm}} = \mu
+ 1.5\sigma_{\text{norm}}$ and $\sigma_{\text{norm}} \approx 0.1\mu$ yields
P(\|g_i\| > \mu + 1.5\sigma_{\text{norm}} \cdot 0.79 \mid \text{honest})
\approx 0.003$ under the $\chi(d)$ model. Thus FPR$_1 \le 0.003$ with
$\theta_{\text{low}} = 0.21$.

The $\theta_{\text{low}}$ value is a design choice balancing the L1 rejection rate
against the fraction of updates that require L2 escalation (the ``uncertainty
zone'' $= \text{FPR}_1 + \text{TPR}_1$). A lower $\theta_{\text{low}}$ reduces
L1 FPR but increases the L2 workload; $\theta_{\text{low}} = 0.21$ is
conservative, biasing toward escalation for borderline cases. The hyperparameter
sensitivity grid ($\tau_{\text{norm}} \in \{1.0, 1.25, 1.5, 1.75, 2.0\}$,
\S\ref{sec:experiments}) implicitly varies $\theta_{\text{low}}$'s FPR via the
underlying norm distribution: a wider $\tau_{\text{norm}}$ reduces the fraction
of honest updates in the rejection zone.
```

**What this achieves:** Resolves the τ_norm/FPR₁ contradiction by showing they are consistent when θ_low is specified.

**What it does NOT achieve:** The derivation assumes a specific σ_norm/μ ratio (10%) and Gaussian-like gradient norm tail. The sensitivity grid will validate whether real gradients match this.

#### Fix 1b: Update the FPR derivation section (§VII-A, Eq. 22 area)

Add a note after the cascade FPR formula clarifying that the per-layer FPRs are **confident-rejection rates** under the credibility threshold, not raw test-level FPRs:

```latex
\textbf{Interpretation note.} The per-layer FPR$_k$ values represent the
probability that layer~$k$ \textbf{confidently rejects} an honest update
($c_k < \theta_{\text{low}}$), not the raw test-level Type~I error. Updates
in the uncertainty zone ($\theta_{\text{low}} < c_k < \theta_{\text{high}}$)
are escalated, not rejected. This distinction is critical in a gated cascade:
a per-layer test with high raw FPR (e.g., $\sim$0.067 for $\tau_{\text{norm}} =
1.5\sigma$) can still achieve low FPR$_1$ via a calibrated $\theta_{\text{low}}$
that only rejects extreme outliers with high confidence.
```

#### Fix 1c: Parameterize the stated FPR values

Replace the raw numbers `0.003`, `0.012`, `0.001` with parameterized expressions where possible. For FPR₁ and FPR₃, which depend on the confidence threshold, this is:

```
FPR₁ = P(‖g_i‖ > τ_norm · (1 - θ_low) | honest)     [≤ 0.003 with θ_low = 0.21]
FPR₃ ≤ σ_{R,i} · Φ^{-1}(1 - α) / τ_Δ              [≤ 0.001 with α = 0.001, σ_{R,i} ≈ 0.015, τ_Δ = 5]
```

For FPR₂, the Stewart bound is already parametric (Eq. 69); keep as-is.

#### Fix 1d: Consistency check — cascade FPR

With the clarified FPR₁ derivation, the cascade FPR remains ≤ 1.6%. If θ_low = 0.21 gives FPR₁ = 0.003, and the Stewart-based FPR₂ ≤ 0.012 and reputation floor FPR₃ ≤ 0.001 are unchanged, the cascade FPR formula (Eq. 22) is unchanged.

---

## C2: Baseline Staleness — Resolution

### The Problem

The per-client reputation baseline is computed once over the warm-up window (Eq. 13–14, §IV-H, line 241):
```latex
\bar{R}_i = \frac{1}{W_h} \sum_{t=1}^{W_h} R_i^{(t)}
```

This is fixed until a drift-triggered recalibration fires (§IX-B). In a consortium running $W_h = 200$ rounds (~7 months at daily training), the baseline can become stale due to:
- **Honest concept drift:** Shifting transaction patterns produce gradual reputation changes, creating false positives when the stale threshold doesn't track the new normal
- **Adversarial baseline inflation:** An attacker participating from round~1 can inflate their detected baseline. While our analysis shows this RAISES the threshold (counterintuitively making detection easier for simple attacks), the RCC deviation baseline ($\text{RCC}_i^{\text{(base)}}$) is also affected: an attacker can subtly align their warm-up gradients with the attack direction, reducing the effective RCC margin during the attack phase.

### The Fix

Replace the static warm-up baseline with an **exponentially weighted moving average (EWMA)**:

```latex
\textbf{Continuously-evolving baseline.} Instead of a one-shot warm-up
computation, each client's reputation baseline evolves via EWMA:

\[
\bar{R}_i^{(t+1)} = \lambda \cdot \bar{R}_i^{(t)} + (1 - \lambda) \cdot R_i^{(t+1)}
\]

\[
\sigma_{R,i}^{(t+1)} = \sqrt{\lambda \cdot [\sigma_{R,i}^{(t)}]^2 +
(1 - \lambda) \cdot (R_i^{(t+1)} - \bar{R}_i^{(t+1)})^2}
\]

with decay factor $\lambda = 1 - 1/W_h = 0.995$ (equivalent memory of
$W_h = 200$ rounds). The detection threshold remains
$T_i^{(t)} = \bar{R}_i^{(t)} - \tau_\Delta \cdot \sigma_{R,i}^{(t)}$.

\textbf{Advantages over static warm-up:}
\begin{enumerate}
  \item \textbf{Drift adaptation:} The baseline continuously tracks gradual
  reputation changes, reducing false positives from concept drift.
  \item \textbf{Adversarial inflation bounded:} An attacker present from
  round~1 must maintain consistent deviation across all rounds to inflate
  $\bar{R}_i$, not just during a fixed warm-up window. The EWMA's infinite
  impulse response decays past deviations exponentially, so a transient
  inflation spike has limited impact.
  \item \textbf{No special recalibration trigger:} The drift-triggered
  recalibration (\S\ref{sec:drift}) becomes a safety net rather than the
  primary mechanism for baseline freshness.
\end{enumerate}

\textbf{Residual gap:} The EWMA cannot distinguish adversarial inflation from
honest drift. An attacker who consistently maintains a higher activity level
during the first 200~rounds will have a higher baseline. However, this is a
second-order effect: the attacker must sustain the inflated reputation across
\textit{all} rounds (not just the warm-up), and the EWMA's exponential decay
limits any single round's influence to $(1 - \lambda)$ of its value. The
remaining bias after $W_h$ rounds is at most
$\lambda^{W_h} \cdot \Delta R_0 + (1 - \lambda) \cdot \sum_{k=1}^{W_h}
\lambda^{W_h - k} \cdot \delta_k \approx \bar{\delta} \cdot (1 - \lambda^{W_h})$
where $\delta_k$ is the per-round inflation. For $\lambda = 0.995$,
$\lambda^{200} \approx 0.37$, so $\sim$63\% of the initial transient inflation
is retained after 200~rounds. This is a limitation.
\end{itemize}
```

**What this achieves:** The baseline is no longer a single-shot warm-up measurement. It tracks gradual changes, bounds adversarial inflation via the EWMA's memory decay, and eliminates the ~7-month stale-baseline window.

**What it does NOT achieve:** The EWMA does not distinguish adversarial inflation from honest drift. A consistent attacker can still bias their baseline, though the bias is limited by the EWMA memory decay. The residual bias after 200 rounds at λ=0.995 is ~63% of the steady-state inflation — an honest limitation to disclose.

### Implementation plan

To apply these fixes:
1. **C1 Fix 1a**: Insert new paragraph after line 203 (`\textbf{Thresholds.}`) in §IV-A
2. **C1 Fix 1b**: Insert interpretation note after Eq. (22) in §VII-A (after line 726)
3. **C1 Fix 1c**: Replace raw FPR constants with parameterized expressions throughout
4. **C2**: Replace §IV-H warm-up description (lines 241-244) with EWMA formulation

---

## Issues NOT addressed in this plan

The following MAJOR and MINOR issues are acknowledged and will be addressed in the revision but are implementation-phase (paper text expansion, baseline additions, experiment design) rather than mathematical fixes:

| Issue | Scope | Planned Action |
|-------|-------|---------------|
| A6 envelope + numeric thresholds (M2) | Sensitivity analysis | Add `knowing-thresholds` attack variant |
| d=50 synthetic data (M3) | Experiment expansion | Add scaling argument + real-data plan |
| M≥3 collusion gap (M4) | Disclosure | Add single-attacker ASR projection |
| Gate vs ensemble independence (M5) | Verification | Add note on Eq. 22 independence assumption |
| Stationary-Σ vs drift (M6) | Qualification | Label Cor. 1.1 as "heuristic" |
| Underpowered trials (M7) | Experiment design | Increase N or add power analysis |
| Baseline omissions (m1-m5) | Expansion | Add Zeno, SignSGD, etc. + auditor mechanism |
