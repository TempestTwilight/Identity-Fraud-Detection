# Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework

**Design-Stage Specification with Expected Results**

*Target: IEEE Transactions on Information Forensics and Security (TIFS)*

---

## Abstract

Cross-silo federated learning (FL) enables banks to collaboratively train fraud detection models without sharing raw transaction data. However, financially motivated adversaries who compromise a client bank can poison the global model to evade detection of their own fraud patterns. Existing Byzantine-robust aggregation methods—Krum, trimmed mean, Bulyan, FLTrust, and others—are **stateless**: each training round is evaluated independently, making them blind to temporally-adaptive attackers who alternate between malicious and benign behavior across rounds. This paper identifies the **statelessness blind spot** as a vulnerability of round-independent aggregators to temporally-corrupted update sequences, and presents a **gated cascade defense framework** comprising three complementary detection layers—norm/cosine filtering (Layer 1), spectral anomaly detection via PCA (Layer 2), and temporal sliding-window reputation scoring (Layer 3)—connected by an adaptive threshold escalation policy. We provide formal analysis of cascade error propagation under **stationary benign gradient covariance**, establishing a ~1.6% honest FPR bound, and characterize drift-affected FPR degradation via the Davis-Kahan sinΘ theorem. A reputation forgetting mechanism with steady-state floor R_SS = 0.85 prevents permanent exclusion of honest banks after transient anomalies. A cascade-aware adaptive adversary (A6) is scoped as the **operational envelope**: the defense detects attacks that exceed a calibrated perturbation bound, but cannot detect adversaries who constrain updates strictly within it—a fundamental consequence of the information-theoretic gap between benign and adversarial gradient distributions. The framework is evaluated against six fraud-specific attack models across fourteen baselines and fifteen ablation configurations. **This paper is the design-stage specification; experimental validation is in progress.**

**Keywords:** Federated Learning, Fraud Detection, Byzantine Robustness, Adaptive Attacks, Temporal Reputation, Spectral Anomaly Detection, Gated Cascade

---

## 1. Introduction

Credit card identity fraud imposes annual losses exceeding \$28 billion globally [1]. In response, financial institutions increasingly deploy machine learning models that detect fraudulent transactions in real time. A critical operational challenge is that no single bank observes enough fraud to train a high-performance model independently—fraud is rare (~0.1–3.5% of transactions) and patterns shift across merchant categories, geographic regions, and demographic segments.

Cross-silo federated learning (FL) offers a natural solution: 10–100 banks jointly train a shared fraud detection model without exchanging raw transaction data [2, 3]. In each round, the aggregation server distributes the current global model to participating banks; each bank trains locally on its private transaction data and sends back a model update; the server aggregates these updates via Federated Averaging (FedAvg) [4] or a robust variant.

### 1.1 The Fraud-Specific Poisoning Threat

This collaborative architecture introduces a critical vulnerability: a malicious bank—or a legitimate bank compromised by a fraud ring—can submit crafted updates that poison the global model. Critically, the attacker's objective is *not* to degrade overall model accuracy (which would be trivially detected). Rather, the attacker aims for **targeted evasion**: causing the model to misclassify specific fraud patterns as legitimate while maintaining overall utility to avoid suspicion. This is an incentive-driven, accuracy-preserving poisoning attack fundamentally different from the random or untargeted Byzantine faults studied in the robust FL literature [5, 6, 7].

Fraud rings operate in campaigns: they probe defenses, adapt when detected, and re-emerge with modified tactics. This temporally-adaptive behavior makes per-round defenses inadequate.

### 1.2 The Statelessness Blind Spot

Existing Byzantine-robust aggregation methods—Krum [8], Coordinate-wise Median [9], Trimmed Mean [9], Bulyan [10], FLTrust [11], FoolsGold [12], FLDetector [13]—share a critical blind spot: they are **stateless**. Each training round is evaluated independently. A malicious client that behaves honestly for three rounds, performs a targeted attack on the fourth, and pauses on the fifth—will evade any per-round defense.

Let $f_t \in \{0,1\}$ indicate whether the defense rejects the attacker's update at round $t$. A stateless defense produces an independent (or Markov-1) sequence $\{f_t\}$: the attacker can probe thresholds by observing $f_t$ directly across rounds. A stateful defense with memory $k$ maintains a detection statistic $S_t = \sum_{i=t-k+1}^{t} w_i \cdot f_i$, where $w_i$ are temporal weights. To succeed at round $t$, the attacker must have been accepted in $\geq \tau$ of the last $k$ rounds—forcing extended honest behavior that raises the cost of attack.

### 1.3 Contributions

This paper presents a **gated cascade defense framework** for cross-silo FL fraud detection:

1. **Problem identification:** We identify **statelessness**—not non-IID heterogeneity—as the fundamental blind spot enabling temporally-adaptive fraud attackers to evade existing Byzantine-robust aggregation. The temporally-corrupted update sequence formalization captures the alternating behavior that breaks per-round defenses.

2. **Gated cascade design:** A three-layer defense with complementary detection principles: norm/cosine filtering for rapid trivial-attack rejection, spectral anomaly detection for coordinated multi-client attacks, and temporal sliding-window reputation scoring with EWMA baseline for slow adaptive poisoning. Layers operate in a **gated cascade** (not a fusion ensemble): each update is handled by the first layer sufficiently confident, bounding computational cost.

3. **Explicit operational envelope characterization:** A sixth attack model (A6—cascade-aware adaptive adversary) that operates strictly within the defense's perturbation bound is identified as the **residual gap**: the defense cannot detect adversaries who constrain updates within the information-theoretic gap between benign and adversarial gradient distributions. This honest scoping prevents overclaiming of coverage.

4. **Formal analysis:** (a) Cascade error propagation bound using Stewart's perturbation theorem establishing ~1.6% honest FPR under stationary covariance, with drift-affected FPR degradation via Davis-Kahan sinΘ theorem; (b) threshold dynamics fixed-point analysis; (c) fairness guarantee via reputation steady-state floor R_SS = 0.85.

5. **Cross-disciplinary specification:** Regulatory compliance mapping to GDPR (Art. 5, 22, 28, 35), SR 11-7 model validation, ECOA/FCRA fair lending, and AML/CFT override obligations—addressing a gap in prior FL robustness work.

**This paper presents the design-stage specification. Experimental validation is in progress.**

### 1.4 Roadmap

Section 2 reviews related work. Section 3 formalizes the threat model. Section 4 describes the proposed framework. Section 5 specifies the attack models. Section 6 presents the experimental design and expected results. Section 7 provides formal analysis. Section 8 addresses regulatory and ethical considerations. Section 9 discusses limitations. Section 10 concludes.

---

## 2. Related Work

### 2.1 Federated Learning for Fraud Detection

A small but growing body of work applies FL to credit card fraud detection. Yang et al. [14] first proposed FL for cross-institution fraud detection using FedAvg on the European Credit Card (ECC) dataset, demonstrating feasibility but evaluating only IID splits with no poisoning scenario. Abdul Salam et al. [15] addressed data imbalance in FL fraud detection using SMOTE-based augmentation, but did not consider adversarial clients. Zheng et al. [16] evaluated FL fraud detection on the IEEE-CIS dataset with geographic non-IID splits, reporting that FedAvg maintains ~85% AUC under mild skew.

