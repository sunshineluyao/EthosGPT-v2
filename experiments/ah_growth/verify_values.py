"""Stream a full-grid Bellman residual without allocating all action/state pairs.

Uses the declared three-point reward quadrature and independently performs
bilinear continuation interpolation. Saved values remain inputs.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ah = args.root.resolve()
    sys.path.insert(0, str(ah))
    from model import burden_step, production
    from node2 import conditional_parameters
    from node2_diagnostics import HeldPolicy

    results = {}
    for country in ["China", "Germany", "Egypt"]:
        p, _ = conditional_parameters(country, R=.0103 if country == "Egypt" else None)
        z = np.load(ah / f"country_revision_results/policy-{country}-base-101-61-0.125.npz")
        grid = z["grid"]; value = z["value"].ravel(); size = len(grid)
        uv = np.array(np.meshgrid(grid, grid, indexing="ij")).reshape(2, -1)
        aa, rr = np.meshgrid(np.linspace(0, min(1., p.capacity / p.aid_labor), 61), np.linspace(0, 1, 61), indexing="ij")
        a = aa.ravel()[:, None]; n = rr.ravel()[:, None] * (p.capacity - p.aid_labor * a)
        dt = .125
        discount = np.exp(-(p.rho - p.q * p.chi * n) * dt)
        nodes, weights = np.polynomial.legendre.leggauss(3)
        largest = 0.
        for start in range(0, uv.shape[1], 48):
            u = uv[:, None, start:start + 48]
            reward = np.zeros((len(a), u.shape[2]))
            for t, w in zip((nodes + 1) * dt / 2, weights * dt / 2):
                ut = burden_step(u, n, a, t, p)
                reward += w * np.exp(-(p.rho - p.q * p.chi * n) * t) * (production(ut, n, a, p)[1] - p.omega * ut.max(axis=0))
            nxt = burden_step(u, n, a, dt, p) * (size - 1)
            ij = np.minimum(np.maximum(np.floor(nxt).astype(int), 0), size - 2)
            f = nxt - ij; i = ij[0] * size + ij[1]
            continuation = ((1 - f[0]) * (1 - f[1]) * value[i] + f[0] * (1 - f[1]) * value[i + size]
                            + (1 - f[0]) * f[1] * value[i + 1] + f[0] * f[1] * value[i + size + 1])
            q = reward + discount * continuation
            largest = max(largest, float(np.max(np.abs(q.max(axis=0) - value[start:start + 48]))))
        assert largest < 1e-8, (country, largest)
        # Check selected off-grid actions against higher reward quadrature.
        hp = HeldPolicy(p, grid, z["value"], 61, dt)
        action_checks = []
        for u in [(.08, .08), (.3, .05), (.05, .3), (.45, .35), (.8, .8)]:
            q3 = np.zeros(len(hp.a)); q5 = q3.copy()
            for degree, target in [(3, q3), (5, q5)]:
                xx, ww = np.polynomial.legendre.leggauss(degree)
                for t, w in zip((xx + 1) * dt / 2, ww * dt / 2):
                    ut = burden_step(np.asarray(u)[:, None], hp.n, hp.a, t, p)
                    target += w * np.exp(-(p.rho - p.q * p.chi * hp.n) * t) * (production(ut, hp.n, hp.a, p)[1] - p.omega * ut.max(axis=0))
                un = burden_step(np.asarray(u)[:, None], hp.n, hp.a, dt, p)
                target += hp.disc * hp.iv(np.clip(un.T, 0, 1))
            action_checks.append({"state": list(u), "max_action_value_quadrature_difference": float(np.max(np.abs(q3 - q5))),
                                  "same_selected_action": bool(np.argmax(q3) == np.argmax(q5))})
        results[country] = {"state_nodes": len(value), "action_candidates": len(a), "max_residual": largest,
                            "off_grid_quadrature_checks": action_checks}
        print(json.dumps({"country": country, "max_residual": largest}), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"status": "passed", "results": results,
                                      "scope": "Full-grid residual of saved reference values, not a fresh solver convergence proof"}, indent=2) + "\n")


if __name__ == "__main__":
    main()
