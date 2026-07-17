# IFD-Fintech: Robust Federated Learning for Credit Card Identity Fraud Detection

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Target:** IEEE TIFS  
**Framework:** Flower (PyTorch backend)

---

## Project Structure

```
IFD-Fintech/
├── pyproject.toml                # Package config (uv-based)
├── uv.lock                       # Locked dependency versions
├── .python-version               # Python version pin
├── .gitignore
├── README.md
├── adaptive-threshold-escalation.md   # Formal spec for the core mechanism
└── ifd_fintech/                       # Main package
    ├── __init__.py
    ├── layers/                        # Detection layers (each implements .score)
    │   ├── __init__.py
    │   ├── layer1_norm_cosine.py      # O(d) norm + cosine filter
    │   ├── layer2_spectral.py         # PCA/SVD spectral anomaly detection
    │   └── layer3_temporal.py         # EMA reputation tracking
    └── orchestration/                 # Adaptive threshold escalation core
        ├── __init__.py                # AdaptiveThresholdEscalation orchestrator
        └── flower_strategy.py         # Flower-compatible strategy wrapper
```

**Convention:** Every layer exposes `score(update) -> (anomaly_score, confidence)` where
- `anomaly_score` in [0, 1]; 1 = definitely honest, 0 = definitely malicious
- `confidence` in [0, 1]; 1 = absolutely certain

The orchestrator uses these scores + confidence to decide escalation, update thresholds,
and compute the reputation-weighted aggregated gradient.

---

## Current Status

| Issue | Status | Deliverable |
|-------|--------|-------------|
| R1: Spectral contradiction | ✅ Resolved | `Expedition/06_Drafts/revised-argument-flow.md` |
| R2: Adaptive threshold formalization | ✅ Spec + code complete | `adaptive-threshold-escalation.md` + `ifd_fintech/orchestration/` |
| R3: Privacy model | ✅ Spec complete | `privacy-model.md` |
| R4: Adaptive attacker design | ✅ Design + code complete | `attacker-design.md` + `ifd_fintech/attacks/` |
| R5: Fraud-specific metrics | ✅ Design + code complete | `fraud-metrics.md` + `ifd_fintech/experiment/metrics.py` |
| R6: Missing baselines | ✅ Design + code complete | `baselines.md` + `ifd_fintech/baselines/` |
| R7: Dirichlet non-IID splits | ✅ Design + code complete | `noniid-splits.md` + `ifd_fintech/data/` |
| R8: Ablation study | ✅ Design + code complete | `ablation-study.md` + `ifd_fintech/experiment/ablation.py` |
| R9: Regulatory explainability | ✅ Design + code complete | `explainability.md` + `ifd_fintech/experiment/explainer.py` |
| R10: Fairness analysis | ✅ Design + code complete | `fairness-analysis.md` + `ifd_fintech/experiment/fairness.py` |