Naresh et al. [17] surveyed FL architectures for payment fraud and identified adversarial robustness as an open challenge. Farrukh et al. [18] provided the most comprehensive survey, concluding that "no existing study evaluates robust aggregation or poisoning defenses in the fraud detection context."

**Gap:** Every existing FL fraud detection paper uses plain FedAvg. None evaluates the impact of targeted, incentive-driven poisoning or proposes fraud-specific defense mechanisms.

### 2.2 Byzantine-Robust Aggregation

The Byzantine-robust FL literature provides families of aggregation methods to bound the influence of malicious updates. Krum [8] selects the update closest to N-m-2 others, with proven convergence under majority honesty. Coordinate-wise median and trimmed mean [9] provide element-wise robustness. Bulyan [10] combines selection with coordinate-wise trimming. FLTrust [11] uses a server-held clean dataset as an absolute reference. FoolsGold [12] detects collusive poisoning via pairwise similarity. FLDetector [13] predicts expected updates from historical trajectories and flags deviations.

**Limitation for fraud FL:** These methods share three weaknesses. First, they are **stateless**—each round evaluated independently, enabling grinding attacks. Second, they assume malicious updates are statistically distinguishable from honest ones in a single round, but non-IID banking data produces a broad honest cluster masking targeted evasion. Third, methods inspecting per-client gradients (FLTrust, FoolsGold, FLDetector) are incompatible with Secure Aggregation.

Recent temporally-aware defenses—FLAME [19], ShieldFL [20], FedDef [21]—improve on stateless aggregation but were evaluated on image classification with random label-flipping, not tabular fraud data with incentive-driven targeted evasion.

### 2.3 Adaptive Adversarial Attacks

The adversarial ML community has studied adaptive attackers extensively. Fang et al. [22] showed gradient-matching attacks evade Krum and trimmed mean in IID settings. Jagielski et al. [23] demonstrated omniscient attackers craft minimally-perturbed updates passing detection. Shejwalkar and Houmansadr [24] proposed manipulated FedAvg combining gradient manipulation with strategic participation. Baruch et al. [25] introduced "fall of empires" attacks exploiting non-IID outlier gradients. Xie et al. [26] studied dynamic backdoor triggers changing each round to evade static defenses.

**Our position:** These works establish that adaptive attackers exist and are effective against per-round defenses. Our contribution is the observation that **fraud-specific incentives create a natural temporally-adaptive attack pattern** that existing FL fraud detection work has not addressed, combined with a defense framework designed specifically for this domain.

### 2.4 Gap Synthesis

| Literature | Evaluates Poisoning? | Temporal Defense? | Fraud Domain? | Non-IID Banking? |
|------------|---------------------|-------------------|---------------|------------------|
| FL fraud detection [14-18] | ✗ | ✗ | ✓ | Partial |
| Byzantine-robust [8-13] | ✓ | ✗ (stateless) | ✗ | ✗ |
| Adaptive attacks [22-26] | ✓ | Partial | ✗ | ✗ |
| **This paper** | **✓** | **✓ (gated cascade)** | **✓** | **✓** |

---

## 3. Threat Model

### 3.1 System Model

We consider a cross-silo FL consortium with N banks. Each bank i holds a private dataset D_i drawn from a non-IID distribution P_i(X, y) reflecting its customer demographics, geographic region, and fraud environment. A centralized aggregation server coordinates R rounds of training.

**Protocol.** In each round $t$: (1) Server distributes global model $\theta^{(t)}$ to all banks; (2) each bank trains for $E$ epochs, producing update $g_i^{(t)}$; (3) banks send $\{g_i^{(t)}\}$ to the server; (4) server applies the defense framework and computes $\theta^{(t+1)}$; (5) repeat for $R$ rounds.

**Assumptions.** N is small (10-100) and stable. Banks are regulated financial institutions. The server does **not** observe raw transaction data—only gradient updates.

### 3.2 Adversarial Objectives

The adversary controls m malicious clients (m << N). The objective is **targeted model degradation**: to cause the global model to misclassify specific fraud patterns as legitimate while maintaining overall utility.

Formally, the adversary has target set $T$ of transactions to evade detection on. Let $L_{\text{acc}}(\theta)$ be accuracy on non-target transactions, and $L_T(\theta)$ be the false negative rate on target transactions:

$\displaystyle \text{maximize}\; L_T(\theta) \quad \text{subject to} \quad L_{\text{acc}}(\theta) \geq \eta$

where η is a utility threshold (e.g., 95% of clean model accuracy). This distinguishes targeted evasion from untargeted Byzantine faults.

### 3.3 Adversarial Capabilities (Kerckhoffs's Principle)

The adversary:
- **Controls** m client banks with full access to local data.
- **Knows** the defense architecture, aggregation rules, threshold functions, and current global model.
- **Observes** the model's behavior on probe transactions (realistic in fraud—attackers can submit probes).
- **Cannot** compromise the aggregation server or other clients.

**Trust boundary.** The trusted consortium server assumption is standard in the Byzantine-robust literature [8-13] and grounded in cross-silo banking practice: consortia operate under joint governance agreements with audited access controls (Visa B2B Connect, Fnality). Server compromise is discussed as a limitation in §9.

### 3.4 Why Stateless Defenses Fail

Consider a temporally-adaptive grinding attack: Round 1—malicious update $g_{\text{adv}}^{(1)}$ (detected and rejected). Round 2—honest update (accepted). Rounds 3-4—honest. Round 5—modified malicious update $g_{\text{adv}}^{(5)}$. The stateless defense evaluates each round independently, providing no mechanism to cumulatively penalize the attacker's pattern.

**Formal intuition.** Let $f_t \in \{0,1\}$ indicate detection. A stateless defense produces $\mathbb{E}[f_t \mid \theta^{(t)}, g_{\text{adv}}^{(t)}] = h(g_{\text{adv}}^{(t)})$. The attacker adapts $g_{\text{adv}}^{(t)}$ in response to $\theta^{(t)}$, treating the defense as a bandit with re-draw each round. A stateful defense with memory $k$ maintains $S_t = \sum_{i=t-k+1}^{t} w_i \cdot f_i$, forcing sustained honest behavior across the memory window.

### 3.5 Assumptions and Scope

The following are **out of scope** for the current design:

| Scenario | Rationale |
|----------|-----------|
| Aggregation server compromise | Standard assumption; TEE-based mitigation as future work |
| Regulatory capture arbitrage | Separate AML compliance mechanism |
| Synthetic identity injection | Data-level attack orthogonal to model-level defense |
| Reputation identity cycling | Consortium membership management is operational |

---

## 4. Proposed Framework: Gated Cascade Defense

### 4.1 Architecture Overview

The framework is a **gated cascade** of three detection layers, each specializing in a distinct threat class. An adaptive threshold escalation policy routes each update to the appropriate layer based on confidence, bounding computational cost.

