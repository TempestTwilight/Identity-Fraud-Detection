"""
Fraud-specific evaluation metrics module.

Implements the metrics suite defined in `fraud-metrics.md`:
- Attack Success Rate (ASR) and AUASR
- Precision@Recall (80, 90, 95)
- Savings curve with configurable cost ratio
- Cost-sensitive F\u03b2 (\u03b2 \u2208 {1, 2, 5, 10})
- Honest-client FPR
- Cumulative detection lag
"""

import numpy as np
from typing import Optional
from sklearn.metrics import precision_recall_curve, roc_auc_score


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: np.ndarray,
    fraud_amounts: Optional[np.ndarray] = None,
    cost_per_fp: float = 5.0,
    avg_fraud_loss: float = 450.0,
) -> dict:
    """Compute all fraud-specific evaluation metrics.

    Args:
        y_true: Binary ground truth (1 = fraud, 0 = legitimate).
        y_pred: Binary predictions.
        y_scores: Raw model scores (higher = more likely fraudulent).
        fraud_amounts: Per-transaction fraud loss amounts (for savings
            calculation). If None, uses avg_fraud_loss per detected fraud.
        cost_per_fp: Cost of reviewing one false positive alert.
        avg_fraud_loss: Average loss per undetected fraud transaction.

    Returns:
        dict containing all computed metrics.
    """
    metrics = {}

    # ---- Basic metrics ----
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))

    eps = 1e-10
    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)
    f1 = 2 * precision * recall / (precision + recall + eps)

    metrics["precision"] = precision
    metrics["recall"] = recall
    metrics["f1"] = f1
    metrics["accuracy"] = (tp + tn) / (tp + fp + fn + tn + eps)
    metrics["fp_rate"] = fp / (fp + tn + eps)
    metrics["auc"] = roc_auc_score(y_true, y_scores)

    # ---- Precision@Recall ----
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_scores)

    def precision_at_recall(target_recall: float) -> float:
        """Max precision achievable at or above target recall."""
        mask = recalls >= target_recall
        if not np.any(mask):
            return 0.0
        return float(np.max(precisions[mask]))

    metrics["precision_at_80_recall"] = precision_at_recall(0.80)
    metrics["precision_at_90_recall"] = precision_at_recall(0.90)
    metrics["precision_at_95_recall"] = precision_at_recall(0.95)

    # ---- Cost-sensitive F\u03b2 ----
    for beta in [1, 2, 5, 10]:
        beta2 = beta ** 2
        f_beta = (
            (1 + beta2) * precision * recall / (beta2 * precision + recall + eps)
        )
        metrics[f"f_beta_{beta}"] = f_beta

    # ---- Savings curve ----
    # Sort by descending score (most suspicious first)
    sort_idx = np.argsort(-y_scores)
    y_true_sorted = y_true[sort_idx]

    if fraud_amounts is not None:
        amounts_sorted = fraud_amounts[sort_idx]
    else:
        amounts_sorted = np.full_like(y_true_sorted, avg_fraud_loss, dtype=float)

    # Cumulative savings at each threshold
    cumulative_tp = np.cumsum(y_true_sorted)
    cumulative_fp = np.cumsum(1 - y_true_sorted)

    savings = cumulative_tp * avg_fraud_loss - cumulative_fp * cost_per_fp
    total_fraud_loss = np.sum(y_true * avg_fraud_loss)
    norm_savings = savings / max(total_fraud_loss, eps)

    metrics["savings_max"] = float(np.max(savings))
    metrics["normalized_savings_max"] = float(np.max(norm_savings))

    # Savings at recall thresholds
    total_pos = np.sum(y_true)
    if total_pos > 0:
        recalls_cum = cumulative_tp / total_pos

        def savings_at_recall(target: float) -> float:
            idx = np.searchsorted(recalls_cum, target)
            if idx < len(savings):
                return float(savings[idx])
            return 0.0

        metrics["savings_at_80_recall"] = savings_at_recall(0.80)
        metrics["savings_at_90_recall"] = savings_at_recall(0.90)

    # Break-even FPR: FP rate where savings = 0
    zero_crossings = np.where(np.diff(np.sign(savings)))[0]
    if len(zero_crossings) > 0:
        zero_idx = zero_crossings[0]
        fpr_at_zero = cumulative_fp[zero_idx] / max(tn + fp, eps)
        metrics["break_even_fpr"] = float(fpr_at_zero)
    else:
        metrics["break_even_fpr"] = 1.0 if np.max(savings) >= 0 else 0.0

    # ---- Savings at different cost ratios ----
    metrics["savings_sensitivity"] = {}
    for fn_fp_ratio in [10, 50, 90, 200]:
        cost_fp_local = cost_per_fp
        cost_fn_local = cost_fp_local * fn_fp_ratio
        savings_local = cumulative_tp * cost_fn_local - cumulative_fp * cost_fp_local
        metrics["savings_sensitivity"][f"ratio_{fn_fp_ratio}"] = float(np.max(savings_local))

    return metrics


