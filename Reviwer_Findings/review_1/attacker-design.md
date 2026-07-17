# Adaptive Attacker Evaluation Design

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Issue:** R4 — Design adaptive attacker evaluation  
**Date:** 2026-07-06

---

## 1. Motivation

The Devil's Advocate review flagged: *"No adaptive attacker — standard for a Q1 security venue is evaluation against defender-aware adaptive attacks (Fang et al. 2020-style optimal attacks)."*

Domain Expert (R2) added: *"An adversary that knows your defense layers … Evaluate against adaptive attacks (e.g., an adversary that passes the norm check, the SVD check, AND maintains a good temporal reputation while injecting a backdoor)."*

**This section designs exactly those adversaries.** Every attack is a concrete algorithm targeting the specific architectural weaknesses of our 3-layer defense.

---

## 2. Threat Model

### 2.1 Attacker Capabilities

| Capability | Assumption | Rationale |
|------------|------------|-----------|
| **Compromised clients** | Controls 1–5 out of N=20 banks | Standard Byzantine FL: minority corruption |
| **Model access** | Full white-box knowledge of architecture + per-round global model | Attacker trains on same data splits; can simulate server-side aggregation |
| **Defense knowledge** | Full knowledge of all 3 layers, including threshold update rules | Kerckhoffs's principle for security venues |
| **Temporal scope** | Persistent across rounds; can coordinate Sybil identities | Real fraud rings operate continuously |
| **Data access** | Own local dataset; can craft arbitrary gradients | Standard FL attacker model |

### 2.2 Attack Goals

| Goal | Definition | Severity |
|------|------------|----------|
| **Backdoor injection** | Embed a targeted trigger (specific transaction pattern) that the global model predicts as benign | Critical |
| **Model degradation** | Increase global model's false negative rate on fraud | High |
| **Model collapse** | Drive global model parameters to random initialization | Moderate (detectable) |

The evaluation focuses on **backdoor injection** as the primary threat — an attacker that wants to make specific fraud transactions invisible to the model while the model performs normally on everything else.

### 2.3 Attack Success Criteria

| Metric | Target for "Successful Attack" |
|--------|-------------------------------|
| Attack Success Rate (ASR) | > 50% (backdoor triggered on held-out test) |
| Main Task Accuracy | Within 2% of clean baseline (attack is stealthy) |
| Evasion of Defenses | 0 attacks flagged across all 3 layers for ≥5 consecutive rounds |
| Undetected Fraud Rate | > 10% increase in misclassified fraud cases |

---

## 3. Attack A1: Oracle White-Box Attack

*Method:* Fang et al. (2020) optimal attack adapted to our layered defense.

### 3.1 Attacker Knowledge

The attacker knows at round $t$:
- All client updates $\{g_1^{(t)}, ..., g_N^{(t)}\}$ (simulated locally — attacker has the same data split)
- The global model $w^{(t)}$
- Layer 1 thresholds: $\tau_1$, norm statistics $\mu_{\text{norm}}^{(t)}, \sigma_{\text{norm}}^{(t)}$
- Layer 2 projection: top-$k$ singular vectors $U_k^{(t-1)}$ from previous round
- Layer 3 parameters: EMA decay $\beta$, reputation time window $T$
- Adaptive threshold parameters: $\eta_{\text{attack}}, \theta_{\text{alarm}}, \gamma$

### 3.2 Attack Procedure

```
Input: Malicious update target g_target (gradient that achieves backdoor on attacker's data)
       Round t, global model w^(t), honest updates g_1 ... g_{N-m}
Parameters: ε_step (learning rate for evasion)

Output: Crafted malicious update g_mal

1. Initialize g_mal = g_target

2. For iteration = 1 .. max_iter:
   a. Compute norm_score, cos_score, confidence from Layer 1
   b. If Layer 1 would reject g_mal:
      - Project g_mal back toward honest manifold:
        g_mal ← g_mal - ε_step · ∇_{g} ℓ_L1(g)
      - (ℓ_L1 is the "evasion loss" — how far from honest norm/cosine bounds)
   
   c. If Layer 2 would reject g_mal:
      - Project g_mal onto top-k singular vectors of honest updates:
        g_mal ← U_k U_k^T · g_mal + (1 - α) · (g_mal - U_k U_k^T · g_mal)
      - (α controls what fraction stays in the honest subspace)
   
   d. If composite anomaly_score < τ_2 (would escalate to Layer 3):
      - Compute whether Layer 3 would reject based on EMA reputation
      - Bound the per-round change: ‖g_mal - g_mal^{(t-1)}‖ < δ_smooth

   e. If all layers would accept g_mal + main task loss not too degraded:
      - Break and return g_mal

3. If no valid evasion found after max_iter:
   - Return g_target (unstealthy high-magnitude attack — serves as baseline)
```

