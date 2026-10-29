# PS-S3 — Trotter error versus noise: finding the best step count

**Team S3 Trotter** · Qiskit Fall Fest 2026, Phase 2 · Quantum Simulation track

## 1. Summary

More Trotter steps shrink the algorithmic error but add gates, and every gate adds noise. We evolve the four-spin ring TFIM H = −Σ Z_i Z_(i+1) − Σ X_i (J = g = 1) from the Néel state |1010⟩ to T = 2 and find the step count n\* that maximises the noisy-state fidelity F = ⟨ψ_exact|ρ|ψ_exact⟩ on Processors A, B and D.

| Processor | 0.5× noise: n\* (F) | **1× noise: n\* (F)** | 2× noise: n\* (F) |
| ----- | ----- | ----- | ----- |
| A (tree, CX) | 7 (0.7196) | **6 (0.5774)** | 5 (0.3985) |
| B (cycle, CX) | 8 (0.7821) | **7 (0.6628)** | 6 (0.5031) |
| D (ring, native RZZ) | 8 (0.8415) | **8 (0.7528)** | 7 (0.6207) |

Four findings, each backed by the measurements below:

1. n\* depends on the device: 6, 7 and 8 at 1× noise for A, B and D. Fewer, cheaper gates per step push the optimum to larger n.

2. Stronger noise moves n\* down on every processor: 7 → 6 → 5 (A), 8 → 7 → 6 (B), 8 → 8 → 7 (D) from 0.5× to 1× to 2×. The shift is slow because n\* sits where a flattening Trotter gain meets a linear noise loss.

3. The crossover is well described by one number per device. The noise loss is linear in n, −ln(F_noisy / F_ideal) ≈ κn, and F_ideal(n) · e^(−κn) reproduces the measured n\* in 8 of 9 cases.

4. Routing gates cost as much as logical ones: about 0.004 of fidelity per two-qubit gate, which is what the official depolarizing rate predicts. At n = 8, Processor A's fidelity is 16% below B's because of the 45 gates added by 15 SWAPs.

## 2. Approach

The locked ring operator is constructed using `qff.tfim_hamiltonian(4, 1.0, 1.0, periodic=True)` (matching the challenge Hamiltonian) and the exact state is exp(−iHT)|1010⟩ (`qff.exact_evolution`), giving M_s(T) = 0.652444. We verified this value, and the noise-free Trotter fidelities for all 12 step counts, with an independent NumPy/SciPy implementation; they agree to better than 10⁻¹³.

Circuits use the official first-order convention U1(Δt) = exp(−i H_X Δt) · exp(−i H_ZZ Δt) with Δt = T/n, the ZZ layer first, even bonds (0,1), (2,3) then odd bonds (1,2), (3,0). On A and B each ZZ term is CX–RZ–CX; on D it is one native RZZ. The unitary is the same, so differences come from topology and gate construction only.

For n ∈ {1, …, 8, 10, 12, 14, 16}, three processors and noise scales 0.5×, 1×, 2× (108 runs) we compute the density-matrix fidelity with `noisy_state_fidelity` (gate noise only) and M_s from 4,096 noisy shots. Official settings are used throughout: optimisation level 1, SABRE, seed 42, depolarizing p1 = 0.001, p2 = 0.005, readout 0.01, all scaled by the sweep factor. n\* is the n with the highest F (smallest n on ties). The organizer's `qff_sim.py` is unchanged. All post-processing and figure generation are executed directly within `main.ipynb` with no external scripts.

## 3. Bell-state verification on Processor D (Objective 1)

We prepared |Φ+⟩ on the adjacent pair (0,1) and on the farthest pair (0,2) of the D ring (distance 2), ideal and noisy, 4,096 shots per basis.

| Pair | Condition | ⟨XX⟩ | ⟨YY⟩ | ⟨ZZ⟩ | 2q gates | Fidelity |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| 0–1 | ideal | 1.0000 | −1.0000 | 1.0000 | 1 | 1.0000 |
| 0–1 | noisy | 0.9463 ± 0.0051 | −0.9468 ± 0.0050 | 0.9463 ± 0.0051 | 1 | 0.9598 ± 0.0022 |
| 0–2 | ideal | 1.0000 | −1.0000 | 1.0000 | 4 | 1.0000 |
| 0–2 | noisy | 0.9238 ± 0.0060 | −0.9141 ± 0.0063 | 0.9458 ± 0.0051 | 4 | 0.9459 ± 0.0025 |