def compute_attack_success_rate(
    trigger_examples: np.ndarray,
    trigger_labels: np.ndarray,
    model_predictions: np.ndarray,
    target_label: int = 0,
) -> tuple[float, np.ndarray]:
    """Compute Attack Success Rate (ASR).

    Args:
        trigger_examples: Test examples containing the backdoor trigger.
        trigger_labels: Ground truth labels for trigger examples.
        model_predictions: Model predictions on trigger examples.
        target_label: The label the attacker wants the model to predict.

    Returns:
        (asr, per_sample_results)
    """
    if len(trigger_examples) == 0:
        return 0.0, np.array([])

    successful = (model_predictions == target_label).astype(float)
    asr = float(np.mean(successful))
    return asr, successful


def compute_defense_metrics(
    attack_matrix: np.ndarray,
    anomaly_scores: np.ndarray,
    detection_threshold: float = 0.5,
) -> dict:
    """Compute defense-specific metrics.

    Args:
        attack_matrix: Boolean matrix of shape (n_clients, n_rounds).
            True = client is attacking at that round.
        anomaly_scores: Float matrix of shape (n_clients, n_rounds).
            Per-client anomaly scores (1 = honest, 0 = malicious).
        detection_threshold: Threshold below which a client is flagged.

    Returns:
        dict with honest_fpr, rounds_to_detection, flagging_layer_dist.
    """
    n_clients, n_rounds = anomaly_scores.shape
    metrics = {}

    # ---- Honest-client FPR ----
    honest_mask = ~attack_matrix.astype(bool)
    flagged = anomaly_scores < detection_threshold
    honest_flagged = flagged & honest_mask

    # Per-round
    per_round_fpr = np.sum(honest_flagged, axis=0) / np.maximum(np.sum(honest_mask, axis=0), 1)
    metrics["honest_fpr_per_round_mean"] = float(np.mean(per_round_fpr))
    metrics["honest_fpr_per_round_std"] = float(np.std(per_round_fpr))

    # Cumulative (ever flagged across all rounds)
    ever_flagged_honest = np.any(honest_flagged, axis=1)
    total_honest = np.sum(~np.any(attack_matrix, axis=1))
    metrics["honest_fpr_cumulative"] = float(
        np.sum(ever_flagged_honest) / max(total_honest, 1)
    )

    # ---- Rounds to detection ----
    rounds_to_detection = []
    for client in range(n_clients):
        attack_rounds = np.where(attack_matrix[client])[0]
        if len(attack_rounds) == 0:
            continue
        attack_start = attack_rounds[0]
        detection_rounds = np.where(flagged[client])[0]
        detection_rounds = detection_rounds[detection_rounds >= attack_start]
        if len(detection_rounds) > 0:
            rounds_to_detection.append(int(detection_rounds[0] - attack_start))
        else:
            rounds_to_detection.append(n_rounds - attack_start)  # never detected

    metrics["rounds_to_detection_mean"] = float(np.mean(rounds_to_detection)) if rounds_to_detection else float(n_rounds)
    metrics["rounds_to_detection_std"] = float(np.std(rounds_to_detection)) if rounds_to_detection else 0.0
    metrics["detection_rate"] = float(
        np.sum(np.array(rounds_to_detection) < n_rounds) / max(len(rounds_to_detection), 1)
    )

    return metrics


def compute_auasr(asr_curve: np.ndarray) -> float:
    """Area Under the ASR Curve \u2014 single-number summary of backdoor evolution.

    Args:
        asr_curve: ASR values per round, shape (n_rounds,).

    Returns:
        AUASR value (lower is better \u2014 attacker is less successful over time).
    """
    return float(np.trapezoid(asr_curve)) / max(len(asr_curve), 1)
