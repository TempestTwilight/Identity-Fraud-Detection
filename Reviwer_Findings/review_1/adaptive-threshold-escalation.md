# Adaptive Threshold Escalation Mechanism — Formal Specification

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Issue:** R2 — Formalize the adaptive threshold escalation mechanism  
**Status:** Draft v1  
**Date:** 2026-07-05

---

## 1. Overview

The framework's novelty claim rests on a **principled orchestration** of three detection layers. The adaptive threshold escalation is the mechanism that controls *when* each layer is consulted and *how* their outputs are fused. This document provides the formal specification.

### Design Goals

| Goal | Requirement | Measured By |
|------|-------------|-------------|
| **Efficiency** | Cheapest layers handle majority of updates | Fraction accepted at Layer 1 per round |
| **Coverage** | All attack types detected by at least one layer | True positive rate per attack type |
| **Robustness** | No single layer failure mode breaks the system | Graceful degradation under adaptive attack |
| **Stability** | Thresholds don't oscillate under normal noise | Variance of $\tau$ under no-attack baseline |

---

## 2. Notation

| Symbol | Meaning | Domain |
|--------|---------|--------|
| $N$ | Number of clients | $\mathbb{N}$ |
| $\mathcal{G}^{(t)} = \{g_1, ..., g_N\}$ | Client updates at round $t$ | $\mathbb{R}^{N \times d}$ |
| $L_k$ | Layer $k$ detector function | $L_k: \mathbb{R}^d \to [0,1]^2$ |
| $a_{k,i}^{(t)}$ | Anomaly score from $L_k$ on $g_i^{(t)}$ | $[0, 1]$ (1 = definitely honest) |
| $c_{k,i}^{(t)}$ | Confidence of $L_k$ in its score for $g_i^{(t)}$ | $[0, 1]$ (1 = absolutely certain) |
| $\tau_k^{(t)}$ | Escalation threshold for layer $k$ at round $t$ | $[0.5, 0.95]$ |
| $\phi^{(t)}$ | Global attack alarm at round $t$ | $\{0, 1\}$ |
| $\rho^{(t)}$ | Fraction of clients flagged as suspicious | $[0, 1]$ |

---

## 3. Per-Layer Confidence Functions

Each layer outputs both an anomaly score and a confidence. The confidence captures how *reliable* the layer's score is given the current data.

### Layer 1 — Norm/Cosine Filtering

```
L1(g_i) -> (a_1, c_1)
```

**Anomaly score:**

$$a_{1,i} = \frac{1}{2}\left( \text{sigmoid}\left(\frac{\mu_{\text{norm}} - \|g_i\|}{\sigma_{\text{norm}}}\right) + \text{sigmoid}\left(\frac{\cos(g_i, g_{\text{ref}}) - \mu_{\text{cos}}}{\sigma_{\text{cos}}}\right) \right)$$

where $\mu_{\text{norm}}, \sigma_{\text{norm}}$ are the running mean and std of honest update norms, and $g_{\text{ref}}$ is the global model update direction.

**Confidence:**

$$c_{1,i} = 1 - \frac{1}{2}\left( \mathbb{1}_{[\text{near-threshold}]} \cdot \alpha_{\text{norm}} + \mathbb{1}_{[\text{near-threshold}]} \cdot \alpha_{\text{cos}} \right)$$

Confidence is *low* when the update is near the decision boundary. $\alpha_{\text{norm}}, \alpha_{\text{cos}}$ are penalty coefficients that drop confidence when the score lies within $\epsilon$ of the threshold.

**Rationale:** Norm and cosine are cheap ($O(d)$) and reliable for extreme cases (very high norm = obvious attack; very low norm = obvious honest). Their confidence degrades for borderline cases — which is exactly when we want to escalate.

### Layer 2 — Spectral Anomaly Detection

```
L2(G, g_i) -> (a_2, c_2)
```

**Anomaly score:**

