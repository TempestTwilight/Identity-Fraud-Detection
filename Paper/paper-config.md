# Paper Configuration Record

Based on the work completed across 21 resolved issues and 5 independent reviews, here is the proposed configuration for the full academic paper pipeline.

## Current Paper State (Post-Rebuttal)

| Setting | Value | Notes |
|---------|-------|-------|
| **Status** | Post-rebuttal — 2 CRITICAL issues resolved in paper.tex | C1 (θ_low calibration) + C2 (EWMA baseline) applied |
| **Paper type** | IMRaD (empirical, design-stage) | Formal analysis completed; experimental validation pending on cloud infra |
| **Discipline** | Computer Science — Federated Learning Security, Financial Fraud Detection | Cross-disciplinary (CS + banking regulation) |
| **Target journal** | IEEE TIFS | Already reviewed against TIFS standards; alternative: IEEE TDSC |
| **Citation format** | IEEE | Standard for TIFS |
| **Output format** | LaTeX (.tex + .bib) | TIFS requires LaTeX submission via ScholarOne |
| **Language** | English (main) | IEEE TIFS is English-only |
| **Word count** | ~10,000–12,000 words | 15 pages in double-column format |
| **Abstract** | Structured (≈250 words) | 6 attack models, 14 baselines, 15 ablation configs |
| **Current sources** | 10 spec docs + S1–S10 resolutions + 6 reviewer reports (review_1–review_6) + IEEE-CIS/ECC dataset refs | Full source corpus established |

## Key Design Decisions (Current)

1. **Gated cascade** (not fusion ensemble) — per Methodology reviewer C2
2. **EWMA baseline** (λ=0.995) replaces one-shot warm-up — addresses CRITICAL M4 staleness gap
3. **θ_low confidence calibration** connects τ_norm=1.5σ to FPR₁=0.003 — addresses CRITICAL DA-C2
4. **A6 operational envelope** bounds residual gap — attacks within perturbation envelope are information-theoretically indistinguishable
5. **Confident-rejection FPR interpretation** distinguishes FPR_k from raw flag rate — prevents cascade FPR bound misinterpretation
6. **Honest server assumption** bounded in §III and §IX — per DA/Perspective S3
7. **Cascade error propagation bound** (§VII-A) — Stewart perturbation theorem, ≤1.6% honest FPR
8. **SR 11-7 validation structure** in §VIII — per Domain P2 S6
9. **Fairness forgetting mechanism** in reputation update — per Perspective S7
10. **No experimental results yet** — paper framed as design methodology with expected results tables

## Paper Structure (Current)

| § | Title | Pages | Key Content |
|---|-------|-------|-------------|
| I | Introduction | ~1.5 pp | Problem, motivation, statelessness gap, contributions |
| II | Related Work | ~1.5 pp | FL fraud detection, Byzantine robustness, adaptive attacks |
| III | Threat Model | ~2 pp | Adversary model, Kerckhoffs principle, A1–A6 taxonomy |
| IV | Gated Cascade Framework | ~4 pp | L1–L3, confusion matrix, forgetting, thresholds, EWMA baseline |
| V | Attack Models | ~1 pp | A2–A6 detailed specifications with ASR bounds |
| VI | Experimental Design | ~2 pp | Setup, 14 baselines, 15 ablations, metrics, expected results |
| VII | Formal Analysis | ~1 pp | Cascade FPR bound (≤1.6%), threshold convergence, fairness guarantee |
| VIII | Regulatory & Ethics | ~1.5 pp | GDPR, SR 11-7, ECOA/FCRA, cross-jurisdictional conflicts |
| IX | Discussion | ~1 pp | Limitations, bootstrap window, scalability, open problems |
| X | Conclusion | ~0.5 pp | Summary and future work |
| **Total** | | **~15 pp** | 10 sections, 1142 lines LaTeX, clean pdflatex |