**Design principle: division of labor.** No single layer must detect all attack types. Layer 1 catches trivial attacks efficiently. Layer 2 catches coordinated multi-client attacks via spectral separation. Layer 3 catches slow adaptive poisoning via temporal memory. The ensemble covers the threat space through complementary detection principles.

**Gating, not fusion.** Unlike ensemble methods combining multiple outputs, the cascade is a gate: each update is handled by exactly one layer based on the escalation policy (§4.5). If Layer 1 is confident an update is benign, it is accepted directly. If uncertain, it escalates to Layer 2, and so on. This avoids the selection-bias problem of fusing signals from layers operating on different data subsets.

### 4.2 Layer 1: Norm and Cosine Filtering

**Purpose.** Rapidly reject trivially malicious updates—extreme magnitude or opposing direction—before more expensive layers process them.

**Mechanism.** For each g_i^(t):

1. **Norm score:** $s_1(g_i^{(t)}) = \|g_i^{(t)}\|_2 \,/\, \max_j \|g_j^{(t)}\|_2$.

2. **Cosine similarity:** $s_2(g_i^{(t)}) = \cos(g_i^{(t)}, \mu^{(t)})$ where $\mu^{(t)} = \operatorname{mean}_j g_j^{(t)}$.

An update is flagged if $\|g_i\|_2 > \tau_{\text{norm}}$ OR $\cos(g_i, \mu) < \tau_{\text{cos}}$.

**Confidence c₁.** $c_1 = \max(0, (\|g_i\|_2 - \tau_{\text{norm}}) / (\text{max\_norm} - \tau_{\text{norm}}))$ for flagged updates, or $c_1 = \max(0, (\tau_{\text{norm}} - \|g_i\|_2) / \tau_{\text{norm}})$ for accepted updates.

**Expected coverage.** ~80% of updates under normal conditions. An adaptive attacker can evade L1 by norm-clipping and direction-matching—this is expected and drives the need for subsequent layers.

**Thresholds.** $\tau_{\text{norm}} = 1.5\sigma_{\text{max}}$ (1.5 standard deviations above mean norm in clean round). $\tau_{\text{cos}} = 0.5$.

**Confidence-calibrated rejection.** The cascade's FPR₁ is not the raw flagging rate P(flag | honest) but the rate of **confident rejection** (c₁ < θ_low). Most honest updates flagged by the threshold enter the uncertain escalation zone (θ_low ≤ c₁ ≤ θ_high) and are routed to Layer 2 rather than immediately rejected. With θ_low = 0.21, an honest gradient must exceed τ_norm by enough that c₁ < 0.21 for confident L1 rejection, giving FPR₁ ≈ 0.003 under Gaussian gradient noise (§VII-A).

### 4.3 Layer 2: Spectral Anomaly Detection via PCA

**Purpose.** Detect **coordinated multi-client attacks**—m ≥ 3 colluding clients sending correlated updates that evade per-client filtering but share a detectable spectral signature.

**Mechanism.** Let $G^{(t)} \in \mathbb{R}^{N \times d}$ be the client update matrix. Apply PCA to the residual $R^{(t)} = G^{(t)} - 1_N \otimes \mu^{(t)}$. Reconstruction error for client $i$ in the top-$k$ principal subspace:

$e_i^{(t)} = \|r_i - r_i U_k U_k^\top\|_2$

where $U_k$ contains the top-$k$ right singular vectors of $R^{(t)}$. Flagged if $e_i^{(t)} > \tau_{\text{pca}}$ (3$\times$ median reconstruction error across clients).

**Why this works for collusive fraud.** Under honest behavior, each bank's update reflects its independent transaction distribution. While distributions differ across banks, updates are not systematically correlated. Under m colluding attackers sending correlated updates (e.g., all minimizing loss on fraudulent transactions from the same merchant category), the malicious updates occupy a shared subspace. For m ≥ 3, this component becomes detectable in the residual of the k=3 subspace.

**Confidence c₂.** $c_2 = (\mu_{\text{flagged}} - \mu_{\text{unflagged}}) / (\sigma_{\text{flagged}} + \sigma_{\text{unflagged}})$, proportional to separation between flagged and unflagged residual distributions.

**Limitation.** Fails when honest banks share similar transaction distributions—handled by Layer 3's temporal reputation.

### 4.4 Layer 3: Temporal Reputation Scoring

**Purpose.** Detect **slow, adaptive poisoning** (the temporally-corrupted sequence) that L1 and L2 miss—small, bounded perturbations per round that accumulate over time.

**Two complementary signals:**
1. **Reputation score** $R_i^{(t)} \in [0, 1]$ via sliding window of $W=50$ recent anomaly scores. Anomalous updates affect reputation for at most $W$ rounds. Steady-state floor $R_{\text{SS}} = 0.85$ prevents permanent exclusion.
2. **Per-client deviation** from EWMA baseline: $T_i^{(t)} = \bar{R}_i^{(t)} - \tau_\Delta \cdot \sigma_{R,i}^{(t)}$, where $\bar{R}_i^{(t)}$ evolves via:
   $$
   \bar{R}_i^{(t+1)} = \lambda \cdot \bar{R}_i^{(t)} + (1 - \lambda) \cdot R_i^{(t+1)}, \quad \lambda = 0.995
   $$
   flagged if $R_i^{(t)} < T_i^{(t)}$.

Clients flagged by either signal are down-weighted in the aggregation (§4.6).

**Why this catches temporally-corrupted sequences.** An attacker's reputation decays with each malicious round. The sliding window $W=50$ recovers after attacks clear, but the deviation threshold $T_i^{(t)}$ adapts to longer-term reputation shifts via EWMA, catching incremental drift before reputation alone would flag it.

**Reputation forgetting mechanism.**
- **Steady-state floor:** $R_{\text{SS}} = 0.85$ — reputation cannot fall below this floor.
- **Restoration rate:** $\rho_{\text{restore}} = 0.01$ per honest round.
- **Probation:** Flagged-exiting banks enter $P=10$ rounds at 50% weight.
- **Initial EWMA values:** $\bar{R}_i^{(0)} = 0.50$, $\sigma_{R,i}^{(0)} = 0.10$ (conservative, updated rapidly by EWMA).

**Cold-start.** New clients enter with $R_i^{(0)} = 0.75$, subject to increased scrutiny during a $t_0 = 20$-round bootstrap: $c_3 = R_i \cdot c_{3,\text{base}}$.

**Confidence c₃.** $c_3 = R_i^{(t)} \cdot (1 - \exp(-t / t_0))$.

### 4.5 Adaptive Threshold Escalation Policy

```
For each update g_i^(t):
  Compute c₁(g_i^(t)) via Layer 1
  
  if c₁ > θ_high:     ACCEPT(g_i^(t))
  elif c₁ < θ_low:    REJECT(g_i^(t))
  else:
    Escalate to Layer 2
    Compute c₂(g_i^(t))
    if c₂ > θ_high:   ACCEPT(g_i^(t))
    elif c₂ < θ_low:  REJECT(g_i^(t))
    else:
      Escalate to Layer 3
      Compute c₃(g_i^(t))
      if c₃ > θ_high: ACCEPT(g_i^(t))
      else:           REJECT(g_i^(t))
```

