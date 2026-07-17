# Dirichlet Non-IID Data Splits

**Paper:** Robust Federated Learning for Credit Card Identity Fraud Detection  
**Issue:** R7 — Add Dirichlet non-IID splits alongside geographic splits  
**Date:** 2026-07-06

---

## 1. Motivation

The paper originally splits data **geographically** (banks in different regions
have different fraud patterns). This is realistic for our deployment scenario
but:

1. **Confounds non-IID degree with dataset structure.** Geographic splits
   produce unknown $\alpha$ — we can't say "our defense works for
   $\alpha \geq 0.5$" because we don't know the $\alpha$ of the geographic
   split.

2. **Not reproducible.** Another consortium with different regional data
   won't match our geographic distribution.

3. **Reviewer R1 expects controlled skew.** Dirichlet splits with known
   $\alpha$ are the FL community standard (Hsu et al. 2019, Li et al. 2020).

---

## 2. Data Split Types

### 2.1 Geographic Splits (Original)

Each client receives data from a specific region. The non-IID degree is
determined by the region's fraud rate distribution. Kept for its ecological
validity — "this is what a real consortium looks like."

| Region | Clients | Fraud Rate | Data Count |
|--------|---------|------------|------------|
| North America | 5 | 3.5% | 200K |
| Europe | 5 | 2.8% | 180K |
| Asia-Pacific | 5 | 5.2% | 220K |
| Latin America | 3 | 6.8% | 100K |
| Africa/Middle East | 2 | 7.5% | 80K |

### 2.2 Dirichlet Splits (New)

For each seed, draw $p_{c,k} \sim \text{Dirichlet}(\alpha)$ for class $k$,
where $p_{c,k}$ is the fraction of class $k$'s data assigned to client $c$.

| $\alpha$ | Skew Level | Typical Client Label Distribution |
|----------|-----------|----------------------------------|
| 0.1 | Extreme | Each client gets 1–2 labels (e.g., only fraud or only legitimate) |
| 0.5 | High | Clients have 2–4 labels with strong majority class |
| 1.0 | Moderate | Nearly uniform — similar to IID |

---

## 3. Protocol

### 3.1 Statistical Rigor

Each $\alpha$ configuration is run with **5 different random seeds** to
ensure results are not an artifact of a particular partition.

### 3.2 Expected Impact on Defense

| $\alpha$ | Expected Worst ASR | Rationale |
|----------|-------------------|-----------|
| 1.0 (near-IID) | Low (0.20–0.30) | Spectral detection works well — honest updates share similar structure |
| 0.5 (high skew) | Moderate (0.30–0.45) | Layer 2 SVD projection changes more between clients, giving attackers more room |
| 0.1 (extreme) | High (0.40–0.60) | Each client's gradient is unique; Layer 1 and 2 thresholds are looser |
| Geographic | Baseline (0.25–0.35) | Realistic middle ground |

**Key insight:** If our defense maintains ASR < 0.35 even at $\alpha = 0.1$,
this is a strong result. The temporal reputation (Layer 3) should be the
most robust to label skew because it tracks consistency with the *global*
trajectory.

### 3.3 Expected Impact on Baselines

| Baseline | $\alpha = 1.0$ | $\alpha = 0.5$ | $\alpha = 0.1$ |
|----------|---------------|---------------|---------------|
| FedAvg | 0.92 ASR | 0.88 ASR | 0.75 ASR |
| Krum | 0.60 ASR | 0.55 ASR | 0.50 ASR |
| FoolsGold | 0.40 ASR | **0.65 ASR** | **0.80 ASR** |
| FLDetector | 0.35 ASR | 0.50 ASR | **0.70 ASR** |
| **Ours** | **0.25 ASR** | **0.30 ASR** | **0.40 ASR** |

FoolsGold and FLDetector are particularly vulnerable to high skew because
they rely on per-client similarity — when honest clients naturally diverge
under extreme non-IID, the similarity signal is lost.

---

## 4. Implementation

```python
def dirichlet_split(
    labels: np.ndarray,
    n_clients: int,
    alpha: float,
    seed: int = 42,
    min_samples_per_client: int = 1,
) -> list[np.ndarray]:
    """Partition data indices by Dirichlet label distribution (Hsu et al. 2019).

    Args:
        labels: Array of class labels for each sample.
        n_clients: Number of federated clients.
        alpha: Dirichlet concentration parameter.
            Smaller = more extreme non-IID.
        seed: Random seed for reproducibility.
        min_samples_per_client: Minimum samples per client.

    Returns:
        List of index arrays, one per client.
    """
    rng = np.random.RandomState(seed)
    n_classes = len(np.unique(labels))
    n_samples = len(labels)

    # For each class, draw a Dirichlet distribution across clients
    class_indices = [np.where(labels == c)[0] for c in range(n_classes)]

    client_indices = [[] for _ in range(n_clients)]
    for c in range(n_classes):
        if len(class_indices[c]) == 0:
            continue
        proportions = rng.dirichlet(np.repeat(alpha, n_clients))
        proportions = np.array([
            min(p, len(class_indices[c]) / n_clients * 2)
            for p in proportions
        ])
        proportions = proportions / proportions.sum()

        # Assign samples
        idx_pool = class_indices[c].copy()
        rng.shuffle(idx_pool)
        assigned = 0
        for client in range(n_clients):
            n_assign = int(proportions[client] * len(class_indices[c]))
            n_assign = min(n_assign, len(idx_pool) - assigned)
            if n_assign > 0:
                client_indices[client].extend(idx_pool[assigned:assigned + n_assign])
                assigned += n_assign

    # Ensure minimum samples per client by redistributing
    for client in range(n_clients):
        if len(client_indices[client]) < min_samples_per_client:
            needed = min_samples_per_client - len(client_indices[client])
            donor = np.random.choice([i for i in range(n_clients) if i != client])
            client_indices[client].extend(client_indices[donor][:needed])
            client_indices[donor] = client_indices[donor][needed:]

    return [np.array(idx, dtype=int) for idx in client_indices]


def geographic_split(
    client_regions: dict[int, str],
    data_region_labels: np.ndarray,
    seed: int = 42,
) -> list[np.ndarray]:
    """Partition data by geographic region.

    Args:
        client_regions: Mapping from client_id to region name.
        data_region_labels: Per-sample region assignment.
        seed: Random seed.

    Returns:
        List of index arrays, one per client.
    """
    rng = np.random.RandomState(seed)
    regions = list(set(client_regions.values()))
    region_clients = {r: [c for c, reg in client_regions.items() if reg == r] for r in regions}

    client_indices = [[] for _ in range(max(client_regions.keys()) + 1)]
    for region in regions:
        region_data = np.where(data_region_labels == region)[0]
        clients = region_clients[region]
        split = np.array_split(rng.permutation(region_data), len(clients))
        for client, indices in zip(clients, split):
            client_indices[client] = list(indices)

    return [np.array(idx, dtype=int) for idx in client_indices]
```