### 3.3 Expected Failure Mode

*What the defense does:* The oracle attack should succeed against Layer 1 alone (norm/cosine can be matched), struggle against Layer 2 (spectral correlation is harder to fake without knowledge of the exact SVD), and be caught by Layer 3 if it's too aggressive (large per-round changes).

*Key insight:* The attack cannot maintain **temporal consistency** — the backdoor gradient is fundamentally different from the honest gradient direction over many rounds. Layer 3's EMA reputation should decay even if each individual round passes L1 and L2 checks.

### 3.4 Variant: A1-Black (Black-Box)

Same as A1 but without access to exact SVD projections — uses stale $U_k$ from up to 5 rounds prior. Measures how quickly the spectral basis changes and whether stale knowledge helps the attacker.

---

## 4. Attack A2: Gradient Grinding Attack

*Method:* Inspired by Jagielski et al. (2018) "manipulating ML by poisoning data samples" — gradient descent on the defense loss.

### 4.1 Mechanism

Instead of injecting a backdoor in one shot, the attacker **slowly drifts** the global model by submitting slightly malicious updates each round. The drift is designed to:

1. Keep each per-round gradient within the normal envelope
2. Accumulate the malicious signal over 50–100 rounds
3. Eventually cause the model to misclassify specific fraud patterns

### 4.2 Formalization

Let $d^{(t)} \in \mathbb{R}^d$ be the attacker's desired drift direction at round $t$. The actual submitted gradient is:

$$g_{\text{grind}}^{(t)} = g_{\text{honest}}^{(t)} + \lambda \cdot d^{(t)}$$

where $\lambda$ is the grinding coefficient chosen such that:

$$\lambda = \min\left(\lambda_{\max}, \frac{\tau_1 - \text{score}(g_{\text{honest}}^{(t)})}{\|d^{(t)}\|}\right)$$

This ensures the composite gradient's norm and cosine score stay just within Layer 1's acceptance region.

### 4.3 Grinding Coefficient Schedule

| Phase | Rounds | λ | Strategy |
|-------|--------|---|----------|
| Burn-in | 1–20 | 0 | Build honest reputation |
| Subliminal | 21–60 | λ_max · 0.3 | Gentle drift, below alarm sensitivity |
| Active | 61–100 | λ_max · 0.6 | Stronger drift, watch for alarm |
| Cooldown | 101–120 | 0 | Detoxify reputation if alarm fired |

### 4.4 Expected Failure Mode

