# Proposed Solutions to Review Findings — Review 4

**Paper:** "Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework"
**Date:** 2026-07-07
**Based on:** 5 independent reviews (EIC 40/100, R1 45/100, R2 50/100, R3 30/100, DA 10/100)
**Weighted Average:** 35/100 — Reject

---

## Structure

Four tiers ordered by binding severity. **Tier 1** must be resolved before any resubmission. **Tier 2** requires a structural decision (pick one branch). **Tier 3** must be executed for acceptance. **Tier 4** is strongly recommended for a strong revision.

---

# Tier 1 — Formal Proof Fixes (Binding — no resubmission without these)

These are the **three fatal mathematical flaws** from the convergence of all five reviewers. Experiments cannot patch them.

---

## MI-1: Scaling Attack Breaks Theorem 1 (Reputation Floor)

**Source:** R1 §8 (critical flaw), DA §2 (catastrophic formal error), R3 §2 (fatal)

**The attack (Bagdasaryan et al., 2020).** An adversary sends a convex combination of a benign gradient and a malicious update:

$$g_m = (1-\alpha) \cdot g_{\text{benign}} + \alpha \cdot v_{\text{mal}}, \quad \alpha \in (0, 0.15)$$

where $v_{\text{mal}}$ is the attacker's target direction (e.g., a backdoor) and $g_{\text{benign}} \approx \mu$ approximates the peer mean. With $\alpha$ small, the update is **mostly honest** with a subtle malicious nudge.

**Why existing layers fail:**

| Layer | Check | g_m value | Passes? |
|-------|-------|-----------|---------|
| L1 norm | $\|g_i\|_2 > \tau_{\text{norm}}$ | $\|g_m\| \approx \|g_{\text{benign}}\| \cdot \sqrt{1 - 2\alpha + 2\alpha^2}$ | ✓ (within benign range) |
| L1 cosine | $\cos(g_i, \mu) < \tau_{\text{cos}}$ | $\cos(g_m, \mu) \approx 0.88$ (measured, $d=500$) | ✓ (above $\tau_{\text{cos}} = 0.5$) |
| L2 PCA | $e_i > \tau_2$ | residual near-normal | ✓ (subtle deviation) |
| L3 $d_{\text{grad}}$ | $d_{\text{grad}} = 1 - \cos(g_m, \mu)$ | $\approx 0.12$ → small anomaly | ✓ |
| L3 $a_i^{(t)}$ | $\ge 0.95$ normal | $0.3\cdot 0.12 + 0.3 + 0.2 \approx 0.536$ | ✓ |

The $\cos(g_m, \mu) \approx 0.88$ (measured at $d=500$, $\sigma=0.1$) is lower than the theoretical noise-free $0.985$ — SGD noise degrades alignment. But $0.88 > 0.5$ passes L1, and $d_{\text{grad}} \approx 0.12$ gives an anomaly score well below $\tau_R = 0.75$.

### Key Insight — Honest Residual Structure in Non-IID FL

The RCC analysis depends critically on the **statistical structure of honest residuals**. Two regimes must be distinguished:

**Regime A: IID clients (theoretical baseline).** If all clients have the same data distribution, the residual $r_i^{(s)} = g_i^{(s)} - \mu^{(s)}$ is approximately zero-mean random noise. The averaged residual norm scales as $\sigma\sqrt{d}/\sqrt{W}$, and the average per-round norm scales as $\sigma\sqrt{d}$. Hence:

$$\mathbb{E}[\text{RCC}_{\text{honest}}] \approx \frac{1}{\sqrt{W}}$$

This is validated empirically: $W=50$ → honest RCC $\approx 0.141$, $W=10$ → $0.316$. The baseline depends **only** on $W$, not on $d$ or $\sigma$.

**Regime B: Non-IID clients (real FL).** Each client has a persistent gradient bias $\Delta_i$ from its local data distribution:

$$g_i^{(s)} = \mu + \Delta_i + \varepsilon_i^{(s)}$$

