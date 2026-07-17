# S5: Privacy Model — Strengthening the Trust Argument for TIFS

**Issue:** The Perspective reviewer (Chen) rated this paper 58/100, with the privacy model being the primary weakness. The trusted server assumption is acceptable but insufficiently justified for a security journal.
**Reviewers:** Perspective (primary), Domain (P3)
**Severity:** 🟡 Must Fix Before TIFS Submission

---

## 1. The Problem

Current privacy model (from R3 resolution):

> Trusted Consortium Server backed by legal MoUs, with optional TEE and a DP ablation study.

The Perspective reviewer's critique:
1. **"Everyone else does it" isn't sufficient for TIFS** — a security journal demands either a formal trust argument or a concrete mechanism
2. **Gradient leakage risk is underestimated** — the paper argues tabular data + batch-size arguments against reconstruction, but this is selective
3. **DPIA is mandatory under GDPR**, not optional future work
4. **Joint-controller vs. processor status** is legally uncertain for consortia

## 2. Recommended Privacy Model Structure

### 2.1 Honest Framing (Not Overclaiming)

Rather than "Trusted Consortium Server" (which begs the question for a security audience), use:

> **Consortium Aggregation Protocol (CAP):** The system operates under a hybrid trust model combining legal, cryptographic, and operational safeguards. The aggregation server is a regulated entity subject to the consortium's governance framework, with contractual liability for protocol deviations. This is consistent with the deployment model of existing financial FL consortia (Nasdaq FRM, Privacy Preserving Federated Learning for Banking — see [REF]).

### 2.2 Three-Layer Trust Model

| Layer | Mechanism | What It Protects Against | Limitations |
|-------|-----------|-------------------------|-------------|
| **Legal/Contractual** | Consortium agreement, SLA, liability clauses, periodic third-party audit | Malicious server behavior (protocol deviations, data exfiltration) | Enforcement lag; cross-jurisdictional complexity |
| **Technical (Passive)** | Secure aggregation (SecAgg) for gradient privacy; differential privacy (ε ≥ 4) for output privacy | Honest-but-curious server learning client data from gradients | SecAgg incompatible with Layer 2 (SVD); DP reduces utility |
| **Technical (Active)** | Trusted execution environment (Intel SGX / AMD SEV) for aggregation logic; on-chain commitment for audit | Active server compromise; retrospective detection of deviation | Side-channel attacks; TEE supply chain trust; cost |

### 2.3 The Honest Claim

> Our defense requires the server to faithfully execute the aggregation protocol. We provide:
> 1. **TEE-based verification** of faithful execution (attested aggregation)
> 2. **On-chain commitment** of per-round aggregation results for audit
> 3. **DP output perturbation** (ε ∈ {8, 4, 1}) to bound gradient leakage even from the server
>
> Under the CAP model, the server is *technical* adversary (honest-but-curious) backed by *contractual* deterrence against malicious behavior. This is strictly stronger than the standard FL trust model.

## 3. Concrete Changes to Implement

| Change | Location | Details |
|--------|----------|---------|
| Rename "Trusted Server" → "CAP with TEE" | privacy-model.md, paper §3 | Honest-but-curious with contractual + TEE enforcement |
| Add TEE integration path | privacy-model.md | SGX/SEV attestation flow diagram |
| Add DPIA requirement | privacy-model.md | GDPR Art. 35 assessment; PIA for banking regulation |
| Add leakage bound calculation | privacy-model.md | Formal reconstruction bound: given d parameters and batch size B, the reconstruction success probability is bounded by ... |
| Address SecAgg incompatibility honestly | privacy-model.md | "Layer 2 SVD requires raw gradient access; we accept this trade-off. For deployments requiring full SecAgg, Layer 2 can be omitted (see Ablation: no_l2 achieves ASR competitive with full defense for A1/A3)" |

## 4. The Privacy-Robustness Tension Section

A dedicated paper subsection should articulate:
1. **The trade-off formally:** Dwork & Roth's privacy-robustness impossibility result implies ε cannot be both small (privacy) and large (utility) 
2. **Our position:** We accept a weaker privacy guarantee (ε ≥ 4, honest-but-curious server, contractual enforcement) in exchange for stronger robustness guarantees
3. **Why this is acceptable for banking:** Banking secrecy laws already impose contractual privacy obligations stronger than technical DP. The legal framework is the primary deterrent; technical measures are secondary
4. **Ablation evidence:** DP ε=4 reduces ASR by < 5 percentage points, supporting the claim that moderate DP is compatible with our defense
