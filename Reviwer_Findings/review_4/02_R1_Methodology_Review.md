# Peer Review Report — R1 (Methodology)
**Paper ID:** TIFS-2026-XXXX
**Title:** "Robust Federated Learning for Credit Card Identity Fraud Detection: A Temporally-Aware Layered Defense Framework"
**Reviewer:** Peer Reviewer 1 (Methodology — ML methodology, statistical rigor, experimental design)

---

**Recommendation: Major Revision**

**Scope and Contribution:** This design-stage specification proposes a gated cascade defense framework for FL-based fraud detection, backed by formal convergence analysis (Stewart perturbation bound, Lipschitz smoothness, reputation floor theorem). The methodology is ambitious and addresses an important problem, but several critical gaps in the formal proofs and the planned experimental design undermine the rigor and internal validity of the claims.

---

### 1. Validity of the Planned Experimental Design

The paper correctly identifies the need for diverse threat models (A1–A6) and proposes a reasonable set of evaluation configurations (10 baselines + 10 ablations). The dataset selection (IEEE-CIS, ECC) is standard.

**Critical Threat to Internal Validity:** The design lacks a control for the confounding effect of early-training instability on the reputation system. In early rounds, losses are high and model divergence is large for *all* clients, causing low cosine similarity scores independent of any attack. The proposed architecture applies the reputation filter from round 1. A planned "warm-up" phase of 10–20 standard FedAvg rounds is essential to establish a baseline reputation signal before the defender can be trusted. Without this, the experimental design cannot distinguish between attack detection and normal model convergence.

### 2. Baselines (Fairness and Comprehensiveness)

The included baselines (B1–B10) are standard and well-motivated. However:

- **Missing Baseline — DP-FedAvg:** A defense providing differential privacy guarantees is the most direct competitor to a defense claiming *provable* attacker exclusion. DP offers a formal, composable bound on the influence of any single client. The paper must plan for a comparison against DP-SGD with a carefully calibrated budget (ε) to contextualize the novelty of the "provable" claim.
- **Computational Cost:** The reputation mechanism requires O(N²·d) pairwise computations per round. No baseline accounts for this runtime overhead. A cost-benefit comparison against O(N) baselines (median, trimmed mean) is required to assess practical feasibility.
- **Evaluation standard:** 5 trials is below the modern standard. At least 10 independent runs (with different seeds for client sampling, data partitioning, and gradient noise) are required for every metric, reported as mean ± std.

### 3. Evaluation Metrics (Appropriateness)

Attack Success Rate (ASR) and honest False Positive Rate (FPR) are appropriate primary metrics.

**Overlooked Metrics:**
- **Reputation System Precision and Recall:** The reputation scoring is a binary classifier (malicious vs. benign). The paper does not plan to report the confusion matrix or F1-score of the defender's detection. A high false-positive rate means benign clients are unfairly excluded—a significant threat to fairness and construct validity.
- **Model Utility:** ASR alone is insufficient. The paper must report clean accuracy, F1-score on the fraud class, and false decline rate alongside ASR to characterize the utility-robustness trade-off.

### 4. Formal Analysis (Soundness)

**Stewart's Perturbation Bound (Section V-A):**
The application of Stewart's bound to bound the honest FPR is mathematically standard. However, the derivation explicitly assumes IID client data and stationary gradient covariance. The paper acknowledges non-IID data and concept drift as challenges but provides no formal argument for bound degradation under non-IID or non-stationary conditions. This step in the proof chain is logically invalid unless concentration inequalities for non-IID sampling and bounded-drift analysis are provided.

**Lipschitz Convergence (Section V-B):**
*Critical Flaw:* The proof of contraction for the adaptive threshold dynamics assumes the reputation weight $w_i(t)$ is independent of the model parameters $\theta(t)$. In reality, $w_i(t)$ is a function of the anomaly score $a_i^{(t)}$, which depends on $\cos(g_i(t), \mu(t))$—both of which depend on $\theta(t)$ through the gradient. This violation of the standard L-smoothness assumption means the convergence guarantee is unsupported. An expectation-bound over the reputation assignment process must be derived to salvage the convergence claim.

