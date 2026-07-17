# Privacy Model Specification

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Issue:** R3 — Specify the privacy model explicitly  
**Date:** 2026-07-05

---

## 1. The Central Tension

The framework requires raw gradient updates for spectral anomaly detection (Layer 2). Standard FL privacy techniques have an incompatible interaction:

| Technique | What It Does | Conflict with Layer 2 |
|-----------|-------------|----------------------|
| **Secure Aggregation (SecAgg)** | Encrypts individual client updates so the server only sees the aggregate sum | **Fatal.** Server cannot compute per-client SVD on encrypted vectors |
| **Differential Privacy (DP)** | Adds calibrated noise to updates before sharing | **Degrades detection.** Noise can mask the spectral signature of collusive attacks |
| **Trusted Execution Environments (TEE)** | Processes updates inside an enclave | **Compatible but complex.** Requires hardware support, limits scale |

**The paper must pick a privacy model and defend it honestly.** TIFS reviewers will scrutinize this.

---

## 2. Proposed Privacy Model: Trusted Consortium Server

### 2.1 Assumption

> The aggregation server is a **trusted node** operated jointly by the banking consortium. It has access to individual, unencrypted client gradient updates per round. Raw transaction data never leaves member banks.

This is the **honest-but-curious** server model applied to cross-silo FL.

### 2.2 Why This Is Realistic for Banking Consortia

| Factor | Justification |
|--------|---------------|
| **Cross-silo ≠ cross-device** | Banking FL involves 10–100 institutions, not 10⁶ mobile phones. Each member is a regulated entity with a contractual relationship. |
| **Consortium governance** | The server is typically operated by a central bank, a payment network (Visa/Mastercard), or a jointly-governed trust. Example: the US Financial Crimes Enforcement Network (FinCEN) consortium model. |
| **Privacy boundary is between banks** | The key privacy protection is that Bank A never sees Bank B's raw transactions. Gradient updates are already aggregated statistics — they leak far less than raw data. |
| **Regulatory precedent** | GDPR Art. 28 allows data processing by a "processor" under contract. The consortium server qualifies as a joint data processor with binding agreements. |

### 2.3 What the Server Sees

```
Round t:
  Bank A sends: g_A (d-dimensional gradient vector)
  Bank B sends: g_B
  ...
  Bank N sends: g_N

Server sees: {g_1, g_2, ..., g_N}  ← raw, unencrypted vectors
Server computes: aggregated model w^{(t+1)}  ← shares only this back
```

**Gradient leakage risk:** Gradients can leak information about local data [Zhu et al., 2019]. We acknowledge this and discuss mitigations in §5.

---

## 3. Relationship to the Detection Layers

Each layer's privacy implications differ:

| Layer | What It Needs | Privacy Cost | Mitigation |
|-------|---------------|-------------|------------|
| L1: Norm/Cosine | $\|g_i\|$, $\cos(g_i, g_{\text{ref}})$ | Low — scalars, not full vectors | Can compute these from DP-noised gradients with minimal accuracy loss |
| L2: Spectral (SVD) | Full $g_i$ vectors | **Highest** — requires raw gradients for SVD decomposition | Central server sees these; never shared with other banks |
| L3: Temporal | $R_i^{(t)}$, $g_i$ history | Medium — aggregated reputation scores share no raw data | Reputation is a scalar per bank — low leakage |

### 3.1 Formal Privacy Guarantee

The system provides **data-level privacy** (also called "input privacy"): raw transaction records never leave their originating bank. It does **not** provide **gradient-level privacy** (the server sees raw gradient vectors).

$$\text{Privacy}_{IFD} = \text{Data-level privacy} \quad \land \quad \lnot\text{Gradient-level privacy}$$

This is a weaker guarantee than full SecAgg+DP FL, but it is the same model used by:
- FLTrust [Cao et al., IEEE S&P 2021] — server stores a trusted reference dataset
- FoolsGold [Fung et al., WWW 2020] — server computes per-client similarity
- Most cross-silo robust FL papers

**Critically, no existing robust aggregation method that requires per-client inspection (Krum, Median, Trimmed Mean, Bulyan, FoolsGold, FLDetector) is compatible with SecAgg.** The paper should argue that this is an open problem in the field, not a unique limitation of our approach.

---

## 4. Differential Privacy Ablation Study

To strengthen the paper, we propose a **DP ablation** showing how spectral detection degrades under Gaussian noise.

### 4.1 Setup

Apply Gaussian DP noise to each client update before sending to the server:

$$\tilde{g}_i = g_i + \mathcal{N}(0, \sigma^2 C^2 I)$$

where $C$ is the clipping threshold (norm bound) and $\sigma$ is the noise multiplier.

### 4.2 Privacy Budgets Tested

| Budget ε | Noise Multiplier σ | Interpretation | Expected Impact on Layer 2 |
|----------|-------------------|----------------|---------------------------|
| ∞ | 0.0 | No DP (baseline) | Full detection accuracy |
| 8 | 0.5 | Typical for banking analytics | Slight degradation; high spectral components survive |
| 4 | 0.8 | Strong privacy, common in FL | Moderate degradation; some collusive signatures obscured |
| 1 | 2.5 | Very strong privacy | Heavy degradation; spectral detection unreliable |

### 4.3 Expected Trade-off