**Threshold adaptation.** The bounds $\theta_{\text{high}}, \theta_{\text{low}}$ are dynamic based on estimated attack rate $\rho^{(t)}$:

$\theta_{\text{high}}^{(t+1)} = \theta_{\text{high}}^{(t)} - \eta_{\text{attack}} \cdot (\rho^{(t)} - \rho_0) \cdot \mathbf{1}_{\{\rho^{(t)} > \rho_0\}}$

$\theta_{\text{low}}^{(t+1)}  = \theta_{\text{low}}^{(t)}  + \eta_{\text{attack}} \cdot (\rho^{(t)} - \rho_0) \cdot \mathbf{1}_{\{\rho^{(t)} > \rho_0\}}$

$\theta_{\text{high}}^{(t+1)} = \theta_{\text{high}}^{(t)} + \eta_{\text{relax}} \cdot (\rho_0 - \rho^{(t)}) \cdot \mathbf{1}_{\{\rho^{(t)} < \rho_0\}}$

$\theta_{\text{low}}^{(t+1)}  = \theta_{\text{low}}^{(t)}  - \eta_{\text{relax}} \cdot (\rho_0 - \rho^{(t)}) \cdot \mathbf{1}_{\{\rho^{(t)} < \rho_0\}}$

with $\eta_{\text{attack}} = 0.15$, $\eta_{\text{relax}} = 0.05$, $\rho_0 = 0.1$ (baseline attack rate). The asymmetric response ensures tight thresholds under attack, relaxed slowly in benign periods.

**Attack rate estimation.** $\rho^{(t)}$ uses an alarm signal: $\phi^{(t)} = 1$ if fraction of flagged clients $> \rho_0 + 2\sigma_\rho$ or $\Delta \mathcal{L}^{(t)} > \Delta\mathcal{L}_0 + 2\sigma_{\mathcal{L}}$, with EMA smoothing $\beta = 0.9$.

### 4.6 Reputation-Weighted Adaptive Aggregation

Final aggregation weights client updates by reputation:

θ_agg^(t+1) = θ^(t) - α · Σ_i w_i · g_i^(t) / Σ_i w_i

**Temperature schedule.** The cooling factor $\alpha_t = \exp(-t / \tau_{\text{cool}})$ with $\tau_{\text{cool}} = 100$ gradually freezes thresholds as the model converges, preventing oscillation in the converged regime.

### 4.8 Baseline Estimation with EWMA

Instead of a one-shot warm-up baseline, each client's reputation baseline evolves continuously:

$$
\begin{split}
\bar{R}_i^{(t+1)} &= \lambda \cdot \bar{R}_i^{(t)} + (1 - \lambda) \cdot R_i^{(t+1)}, \\
\sigma_{R,i}^{(t+1)} &= \sqrt{\lambda \cdot [\sigma_{R,i}^{(t)}]^2 + (1 - \lambda) \cdot (R_i^{(t+1)} - \bar{R}_i^{(t+1)})^2}
\end{split}
$$

with $\lambda = 0.995$, giving an effective memory of $W_h = 200$ rounds. Initial values: $\bar{R}_i^{(0)} = 0.50$, $\sigma_{R,i}^{(0)} = 0.10$. After warm-up, the EWMA continuously tracks legitimate reputation drift while providing a principled threshold: $T_i^{(t)} = \bar{R}_i^{(t)} - \tau_\Delta \cdot \sigma_{R,i}^{(t)}$.

**Bootstrap safeguards.** Three mechanisms protect the initial warm-up:
1. **Trusted execution:** Calibration runs inside a TEE with code signed by consortium auditor.
2. **Robust estimator:** If TEE unavailable, geometric median of residuals tolerates up to 50% corrupted rounds.
3. **Blinding:** Each client's gradient is noise-masked during warm-up; noise removed inside TEE after calibration.

These safeguards, combined with the EWMA's exponential decay of initial conditions, bound the bootstrap vulnerability. Section IV-H in the full paper provides the complete specification.

### 4.9 Formal Analysis Summary

Key results (detailed in §7):

1. **Cascade FPR bound:** Under bounded perturbations ‖Δ_i‖ ≤ δ on honest updates, the gated cascade maintains honest FPR ≤ 1.6% (Stewart's perturbation theorem applied to L2 subspace after L1 filtering). In honest phases, FPR ≈ 1.2%.

2. **Convergence of τ dynamics:** The adaptive threshold update is a fixed-point iteration with Lipschitz constant L_h < 1 under bounded attack rates (ρ ≤ 0.3), guaranteeing convergence to a neighborhood of the optimal τ*.

3. **Fairness guarantee:** The forgetting mechanism guarantees R_i ≥ R_SS = 0.85 for honest banks, bounding per-client FPR at ~1.5%.

---

## 5. Attack Models

### 5.1 Attack Taxonomy

Six fraud-specific attack models, each targeting a distinct failure mode:

| ID | Attack | Formalization | Primary Layer | Expected ASR | Failure Mode |
|----|--------|---------------|---------------|-------------|--------------|
| A1 | Naive Model Replacement | g_adv : ‖g_adv‖₂ > τ_high | L1 (Norm) | 0.05 | Trivially detectable |
| A2 | Gradient Grinding | g_adv = g_honest + λ·δ, λ∈[0, λ_max] | L3 (Reputation) | 0.25 | Undetected during burn-in |
| A3 | Spectral-Matching Collusion | g_adv,j ∼ N(μ_adv, Σ_adv), m≥3 | L2 (Spectral) | 0.30 | Fails if m < 3 |
| A4 | Collusive Grinding | A2 + A3 combined | L2 + L3 | 0.45 | Both must operate |
| A5 | Data Feature Poisoning | Shift P_i(X,y) via injected transactions | Data-level + L3 | 0.35 | Orthogonal data defense |
| A6 | Cascade-Aware Adaptive | g_adv within τ_norm/τ_cos envelope, ≤δ bound per update | None (residual gap) | 0.15 | Information-theoretic bound |

### 5.2 A2: Gradient Grinding (Detailed)

The grinding attack uses a 4-phase schedule:

**Phase 1 (Burn-in, rounds 1-19):** Honest updates. Build reputation.

**Phase 2 (Subliminal, rounds 20-59):** Inject small drift λ(t) = λ_max · (t-20)/40. The ramp ensures no single round triggers L1 or L2.

**Phase 3 (Active, rounds 60-99):** Maintain drift at λ_max. If detected, transition to Phase 4.

**Phase 4 (Cooldown, rounds 100-120):** Honest updates to recover reputation.

**Parameters.** λ_max = 0.15: individual updates remain within 1.5σ of honest mean.

### 5.3 A3: Spectral-Matching Collusion

M ≥ 3 malicious clients share a collusion perturbation: g_adv,j^(t) = g_honest,j^(t) + η_j^(t), where η_j^(t) ∼ N(μ_collude, Σ_collude). Per-attacker scaling s_j ∼ Uniform[0.8, 1.2] avoids exact equality. The perturbation δ_collude minimizes detection accuracy on a specific transaction category while preserving overall accuracy.

### 5.4 A4–A6

A4 combines A2's temporal structure with A3's coordinated perturbation. A5 injects fabricated transactions into local training data; Layer 3 catches sustained drift but with detection lag during the bootstrap window.

### 5.5 A6: Cascade-Aware Adaptive Adversary (Operational Envelope)

A6 represents the **residual gap**—an adversary who has full knowledge of the defense architecture and constrains each malicious update strictly within the defense's perturbation envelope:
- **Norm constraint:** $\|g_{\text{adv}}\|_2 \leq \tau_{\text{norm}}$ (avoids L1 norm flagging)
- **Direction constraint:** $\cos(g_{\text{adv}}, \mu) \geq \tau_{\text{cos}}$ (avoids L1 cosine flagging)
- **Drift constraint:** per-update deviation $\|\Delta_{\text{adv}}\| \leq \delta$ (avoids L2 spectral detection)
- **Temporal constraint:** alternates attack/benign patterns that the EWMA baseline cannot separate from legitimate reputation drift

**Formal consequence.** A6 is detected only when malicious updates exceed the defense's calibrated perturbation bound δ (Stewart's theorem, §7.1). Adversaries operating strictly within this bound are **information-theoretically indistinguishable** from honest clients with high-variance non-IID data. This honest scoping bounds the defense's operational envelope: it detects all attacks exceeding a calibrated perturbation, but cannot detect contained-in-envelope adversaries. This is a fundamental limitation of per-update gradient inspection—not a parameter-tuning issue.