**Reputation Floor Theorem (Theorem 1, Section V-C):**
*Critical Flaw:* The theorem bounds the reputation score of a malicious client below threshold $\tau_R$ by assuming the malicious gradient's deviation from honest statistics is detectable. A **scaling attack** (malicious client computes $g_m = \alpha \cdot g_{\text{benign}} + \text{noise}$ with $\alpha \in (0, 0.15)$) can achieve arbitrarily high cosine similarity to the peer mean, defeating the reputation filter entirely. The proof of Theorem 1 does not explicitly rule out this well-known attack class (Bagdasaryan et al., 2020). Without a norm-clipping component or a formal bound on allowed gradient magnitudes, the Reputation Floor guarantee is unsupported.

### 5. Ablation Configurations

The planned ablations (Table IV, C1–C10) correctly isolate the contribution of each layer.

**Missing Ablations:**
- **Threshold $\tau_R$ Sweep:** The reputation threshold is the single most important hyperparameter. The paper must plan an ablation sweeping $\tau_R$ from $[0.6, 0.9]$ to compare the theoretically suggested $\tau_R$ against the empirical optimal. If these diverge, the "provable" guarantee is practically empty.
- **Empty Client Pool:** The design must include an explicit ablation for the scenario where the reputation filter rejects *all* clients. Is there a fallback mechanism (e.g., reverting to standard FedAvg)?
- **$W$ vs. $\tau_R$ Interaction:** The window size $W$ and threshold $\tau_R$ are coupled. A 2D sensitivity heatmap is required to verify the chosen operating point is robust and not an artifact of parameter degeneracy.

### 6. Threats to Internal Validity

- **Temporal Burst Attack:** An adaptive attacker can alternate between benign and mildly malicious rounds, maintaining a reputation score just below $\tau_R$ while achieving a cumulative poisoning effect. The formal analysis does not address this jamming or "agenda-setting" attack model.
- **Sybil Boundary:** The Stewart bounds and Theorem 1 implicitly assume $m < N/3$ (malicious clients are a strict minority). If a Sybil attack exceeds this threshold, the entire reputation floor collapses. The paper should explicitly define an operational regime and discuss graceful degradation beyond it.
- **Empty Window Cold Start:** At $t < W$, the window $W=50$ is not yet full. The behavior of the reputation system during the first 50 rounds is formally uncharacterized.

### 7. Hyperparameter Sensitivity Plan

The paper proposes a sensitivity grid, which is adequate but insufficient. The interaction between $W$ (window size) and $\tau_R$ (reputation threshold) is degenerate: a large window with a high threshold is approximately equivalent to a short window with a low threshold. A 2D sensitivity heatmap is required to establish that the projected results are not artifacts of a single parameter configuration.

### 8. Projected ASR Values (Plausibility)

The projected ASR (0.25 for full defense) and honest FPR (1.6%) are ambitious.

**Issue with Formal Consistency:** Theorem 1 (Reputation Floor) guarantees that a malicious client's reputation is strictly below $\tau_R$, formally implying the attacker is fully excluded from aggregation. This should yield an ASR of *exactly 0%* for attacks targeting L3, not 0.25. Projecting a non-zero ASR implicitly acknowledges that the bound is either loose or violated in practice. The paper should reframe Table V values as "theoretical worst-case upper bounds on ASR" or as "speculative empirical targets for validation," not as derived consequences of the formal analysis.

---

## Summary of Required Revisions

1. **Formal Proof:** Address the scaling attack against Theorem 1 (add norm clipping or formalize the bound against scaled gradients).
2. **IID Dependency:** Provide a rigorous argument for how the Stewart bound behaves under non-IID, or restrict formal claims to the IID regime with non-IID characterized empirically.
3. **Lipschitz Proof:** Fix the convergence proof to handle the stochastic dependence of reputation weights on model parameters.
4. **Baselines:** Add DP-FedAvg and a computational runtime comparison table.
5. **Metrics:** Add precision/recall of the reputation classifier and mandate ≥10 independent trials.
6. **Design Changes:** Add a warm-up phase and an empty-client-pool fallback mechanism.
7. **Ablations:** Add a threshold $\tau_R$ sweep and a $W$ vs. $\tau_R$ sensitivity heatmap.
8. **ASR Claims:** Replace point-estimate projections with bound ranges consistent with the formal proofs.