Noise lowers the fidelity because each measured correlator is a parity, and the 1% readout flip on each of two qubits alone multiplies it by (1 − 2p)² = 0.9604; the adjacent pair (0.9598 ± 0.0022) sits almost exactly at this readout-only value, so its single two-qubit gate adds very little. Depolarizing gate errors shrink the correlations further, and the effect grows with gate count. The distant pair needs routing: four two-qubit gates instead of one. That costs about 0.0139 ± 0.0033 more fidelity (dropping from 0.9598 to 0.9459), roughly 0.0046 per extra gate, which matches the per-gate cost in Section 7. The pair difference is consistent with the per-gate cost rather than a precise measurement of it.

## 4. Processor D design (Objective 2)

`processors/processor_D.json` is a **four-qubit ring with a native RZZ basis** (`rz, sx, x, rzz`) and the official error rates (p1 = 0.001, p2 = 0.005, readout 0.01). The file satisfies every rule of `tools/check_processor_d.py` (4 qubits, connected, maximum degree 2, allowed basis, rates not better than official, justification of at least 40 words).

**Bottleneck measured on A and B.** The ring needs a 4-cycle, which A's tree lacks, so on A the closing bond forces SWAPs; B has the cycle but pays two CX per bond.

| Circuit | Proc. | Logical 2q | Total 2q | SWAPs | Depth | 2q depth |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| one step | A | 8 | 11 | 1 | 15 | 7 |
| one step | B | 8 | 8 | 0 | 12 | 4 |
| one step | D | 4 | 4 | 0 | 8 | 2 |
| n = 8 | A | 64 | 109 | 15 | 134 | 77 |
| n = 8 | B | 64 | 64 | 0 | 89 | 32 |
| n = 8 | D | 32 | 32 | 0 | 57 | 16 |

**Expected effect versus measured.** The design predicts no routing and half of B's two-qubit gates. The measurement confirms both: D has 0 SWAPs and 32 gates at n = 8 against 109 (A) and 64 (B), and about 36% lower depth than B (57 vs 89). The noisy result follows: best fidelity 0.7528 on D against 0.6628 on B and 0.5774 on A.

**Trade-off.** D is a specialised four-qubit device with no spare qubits, and it assumes an RZZ gate as good as a CX. Its advantage comes from circuit structure, not better calibration. B and D both provide the 4-cycle without routing, so the B–D gap is attributable mainly to the gate construction (one RZZ against two CX), although B's extra qubits and edges make this a comparison, not a controlled experiment. The A–B gap isolates the cost of missing connectivity.

## 5. Step scan and the best step count (headline)

The left panel shows F(n) on A, B and D at 1× with the noise-free Trotter fidelity (dashed); the right panel is the Processor D noise sweep. The noisy fidelity is a density-matrix result, so n\* is exact for the model; how decisive each optimum is depends on how flat the top of the curve is:

| Processor, noise | n\* | F(n\*) | Runner-up n | F gap |
| ----- | ----- | ----- | ----- | ----- |
| A 0.5× / 1× / 2× | 7 / 6 / 5 | 0.7196 / 0.5774 / 0.3985 | 8 / 7 / 6 | 0.0042 / 0.0077 / 0.0046 |
| B 0.5× / 1× / 2× | 8 / 7 / 6 | 0.7821 / 0.6628 / 0.5031 | 7 / 6 / 5 | 0.0046 / 0.0063 / 0.0161 |
| D 0.5× / 1× / 2× | 8 / 8 / 7 | 0.8415 / 0.7528 / 0.6207 | 10 / 7 / 6 | 0.0003 / 0.0009 / 0.0001 |

On A and B the optimum is a clear step of 0.004–0.016 and moves one step per noise doubling. On D the top of the curve is almost flat: the 0.5× optimum (n = 8) is within 0.0003 of n = 10, and the 2× optimum is within 0.0001 of n = 6. The reported D shift from 8 to 7 is correct on the locked grid, but on D any n between 7 and 10 is practically as good. The 0.5× and 1× optima coincide on D for that reason; their peak fidelities still differ (0.8415 vs 0.7528).

## 6. Why fidelity rises and then falls