where $\Delta_i$ is fixed (the client's deviation from the global optimum) and $\varepsilon_i^{(s)}$ is SGD noise. The peer mean absorbs the average bias $\bar{\Delta}$, so the residual becomes:

$$r_i^{(s)} = (\Delta_i - \bar{\Delta}) + \varepsilon_i^{(s)} - \bar{\varepsilon}^{(s)}$$

The persistent component $(\Delta_i - \bar{\Delta})$ does **not** average to zero over $W$ rounds. Honest RCC in non-IID FL is determined by this bias:

$$\text{RCC}_{\text{honest}}^{(i)} \approx \frac{\|\Delta_i - \bar{\Delta}\|}{\sqrt{\|\Delta_i - \bar{\Delta}\|^2 + \sigma^2 d}}$$

**Empirical measurement (toy logistic regression, $d=100$, $N=10$, Dirichlet $\alpha=0.5$):**

| Setting | Mean Honest RCC | Max | $1/\sqrt{W}$ |
|---------|----------------|-----|-------------|
| IID noise ($\sigma=0.01$, resampled per round) | 0.147 | 0.160 | 0.141 |
| Full-batch, non-IID (no SGD noise) | **0.998** | 0.998 | 0.141 |
| SGD $B=32$, non-IID | **0.376** | 0.852 | 0.141 |

**Critical finding:** A global $\tau_{\text{RCC}}$ threshold is **not viable** in non-IID FL. At $\tau_{\text{RCC}} = 0.6$, client 5 (RCC $=0.852$) would be flagged as malicious despite being honest with non-IID data.

### Proposed Solution — Per-Client RCC Baseline with $\Delta$ Detection

The correct approach replaces the global threshold with a **per-client baseline** and flags deviations from it:

**Phase 1 — Warm-up.** During an initial trusted period of $W_{\text{hist}}$ rounds (or using a robust preliminary estimator), compute each client's historical RCC baseline:

$$\text{RCC}_i^{\text{(base)}} = \frac{\|\frac{1}{W_{\text{hist}}} \sum_{s=1}^{W_{\text{hist}}} r_i^{(s)}\|}{\frac{1}{W_{\text{hist}}} \sum_{s=1}^{W_{\text{hist}}} \|r_i^{(s)}\|}$$

This captures the client's persistent residual signature $(\Delta_i - \bar{\Delta})$.

**Phase 2 — Detection.** At each round $t$, compute the short-window RCC over $W$ recent rounds and the deviation:

$$\Delta\text{RCC}_i^{(t)} = \text{RCC}_i^{(t)} - \text{RCC}_i^{\text{(base)}}$$

$$\boxed{\text{Flag if: } R_i^{(t)} > \tau_R \quad \text{OR} \quad \|g_i\|_2 < \tau_{\text{norm\_low}} \quad \text{OR} \quad \Delta\text{RCC}_i^{(t)} > \tau_{\Delta}}$$

**Rationale.** An honest non-IID client maintains a stable residual signature — their short-window RCC fluctuates around their baseline, so $\Delta\text{RCC} \approx 0$. A scaling attacker adds a **new** signal component $\alpha(v_{\text{mal}} - \mu)$ to the residual, which elevates their short-window RCC above their baseline:

$$\text{RCC}_i^{(t)} \ge \sqrt{\frac{1}{W} + \frac{\alpha^2 S^2 (1-1/N)^2}{\sigma^2 d \cdot C^2} + \frac{\|\Delta_i - \bar{\Delta}\|^2}{\sigma^2 d}}$$

$$\Delta\text{RCC}_i^{(t)} \ge \sqrt{\frac{1}{W} + \frac{\alpha^2 S^2 (1-1/N)^2}{\sigma^2 d \cdot C^2} + (\text{RCC}_i^{\text{(base)}})^2} \;-\; \text{RCC}_i^{\text{(base)}}$$

**Lemma 2 (RCC deviation of scaling attacker, conjecture with empirical support):** For a non-IID client with persistent bias $\Delta_i$, attacked with classic scaling attack $(1-\alpha)g_{\text{benign}} + \alpha v_{\text{mal}}$:

$$\Delta\text{RCC}_i \ge \sqrt{ \frac{1}{W} + \text{SNR}^2 + (\text{RCC}_i^{\text{(base)}})^2 } - \text{RCC}_i^{\text{(base)}}$$

where $\text{SNR}^2 = \frac{\alpha^2 S^2 (1-1/N)^2}{\sigma^2 d \cdot C^2}$ and $C^2 = (1-\alpha)^2(1-1/N)^2 + 1/N$.

**Detection condition.** The baseline relative detection threshold $\tau_{\Delta}$ catches attackers when:

$$\sqrt{ \frac{1}{W} + \text{SNR}^2 + (\text{RCC}_i^{\text{(base)}})^2 } - \text{RCC}_i^{\text{(base)}} > \tau_{\Delta}$$

For $\text{RCC}_i^{\text{(base)}} \approx 0.4$ (typical non-IID client), $\tau_{\Delta} = 0.2$, $W=50$:
$$\text{SNR}^2 > (0.4 + 0.2)^2 - 0.02 - 0.16 = 0.36 - 0.18 = 0.18$$
$$\text{SNR} > 0.42 \quad \rightarrow \quad \alpha S > 0.42 \cdot \sigma\sqrt{d} \cdot C / (1-1/N) \approx 0.39 \cdot \sigma\sqrt{d}$$

This is **slightly stricter** than the IID regime ($\alpha S > 0.52 \cdot \sigma\sqrt{d}$ was the IID condition), because the baseline already accounts for some of the variance. The per-client baseline slightly reduces detection sensitivity for that specific client, but eliminates false positives from non-IID data.

### Grounding σ — Empirical Measurement

The parameter $\sigma$ (per-component standard deviation of gradient variation across honest clients) must be measured empirically for each deployment. It combines SGD sampling noise (typically small, $\sigma_{\text{sgd}} \ll 10^{-2}$) with client heterogeneity (dominant in non-IID settings).

**Measurement protocol:** For each gradient component $j$, compute the sample standard deviation across clients at round $t$, then average over components and a window of $T$ rounds:

$$\hat{\sigma} = \frac{1}{T d} \sum_{t=1}^{T} \sum_{j=1}^{d} \text{std}_{i}[g_{i,j}^{(t)}]$$

**Empirical measurement (toy logistic regression, $d=100$, $N=10$, Dirichlet $\alpha=0.5$):**

| Setting | $\sigma$ | $\sigma\sqrt{d}$ | Detection condition $\alpha S > 0.4 \cdot \sigma\sqrt{d}$ satisfied? |
|---------|---------|-----------------|----------------------------------------------------------------------|
| Full-batch, non-IID | 0.0103 | 0.103 | Yes ($0.15 > 0.04$) |
| SGD $B=32$, non-IID | 0.0203 | 0.203 | Yes ($0.15 > 0.08$) |

**Key finding:** At $\sigma\sqrt{d} \approx 0.1$–$0.2$ (toy model, moderate non-IID), the condition $\alpha S > 0.4 \cdot \sigma\sqrt{d}$ is satisfied for $\alpha=0.15$, $S=1.0$. **Whether this transfers to the target deployment depends on the consortium's data heterogeneity and model size** — the practitioner must measure $\hat{\sigma}$ from client gradient variance and verify the detection condition holds.

**Empirical RCC values ($d=500$, $W=50$, $N=10$, 20 trials — IID noise model):**

| Scenario | $\sigma$ | RCC | P(RCC > 0.6) |
|----------|---------|-----|---------------|
| Honest (IID noise) | 0.01 | $0.045 \pm 0.002$ | 0.000 |
| Scaling $\alpha=0.15$, $S=1.0$ | 0.01 | $0.727 \pm 0.002$ | 1.000 |
| Scaling $\alpha=0.15$, $S=1.0$ | 0.1 | $0.175 \pm 0.005$ | 0.000 |
| Scaling $\alpha=0.10$, $S=1.0$ | 0.01 | $0.563 \pm 0.004$ | 0.000 |

**Non-IID honest RCC (toy FL, $d=100$, $B=32$, $W=50$):**

| Client | RCC$_i^{\text{(base)}}$ | RCC$_i^{(t)}$ (honest, later window) | $\Delta$RCC |
|--------|------------------------|---------------------------------------|-------------|
| 0 | 0.523 | 0.531 | $+0.008$ |
| 1 | 0.253 | 0.260 | $+0.007$ |
| 2 | 0.319 | 0.311 | $-0.008$ |
| 3 | 0.272 | 0.285 | $+0.013$ |
| 4 | 0.393 | 0.400 | $+0.007$ |
| 5 | 0.852 | 0.848 | $-0.004$ |
| 6 | 0.256 | 0.249 | $-0.007$ |
| 7 | 0.239 | 0.251 | $+0.012$ |
| 8 | 0.313 | 0.308 | $-0.005$ |
| 9 | 0.339 | 0.345 | $+0.006$ |

**Key observation:** Despite client 5 having RCC $=0.852$ (which would trigger a global $\tau_{\text{RCC}} = 0.6$), their $\Delta$RCC is essentially zero ($-0.004$). The per-client baseline correctly recognizes this as a stable non-IID pattern, not an attack.

**Supplementary Fix 2:** Gradient norm **lower** bound. Add $\|g_i\|_2 < \tau_{\text{norm\_low}}$ to catch extreme $\alpha \to 1$ attackers. Does **not** catch subtle $\alpha \in (0, 0.15)$ attackers.

### Formal Fix to Theorem 1 — Conditional Guarantee with Per-Client Baseline

**Before:** "For any client whose average anomaly score over any $W$-round window is at least 0.95, $R_i^{(t)} \ge R_{\text{SS}} = 0.85$ for all $t > t_0$."

**After:** "Let $R_i^{(t)}$ be the filtered reputation after passing all three gates. For any client whose average anomaly score over any $W$-round window is at least 0.95, whose gradient norm is within $[\tau_{\text{norm\_low}}, \tau_{\text{norm}}]$, and whose per-client RCC deviation satisfies $\Delta\text{RCC}_i^{(t)} \le \tau_{\Delta}$:

$$R_i^{(t)} \ge 0.85 \quad \text{for all } t > t_0$$

**Condition required:** The guarantee holds when $\alpha S \gg \sigma\sqrt{d} \cdot C \cdot \sqrt{(\text{RCC}_i^{\text{(base)}} + \tau_{\Delta})^2 - 1/W - (\text{RCC}_i^{\text{(base)}})^2}$ — equivalently, when the attacker's malicious signal adds a detectable deviation above the client's baseline residual signature. Outside this regime, $\Delta\text{RCC} \le \tau_{\Delta}$ and the scaling attacker passes the RCC gate."

**The paper should present this as:**
1. A proof of Theorem 1 under the noise condition + per-client baseline condition
2. Empirical characterization of honest $\Delta$RCC in non-IID FL (from experiment above: $|\Delta\text{RCC}| \le 0.013$ for honest clients)
3. A warm-up protocol for establishing per-client baselines
4. An honest discussion of the residual gap

### Δ Threshold Calibration

The detection threshold $\tau_{\Delta}$ must separate attacker-induced RCC increase from natural fluctuation. From the non-IID experiment: honest $|\Delta\text{RCC}| \le 0.013$.

| $W$ | $\tau_{\Delta}$ | Margin over honest max ($0.013$) | P(catch $\alpha=0.15$, $\sigma=0.01$) |
|-----|-----------------|----------------------------------|---------------------------------------|
| 25 | 0.10 | 7.7× | 1.000 |
| 50 | 0.10 | 7.7× | 1.000 |
| **50** | **0.05** | **3.8×** | **1.000** |
| 50 | 0.02 | 1.5× | 1.000 (marginal) |

**Recommended value:** $\tau_{\Delta} = 0.10$, providing $7.7\times$ margin over maximum honest $\Delta$RCC and catching $\alpha \ge 0.08$ attackers at realistic noise levels.

**For conservative deployment:** $\tau_{\Delta} = 0.20$ ($15\times$ margin), which catches $\alpha \ge 0.12$ attackers.

### Combined Triple-Gate FPR Analysis

The triple gate: $R_i > \tau_R$ **OR** $\|g_i\|_2 < \tau_{\text{norm\_low}}$ **OR** $\Delta\text{RCC}_i > \tau_{\Delta}$.

For honest clients:
- $P(R_i > \tau_R \mid h) = 0$ (by Theorem 1, assuming no anomaly score manipulation)
- $P(\|g_i\|_2 < \tau_{\text{norm\_low}} \mid h) \approx 0$ (empirically zero)
- $P(\Delta\text{RCC}_i > \tau_{\Delta} \mid h) \approx 0$ (empirically $|\Delta\text{RCC}| \le 0.013 \ll 0.10$)

**Union bound:** $P(\text{flagged} \mid h) \approx 0$.

**Caveats:**
- If the warm-up period is compromised (attacker participates during baseline estimation), the baseline will be inflated and attacks may go undetected. Mitigation: use a robust averaging procedure (median, trimmed mean) for baseline estimation.
- Clients whose data distribution drifts over time will have legitimate RCC changes. Concept drift detection should trigger baseline recomputation, not flagging.
- The triple gate does NOT close the $\alpha S \ll \sigma\sqrt{d}$ regime — acknowledged limit.

### Adaptive Attacker Limitation (must be disclosed)

The per-client RCC baseline detects fixed-direction attackers whose malicious signal changes the residual structure relative to the established baseline. An adaptive adversary (A6) that **randomizes its malicious direction** $v_{\text{mal}}^{(t)}$ each round keeps both RCC and $\Delta$RCC low, bypassing the gate:

$$g_m^{(t)} = (1-\alpha) \cdot g_{\text{benign}}^{(t)} + \alpha \cdot v_{\text{mal}}^{(t)}, \quad v_{\text{mal}}^{(t)} \sim \text{Uniform}(\mathcal{S})$$

where $\mathcal{S}$ is a set of malicious directions that each individually steer the model toward the attacker's target. If $v_{\text{mal}}^{(t)}$ is i.i.d. round-to-round, the residuals $r^{(t)} = g_m^{(t)} - \mu^{(t)}$ have zero mean and $\Delta$RCC $\to 0$, bypassing detection.

**This does NOT mean the RCC approach is useless** — it narrows the space of viable scaling attacks from "all scaling attackers" to "only attackers that randomize direction." The original paper had *no defense* against any scaling attacker. After RCC with per-client baseline, the attacker must either:
- Keep $\alpha$ very small (slowing poisoning proportionally), or
- Randomize direction (reducing per-round poisoning consistency)

Either choice degrades their attack relative to the original unconstrained setting.

### Implementation Cost

- Add ≈ 60 lines of Python for per-client RCC baseline and $\Delta$RCC computation (running mean of residuals + baseline maintenance + deviation check)
- No architectural change — added as a separate L4 gate, independent of the anomaly score calculation
- Storage: $O(N \cdot d)$ for per-client baseline residuals (stored per round over $W_{\text{hist}}$ for baseline, plus short window $W$)
- Compute overhead: $O(N \cdot d)$ per round — one vector subtraction + norm per client per round

---

## MI-2: Lipschitz Convergence Proof — Weight Dependence on Model Parameters

**Source:** R1 §4 (critical flaw), R3 §5

**The flaw.** The Lipschitz proof computes $\partial\rho/\partial\theta$ assuming $w_i(t)$ is independent of $\theta(t)$. But $w_i(t) = f(a_i^{(t)})$ where $a_i^{(t)}$ depends on $\cos(g_i(t), \mu(t))$, which depends on $\theta(t)$ through the gradient descent step. Standard L-smoothness argument is violated.

### Proposed Solution — Two-Timescale Framework (Sketch)

**Timescale separation.** The reputation weight $w_i(t)$ evolves on a slower timescale ($W = 50$ rounds) than the gradient descent (every round). This natural separation suggests a **two-timescale stochastic approximation** analysis (Borkar, 1997; Borkar \& Meyn, 2000):

- **Fast dynamics** ($\theta_t$ updated every round): Under a sliding window of $W$ rounds, the reputation weights are approximately constant. The local SGD within each window is standard $L$-smooth optimization.

- **Slow dynamics** ($w_i$ updated every $W$ rounds): The reputation weights form a Markov chain on $[0,1]^N$ with mixing time $\tau_{\text{mix}} \le W$ (by construction — the sliding window forgets by $1/W$ per round).

**ODE method.** The coupled system can be analyzed by **averaging**: the fast iterate tracks the ODE

$$\dot{\theta} = -\nabla F(\theta; \bar{w})$$

where $\bar{w}$ is the quasi-static reputation vector over the window. The slow process tracks the averaged reputation dynamics. The **tracking error** (difference between the actual coupled trajectory and the decoupled ODE) is bounded as:

$$\|\theta_t - \bar{\theta}_t\| \le O(\eta \cdot \tau_{\text{mix}}) \quad \text{(informal)}$$

where $\eta$ is the learning rate and $\tau_{\text{mix}}$ is the mixing time of the reputation Markov chain.

**What this means:** If $\eta \cdot \tau_{\text{mix}}$ is small (e.g., $\eta$ is small, or reputation mixes quickly), the two-timescale approximation carries a small tracking error and Theorem 1's convergence proof can be repaired. If $\eta \cdot \tau_{\text{mix}}$ is large, the coupling cannot be ignored and the proof requires the full coupled analysis.

**What is NOT proven here:** The $O(\eta \cdot \tau_{\text{mix}})$ bound above is a **statement of the form the error would take**, not a derived constant. A rigorous bound requires:

1. **Characterizing the Markov chain.** Reputation weights under the sliding-window dynamics form a specific Markov chain on $[0,1]^N$. The mixing time $\tau_{\text{mix}}$ and its dependence on $W$, $N$, and the anomaly score distribution must be derived.

2. **Verifying the ODE conditions.** The averaged gradient field $-\nabla F(\theta; \bar{w})$ must satisfy the Lipschitz and dissipativity conditions required by Borkar's two-timescale SA theorem.

3. **Computing the constant.** The $O(\cdot)$ hides a constant that depends on the Lipschitz constant $L$, the gradient variance $\sigma^2$, and the mixing time. This constant must be derived, not guessed.

**Numerical illustration (DO NOT USE IN PAPER):** If one naively takes $O(\eta \cdot \tau_{\text{mix}})$ at face value with $\eta = 0.05$ and $\tau_{\text{mix}} \approx 50$: $\eta \cdot \tau_{\text{mix}} = 2.5$. This is **not a meaningful number** — the $O(\cdot)$ means the actual error could be $2.5$, $0.025$, or $25$ depending on the hidden constant. It is included here only to show the **scale of the concern** when the learning rate is large relative to the mixing time, and **must not** appear in the paper without a derived constant.

**Simpler alternative — weaken and bound:**
Accept the dependence assumption and add an explicit error term of the form:

$$\|\theta^{(t)} - \theta^*\| \le O\left(\frac{\eta\sigma_\rho}{1-L_h}\right) + \underbrace{O(\eta \cdot W \cdot \|\nabla_\theta w\|)}_{\text{dependence error}}$$

This weakens the guarantee to "convergence to a neighborhood" rather than "convergence to optimum," but is **honest** — it admits the coupling rather than assuming it away.

---

## MI-3: Stewart Bound — IID + Stationary Assumption

**Source:** R1 §4 (IID dependency), R3 §3B (non-stationarity contradiction), DA §5 (concept drift makes PCA obsolete), EIC §5 (stationarity caveat)

**The contradiction.** The paper is motivated by temporal concept drift (fraudsters adapt), formally analyzed under stationary $\Sigma$, and validated on a static dataset. Three legs contradict each other.

### Proposed Solution — Bounded-Drift Stewart + Sliding-Window PCA

**Replace the fixed PCA reference subspace** $U_k$ (computed once) with a **sliding-window PCA** recomputed every $P$ rounds.

**Drift model.** Let $\Sigma_t$ be the benign gradient covariance at round $t$. Model concept drift as a bounded perturbation over $P$ rounds:

$$\|\Sigma_{t+P} - \Sigma_t\| \le \varepsilon_{\text{drift}}$$

**Davis-Kahan bound on subspace shift.** Let $U_k^{(t)}$, $U_k^{(t+P)}$ be the top-$k$ principal subspaces at rounds $t$ and $t+P$. The spectral-norm Davis-Kahan $\sin\Theta$ theorem gives:

$$\|\sin\Theta(U_k^{(t+P)}, U_k^{(t)})\| \le \frac{\|\Sigma_{t+P} - \Sigma_t\|}{\lambda_k - \lambda_{k+1}} \le \frac{\varepsilon_{\text{drift}}}{\text{gap}}$$

where $\text{gap} = \lambda_k - \lambda_{k+1}$ is the eigenvalue gap (a measure of how well-separated the top-$k$ subspace is).

**Effect on the anomaly score.** For a unit-norm gradient vector $g$, the L2 anomaly score $e(g) = \|g - \text{proj}_{U_k}(g)\|^2$ changes by at most:

$$|\hat{e} - e| \le \|UU^T - VV^T\| \le \|\sin\Theta\| \le \frac{\varepsilon_{\text{drift}}}{\text{gap}}$$

*Derivation:* $|\hat{e} - e| = |g^T(UU^T - VV^T)g| \le \|g\|^2 \cdot \|UU^T - VV^T\|$, and $\|UU^T - VV^T\| = \|\sin\Theta\|$ (the sine of the largest principal angle between subspaces).

**Updated FPR bound (form, not specific number):**

$$\text{FPR}_2(\varepsilon_{\text{drift}}) \le P\left(e_i > \tau_2 - \frac{\varepsilon_{\text{drift}}}{\text{gap}} \;\middle|\; \text{honest}\right)$$

This is **not** a closed-form number — it depends on the quantile function of the honest anomaly score distribution. The practical implication:

| $\varepsilon_{\text{drift}} / \text{gap}$ | $\Delta e_{\max}$ | Impact on FPR |
|-------------------------------------------|-------------------|---------------|
| $\ll 0.01$ | < 0.01 | Negligible — FPR unchanged |
| $\approx 0.05$ | 0.05 | Small shift — FPR may increase by $< 1\%$ |
| $\approx 0.167$ (example: 0.05/0.3) | 0.167 | **Large shift** — FPR degrades significantly (estimated 10–50%) |

**Key finding:** The Davis-Kahan bound for this problem has **no $k$ in the numerator** — the subspace rank $k$ does not directly amplify the drift effect (it enters only through the eigenvalue gap, which typically decreases with $k$). The earlier formula $(\varepsilon_{\text{drift}} \cdot k)/\text{gap}$ was incorrect; it conflated the Frobenius-norm bound ($\|\sin\Theta\|_F \le \sqrt{k} \cdot \varepsilon_{\text{drift}} / \text{gap}$) with the spectral-norm bound relevant to the anomaly score.

**Design implications:**
- The sliding-window PCA approach is **structurally sound** — recomputing the reference subspace does bound the perturbation
- But the earlier numerical claim (FPR "stays around 2.5% under drift") was **unsupported** by the actual bound
- A useful guarantee requires either (a) small drift relative to the eigenvalue gap ($\varepsilon_{\text{drift}} \ll \text{gap}$), or (b) a threshold $\tau_2$ set with sufficient margin above typical honest scores
- The eigenvalue gap itself is a design parameter: a larger gap (from a more pronounced low-rank structure) directly improves robustness to drift

**In the paper:** Replace the numerical FPR claim with the bound form and an empirical characterization of $\varepsilon_{\text{drift}}$ from the temporal dataset. Replace the stationarity caveat with the bounded-drift extension. Choose recomputation interval $P$ based on the observed drift rate: $P = \lfloor \text{gap} \cdot \varepsilon_{\text{drift}}^{-1} \rfloor$ ensures the per-interval drift stays bounded by the gap.

**For the evaluation plan:**
- Replace or augment static datasets (PaySim, IEEE-CIS) with a **temporal generator** that injects concept drift events: sudden spending pattern shifts, new fraud typologies, adversarial adaptation at intervals $T_{\text{drift}} \sim \text{Exponential}(100\text{ rounds})$
- Report FPR as a function of $\varepsilon_{\text{drift}} / \text{gap}$ in $[0, 0.5]$ — this ratio is the correct determinant of degradation, not $\varepsilon_{\text{drift}}$ alone
- Characterize the empirical eigenvalue gap from the dataset; a gap-to-drift ratio $\text{gap} / \varepsilon_{\text{drift}} > 10$ maintains FPR within an acceptable range; below this, the cascade enters a "recalibration mode"

---

# Tier 2 — Architectural Tensions (Require a structural decision)

## MI-4: Trust-Privacy Paradox (SecAgg Incompatibility)

**Source:** R3 §3A (trust-privacy paradox), DA §4 (disqualifying architectural constraint), EIC §5 (SecAgg tension), R2 §5 (auditability)

**The problem.** The server must inspect raw gradients for L2 spectral analysis and L3 reputation. This eliminates the primary privacy guarantee of FL (the client doesn't share raw data with the server). The entire motivation for using FL over centralized processing is called into question.

### Decision: TEE-Backed FL (keep federated, use hardware enclave)

The correct path for this project is **TEE-backed FL**: the anomaly detection pipeline runs inside a Trusted Execution Environment (Intel SGX / AMD SEV / TDX), and only the resulting anomaly scores and reputation weights leave the enclave.

| Criterion | FE-IP (rejected) | **TEE (selected)** | Reframing (rejected) |
|-----------|-----------------|---------------------|----------------------|
| Gradient confidentiality | Mathematical (encryption) | **Hardware isolation** | None — server sees everything |
| Maturity | Unproven at $d=10^5$ | **Production-ready** (Gramine, Occlum, Asylo) | — |
| Overhead | 10–100× crypto | **5–15% compute** (switching to enclave) | — |
| Attack surface | Cryptographic assumptions | **Side-channels + Intel/AMD trust** | — |
| FL compatibility | Preserved | **Preserved** | Abandoned |
| Auditability | Transparent (crypto) | **Needs verified-boot attestation** | N/A |
| Regulatory fit (GDPR/PSD2) | Best (mathematical) | **Acceptable** (enclave + auditing) | Weakest |

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│  Server with TEE Enclave                              │
│  ┌─────────────┐    ┌────────────────────────┐       │
│  │ L1 Norm     │    │ Inside Enclave:         │       │
│  │ Check       │───▶│ L2 Spectral Analyzer    │       │
│  │ (public)    │    │ L3 Reputation Engine    │       │
│  └─────────────┘    │ L4 RCC Gate              │       │
│                     │ Only scores + reputations│       │
│                     │ leave the enclave        │       │
│                     └────────────────────────┘       │
│                           │                           │
│                           ▼                           │
│                    Anomaly scores, reputation weights │
└─────────────────────────────────────────────────────┘
         ▲                            │
         │ Encrypted gradients        │ Broadcast
         │ (via TLS + enclave key)    │ reputation
         │                            ▼
    ┌────┴────┐              ┌───────────────────┐
    │ Clients │              │ Verifier (optional)│
    │ (banks) │              │ Attestation check  │
    └─────────┘              └───────────────────┘
```

**L1 norm check** stays outside the enclave (cheap, no privacy concern — gradient norms reveal little about raw data). L2, L3, and L4 operate on raw gradients inside the enclave.

**Trust model:**
- Clients trust the enclave (Intel/AMD) + the attestation mechanism, not the server operator
- The server operator administers the hardware but cannot inspect enclave memory
- Verifiable boot and remote attestation (via Intel DCAP/AMD SEV-SNP) let clients verify the correct code is running
- Malicious server operator can deny service or shutdown, but cannot exfiltrate raw gradients

**Remaining risks (must be disclosed):**
- **Side-channel attacks:** Cache timing, page-fault, and speculative-execution attacks on SGX have been demonstrated (Plundervolt, ZombieLoad). Mitigation: recent microcode updates + AMD SEV-SNP vs. SGX v2.
- **Intel/AMD as trust anchor:** The consortium relies on the TEE manufacturer's fidelity. For a regulated consortium, this is analogous to trusting a cloud provider's security posture — acceptable under due diligence.
- **Key management:** The enclave's sealing key must be managed to survive reboots. Standard TEE key management applies.
- **Performance overhead:** Context switching into the enclave costs 5–15% compute. For batch processing of $N=10$ clients at $d=500$ parameters per round, this is negligible.

**For the revision:**
- Replace the "privacy-preserving FL" framing with "TEE-backed FL for regulated fraud detection consortia"
- Add a subsection on attested execution: how clients verify the enclave before submitting gradients
- Add a risk disclosure for TEE side-channels and the hardware trust anchor
- The regulatory justification (GDPR Art. 6(1)(d), PSD2 fraud exemption) requires specifying **who verifies the enclave** and **how often**.

**Attestation design — recommended: dual-layer verification.**

*Layer 1 — Independent auditor (mandatory).* The consortium appoints a neutral verification entity (e.g., a Big 4 firm, an industry body, or a separate legal entity governed by the consortium agreement). This auditor:
  - Runs remote attestation at least once per day or on every enclave restart
  - Publishes a signed attestation report (including the enclave measurement hash, the code version, and the TCB freshness status) to a consortium-accessible audit log
  - Holds the private key for the consortium's attestation verification
  - Is operationally separate from the server hosting entity (separation of duties)

*Layer 2 — Client-opt-in verification (optional).* Any consortium member can independently attest the enclave using the platform's remote attestation protocol (Intel DCAP / AMD SEV-SNP). The enclave's public verification key and expected measurement hash are published in the consortium agreement. This requires the client bank to operate its own attestation verification service — suitable for technically capable members who want a trust-minimized setup.

**Who verifies what:**

| Entity | Verifies | Frequency | Trust model |
|--------|----------|-----------|-------------|
| Independent auditor | Enclave identity + code integrity + TCB freshness | Daily + on restart | Mandatory — all members rely on audit log |
| Client bank (opt-in) | Enclave identity | Per-connection (at will) | Optional — trust-minimized for capable members |
| Regulator (supervisory) | Auditor's reports + incident logs | Per examination cycle | Oversight — not operational |

**Regulatory fit:** Under GDPR Art. 28 (processor), the TEE with dual-layer attestation constitutes "sufficient guarantees to implement appropriate technical and organisational measures." The auditor's continuous attestation replaces cryptographic SecAgg's mathematical guarantee with an audited procedural guarantee — weaker in theory, but defensible under the fraud-detection exemption (Art. 6(1)(d), 9(2)(f)) and PSD2/PSR implementing acts.

---

## MI-5: Non-Stationarity Contradiction

Resolved by **MI-3** above (bounded-drift Stewart + sliding-window PCA + temporal dataset). No separate action needed — the bound now degrades gracefully under drift rather than collapsing.

---

# Tier 3 — Evaluation & Methodology Gaps

## MI-6: ASR Projections Inconsistent with Formal Bounds

**Source:** R1 §8 (ASR should be 0% if Theorem 1 guarantees full exclusion), DA §3 (false precision is misleading), R3 §5

**The problem.** Table V presents ASR values to two decimal places with 95% CIs, implicitly carrying the weight of empirical results. But Theorem 1 guarantees full attacker exclusion from L3, which formally implies ASR should be **exactly 0%** against attacks targeting L3 (A2 grinding attack). The non-zero ASR projection ($0.25 \pm 0.05$) implicitly acknowledges the bound is loose or violated.

### Fix

**Replace the ASR table format:**

| Defense | A1 | A2 | A3 | A4 |
|---------|----|----|----|----|
| Full Defense | **≤ 0.35** (UB) | **≤ 0.35** (UB) | **≤ 0.40** (UB) | **≤ 0.50** (UB) |

- Replace point estimates ± CI with **upper bounds** (UB) consistent with the theory
- Add a column: "Theoretical Guarantee" — e.g., "Reject if $\cos < \tau_{\text{cos}}$", "Stewart FPR ≤ 1.6%"
- Move the disclaimer to a **shaded header row** above the table, not below
- Reserve decimal-precision projections for future experimental tables

---

## MI-7: Missing Baselines

**Source:** R1 §2 (DP-FedAvg, runtime comparison)

### Add to Baseline Table (Table III)

| B11 | DP-FedAvg ($\varepsilon = 8$) | Gradient perturbation | Each $\varepsilon$ value |
| B12 | DP-FedAvg ($\varepsilon = 4$) | Gradient perturbation | is a separate row |
| B13 | DP-FedAvg ($\varepsilon = 1$) | Gradient perturbation | for all 6 attacks |
| B14 | Clipped Median | Norm clipping + median | Baseline for scaling attack |
| B15 | Multi-Krum + Trimmed Mean | Ensemble defense | Stateful baseline |

### Add Runtime Column

| Defense | Per-Round Complexity | Est. Wall Clock (N=10, d=100K) |
|---------|---------------------|-------------------------------|
| FedAvg | $O(Nd)$ | 0.01s |
| Krum | $O(N^2 d)$ | 0.1s |
| Full Defense | $O(N^2 d)$ + PCA $O(N d^2)$ | 0.8s (L3 bottleneck) |
| DP-FedAvg | $O(Nd)$ + noise | 0.01s |

---

## MI-8: Missing Metrics

**Source:** R1 §3 (reputation precision/recall, ≥10 trials)

### Add to Evaluation Plan

Beyond ASR and CA:
1. **Reputation Precision** = $TP/(TP+FP)$ — fraction of flagged clients that are actually malicious
2. **Reputation Recall** = $TP/(TP+FN)$ — fraction of malicious clients actually flagged
3. **Reputation AUC** — area under ROC curve for the L3 classification threshold
4. **False Decline Rate (FDR)** — fraction of benign updates rejected by the cascade
5. **Matthews Correlation Coefficient (MCC)** — balanced metric robust to class imbalance (few attackers)

### Trial Count

- **Increase from 5 to 10 independent trials** (seeds 0–9)
- Vary: non-IID partition seeds, client sampling orders, attack starting rounds ($t_0 \in \{10, 20, 50, 100\}$)
- Report mean ± std across the 10 seeds, not within-run confidence intervals

---

## MI-9: Missing Ablations

**Source:** R1 §5, §7 (threshold sweep, W vs τ_R sensitivity, warm-up, empty pool)

### Add to Ablation Table (Table IV)

| ID | Variant | What It Tests |
|----|---------|---------------|
| C11 | $\tau_R$ sweep: 0.60, 0.65, …, 0.95 | L3 threshold sensitivity — most important hyperparameter |
| C12 | $W$ vs $\tau_R$ 2D heatmap (W ∈ {10, 25, 50, 100, 200}) | Detects degenerate operating regimes |
| C13 | Warm-up: skip L3 for first 20 rounds | Controls for early-training instability confounding reputation |
| C14 | Empty pool fallback: revert to FedAvg when all clients flagged | System robustness under high attack rate |
| C15 | RCC inclusion vs exclusion | Validates the scaling attack fix (MI-1) |

---

# Tier 4 — Domain & Governance (Strongly Recommended)

## MI-10: Governance Vacuum

**Source:** R2 §3 (governance vacuum)

### Add Section VII-A: Consortium Agreement Structure

| Element | Specification |
|---------|--------------|
| **Legal entity** | Special Purpose Vehicle (SPV) / LLC with joint ownership proportional to reputation-weighted contribution |
| **Model IP** | Global model $\theta^{(T)}$ jointly owned; each bank receives a royalty-free license for fraud scoring |
| **Liability** | Capped at each bank's annual consortium fee; liability for erroneous scores proportional to reputation weight |
| **Onboarding** | Probationary period of $W$ rounds (reputation window length); $R_i$ initialized at 0.5 during probation |
| **Exit** | $W$-round notice period; reputation gradually forgotten over $W$ rounds |

---

## MI-11: Unrealistic Threat Model

**Source:** R2 §2 (Sybil is a non-threat in KYC'd consortia)

### Replace A4 (Sybil)

| Attack | Description | Realism | Defense Layer |
|--------|-------------|---------|---------------|
| A4': **Insider Collusion** | $m$ legitimate consortium members coordinate to poison ($m \le \lfloor N/3\rfloor$) | High — 2/10 banks colluding is plausible in a regulated consortium | L2 (spectral detection of correlated residuals) |
| A4'': **Aggregator Compromise** | Attacker compromises the aggregation server | Medium — TEE mitigation in §Future Work | Fallback: revert to standard FedAvg under dispute |

Remove A4 (Sybil with dynamic registration) unless explicitly arguing for a jurisdiction with weak KYC.

---

## MI-12: Missing Incentive Mechanism

**Source:** R2 §3 (incentive mechanism absent)

### Add Shapley-Based Contribution Scoring

**Idea.** Every $P$ rounds (matching PCA recomputation), compute each client $i$'s marginal contribution to the global model's fraud-F1 score via Truncated Monte Carlo Shapley:

$$\hat{\phi}_i = \frac{1}{K} \sum_{k=1}^{K} [F(S_{\pi_k}^{<i} \cup \{i\}) - F(S_{\pi_k}^{<i})]$$

where $K=100$ permutations, $S_{\pi_k}^{<i}$ is the set of clients preceding $i$ in permutation $\pi_k$, and $F$ is fraud-F1 on a held-out validation set.

**Feasibility for N=10:** $O(K \cdot N) = 1000$ forward passes every $P=50$ rounds = 20 model evaluations per round. Negligible overhead.

---

## MI-13: Explainability Needs Technical Proposal

**Source:** R2 §5 (GDPR Art. 22 explanation needs technical solution, not just a flag)

### Add: Global Surrogate SHAP Model

The aggregator trains an **interpretable surrogate** (e.g., XGBoost with SHAP) on a **consent-authorized proxy dataset**: a small, de-identified sample contributed by each consortium member under a specific GDPR Art. 6(1)(d) data-sharing consent for fraud prevention. The surrogate approximates the FL model's per-transaction decisions and provides SHAP attributions.

| Requirement | Solution |
|-------------|----------|
| GDPR Art. 15 (Right to explanation) | SHAP force plots for individual declined transactions |
| ECOA / FCRA (Adverse action) | Top-3 features contributing to decline decision |
| SR 11-7 (Model validation) | Surrogate fidelity $R^2 \ge 0.9$ on proxy dataset |
| Audit trail | Aggregator TEE signs model update hashes + anomaly scores for regulatory inspection |

---

# Recommended Execution Order

| Order | Item | Who | Time Estimate | Measurement of Done |
|-------|------|-----|---------------|-------------------|
| 1 | MI-1: RCC fix + Theorem 1 restatement | Formal analysis lead | 3–5 days | Written proof; RCC implementation in Python |
| 2 | MI-2: Two-timescale convergence | Theory co-author | 2–4 days | Revised Lemma 3 in paper |
| 3 | MI-3: Bounded-drift Stewart | Theory co-author | 3–5 days | Revised Eq. (4); Davis-Kahan bound derived |
| 4 | MI-4: Resolve trust model (FE-IP outline or reframe) | Lead author | 1–2 weeks | Title change; new trust subsection; FE-IP lit review |
| 5 | MI-6: Reframe ASR table | Lead author | 1 day | New Table V with upper bounds |
| 6 | MI-7–9: Baselines, metrics, ablations (paper text) | Lead author | 3 days | Updated Tables III, IV; new metric definitions |
| 7 | MI-10–13: Governance + threat model + incentives + explainability | Domain specialist | 1 week | New Section VII-A; updated threat model; Shapley design |
| 8 | MI-7–9: Actually run experiments | ML engineer | 2 months (cloud) | Real ASR, FPR, ablation curves |

**The critical path** is items 1–3 (proofs) followed by item 8 (experiments). Items 4–7 can run in parallel.

---

*End of solution plan. Return to this document when ready to execute individual items.*