Let $\mathbf{R}^{(t)} = \mathbf{G}^{(t)} - \mathbf{1}_N \otimes \bar{g}^{(t)}$ be the residual matrix. Perform PCA on $\mathbf{R}^{(t)}$ and retain top $k$ components $V_k$ explaining $\geq \gamma\%$ of variance.

$$a_{2,i} = 1 - \frac{\|g_i - \text{proj}_{V_k}(g_i)\|}{\max_j \|g_j - \text{proj}_{V_k}(g_j)\|}$$

A score near 0 means $g_i$ lies *outside* the principal subspace (suspicious). A score near 1 means it lies *within* (consistent with majority variance).

**Confidence:**

$$c_{2,i} = \min\left(\frac{\lambda_k}{\lambda_1}, \frac{m}{m+1}\right)$$

where $\lambda_k$ is the $k$-th singular value and $m$ is the number of flagged clients from Layers 1+3 in this round. Confidence is *high* when (a) the principal subspace explains most variance cleanly, and (b) multiple layers independently flag the same client.

### Layer 3 — Temporal Reputation

```
L3(g_i, R_i^{(t)}) -> (a_3, c_3)
```

Where $R_i^{(t)} \in [0, 1]$ is client $i$'s running reputation score.

**Anomaly score:**

$$a_{3,i} = R_i^{(t)} \cdot \left(1 - \frac{\|g_i - \hat{g}_i^{(t)}\|}{\max_j \|g_j - \hat{g}_j^{(t)}\|}\right)$$

where $\hat{g}_i^{(t)}$ is the expected update based on $i$'s historical behavior (e.g., exponential moving average of past updates). This scores how *consistent* the current update is with the client's own history.

**Confidence:**

$$c_{3,i} = \min\left(\frac{t}{t_0}, 1\right) \cdot R_i^{(t)}$$

Confidence grows with observation history $t$ (up to maturity $t_0$) and scales with current reputation. New clients get low confidence until sufficient history accumulates.

---

## 4. Escalation Policy

### 4.1 Per-Client Escalation Decision

For client $i$ at round $t$:

```
def escalate(client_update g_i, thresholds [τ1, τ2]):
    # Layer 1
    a1, c1 = L1(g_i)
    if c1 >= τ1:
        return a1  # Layer 1 confident — accept its score
    
    # Layer 2
    a2, c2 = L2(G, g_i)
    if c2 >= τ2:
        return a2  # Layer 2 confident — accept its score
    
    # Layer 3
    a3, c3 = L3(g_i, R_i)
    return a3     # Always decide at Layer 3 (no further escalation)
```

**Key property:** The system guarantees a decision with bounded computational cost. Worst case: all three layers run. Best case: only Layer 1 runs.

### 4.2 Decision Aggregation

Once each client $i$ has a final anomaly score $a_i^{(t)}$, the aggregation server:

1. **Rejects** clients with $a_i^{(t)} < \theta_{\text{reject}}$ (malicious)
2. **Down-weights** clients with $\theta_{\text{reject}} \leq a_i^{(t)} < \theta_{\text{accept}}$ (suspicious)
3. **Accepts** clients with $a_i^{(t)} \geq \theta_{\text{accept}}$ (honest)

The accepted/down-weighted updates are aggregated via **reputation-weighted trimmed mean**:

$$g_{\text{agg}}^{(t)} = \frac{\sum_{i \in \mathcal{A}} w_i \cdot g_i}{\sum_{i \in \mathcal{A}} w_i}$$

where:
- $\mathcal{A}$ is the set of clients not rejected
- $w_i = R_i^{(t)} \cdot \mathbb{1}_{[a_i \geq \theta_{\text{accept}}]} + (R_i^{(t)} \cdot \beta) \cdot \mathbb{1}_{[\theta_{\text{reject}} \leq a_i < \theta_{\text{accept}}]}$ with $\beta \in (0, 1)$
- The trim rate $\delta^{(t)}$ is adaptive: $\delta^{(t)} = \delta_0 \cdot (1 + \phi^{(t)} \cdot \alpha_{\text{trim}})$

