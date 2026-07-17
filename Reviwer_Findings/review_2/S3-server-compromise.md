# S3: Server Compromise Threat Model

**Issue:** The most realistic attack in real-world banking FL is server manipulation — yet the threat model only considers client-side attackers.
**Reviewers:** Domain (P1), Perspective, DA
**Severity:** 🔴 Must Fix

---

## 1. Why This Matters

The current threat model assumes:

- **Trusted server** — honest-broker model backed by legal MoU + optional TEE
- **Client-side attackers** — malicious banks controlling ≤ f clients
- **Kerckhoffs's principle** — attackers know the protocol, not secret keys

This omits the most realistic attack in cross-silo banking FL: a server compromise or malicious insider at the consortium operator level. In real-world banking consortia (e.g., Nasdaq FRM, featurespace), the aggregation server is operated by a third-party consortium — it's a single point of failure and an attractive target.

## 2. Server Compromise Attack Taxonomy

| Attack | Description | Feasibility | Defense Applicability |
|--------|-------------|-------------|----------------------|
| **S-C1: Update manipulation** | Server replaces aggregated gradient with attacker-controlled value | High — server controls final aggregation | Defense-unaware: our 3 layers run on the server; a compromised server can skip them entirely |
| **S-C2: Threshold manipulation** | Server sets τ₁=τ₂=1.0 (never escalate) or τ₁=τ₂=0.0 (always reject honest clients) | High — thresholds are server-side state | Defense-aware: attacker can set thresholds to disable defense |
| **S-C3: Reputation poisoning** | Server zeros honest clients' reputations, boosts malicious ones | High — R_i(t) stored on server | Can be partially mitigated by client-side reputation tracking (appendix) |
| **S-C4: Gradient leakage** | Server exfiltrates client gradients to reconstruct transaction data | High — server sees raw gradients | Our defense doesn't change gradient visibility; gradient leakage is a separate concern |
| **S-C5: Delayed aggregation** | Server selectively drops or delays client updates | Medium — detectable via audit logs | Out of scope for our defense; requires Byzantine broadcast or commit-chains |

## 3. Position in Paper

**Not a weakness of our defense** — server compromise is a fundamentally different threat model. Our defense protects against client-side poisoning under the assumption of an honest server. This is standard in Byzantine-resilient FL literature (Krum, Bulyan, FLDetector all assume honest aggregation).

**However**, the paper must explicitly acknowledge this limitation and bound our claims:

### 3.1 Honest Framing

> Our defense assumes an honest-but-curious aggregation server: the server faithfully executes the aggregation protocol but may attempt to learn private information from client updates. We do not defend against a malicious server that deviates from the aggregation protocol, as this constitutes a qualitatively different threat model requiring infrastructure-level protections (e.g., trusted execution environments, decentralized aggregation, or on-chain verification).

### 3.2 How TIFS Reviewers Will Evaluate This

The reviewers flagged this because TIFS is a security journal — claiming a trusted server without justifying it for a security context is a red flag. The correct response is:

1. **Acknowledge** the limitation explicitly
2. **Justify** why it's reasonable for the intended deployment scenario (regulated banking consortium with legal agreements)
3. **Bound** what we do and don't defend against
4. **Provide options** for extending beyond the trusted server assumption (as future work)

### 3.3 The Trust Argument

In a regulated banking consortium:

| Protection Layer | How It Works | Limitations |
|-----------------|--------------|-------------|
| **Legal MOU** | Consortium members sign agreement; server breach = liability | Enforcement depends on jurisdiction; slow |
| **Audit trail** | All server operations logged; periodic third-party audit | Retroactive, not preventive |
| **TEE (SGX/CSV)** | Server-side aggregation runs in hardware enclave | Side-channel attacks; cost; deployment complexity |
| **Threshold decryption** | Clients hold key shares; aggregation requires quorum | Communication overhead; assumes honest majority of clients |
| **On-chain verification** | Aggregation results committed to blockchain | Gas costs; latency; privacy implications |

### 3.4 Recommended Position

**Primary model:** Honest server + legal MOU + audit trail (current)

**Boundary statement:** "We restrict our analysis to the case of an honest-but-curious aggregation server. This is consistent with the threat model of Byzantine-resilient aggregation in cross-silo FL (Krum, Bulyan, FLTrust, FLDetector). The case of a malicious server is orthogonal to our poisoning defense and can be addressed by orthogonal infrastructure-level mechanisms (Section: Limitations)."

**Future work:** Formal TEE integration specification + on-chain commitment

## 4. Required Changes

| Change | Location | Effort |
|--------|----------|--------|
| Add "Server Compromise" section to threat model | Paper §3 (Threat Model) | 1 paragraph |
| Add honest server assumption to limitations | Paper §9 (Discussion) | 1 paragraph |
| Add TEE/on-chain commitment to future work | Paper §9 (Discussion) | 2-3 sentences |
| Remove "Trusted Consortium Server" language that implies absolute trust | privacy-model.md | Search/replace | 