**Rise: Trotter error.** The noise-free fidelity is not monotonic at the smallest step counts: 0.115, 0.289, 0.066, 0.518 for n = 1, 2, 3, 4. With Δt = T/n of 2, 1 and 0.67, the step is too large for the first-order formula to be in its convergent regime, so the product-formula state does not approach the exact one monotonically; the noisy curves follow the same dip. This is our reading of the data and we did not derive it. From n = 4 the fidelity rises steadily (0.760 at n = 5, 0.942 at n = 8, 0.990 at n = 16). For n ≥ 8 the infidelity falls with a log-log slope of −2.5, steeper than the −2 expected asymptotically for first order (state error ∝ 1/n), so the asymptotic regime is not yet fully reached. The non-monotonic part does not affect n\* (all optima are at n ≥ 5), but the small-n points should not be read as a trend.

**Fall: noise.** For n ≥ 5 the noise loss is linear in the step count, −ln(F_noisy / F_ideal) ≈ κn:

| Processor | κ at 0.5× | κ at 1× | κ at 2× | 2q gates per step |
| ----- | ----- | ----- | ----- | ----- |
| A | 0.0345 | 0.0657 | 0.1122 | 13.7 |
| B | 0.0231 | 0.0448 | 0.0828 | 8.0 |
| D | 0.0141 | 0.0276 | 0.0532 | 4.0 |

κ grows roughly in proportion to the noise factor, and the product F_ideal(n) · e^(−κn) matches the measured curves (middle panel below) and reproduces n\* in 8 of 9 cases (the miss is A at 2×: model 6, measured 5).

**Where the optimum sits.** n\* is where the relative gain from one more step,

```
d(ln F_ideal) / dn
```

equals the loss rate κ. The gain shrinks as a power of n while the loss stays constant, so a larger κ moves the optimum to fewer steps, slowly. Heuristically, an infidelity falling as n^(−s) gives n\* ∝ κ^(−1/(s+1)); with the measured s ≈ 2.5 a factor 4 in noise (0.5× to 2×) predicts roughly a 30% drop, and we observe 12–29% on the discrete grid (D: 8 → 7, B: 8 → 6, A: 7 → 5). This is a rough argument, not a fit.

## 7. Gate split and connectivity

At n = 8 and 1× noise:

| Processor | Logical 2q | Routing 2q | Total | F |
| ----- | ----- | ----- | ----- | ----- |
| A | 64 | 45 (15 SWAPs) | 109 | 0.5480 |
| B | 64 | 0 | 64 | 0.6519 |
| D | 32 | 0 | 32 | 0.7528 |

Across processors the loss rate follows κ ≈ a + b · (2q gates per step) with b = 0.0039 per two-qubit gate and a = 0.0126 per step. The fit uses three points, so it is indicative. Still, b is close to the 0.00375 (= 0.75 · p2) state-fidelity cost expected for a two-qubit depolarizing error of 0.005 if the simulator's depolarizing parameter has its usual meaning (we did not verify that convention in the simulator source), and a is the per-step single-qubit cost.

Routing gates are as costly as logical ones. A against B at n = 8 has the same logical gates but 45 extra routing gates; its fidelity is 0.841 of B's, i.e. 0.0039 per routing gate, matching b. B against D has 32 fewer gates and a fidelity ratio of 0.866 (0.0045 per saved gate).

**Why the ring is harder on some processors.** A ring needs a 4-cycle. Processor A is a tree: the closing bond (3,0) is not an edge, so every Trotter step needs routing (one SWAP, 3 extra CX, in the single-step circuit; 15 SWAPs, 45 extra gates, over 8 steps). B has a cycle and needs no routing, but its CX-based ZZ doubles the logical count; D removes both. The open chain used in PS-S1 and PS-S2 maps onto a line on every processor and would show none of this.

## 8. Observable-level check

The sampled staggered magnetization, estimated from 4,096 noisy shots (standard error ≈ 0.010), does not reach the exact 0.6524 anywhere on the grid. At n\* it is 0.370 on A (57% of exact), 0.441 on B (68%) and 0.503 on D (77%). Readout error alone only scales ⟨Z_i⟩ by 1 − 2p = 0.98, so the shortfall comes mainly from gate depolarization, which pulls the state toward the maximally mixed state (M_s = 0); we infer this from the magnitudes and did not separate the two sources in a run. The M_s-closest n differs by one step from the fidelity-optimal one on B (6 vs 7) and D (7 vs 8), but those differences (e.g. 0.4436 vs 0.4409) are within shot noise, so we do not claim a different observable-optimal n\*.

