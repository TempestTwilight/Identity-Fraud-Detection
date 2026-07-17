"""
Measure honest RCC directly in a non-IID FL setting.

The key question: in real FL with non-IID data, what is the honest RCC?
If clients have persistent per-client gradient biases, their residuals
are NOT zero-mean random noise → honest RCC != 1/√W.

This directly tests whether the RCC gate would work in practice.
"""
import numpy as np
import math
from numpy.random import dirichlet

SEED = 42
np.random.seed(SEED)

D = 100
N = 10
SAMPLES_PER_CLIENT = 500
N_ROUNDS = 80
W = 50       # RCC window
ETA = 0.1
ALPHA_DIRICHLET = 0.5

# ── Generate data (same as before) ─────────────────────────────────
w_true = np.random.randn(D) / math.sqrt(D)
base_X = np.random.randn(N * SAMPLES_PER_CLIENT, D) * 0.5
base_y = (base_X @ w_true + 0.1 * np.random.randn(N * SAMPLES_PER_CLIENT)) > 0
base_y = base_y.astype(float)

label_props = dirichlet([ALPHA_DIRICHLET] * N, size=2)
indices_0 = np.where(base_y == 0)[0]
indices_1 = np.where(base_y == 1)[0]
np.random.shuffle(indices_0)
np.random.shuffle(indices_1)

n_0, n_1 = len(indices_0), len(indices_1)
client_counts_0 = np.floor(label_props[0] * n_0).astype(int)
client_counts_1 = np.floor(label_props[1] * n_1).astype(int)
client_counts_0[-1] += n_0 - client_counts_0.sum()
client_counts_1[-1] += n_1 - client_counts_1.sum()

client_data = []
ptr0, ptr1 = 0, 0
for k in range(N):
    c0, c1 = client_counts_0[k], client_counts_1[k]
    idx = np.concatenate([indices_0[ptr0:ptr0+c0], indices_1[ptr1:ptr1+c1]])
    ptr0 += c0; ptr1 += c1
    client_data.append((base_X[idx], base_y[idx]))

# ── Training with full-batch (no SGD noise, only heterogeneity) ────
w = np.zeros(D)
all_residuals = []  # all_residuals[round][client] = residual vector

for t in range(N_ROUNDS):
    grads = []
    for k in range(N):
        X_k, y_k = client_data[k]
        p_k = 1.0 / (1.0 + np.exp(-X_k @ w))
        g_k = X_k.T @ (p_k - y_k) / len(y_k)
        grads.append(g_k)
        w = w - ETA * g_k  # full-batch update
    
    # Peer mean
    mu_t = np.mean(grads, axis=0)
    
    # Residuals
    residuals_t = [g_k - mu_t for g_k in grads]
    all_residuals.append(residuals_t)

# ── Compute RCC per client over sliding window ─────────────────────
def compute_rcc(residuals, t, W):
    """RCC for all clients at round t over window W."""
    rccs = []
    for k in range(N):
        r_window = [residuals[s][k] for s in range(t - W + 1, t + 1)]
        r_avg = np.mean(r_window, axis=0)
        r_norm_avg = np.mean([np.linalg.norm(r) for r in r_window])
        rcc = np.linalg.norm(r_avg) / r_norm_avg if r_norm_avg > 1e-12 else 0.0
        rccs.append(rcc)
    return rccs

# RCC over final available window
rcc_final = compute_rcc(all_residuals, N_ROUNDS - 1, W)

# Also compute the per-client persistent bias (Δ_i - Δ̄)
final_grads = []
for k in range(N):
    X_k, y_k = client_data[k]
    p_k = 1.0 / (1.0 + np.exp(-X_k @ w))
    g_k = X_k.T @ (p_k - y_k) / len(y_k)
    final_grads.append(g_k)
mu_final = np.mean(final_grads, axis=0)
persistent_biases = [g_k - mu_final for g_k in final_grads]

# ── SGD noise measurement ──────────────────────────────────────────
# Add SGD sampling noise (mini-batch) and recompute RCC
np.random.seed(SEED)
w_sgd = np.zeros(D)
all_residuals_sgd = []

for t in range(N_ROUNDS):
    grads = []
    for k in range(N):
        X_k, y_k = client_data[k]
        n_k = len(y_k)
        # Mini-batch: B = 32
        idx_b = np.random.choice(n_k, min(32, n_k), replace=False)
        X_b = X_k[idx_b]
        y_b = y_k[idx_b]
        p_b = 1.0 / (1.0 + np.exp(-X_b @ w_sgd))
        g_k = X_b.T @ (p_b - y_b) / len(y_b)
        grads.append(g_k)
        w_sgd = w_sgd - ETA * g_k
    
    mu_t = np.mean(grads, axis=0)
    residuals_t = [g_k - mu_t for g_k in grads]
    all_residuals_sgd.append(residuals_t)

rcc_final_sgd = compute_rcc(all_residuals_sgd, N_ROUNDS - 1, W)