---

## 5. Adaptive Threshold Update

This is the core of the mechanism — thresholds $\tau_1, \tau_2$ evolve across rounds based on attack conditions.

### 5.1 Attack Alarm Signal

A global attack alarm $\phi^{(t)} \in \{0, 1\}$ fires at round $t$ if:

$$\phi^{(t)} = \mathbb{1}\left[ \rho^{(t)} > \rho_0 + 2\sigma_{\rho} \quad \text{OR} \quad \Delta\mathcal{L}^{(t)} > \Delta\mathcal{L}_0 + 2\sigma_{\mathcal{L}} \right]$$

where:
- $\rho^{(t)} = \frac{1}{N}\sum_i \mathbb{1}_{[a_i^{(t)} < \theta_{\text{accept}}]}$ — fraction flagged
- $\Delta\mathcal{L}^{(t)} = \mathcal{L}^{(t)} - \mathcal{L}^{(t-1)}$ — change in validation loss
- $\rho_0, \sigma_{\rho}, \Delta\mathcal{L}_0, \sigma_{\mathcal{L}}$ — stable-state statistics

### 5.2 Threshold Update Rules

**Under normal conditions ($\phi^{(t)} = 0$):**
Thresholds relax to reduce computational overhead:

$$\tau_k^{(t+1)} = \min\left(\tau_k^{\max}, \tau_k^{(t)} + \eta_{\text{relax}} \cdot (\tau_k^{\max} - \tau_k^{(t)})\right)$$

**Under attack ($\phi^{(t)} = 1$):**
Thresholds tighten to force escalation to stronger layers:

$$\tau_k^{(t+1)} = \max\left(\tau_k^{\min}, \tau_k^{(t)} - \eta_{\text{attack}} \cdot \rho^{(t)}\right)$$

**Bounded range:** $\tau_k^{(t)} \in [\tau_k^{\min}, \tau_k^{\max}]$

### 5.3 Default Parameters

| Parameter | Layer 1 | Layer 2 | Rationale |
|-----------|---------|---------|-----------|
| $\tau^{\min}$ | 0.55 | 0.55 | Minimum confidence threshold (must be > 0.5 to mean anything) |
| $\tau^{\max}$ | 0.90 | 0.85 | Maximum — above this, even cheap layers are trusted |
| $\eta_{\text{relax}}$ | 0.05 | 0.03 | How fast thresholds relax back to max after an attack |
| $\eta_{\text{attack}}$ | 0.15 | 0.10 | How fast thresholds tighten under attack detection |

These parameters would be tuned empirically in the experiments.

---

## 6. Pseudo-Code