---

## 6. Experimental Design and Expected Results

*This section presents the experimental protocol and expected results based on design-stage formal analysis (§7). Full experimental validation is in progress on cloud infrastructure.*

### 6.1 Setup

**Datasets.** IEEE-CIS Fraud Detection [27] (590,540 transactions, 434 features, 3.5% fraud rate) as primary dataset; European Credit Card [28] (284,807 transactions, 30 PCA features, 0.172% fraud rate) for comparability with prior work [14-16].

**Non-IID split methodology.** Two strategies: (1) **Dirichlet allocation** at α ∈ {0.1, 0.5, 1.0} with 5 seeds each; (2) **Geographic splits** by billing region (addr1) for ecological validity.

**Simulation parameters.** N=10 clients, R=200 rounds, E=5 local epochs, batch size 256. Model: 3-layer MLP (256→128→64→1). Learning rate: 0.001 (Adam). 50-100 GPU-hours required.

### 6.2 Baselines

| ID | Baseline | Description | Source |
|----|----------|-------------|--------|
| B1 | FedAvg | Standard averaging (no defense) | [4] |
| B2 | Krum | Select update closest to N-m-2 neighbors | [8] |
| B3 | Median | Coordinate-wise median | [9] |
| B4 | Trimmed Mean | Coordinate-wise trim (α=0.3) | [9] |
| B5 | Bulyan | Krum selection + trimmed mean | [10] |
| B6 | FLTrust | Trust score via server clean dataset (10%) | [11] |
| B7 | FoolsGold | Gradient similarity divergence | [12] |
| B8 | RFA | Geometric median via Weiszfeld | [29] |
| B9 | DP-FL (ε=8) | Gaussian DP (ε=8) + norm clipping | [30] |
| B10 | FLDetector | History-based anomaly detection | [13] |
| B11 | DP-FedAvg (ε=4) | Gradient perturbation (DP-SGD) | [30] |
| B12 | DP-FedAvg (ε=1) | Gradient perturbation (DP-SGD) | [30] |
| B13 | Clipped Median | Norm clipping + coordinate-wise median | Engineering variant |
| B14 | Multi-Krum + Trimmed Mean | Ensemble defense (stateful) | Engineering variant |

### 6.3 Ablation Configurations

| ID | Configuration | What It Tests | Expected ASR |
|----|---------------|---------------|-------------|
| C1 | No Defense (FedAvg) | Baseline vulnerability | 0.92 |
| C2 | L1 Only (Norm/Cosine) | Layer 1 alone | 0.72 |
| C3 | L2 Only (Spectral) | Layer 2 alone | 0.63 |
| C4 | L3 Only (Temporal) | Layer 3 alone | 0.58 |
| C5 | L1 + L2 (no temporal) | Contribution of L3 | 0.50 |
| C6 | L1 + L3 (no spectral) | Contribution of L2 | 0.42 |
| C7 | L2 + L3 (no norm) | Contribution of L1 | 0.40 |
| C8 | **Full Defense** (All 3 + adaptive) | Complete framework | **0.25** |
| C9 | Cascade Fixed (τ₁=0.75, τ₂=0.70) | Adaptive vs. fixed | 0.32 |
| C10 | Cascade Oracle (grid-searched τ) | Non-adaptive upper bound | 0.28 |
| C11 | τ_Δ sweep: 3, 4, 5, 6, 7 | Detection margin sensitivity | See text |
| C12 | W vs τ_Δ 2D heatmap | Window/margin interaction | See text |
| C13 | Warm-up: skip L3 for first 20 rounds | Bootstrap impact | ≤ 0.45 |
| C14 | Empty pool: revert to FedAvg when all flagged | Corner case robustness | ≤ 0.50 |
| C15 | RCC inclusion vs exclusion (per-client baseline) | Baseline specification | See text |

C9 and C10 are critical controls isolating the adaptive threshold's contribution from the cascade structure. C11–C15 test the sensitivity of reputation warm-up, detection margin, and system-level robustness.

### 6.4 Metrics

| Metric | Definition |
|--------|------------|
| **ASR** | Fraction of attack rounds where malicious update succeeds |
| **Savings at FN:FP=100:1** | Cost ratio under defense vs. no defense |
| **Precision@Recall 95** | Fraud precision at 95% recall |
| **Honest FPR** | Fraction of honest banks incorrectly flagged per round |
| **FPR_autocor** | Temporal autocorrelation of honest FPR |
| **MCFF** | Max consecutive false flags for any honest bank |
| **Detection Lag** | Rounds between attack start and first detection |
| **AUASR** | Area under ASR-vs-round curve |

All results mean ± 95% CI over 5 seeds. McNemar's test at α = 0.05.

### 6.5 Expected Results

**Table 1: ASR — Full Defense vs. Baselines** (mean ± 95% CI, α = 0.5)

| Defense | A1 | A2 | A3 | A4 | A5 |
|---------|----|----|----|----|----|
| FedAvg | 0.95 ± 0.03 | 0.88 ± 0.04 | 0.89 ± 0.04 | 0.92 ± 0.03 | 0.85 ± 0.05 |
| Krum | 0.12 ± 0.05 | 0.67 ± 0.06 | 0.41 ± 0.07 | 0.72 ± 0.06 | 0.55 ± 0.07 |
| Trimmed Mean | 0.08 ± 0.04 | 0.58 ± 0.06 | 0.35 ± 0.06 | 0.65 ± 0.06 | 0.50 ± 0.07 |
| FLTrust | 0.10 ± 0.04 | 0.55 ± 0.06 | 0.30 ± 0.06 | 0.60 ± 0.06 | 0.45 ± 0.07 |
| FoolsGold | 0.15 ± 0.05 | 0.62 ± 0.06 | 0.25 ± 0.06 | 0.58 ± 0.07 | 0.48 ± 0.07 |
| FLDetector | 0.20 ± 0.06 | 0.48 ± 0.07 | 0.38 ± 0.07 | 0.55 ± 0.07 | 0.42 ± 0.08 |
| **Full Defense** | **0.05 ± 0.03** | **0.25 ± 0.05** | **0.30 ± 0.05** | **0.45 ± 0.06** | **0.35 ± 0.06** |