*What the defense does:* The grinding attack should succeed against Layer 2 (per-round SVD won't detect a gentle drift) and partially against Layer 3 (the EMA smooths over slow changes). However, the adaptive threshold escalation should tighten as the drift accumulates — the attack alarm ($2\sigma$ detection) should fire around round 60-80.

*Key insight:* The adaptive threshold's statistical test on $\Delta \bar{s}^{(t)}$ is designed exactly for this: it detects when the *system's* average anomaly score drifts beyond expected variation, catching the grinding attack even when no individual client looks anomalous.

---

## 5. Attack A3: Spectral-Matching Attack

*Method:* The attacker crafts updates that lie in the low-rank "normal" subspace identified by SVD.

### 5.1 Mechanism

After round $t-1$, the attacker learns the top-$k$ right singular vectors $V_k \in \mathbb{R}^{d \times k}$ from the SVD of honest updates (these are publicly observable if the server broadcasts the SVD basis for verification — or the attacker estimates them from local simulation).

The malicious gradient is projected onto the honest subspace:

$$g_{\text{spectral}} = V_k V_k^T \cdot g_{\text{mal}} + \underbrace{(I - V_k V_k^T) \cdot g_{\text{mal}}}_{\text{cut off}}$$

Then a small adversarial signal $\epsilon$ is injected in the *nullspace* directions (those SVD discards):

$$g_{\text{final}} = V_k V_k^T \cdot g_{\text{mal}} + \epsilon_{\text{null}}$$

where $\|\epsilon_{\text{null}}\| \ll \|g_{\text{mal}}\|$ and $\epsilon_{\text{null}}$ carries the backdoor signal in SVD-invisible dimensions.

### 5.2 SVD Update Frequency Impact

The attack's success depends on whether the SVD basis changes each round:

| SVD Update Policy | Attacker Knowledge | Attack Success |
|-------------------|-------------------|----------------|
| Every round $U_k^{(t)}$ | Perfect (current basis) | High |
| Every $k$ rounds | Stale basis | Moderate (if basis drifts) |
| Only on alarm | Very stale | Low |

**Recommendation for the paper:** Update the SVD basis every round (cheap, $O(Nd^2)$ for $N=20$). This forces the attacker to estimate the current basis and reduces spectral-matching effectiveness.

### 5.3 Expected Failure Mode

*What the defense does:* The spectral-matching attack is the hardest for Layer 2 to detect — the gradient literally lives in the honest subspace. However:

- The residual $\epsilon_{\text{null}}$ carries the backdoor signal. If the subspace captures $90\%$ of variance, the remaining $10\%$ may not carry enough signal for a successful backdoor.
- Layer 3 catches this: if the attacker consistently uses the same subspace-projected gradient while honest clients' gradients span a wider space, the EMA reveals anomalously low variance.
- The norm and cosine scores (Layer 1) will detect any misalignment between the subspace projection and the true honest gradient direction.

---

## 6. Summary: Defense Coverage Against Each Attack

| Attack | Layer 1 (Norm/Cos) | Layer 2 (SVD) | Layer 3 (Temporal) | Adaptive Thresholds |
|--------|-------------------|---------------|-------------------|-------------------|
| **A1: Oracle white-box** | 🟡 Matchable | 🟡 Harder with current basis | 🔴 EMA decay catches long-term deviation | 🟡 Tightens over time |
| **A1-Black** | 🟡 Matchable | 🟡 Stale basis = noisy constraint | 🟢 Same as A1 | 🟢 Same |
| **A2: Grinding** | 🟢 Each round passes | 🟢 Per-round invisible | 🟡 Slow drift partially captured | 🟢 **Primary defense** — statistical alarm on cumulative drift |
| **A3: Spectral-matching** | 🟢 Matches norm/cos | 🟢 **Bypasses** subspace detection | 🟢 Excessive consistency = anomalous | 🟡 Tightens but hard to catch clean subspace match |

**Key insight for paper narrative:** No *single* layer catches all 3 attacks. The orchestration's value is that each attack is caught by a *different* layer combination. The adaptive thresholds raise the bar against A2 (grinding) specifically — which is the hardest type of fraud attack to detect in practice.

---

## 7. Evaluation Protocol

### 7.1 Experiment Setup

| Parameter | Value |
|-----------|-------|
| N banks | 20 (16 honest, 4 malicious) |
| Malicious fraction | 20% (conservative — realistic fraud rings don't control half the consortium) |
| Rounds | 200 |
| Attacks per experiment | Each A1–A3 run independently (separate experiments) |
| Random seeds | 5 per configuration |
| Dataset | IEEE-CIS (primary), ECC (secondary) |

### 7.2 Metrics Reported Per Attack

| Metric | What It Measures |
|--------|------------------|
| ASR (Attack Success Rate) | Fraction of backdoor triggers misclassified as benign |
| Main Task Accuracy | Model accuracy on clean test data (stealth metric) |
| Rounds to Detection | First round where defense outputs non-zero anomaly score for attacker |
| Escape Rate | Fraction of attackers flagged after 200 rounds |
| Per-Layer Contribution | Which layer(s) flagged the attacker, per round |

### 7.3 Expected Results Matrix

```
                          ASR ↓    Acc ↓    Flagged ↓  Rounds to Detection ↓
No defense                0.92     0.04     0/4         —
FedAvg                     0.85     0.03     0/4         —
Krum                       0.60     0.05     1/4         45
Trimmed Mean              0.55     0.04     1/4         52
FoolsGold                  0.40     0.06     2/4         38
Our defense (A1)           0.25     0.03     3/4         22
Our defense (A2)           0.15     0.02     3/4         68 (adaptive alarm fires)
Our defense (A3)           0.35     0.04     2/4         31
```

(Specific numbers are heuristics — to be filled with actual experiment results.)

### 7.4 Statistical Rigor (Reviewer R1's Requirement)

- **5 random seeds** per experiment
- **Confidence intervals** reported at 95% (bootstrapped)
- **Statistical significance** tested via paired bootstrap test (p < 0.05) against best baseline

---

## 8. Implementation: `ifd_fintech/attacks/` Module

The attacks are implemented in the Python package under `ifd_fintech/attacks/` with the following interface:

```python
class AdaptiveAttacker(ABC):
    """Base class for all adaptive attacks."""

    def __init__(self, n_malicious: int, defense_knowledge: dict):
        ...

    @abstractmethod
    def craft_update(self, round_t: int, updates: list, 
                     global_model: np.ndarray) -> list[np.ndarray]:
        """Craft malicious updates given observed state."""
        ...

    def set_backdoor_target(self, trigger_pattern: np.ndarray, 
                            target_label: int):
        """Define the backdoor the attacker wants to embed."""
        ...
```

Each attack variant (A1, A2, A3) implements `craft_update()` with the specific evasion strategy from sections 3–5.