```python
# =============================================================================
# Adaptive Threshold Escalation — Orchestration Logic
# =============================================================================

class AdaptiveThresholdEscalation:
    """
    Orchestrates the 3-layer defense with adaptive thresholds.
    
    The key design principle: most updates are handled by Layer 1 (cheap).
    Only genuinely ambiguous cases escalate to Layer 2 or Layer 3.
    Thresholds adapt based on detected attack intensity.
    """
    
    def __init__(self, n_clients: int, dim: int):
        # Layer thresholds — these adapt across rounds
        self.tau_1 = 0.75  # τ1: Layer 1 confidence threshold
        self.tau_2 = 0.70  # τ2: Layer 2 confidence threshold
        
        # Threshold bounds
        self.TAU_1_MIN, self.TAU_1_MAX = 0.55, 0.90
        self.TAU_2_MIN, self.TAU_2_MAX = 0.55, 0.85
        
        # Hyperparameters
        self.eta_relax = 0.05    # relaxation rate (no attack)
        self.eta_attack = 0.15   # tightening rate (under attack)
        self.rho_0 = 0.10        # expected baseline flag rate
        self.sigma_rho = 0.05    # std of flag rate under normal conditions
        
        # Stable-state statistics (updated each round)
        self.rho_history = []    # rolling window of flag rates
        self.window_size = 20
        
        # Reputation scores
        self.reputations = [1.0] * n_clients
        self.t = 0              # round counter
        
        # Detection layers
        self.layer1 = NormCosineFilter()
        self.layer2 = SpectralDetector(dim)
        # Layer 3 is implicit in the reputation tracking
        
    def process_round(self, updates: List[np.ndarray]) -> Tuple[np.ndarray, Dict]:
        """
        Process one FL round.
        
        Args:
            updates: list of N client gradient updates
            
        Returns:
            aggregated gradient, per-client anomaly info
        """
        N = len(updates)
        final_scores = np.zeros(N)
        escalation_stats = {'layer1': 0, 'layer2': 0, 'layer3': 0}
        
        for i, g_i in enumerate(updates):
            # ---- Layer 1: Norm/Cosine Filter ----
            a1, c1 = self.layer1.score(g_i)
            
            if c1 >= self.tau_1:
                # Layer 1 is confident — accept its score, stop here
                final_scores[i] = a1
                escalation_stats['layer1'] += 1
                continue
            
            # ---- Layer 2: Spectral Anomaly Detection ----
            a2, c2 = self.layer2.score(updates, i)
            
            if c2 >= self.tau_2:
                # Layer 2 is confident — accept its score, stop here
                final_scores[i] = a2
                escalation_stats['layer2'] += 1
                continue
            
            # ---- Layer 3: Temporal Reputation (always decides) ----
            a3 = self._temporal_reputation_score(g_i, i)
            final_scores[i] = a3
            escalation_stats['layer3'] += 1
        
        # ---- Decision Aggregation ----
        mask = self._flag_clients(final_scores)
        aggregated_grad = self._reputation_weighted_aggregate(updates, final_scores)
        
        # ---- Adaptive Threshold Update ----
        self._update_thresholds(final_scores)
        
        # ---- Update Reputations ----
        self._update_reputations(final_scores, updates)
        self.t += 1
        
        info = {
            'final_scores': final_scores,
            'escalation_stats': escalation_stats,
            'tau_1': self.tau_1,
            'tau_2': self.tau_2,
            'reputations': self.reputations.copy(),
        }
        
        return aggregated_grad, info
    
    def _temporal_reputation_score(self, g_i: np.ndarray, client_id: int) -> float:
        """Score based on client's reputation and consistency with history."""
        # Reputation provides the base trust score
        # (Implementation depends on specific temporal model)
        return self.reputations[client_id]
    
    def _flag_clients(self, scores: np.ndarray) -> np.ndarray:
        """Classify clients as accept / suspicious / reject based on scores."""
        THETA_ACCEPT = 0.6
        THETA_REJECT = 0.3
        flags = np.zeros(len(scores), dtype=int)
        flags[scores >= THETA_ACCEPT] = 1      # accepted
        flags[scores <= THETA_REJECT] = -1     # rejected
        # Remainder (0) = suspicious — down-weighted
        return flags
    
    def _reputation_weighted_aggregate(
        self, 
        updates: List[np.ndarray], 
        scores: np.ndarray
    ) -> np.ndarray:
        """Aggregate accepted + down-weighted suspicious updates."""
        THETA_ACCEPT = 0.6
        THETA_REJECT = 0.3
        BETA = 0.5  # down-weight for suspicious
        
        weights = np.zeros(len(updates))
        for i in range(len(updates)):
            if scores[i] >= THETA_ACCEPT:
                weights[i] = self.reputations[i]
            elif scores[i] >= THETA_REJECT:
                weights[i] = self.reputations[i] * BETA
            # else: rejected -> weight = 0
        
        if weights.sum() == 0:
            return np.zeros_like(updates[0])
        
        agg = sum(w * u for w, u in zip(weights, updates))
        return agg / weights.sum()
    
    def _detect_attack(self, scores: np.ndarray) -> bool:
        """Fire attack alarm if flag rate deviates significantly from baseline."""
        rho_t = np.mean(scores < 0.6)  # fraction not fully accepted
        
        self.rho_history.append(rho_t)
        if len(self.rho_history) > self.window_size:
            self.rho_history.pop(0)
        
        if len(self.rho_history) < 10:
            return False  # not enough history
        
        rho_mean = np.mean(self.rho_history)
        rho_std = np.std(self.rho_history) + 1e-8
        
        return rho_t > rho_mean + 2 * rho_std
    
    def _update_thresholds(self, scores: np.ndarray):
        """Adapt thresholds based on detected attack intensity."""
        under_attack = self._detect_attack(scores)
        
        if under_attack:
            rho_t = np.mean(scores < 0.6)
            # Tighten: lower thresholds = more escalation
            self.tau_1 = max(self.TAU_1_MIN, self.tau_1 - self.eta_attack * rho_t)
            self.tau_2 = max(self.TAU_2_MIN, self.tau_2 - self.eta_attack * rho_t)
        else:
            # Relax: raise thresholds = less escalation (efficiency)
            self.tau_1 = min(self.TAU_1_MAX, self.tau_1 + self.eta_relax * 
                           (self.TAU_1_MAX - self.tau_1))
            self.tau_2 = min(self.TAU_2_MAX, self.tau_2 + self.eta_relax * 
                           (self.TAU_2_MAX - self.tau_2))
    
    def _update_reputations(self, scores: np.ndarray, updates: List[np.ndarray]):
        """Update per-client reputation scores based on current round."""
        ALPHA = 0.1  # EMA smoothing factor
        for i in range(len(scores)):
            # Reputation update: exponential moving average of anomaly scores
            # Higher anomaly score → better reputation
            self.reputations[i] = (1 - ALPHA) * self.reputations[i] + ALPHA * scores[i]
```