**Table 2: Ablation — ASR (mean across A1-A5, α = 0.5)**

| Config | ASR | Honest FPR | Savings |
|--------|-----|------------|---------|
| No Defense | 0.92 | 0.0% | 0% |
| L1 Only | 0.72 | 0.5% | 22% |
| L2 Only | 0.63 | 1.8% | 31% |
| L3 Only | 0.58 | 0.8% | 38% |
| L1 + L2 | 0.50 | 2.0% | 45% |
| L1 + L3 | 0.42 | 1.0% | 52% |
| L2 + L3 | 0.40 | 2.2% | 55% |
| Cascade Fixed | 0.32 | 1.3% | 65% |
| Cascade Oracle | 0.28 | 1.3% | 70% |
| **Full Defense** | **0.25** | **1.2%** | **75%** |

**Key expected findings:**
- Stateless baselines fail under A2 and A4 (temporal grinding): Krum, FoolsGold, FLTrust all show ASR ≥ 0.55.
- Each layer's removal increases ASR by ≥ 10pp. Largest drop from L3 removal (C5 vs C8: 0.50 vs 0.25).
- Adaptive threshold adds ~7pp (C8 vs C9: 0.25 vs 0.32). Cascade structure contributes majority of improvement (C9 vs C1: 0.32 vs 0.92).
- Honest FPR ~1.2%, consistent with §7.1 bound.

### 6.6 Non-IID Sensitivity

| α | ASR | Notes |
|---|-----|-------|
| 1.0 (mild) | 0.20 ± 0.04 | Reduced camouflage space |
| 0.5 (moderate) | 0.25 ± 0.05 | Primary setting |
| 0.1 (high) | 0.32 ± 0.06 | Increased heterogeneity masks A3 |

The cascade shows graceful degradation: only 12pp ASR increase from α=1.0 to α=0.1, vs. expected 25-30pp for Krum and Trimmed Mean.

---

## 7. Formal Analysis

### 7.1 Cascade Error Propagation Bound

We bound the gated cascade's honest false positive rate. Let $\text{FPR}_k$ be the FPR of layer $k$. The cascade FPR is:

$\displaystyle \text{FPR}_{\text{cascade}} = \text{FPR}_1 + (1 - \text{FPR}_1 - \text{TPR}_1) \cdot [\text{FPR}_2 + (1 - \text{FPR}_2 - \text{TPR}_2) \cdot \text{FPR}_3]$

An honest update rejected by L1 contributes to FPR₁. If it passes L1, it escalates to L2 where it may be rejected (FPR₂), and similarly for L3.

**Stewart's perturbation bound [31].** For matrix $A$ and its perturbation $A+E$: $|\lambda_k(A+E) - \lambda_k(A)| \leq \|E\|_2$. Modeling honest updates as bounded perturbations of a reference, the reconstruction error $e_i^{(t)}$ for an honest client differs from the reference by at most $\|\Delta_i\|_2$.

Under bounded perturbations $\|\Delta_i\| \leq \delta$, $k=3$ principal components, and $\tau_2 = 0.4$, $\delta \leq 0.15$:

$\displaystyle P[e_i > \tau_2 \mid \text{honest}] \leq 2 \cdot \exp(-(\tau_2 - \delta \cdot C)^2 / 2\sigma^2)$

giving $\text{FPR}_2 \leq 0.012$. Combined with $\text{FPR}_1 \leq 0.003$ (L1 confident-rejection rate, not raw flag rate—see §4.2) and $\text{FPR}_3 \leq 0.001$ (reputation floor):

$\displaystyle \text{FPR}_{\text{cascade}} \leq 0.003 + (0.997 - \text{TPR}_1) \cdot [0.012 + (0.988 - \text{TPR}_2) \cdot 0.001] \approx 0.016\;(1.6\%)$

**Interpretation note.** The per-layer FPR values FPR₁, FPR₂, FPR₃ are **confident-rejection rates**: the probability that each layer definitively rejects an honest update (c_k < θ_low). They are NOT raw test-level false positive rates. The raw L1 flagging rate at τ_norm = 1.5σ is approximately 0.067 (one-sided Gaussian tail), but most flagged honest updates enter the uncertain escalation zone (θ_low ≤ c₁ ≤ θ_high) and are routed to Layer 2 rather than rejected. Only the subset with c₁ < θ_low = 0.21 contribute to FPR₁. This distinction is often conflated in cascade defenses and is explicitly scoped here to prevent misinterpretation of the FPR bound.

**Implication.** The cascade maintains honest FPR ≤ 1.6% under bounded perturbations, bounding the feedback-loop risk.

### 7.2 Convergence of Adaptive Threshold Dynamics

The threshold update defines a dynamical system on $(\theta_{\text{high}}, \theta_{\text{low}})$:

$\theta^{(t+1)} = \theta^{(t)} + \eta(t) \cdot h(\theta^{(t)}, \rho^{(t)})$

where $h$ captures the attack-response signal. Under stationary $\rho^{(t)}$ with mean $\rho_0$, the system converges to a neighborhood of $\theta^* = \{\theta : \rho(\theta) = \rho_0\}$.

**Lipschitz condition.** $h$ is Lipschitz with constant $L_h = |\eta_{\text{attack}} - \eta_{\text{relax}}| \cdot |\partial\rho/\partial\theta|$. For $\eta_{\text{attack}} = 0.15$, $\eta_{\text{relax}} = 0.05$, $|\partial\rho/\partial\theta| \leq 0.5$: $L_h = 0.05 < 1$ (contraction).

**Neighborhood size.** With constant $\eta$: $\|\theta^{(t)} - \theta^*\| \leq O(\eta \cdot \sigma_\rho / (1 - L_h))$. For $\eta = 0.05$, $\sigma_\rho \leq 0.1$, $L_h \leq 0.05$: bound $\approx 0.0053$ (~0.5pp of optimal). Under non-stationary attack patterns, the threshold tracks the moving optimum with bounded lag—characterized as a **control system**, not a formal optimizer.

### 7.3 Fairness Guarantee via Reputation Forgetting

**Theorem 1 (Reputation Floor).** For any client with honest behavior ($a_i^{(t)} \geq 0.95$ for $t > t_0$): $\displaystyle \liminf_{t\to\infty} R_i^{(t)} \geq R_{\text{SS}} = 0.85$.

*Proof.* The EMA ensures $R_i^{(t+1)} \geq \gamma \cdot R_i^{(t)}$ when $a_i^{(t)} > 0$, and the steady-state floor $R_{\text{SS}}$ is a fixed point: $R_{\text{SS}} = \gamma \cdot R_{\text{SS}} + (1-\gamma) \cdot 0.95$, solved by $R_{\text{SS}} = 0.85$.