```
Detection TPR
   1.0 |●    (ε=∞)
       |●
   0.8 |  ●  (ε=8)
       |   ●
   0.6 |    ● (ε=4)
       |
   0.4 |       ● (ε=1)
       |
   0.2 |          ● (DP destroys spectral signature)
       |
       └─────────────────────
        0.2  0.4  0.6  0.8  1.0   Honest-client FPR
```

**Expected result:** At ε ≥ 4, Layer 2 maintains moderate detection. At ε = 1, the defense collapses to Layer 1 + Layer 3 only. This trade-off is reported explicitly as a limitation.

### 4.4 Reporting

```
| Privacy Setting | Layer 2 TPR | Layer 2 FPR | Overall Defense TPR |
|-----------------|-------------|-------------|---------------------|
| No DP (ε=∞)    | 0.92        | 0.05        | 0.95                |
| ε=8             | 0.85        | 0.08        | 0.91                |
| ε=4             | 0.72        | 0.12        | 0.84                |
| ε=1             | 0.38        | 0.22        | 0.61                |
```

---

## 5. Gradient Leakage and Mitigations

### 5.1 What Gradients Leak

Given a gradient $g = \nabla \mathcal{L}(w, \mathcal{D})$ for a batch $\mathcal{D}$, an adversary can:

- **Infer membership:** Determine whether specific data points were in the training batch [Shokri et al., 2017]
- **Reconstruct data:** Recover input features from gradients under certain conditions [Zhu et al., 2019]
- **Infer properties:** Learn aggregate statistics about local data distributions

### 5.2 Realistic Risk in the Banking Context

| Factor | Risk Level | Explanation |
|--------|------------|-------------|
| Batch size | **Low** | Banks train on batches of 10⁴–10⁶ transactions. Gradient inversion requires small batches (≤ 64). |
| DNN architecture | **Low** | Tabular fraud models have fewer parameters than vision models where inversion is demonstrated |
| Adversary: other banks | **None** | Other banks never see gradients — only the server does |
| Adversary: server operator | **Moderate** | The server sees gradients. This is a trust requirement. |

### 5.3 Mitigations

| Mitigation | Description | Status |
|------------|-------------|--------|
| **DP ablation** | Report performance under DP as in §4 | Planned experiment |
| **Gradient compression** | Top-k sparsification or quantization reduces information content | Future work |
| **Trusted hardware** | Intel SGX / AMD SEV enclave for server-side computation | Future work (see §7) |

---

## 6. Regulatory Compliance

### 6.1 GDPR (Europe)

| Art. | Requirement | Compliance |
|------|-------------|------------|
| 5(1)(c) | Data minimization | Banks share gradients, not raw transactions ✅ |
| 22 | Automated decision-making | Banks must explain individual decisions (see R9) |
| 28 | Data processor agreement | Consortium server qualifies under joint-controller model ✅ |
| 35 | Data Protection Impact Assessment | Required before deployment — flagged as future work |

### 6.2 Banking Supervision (ECB, OCC, APRA)

| Requirement | Compliance |
|-------------|------------|
| Model risk management (SR 11-7) | FL model must be validated like any production model. The defense's impact on model performance must be quantified. ✅ (planned) |
| Anti-money laundering (AML) | Shared fraud model improves AML compliance across institutions ✅ |
| Fair lending (ECOA, FHA) | Model must not discriminate. The temporal reputation system must be audited against disparate impact (see R10) |
| Third-party risk | The consortium server operator is a regulated entity. SLAs and audit rights are required. |

### 6.3 Data Residency

Some jurisdictions require transaction data to remain within national borders. Our model satisfies this: only gradient updates cross borders, and only to a consortium server that may be jurisdictionally bounded.

---

## 7. Limitations and Future Work

### 7.1 Honest Limitations to Acknowledge in the Paper

1. **No gradient-level privacy.** The server sees raw updates. This is the same assumption made by prior robust aggregation methods (Krum, Median, FoolsGold, FLTrust), but it should be stated upfront.

2. **DP degrades spectral detection.** At ε < 4, Layer 2 becomes unreliable. This is an inherent tension between privacy and detectability.

3. **Trust requirement.** The consortium must agree on a trusted server operator. This is feasible for a banking consortium but non-trivial.

### 7.2 Future Directions (list to suggest, not claim)

- **Functional encryption for spectral analysis:** Recent work on encrypted linear algebra [Ryffel et al., 2022] could enable SVD on encrypted updates. Not yet practical but worth noting.
- **Split learning alternative:** Banks compute representations; server computes the classification head. Spectral analysis moves to the representation layer.
- **SecAgg-friendly proxy features:** Replace raw gradients with spectral sketches (random projections) that preserve relative distances but hide exact values.

---

## 8. Summary: Where This Appears in the Paper

| Section | Content |
|---------|---------|
| **§2.1 System Model** (new) | Trusted consortium server. Privacy boundary: data stays at banks, gradients go to server. Referenced as common assumption in cross-silo robust FL. |
| **§2.2 Privacy Guarantees** (new) | Data-level privacy guaranteed. Gradient-level privacy not provided. Table of what each layer sees. |
| **§4.5 DP Ablation** (new subsection in Experiments) | TPR/FPR trade-off under ε ∈ {∞, 8, 4, 1}. Defense reliability across privacy budgets. |
| **§6 Limitations** | Honest statement of trust assumptions. Future directions for SecAgg compatibility. |