---

## 7. Convergence Analysis (Sketch)

### 7.1 Claim

Under bounded non-IID and a Byzantine fraction $f < \frac{1}{3}$, the adaptive threshold mechanism converges to a fixed point $\tau_1^*, \tau_2^*$ such that:

$$\mathbb{P}[\text{false reject}] + \mathbb{P}[\text{false accept}] \leq \epsilon(f)$$

where $\epsilon(f)$ is a monotone increasing function of the Byzantine fraction $f$.

### 7.2 Intuition

The threshold update is a **stochastic approximation** process:

$$\tau_k^{(t+1)} = \tau_k^{(t)} + \eta^{(t)} \cdot h(\tau_k^{(t)}, \xi^{(t)})$$

where $h$ is the update direction (tightening or relaxing) and $\xi$ captures the random attack pattern.

Under the ODE method for stochastic approximations [Borkar, 2008], the iterates converge to the equilibrium of:

$$\dot{\tau}_k = \mathbb{E}_{\xi}[h(\tau_k, \xi)]$$

At equilibrium, the tightening force (false accept rate too high → lower threshold) balances the relaxing force (false reject rate too high → higher threshold). The balance point depends on the true attack rate.

### 7.3 Convergence Condition

If:
- $\eta^{(t)}$ satisfies the Robbins-Monro conditions ($\sum \eta^{(t)} = \infty$, $\sum (\eta^{(t)})^2 < \infty$)
- $h$ is Lipschitz in $\tau_k$
- The process $\{\xi^{(t)}\}$ is a Markov chain with a unique stationary distribution

Then $\tau_k^{(t)} \to \tau_k^*$ almost surely.

**Practical note:** We use constant $\eta$ (not decaying) in the implementation to maintain adaptivity to changing attack patterns. This means we get convergence to a *neighborhood* rather than a point — which is actually desirable for a fraud detection system that must adapt to evolving attacks.

### 7.4 Stability Bounds

The bounded range $[\tau_k^{\min}, \tau_k^{\max}]$ guarantees:

- **No runaway tightening:** $\tau_k^{(t)} \geq \tau_k^{\min} > 0.5$ prevents thresholds from collapsing to zero (which would escalate every update to Layer 3, destroying efficiency).
- **No runaway relaxation:** $\tau_k^{(t)} \leq \tau_k^{\max} < 1.0$ prevents thresholds from reaching 1.0 (which would never escalate, making the additional layers useless).

---

## 8. Parameters Summary

| Parameter | Symbol | Default | Tuning Method |
|-----------|--------|---------|---------------|
| Layer 1 min threshold | $\tau_1^{\min}$ | 0.55 | Fixed — below this, Layer 1's confidence is unreliable |
| Layer 1 max threshold | $\tau_1^{\max}$ | 0.90 | Fixed — | 
| Layer 2 min threshold | $\tau_2^{\min}$ | 0.55 | Fixed |
| Layer 2 max threshold | $\tau_2^{\max}$ | 0.85 | Fixed |
| Initial threshold τ₁ | $\tau_1^{(0)}$ | 0.75 | Sensitive — tune on validation data |
| Initial threshold τ₂ | $\tau_2^{(0)}$ | 0.70 | Sensitive — tune on validation data |
| Attack tightening rate | $\eta_{\text{attack}}$ | 0.15 | Sensitive — too high causes oscillation |
| Relaxation rate | $\eta_{\text{relax}}$ | 0.05 | Less sensitive |
| Target flag rate | $\rho_0$ | 0.10 | Domain-dependent |
| Reputation EMA factor | $\alpha$ | 0.10 | Sensitive — controls memory length |
| Accept threshold | $\theta_{\text{accept}}$ | 0.60 | Fixed — maps anomaly score to decision |
| Reject threshold | $\theta_{\text{reject}}$ | 0.30 | Fixed |
| Suspicious down-weight | $\beta$ | 0.50 | Tunable |
| Reputation maturity | $t_0$ | 20 rounds | Fixed |

---

## 9. Integration with Flower

The adaptive threshold escalation mechanism will be implemented as a **custom aggregation strategy** in Flower. The critical path is the `aggregate_fit` method:

```python
import flwr as fl
from typing import List, Tuple, Dict, Optional

class AdaptiveLayeredDefenseStrategy(fl.server.strategy.Strategy):
    """Flower strategy wrapping the AdaptiveThresholdEscalation orchestrator."""
    
    def __init__(self, n_clients: int, dim: int, **kwargs):
        self.orchestrator = AdaptiveThresholdEscalation(n_clients, dim)
        self.model_dim = dim
        super().__init__(**kwargs)
    
    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[BaseException],
    ) -> Optional[fl.common.Parameters]:
        
        # Extract gradient updates from Flower results
        updates = []
        for client, fit_res in results:
            params = fl.common.parameters_to_ndarrays(fit_res.parameters)
            # params[0] is the model weights
            # Convert to gradient: g_i = w_i^{(t)} - w^{(t-1)}
            grad = params[0] - self.current_global_model
            updates.append(grad)
        
        # Run adaptive threshold escalation
        aggregated_grad, info = self.orchestrator.process_round(updates)
        
        # Log stats for analysis
        self._log_round(server_round, info)
        
        # Convert back to Flower Parameters
        new_weights = self.current_global_model + aggregated_grad
        return fl.common.ndarrays_to_parameters([new_weights]), {}
```

---

## 10. Experimental Validation Plan

To validate the adaptive threshold mechanism itself:

| Experiment | What It Tests | Metric |
|------------|---------------|--------|
| No-attack baseline | Efficiency under normal conditions | % resolved at Layer 1, Layer 2, Layer 3 |
| Attack wave (sudden) | Threshold tightening response | Latency to reach min(τ) after attack starts |
| Attack wave (gradual) | Detection of creeping attacks | False negative rate of attack alarm φ |
| Post-attack recovery | Threshold relaxation dynamics | Time to return to 90% of max(τ) |
| Oscillation test | Stability under no-attack noise | Variance of τ₁, τ₂ over 100 rounds |
| Parameter sweep | Sensitivity to η_attack, η_relax | Convergence time, false alarm rate |