## 9. Bonus: Error Mitigation on Processor D (`mitigation.csv`)

To address the observable shortfall observed at n\* = 8 on Processor D (M_s raw = 0.5032 vs exact 0.6524), we implemented and evaluated two complementary error mitigation techniques:

1. **Readout Error Correction (Matrix Inversion):**
   Using two dedicated calibration circuits (|0000⟩ and |1111⟩, 4,096 shots each, totaling 8,192 calibration shots), we empirically measured the single-qubit assignment error rates on Processor D. Inverting the assignment probabilities unbiases each local ⟨Z_i⟩ expectation:

   ```
   ⟨Z_i⟩_mit = (⟨Z_i⟩_raw − (p10 − p01)) / (1 − p10 − p01)
   ```

   This improves the staggered magnetization to M_s = 0.5135 (78.7% of exact).

2. **Zero-Noise Extrapolation (ZNE):**
   Using the locked noise-scaling sweep (0.5×, 1.0×, 2.0×), we perform linear Richardson extrapolation of M_s(λ) to the zero-noise limit λ → 0. Because two-qubit gate errors dominate over readout errors in 32-gate circuits, linear ZNE successfully recovers physical state depolarization, reaching M_s = 0.6138 (94.1% of the exact value 0.6524).

| Method | M_s (raw) | M_s (mitigated) | Ratio to exact (0.6524) | Extra shots |
| ----- | ----- | ----- | ----- | ----- |
| `readout_error_mitigation` | 0.5032 | 0.5135 | 78.7% | 8,192 |
| `zero_noise_extrapolation_linear` | 0.5032 | 0.6138 | 94.1% | 8,192 |

The results are saved in `results/tables/mitigation.csv` following the official challenge template.

> [!IMPORTANT]
> **Hardware Realism Caveat on ZNE:** In our simulation setup, zero-noise extrapolation leverages the Aer simulator's software noise-scaling knob (λ ∈ {0.5, 1.0, 2.0}). This works cleanly in classical simulation to benchmark asymptotic recovery. However, **this cannot be done on real quantum hardware**, because physical devices do not possess a parameter knob to artificially decrease hardware noise below 1.0×. On real quantum processors, ZNE must instead be executed by intentionally amplifying noise above baseline (λ ≥ 1.0) via digital unitary gate folding (G → G (G†G)^k) or analog microwave pulse stretching, and extrapolating backwards to λ → 0.

## 10. Optional Improvements & Ablation Studies

### 10.1 Mapping Processor D's Flat Plateau (n = 5 to 11)

As noted in Section 5, the fidelity curve on Processor D has an exceptionally flat peak (0.0001–0.0009 gap between neighboring points on the locked grid). To determine the precise breadth of this plateau, we evaluated all intermediate step counts n ∈ {5, 6, 7, 8, 9, 10, 11} at 1× noise (`results/tables/s3_d_plateau.csv`):

| Steps n | F_noisy | F_trotter_ideal | M_s (noisy) | M_s std. error |
| ----- | ----- | ----- | ----- | ----- |
| 5 | 0.6628 | 0.7600 | 0.4685 | 0.0101 |
| 6 | 0.7313 | 0.8642 | 0.5011 | 0.0102 |
| 7 | 0.7519 | 0.9144 | 0.5055 | 0.0104 |
| **8 (n\*)** | **0.7528** | 0.9417 | 0.5032 | 0.0105 |
| 9 | 0.7447 | 0.9578 | 0.4941 | 0.0106 |
| 10 | 0.7323 | 0.9681 | 0.4852 | 0.0106 |
| 11 | 0.7176 | 0.9751 | 0.4762 | 0.0106 |

This fine scan reveals that the plateau spans broadly from n = 6 to n = 10, with F > 0.73 throughout. The global optimum sits at n\* = 8 (F = 0.7528), flanked by n = 7 (F = 0.7519, gap 0.0009) and n = 9 (F = 0.7447, gap 0.0081). Any choice n ∈ [7, 9] captures more than 98.9% of the maximum achievable fidelity.