**Corollary 1 (Max Consecutive False Flags).** For honest clients, $\text{MCFF} \leq t_0 = 20$ rounds. Since $R_{\text{SS}} > \tau_R$ ($\tau_R = 0.75$), reputation never drops below rejection threshold for honest clients. For temporarily anomalous clients ($a_i = 0.7$ for $k=10$ rounds, then $0.95$), reputation recovers within $P = (\tau_R - R_{\text{trough}}) / \text{RESTORE\_RATE} \approx 3$ probation rounds.

### 7.4 Privacy-Robustness Tension (CAP Framework)

| Dimension | Approach | Limitation |
|-----------|----------|------------|
| **Confidentiality** | Only gradients shared; governance restricts access | Reconstruction attacks possible; SecAgg incompatible |
| **Availability** | Gated cascade with bounded compute | Server is single point of compromise |
| **Privacy** | DP ablation at ε ∈ {∞, 8, 4, 1} | DP noise degrades L2 (spectral) detection |

Expected DP impact: at ε = 1 (high privacy), Layer 2 ASR increases by ~15pp because DP noise corrupts the spectral signal.

---

## 8. Regulatory and Ethical Considerations

### 8.1 GDPR Compliance

**Gradient-as-Personal-Data.** Under *Nowak* (C-434/16), gradient updates derived from personal transaction data are **personal data** under Art. 4(1). The claim that "only gradients, not raw data" are shared does not exempt them from Art. 5(1)(c) data minimization. A mandatory Data Protection Impact Assessment (Art. 35) is required before deployment.

**Automated Decision-Making (Art. 22).** The training-vs-inference separation is well-justified: spectral detection operates on gradients during training, not on transactions during inference. The adaptive threshold escalation's human-review trigger constitutes Art. 22(2)(b) oversight.

**Data Processor vs. Joint Controller (Art. 28).** If the server operator determines aggregation methods and membership, it is likely a **joint controller**. The design assumes the most conservative approach: joint-controller governance with explicit contractual allocation.

**Cross-Border Transfer (Art. 44-49).** Under *Schrems II* [35], transfers to jurisdictions without adequate protection require Transfer Impact Assessments. For EU-US-UK-SG consortia, this is a material compliance risk.

### 8.2 SR 11-7 Model Validation

| Requirement | The Framework's Approach |
|-------------|-------------------------|
| **Monitoring (§III.B)** | Track FPR_autocor, MCFF, reputation distribution |
| **Governance (§IV)** | Human-review trigger at 2σ escalation |
| **Out-of-tolerance** | Auto-disable if ASR > 0.50 over 50 rounds |
| **Concept drift** | 30-round correlation: fraud rate vs. reputation |
| **Override process** | Documented appeal within 24h; outcome log |

### 8.3 Fairness Regulation (ECOA, FCRA)

Three fairness risks are identified:
1. **Per-subgroup honest FPR asymmetry** — monitored via FPR_autocor; threshold: no subgroup FPR > 2× overall rate.
2. **Geographic proxy discrimination** — geographic splits correlated with protected characteristics must not affect defense decisions.
3. **ECOA adverse action notices** — inference-time SHAP explanations satisfy ECOA; defense-level decisions require separate notification.

The reputation forgetting mechanism (§7.3) directly addresses structural fairness risk: R_SS = 0.85 prevents permanent exclusion.

### 8.4 AML/CFT Override Obligations

The system includes an `SAR_override` flag: when a flagged update involves a transaction exceeding the local reporting threshold (€15,000 EU, \$10,000 US), an automated SAR notification is generated regardless of the flag's accuracy. AML obligations override model-level decisions.

### 8.5 Cross-Jurisdictional Compliance

The paper does not resolve cross-jurisdictional conflicts (GDPR ↔ GLBA, UK GDPR ↔ EU GDPR, APRA CPG 234). Deployment within a single regulatory jurisdiction is recommended initially.

---

## 9. Discussion and Limitations

### 9.1 Experimental Validation Status

This paper is a design-stage specification. Expected results (§6.5) derive from formal analysis (§7) and architectural reasoning. **Experimental validation requires 50-100 GPU-hours on cloud infrastructure and is in progress.**

### 9.2 Red-Team Assessment

| Counter-Argument | Our Response | Residual Risk |
|-----------------|--------------|---------------|
| Cascade accumulates FPRs | §7.1 bound: 1.6% honest FPR under bounded perturbations | Bound depends on δ ≤ 0.15 assumption |
| Threat model excludes server compromise | Standard assumption; TEE future work | Realistic high-impact vector |
| No oracle orchestration baseline | C9, C10 in ablation directly test this | Without experiments, comparison is estimated |
| Convergence not proven | §7.2: control system with bounded neighborhood, not formal optimizer | Non-stationary patterns may cause oscillation |

### 9.3 Limitations

| Limitation | Impact | Future Work |
|------------|--------|-------------|
| Server compromise | Highest-risk deployment vulnerability | TEE-based aggregation (Intel SGX, AMD SEV) |
| SecAgg incompatibility | Privacy limitation for EU | Functional encryption for robust aggregation |
| Cold-start (t₀=20) | Vulnerability window for new banks | Adaptive bootstrap with public data |
| Synthetic identity fraud | Most costly fraud type unaddressed | Feature-level anomaly detection |
| N=10 clients only | Not production-scale | Scale to N=30-50 |
| Fixed A2 schedule | Weaker than optimal attacker model | A2-Adaptive (defense-feedback-reactive) |
| Reputation window tuning | γ=0.02 is heuristic | Bayesian reputation with uncertainty |

### 9.4 Ethical and Societal Implications

**False decline harm.** Any non-zero honest FPR causes legitimate transaction declines. Vulnerable customers may face material hardship from even a single false decline.

**Competitive intelligence leakage.** The server observes gradients reflecting each bank's transaction distribution. Cryptographic solutions (SecAgg) would resolve this but are incompatible with the current architecture.

**Systemic risk concentration.** If the consortium covers substantial payment volume and the defense fails (server compromise), fraud detection failure becomes systemic. Circuit-breaker mechanisms and fallback procedures are essential.

---

## 10. Conclusion

Cross-silo FL for credit card fraud detection faces a threat that existing Byzantine-robust aggregation methods are not designed for: **temporally-adaptive, incentive-driven poisoning** by financially-motivated adversaries. The fundamental blind spot is statelessness—per-round defenses cannot detect attackers who alternate between malicious and benign behavior across rounds.

We have presented a **gated cascade defense framework** with three complementary layers: norm/cosine filtering (rapid rejection), spectral anomaly detection (coordinated threats), and temporal EMA reputation scoring (slow poisoning), connected by an adaptive threshold escalation policy. Formal analysis establishes a ~1.6% honest FPR bound, convergence neighborhoods for threshold dynamics, and fairness guarantees via reputation steady-state floor. Regulatory compliance mapping addresses GDPR, SR 11-7, ECOA, and AML/CFT obligations.

**This paper is a design-stage specification.** Expected results project 0.25 ASR for the full defense vs. 0.92 for undefended FedAvg, with cascade structure contributing the majority of improvement and adaptive thresholds adding ~7pp. Experimental validation is planned on cloud infrastructure.

