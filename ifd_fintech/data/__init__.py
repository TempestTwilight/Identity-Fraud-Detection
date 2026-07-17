"""
Data partitioning for federated learning.

Supports:
- Geographic splits (region-based, realistic consortium structure)
- Dirichlet label skew (controlled non-IID, α ∈ {0.1, 0.5, 1.0})
"""

import numpy as np


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
    n_classes = int(np.max(labels) + 1) if labels.dtype in (np.int32, np.int64) else len(np.unique(labels))

    class_indices = [np.where(labels == c)[0] for c in range(n_classes)]

    client_indices: list[list[int]] = [[] for _ in range(n_clients)]
    for c in range(n_classes):
        if len(class_indices[c]) == 0:
            continue
        proportions = rng.dirichlet(np.repeat(alpha, n_clients))
        # Cap proportions to prevent a single client hogging all data
        proportions = np.array([
            min(p, len(class_indices[c]) / n_clients * 2)
            for p in proportions
        ])
        proportions = proportions / proportions.sum()

        idx_pool = class_indices[c].copy()
        rng.shuffle(idx_pool)
        assigned = 0
        for client in range(n_clients):
            n_assign = int(proportions[client] * len(class_indices[c]))
            n_assign = min(n_assign, len(idx_pool) - assigned)
            if n_assign > 0:
                client_indices[client].extend(idx_pool[assigned:assigned + n_assign].tolist())
                assigned += n_assign

    # Ensure minimum samples per client
    for client in range(n_clients):
        if len(client_indices[client]) < min_samples_per_client:
            needed = min_samples_per_client - len(client_indices[client])
            donors = [i for i in range(n_clients) if i != client and len(client_indices[i]) > needed]
            if donors:
                donor = int(rng.choice(donors))
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
        data_region_labels: Per-sample region assignment (string array).
        seed: Random seed for reproducibility.

    Returns:
        List of index arrays, one per client.
    """
    rng = np.random.RandomState(seed)
    regions = list(set(client_regions.values()))
    region_clients: dict[str, list[int]] = {}
    for r in regions:
        region_clients[r] = [c for c, reg in client_regions.items() if reg == r]

    max_client = max(client_regions.keys())
    client_indices: list[list[int]] = [[] for _ in range(max_client + 1)]

    for region in regions:
        region_data = np.where(data_region_labels == region)[0]
        clients = region_clients[region]
        if len(clients) == 0:
            continue
        split = np.array_split(rng.permutation(region_data), len(clients))
        for client, indices in zip(clients, split):
            client_indices[client] = indices.tolist()

    return [np.array(idx, dtype=int) for idx in client_indices]


def compute_partition_stats(client_indices: list[np.ndarray], labels: np.ndarray) -> dict:
    """Compute summary statistics for a data partition.

    Args:
        client_indices: List of per-client index arrays.
        labels: Full dataset labels.

    Returns:
        dict with per-client label distributions and aggregate skew metrics.
    """
    n_classes = int(np.max(labels) + 1)
    n_clients = len(client_indices)

    distributions = np.zeros((n_clients, n_classes))
    for c, indices in enumerate(client_indices):
        if len(indices) > 0:
            for cls in range(n_classes):
                distributions[c, cls] = np.sum(labels[indices] == cls)

    # Shannon entropy per client (normalized)
    entropies = []
    for c in range(n_clients):
        total = distributions[c].sum()
        if total > 0:
            probs = distributions[c] / total
            probs = probs[probs > 0]
            entropy = -np.sum(probs * np.log2(probs)) / np.log2(n_classes)
            entropies.append(entropy)
        else:
            entropies.append(0.0)

    total_samples = sum(len(idx) for idx in client_indices)
    return {
        "n_clients": n_clients,
        "total_samples": total_samples,
        "mean_samples_per_client": total_samples / n_clients,
        "label_entropy_mean": float(np.mean(entropies)),
        "label_entropy_std": float(np.std(entropies)),
        "per_client_distributions": distributions,
    }