### 10.2 Four-Qubit Ring with CX Basis: Disentangling Topology from Gate Synthesis

Processor D differs from Processor B in two distinct ways: ring topology (4-cycle) and native RZZ basis gates (versus CX-RZ-CX). To isolate these two effects, we constructed and simulated an ablation benchmark: a 4-qubit ring processor restricted to the standard CX basis (`results/tables/s3_ring_cx_ablation.csv`):

| Steps n | Total 2Q Gates | SWAPs | F_noisy (Ring-4 CX) | F_noisy (Processor B, Hex CX) | F_noisy (Processor D, Ring RZZ) |
| ----- | ----- | ----- | ----- | ----- | ----- |
| 1 | 8 | 0 | 0.1112 | 0.1112 | 0.1138 |
| 2 | 16 | 0 | 0.2689 | 0.2689 | 0.2829 |
| 4 | 32 | 0 | 0.4375 | 0.4375 | 0.4918 |
| 6 | 48 | 0 | 0.6565 | 0.6565 | 0.7313 |
| 7 | 56 | 0 | 0.6628 | 0.6628 | 0.7519 |
| **8** | **64** | **0** | **0.6519** | **0.6519** | **0.7528** |
| 10 | 80 | 0 | 0.6124 | 0.6124 | 0.7323 |

This ablation experiment yields two key conclusions:

1. **Ring topology eliminates routing:** Both the Ring-4 CX benchmark and Processor B feature a 4-cycle, requiring exactly 0 SWAPs and 64 CX gates at n = 8. Their noisy fidelities match identically to 4 decimal places (F = 0.6519 at n = 8). Topology alone explains why neither pays the 45-gate routing penalty incurred by Processor A's tree.

2. **Native RZZ halves the two-qubit gate count:** Moving from Ring-4 CX to Processor D keeps the ring topology constant while replacing CX-RZ-CX pairs with native RZZ gates. At n = 8, this cuts two-qubit gates from 64 to 32, delivering an immediate +0.1009 fidelity boost (0.6519 → 0.7528).

Thus, the advantage of Processor D over Processor B is driven purely by the native RZZ gate decomposition rather than residual topological differences.

## 11. Limitations and next steps

* **Flat optimum on D.** As demonstrated in Section 10.1, the plateau on D between n = 7 and n = 9 is within 0.008 of peak fidelity. In experimental workflows with finite sampling budgets, running n = 7 (28 gates) provides comparable accuracy to n = 8 (32 gates) while saving 4 two-qubit pulses.

* **Topology versus gate construction.** Directly tested in Section 10.2: the 4-qubit ring with CX basis confirms that 100% of the B-versus-D fidelity difference stems from native RZZ gate synthesis.

* **Hardware-compatible ZNE.** As highlighted in Section 9, translating our 94.1% ZNE recovery to physical quantum hardware requires digital unitary folding (G → G G†G) or pulse stretching rather than simulator parameter scaling.

* **Noise model.** Synthetic depolarizing and readout noise only; no coherent errors, crosstalk, or drift. The fit κ ≈ a + b · (2q per step) rests on three processors and would need more devices to be trusted quantitatively.

* **One instance.** Single ring, N = 4, g = 1, T = 2; n\* will shift with total evolution time T, transverse coupling g, and system size.

## 12. Reproduction

Install the pinned versions from `requirements.txt` under Python 3.11–3.13 (re-run and verified on Python 3.12.10). Execute `main.ipynb` from the project root:

* Notebook: `jupyter nbconvert --to notebook --execute main.ipynb --output main.ipynb` (or run interactively via Jupyter Notebook / VS Code).

The notebook is completely self-contained and runs top to bottom without external scripts. It sets `RECOMPUTE = True` by default to re-simulate all benchmarks and generate all tables and figures on CPU in ~10 seconds top-to-bottom. Required tables are located in `results/tables/` (`bell.csv`, `resources.csv`, `s3_scan.csv`, `s3_summary.csv`, and bonus `mitigation.csv`). The extended analysis tables `s3_d_plateau.csv` and `s3_ring_cx_ablation.csv`, along with `s3_nstar_margin.csv` and `s3_decay_fit.csv`, are written to `results/tables/`. Every number in this report matches the notebook outputs exactly. AI assistance is declared in `README.md`.