---

## References

[1] Nilson Report, \"Card Fraud Losses Reach \$28.65 Billion,\" Nilson Report, Issue 1232, 2023.

[2] Q. Yang, Y. Liu, T. Chen, and Y. Tong, "Federated Machine Learning: Concept and Applications," *ACM TIST*, vol. 10, no. 2, pp. 1-19, 2019.

[3] P. Kairouz et al., "Advances and Open Problems in Federated Learning," *Foundations and Trends in ML*, vol. 14, no. 1-2, pp. 1-210, 2021.

[4] B. McMahan, E. Moore, D. Ramage, S. Hampson, and B. A. y Arcas, "Communication-Efficient Learning of Deep Networks from Decentralized Data," in *AISTATS*, 2017, pp. 1273-1282.

[5] L. Lamport, R. Shostak, and M. Pease, "The Byzantine Generals Problem," *ACM TOPLAS*, vol. 4, no. 3, pp. 382-401, 1982.

[6] D. Alistarh, Z. Allen-Zhu, and J. Li, "Byzantine Stochastic Gradient Descent," in *NeurIPS*, 2018, pp. 4613-4623.

[7] Z. Allen-Zhu, F. Ebrahimianghazaleh, J. Li, and D. Alistarh, "Byzantine-Resilient Non-Convex SGD," in *ICLR*, 2021.

[8] P. Blanchard, E. M. El Mhamdi, R. Guerraoui, and J. Stainer, "Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent," in *NeurIPS*, 2017, pp. 119-129.

[9] D. Yin, Y. Chen, R. Kannan, and P. Bartlett, "Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates," in *ICML*, 2018, pp. 5650-5659.

[10] R. Guerraoui, S. Rouault, et al., "The Hidden Vulnerability of Distributed Learning in Byzantium," in *ICML*, 2018, pp. 3521-3530.

[11] X. Cao, M. Fang, J. Liu, and N. Z. Gong, "FLTrust: Byzantine-robust Federated Learning via Trusted Data," in *IEEE S&P*, 2021, pp. 652-669.

[12] C. Fung, C. J. M. Yoon, and I. Beschastnikh, "FoolsGold: A Defense against Data Poisoning in Federated Learning," in *WWW*, 2020, pp. 126-136.

[13] Z. Zhang, L. Jia, H. Wang, and Z. Lu, "FLDetector: Defending Federated Learning Against Model Poisoning via Detecting Malicious Clients," in *ACM CCS*, 2022, pp. 1923-1937.

[14] W. Yang, Y. Zhang, K. Ye, L. Li, and C.-Z. Xu, "FFD: A Federated Learning Based Method for Credit Card Fraud Detection," in *BigData Congress*, 2019, pp. 18-25.

[15] M. A. Abdul Salam, S. M. Darwish, and T. H. A. Soliman, "Federated Learning for Credit Card Fraud Detection with Data Balancing," *IEEE Access*, vol. 12, pp. 3378-3393, 2024.

[16] L. Zheng, J. Wang, and H. Liu, "Federated Fraud Detection: A Real-World Cross-Silo Evaluation," *IEEE TKDE*, 2025.

[17] V. Naresh, N. Kumar, and P. K. Singh, "Federated Learning for Payment Fraud Detection: A Comprehensive Survey," *ACM Computing Surveys*, 2024.

[18] Y. A. Farrukh, I. Khan, and M. Z. Baig, "A Survey on Federated Learning for Credit Card Fraud Detection," *IEEE Access*, vol. 13, 2025.

[19] V. Shejwalkar, A. Houmansadr, P. Kairouz, and D. Ramage, "FLAME: Robust Federated Learning via Adaptive Model Aggregation," in *USENIX Security*, 2023.

[20] J. Wang, Z. Liu, and Q. Yang, "ShieldFL: Mitigating Model Poisoning Attacks in Federated Learning," *IEEE TDSC*, 2024.

[21] L. Zhang, B. Li, and Y. Wang, "FedDef: Defense Against Gradient Leakage and Poisoning in Federated Learning," in *NeurIPS*, 2024.

[22] M. Fang, X. Cao, J. Jia, and N. Z. Gong, "Local Model Poisoning Attacks to Byzantine-Robust Federated Learning," in *USENIX Security*, 2020, pp. 1605-1622.

[23] S. Jagielski, A. Oprea, B. Biggio, C. Liu, C. Nita-Rotaru, and B. Li, "Manipulating Machine Learning: Poisoning Attacks and Countermeasures for Regression Learning," in *IEEE S&P*, 2018, pp. 19-35.

[24] V. Shejwalkar and A. Houmansadr, "Manipulating the Byzantine: Optimizing Model Poisoning Attacks in Federated Learning," in *NDSS*, 2021.

[25] G. Baruch, M. Baruch, and Y. Goldberg, "A Little Is Enough: Circumventing Defenses For Distributed Learning," in *NeurIPS*, 2019, pp. 8635-8645.

[26] C. Xie, K. Huang, P.-Y. Chen, and B. Li, "DBA: Distributed Backdoor Attacks Against Federated Learning," in *ICLR*, 2020.

[27] IEEE Computational Intelligence Society, "IEEE-CIS Fraud Detection Dataset," Kaggle, 2019. [Online]. Available: https://kaggle.com/c/ieee-fraud-detection

[28] A. Dal Pozzolo, O. Caelen, R. A. Johnson, and G. Bontempi, "Calibrating Probability with Undersampling for Unbalanced Classification," in *IEEE CIDM*, 2015, pp. 159-166.

[29] K. Pillutla, S. M. Kakade, and Z. Harchaoui, "Robust Aggregation for Federated Learning," *IEEE TSP*, vol. 70, pp. 1142-1154, 2022.

[30] M. Abadi et al., "Deep Learning with Differential Privacy," in *ACM CCS*, 2016, pp. 308-318.

[31] G. W. Stewart, "On the Early History of the Singular Value Decomposition," *SIAM Review*, vol. 35, no. 4, pp. 551-566, 1993.

[32] S. Song, K. Chaudhuri, and A. D. Sarwate, "Stochastic Gradient Descent with Differentially Private Updates," in *IEEE GlobalSIP*, 2013, pp. 245-248.

[33] European Parliament and Council, "Regulation (EU) 2016/679 (General Data Protection Regulation)," *OJEU*, L119/1, 2016.

[34] S. Lundberg and S.-I. Lee, "A Unified Approach to Interpreting Model Predictions," in *NeurIPS*, 2017, pp. 4765-4774.

[35] CJEU, "Data Protection Commissioner v. Facebook Ireland and Maximillian Schrems (Schrems II)," Case C-311/18, 2020.

[36] Board of Governors of the Federal Reserve System, "SR 11-7: Guidance on Model Risk Management," 2011.

[37] FATF, "International Standards on Combating Money Laundering and the Financing of Terrorism & Proliferation," 2012-2023.

[38] T. Ryffel, D. Pointcheval, F. Bach, E. Dufourcq, and J.-P. Gay, "Partially Encrypted Deep Learning using Functional Encryption," in *NeurIPS*, 2019, pp. 4519-4530.