# ── Also compute honest RCC for the i.i.d. noise case (no persistent bias) ──
# to verify the 1/√W baseline
np.random.seed(SEED)
w_iid = np.zeros(D)
all_residuals_iid = []
sigma_noise = 0.01  # per-component noise

for t in range(N_ROUNDS):
    grads = []
    for k in range(N):
        # IID clients: all have the SAME data distribution (full dataset)
        X_full = base_X
        y_full = base_y
        p_full = 1.0 / (1.0 + np.exp(-X_full @ w_iid))
        g_true = X_full.T @ (p_full - y_full) / len(y_full)
        # Add i.i.d. noise (as in the original simulation)
        g_k = g_true + sigma_noise * np.random.randn(D)
        grads.append(g_k)
        w_iid = w_iid - ETA * g_true  # update with true gradient
    
    mu_t = np.mean(grads, axis=0)
    residuals_t = [g_k - mu_t for g_k in grads]
    all_residuals_iid.append(residuals_t)

rcc_final_iid = compute_rcc(all_residuals_iid, N_ROUNDS - 1, W)

# ── Report ─────────────────────────────────────────────────────────
print("=" * 70)
print("  HONEST RCC IN NON-IID FL (toy logistic regression)")
print("=" * 70)
print(f"\n  Settings: d={D}, N={N}, samples/client={SAMPLES_PER_CLIENT}")
print(f"  Dirichlet α={ALPHA_DIRICHLET}, RCC window W={W}")
print()

print(f"  {'Client':>8} {'RCC (full-batch)':>18} {'RCC (SGD B=32)':>18} {'||persist_bias||':>18} {'RCC (IID noise)':>18}")
print(f"  {'':->8} {'':->18} {'':->18} {'':->18} {'':->18}")
for k in range(N):
    pb_norm = np.linalg.norm(persistent_biases[k])
    print(f"  {k:>8} {rcc_final[k]:>18.4f} {rcc_final_sgd[k]:>18.4f} {pb_norm:>18.6f} {rcc_final_iid[k]:>18.4f}")

print(f"\n  {'Mean':>8} {np.mean(rcc_final):>18.4f} {np.mean(rcc_final_sgd):>18.4f} {'':>18} {np.mean(rcc_final_iid):>18.4f}")
print(f"  {'Std':>8} {np.std(rcc_final):>18.4f} {np.std(rcc_final_sgd):>18.4f} {'':>18} {np.std(rcc_final_iid):>18.4f}")
print(f"  {'Max':>8} {np.max(rcc_final):>18.4f} {np.max(rcc_final_sgd):>18.4f} {'':>18} {np.max(rcc_final_iid):>18.4f}")
print(f"  {'Min':>8} {np.min(rcc_final):>18.4f} {np.min(rcc_final_sgd):>18.4f} {'':>18} {np.min(rcc_final_iid):>18.4f}")
print()

# Comparison with 1/√W
print(f"  Honest RCC baseline (IID noise): mean = {np.mean(rcc_final_iid):.4f}")
print(f"  Expected 1/√W = {1/math.sqrt(W):.4f}")
print(f"  Match: {'YES ✓' if abs(np.mean(rcc_final_iid) - 1/math.sqrt(W)) < 0.02 else 'NO ✗'}")
print()

print("─" * 70)
print("  INTERPRETATION")
print("─" * 70)
print()
non_iid_mean = np.mean(rcc_final)
print(f"  Non-IID honest RCC (full-batch): {non_iid_mean:.4f}")
print(f"  Non-IID honest RCC (SGD):        {np.mean(rcc_final_sgd):.4f}")
print(f"  IID noise honest RCC:             {np.mean(rcc_final_iid):.4f}")
print(f"  τ_RCC = 0.60:")
if non_iid_mean > 0.6:
    print(f"    ✗ Mean honest RCC ({non_iid_mean:.4f}) > 0.6 — gate would")
    print(f"      flag honest clients. RCC gate FAILS in non-IID FL.")
else:
    max_rcc = np.max(rcc_final)
    if max_rcc > 0.6:
        print(f"    ✗ Max honest RCC ({max_rcc:.4f}) > 0.6 — at least one honest")
        print(f"      client gets flagged. RCC gate has false positives.")
    else:
        margin = 0.6 - max_rcc
        print(f"    ✓ All honest RCC below 0.60 (margin: {margin:.4f})")
        print(f"      RCC gate viable in this non-IID setting.")

print()
print("─" * 70)
print("  RECOMMENDATION")
print("─" * 70)
print()
print("  If honest RCC > 0.6: the global τ_RCC threshold is not viable.")
print("  Replace with PER-CLIENT RCC BASELINE:")
print("    1. Compute each client's historical RCC over a long window")
print("    2. Flag if short-window RCC significantly exceeds historical baseline")
print("    3. This catches attacker (whose RCC increases) while")
print("       accommodating non-IID clients (whose RCC is stable)")
print()
