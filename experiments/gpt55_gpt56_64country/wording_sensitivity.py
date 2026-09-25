#!/usr/bin/env python3
"""Exploratory, paired-country sensitivity to disputed prompt wording.

Recompute only the linear distributional losses W1 and TVD from the frozen
country-question score table. Omission cannot identify what a corrected prompt
would have elicited; it diagnoses dependence of the recorded contrast on items.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


HERE = Path(__file__).resolve().parent
SEED = 20260902 + 121106
MODELS = ("GPT-5.5", "GPT-5.6 Sol")
QUESTIONS = ("Q48", "Q57", "Q106", "Q108", "Q121", "Q159")
SCENARIOS = (
    ("all six anchors", ()),
    ("exclude Q106", ("Q106",)),
    ("exclude Q121", ("Q121",)),
    ("exclude Q106 and Q121", ("Q106", "Q121")),
    ("exclude Q108", ("Q108",)),
    ("exclude Q106 and Q108", ("Q106", "Q108")),
)


def bca_interval(draws: np.ndarray, estimate: float, jackknife: np.ndarray) -> tuple[float, float]:
    # Same BCa convention as score_wave1.py; a country is the bootstrap unit.
    prop = np.clip((np.sum(draws < estimate) + 0.5 * np.sum(draws == estimate)) / len(draws),
                   1 / (2 * len(draws)), 1 - 1 / (2 * len(draws)))
    z0 = norm.ppf(prop)
    residual = jackknife.mean() - jackknife
    denominator = 6 * np.power(np.square(residual).sum(), 1.5)
    acceleration = float(np.power(residual, 3).sum() / denominator) if denominator > 0 else 0.0
    quantiles = []
    for probability in (0.025, 0.975):
        z = norm.ppf(probability)
        quantiles.append(norm.cdf(z0 + (z0 + z) / (1 - acceleration * (z0 + z))))
    return tuple(np.quantile(draws, np.clip(quantiles, 0, 1)))


def signflip(values: np.ndarray, permutations: int, rng: np.random.Generator) -> tuple[float, float]:
    extreme = 0
    observed = abs(values.mean())
    for start in range(0, permutations, 10_000):
        n = min(10_000, permutations - start)
        null = (rng.choice(np.array([-1.0, 1.0]), size=(n, len(values))) * values).mean(axis=1)
        extreme += int(np.sum(np.abs(null) >= observed - 1e-15))
    p = (extreme + 1) / (permutations + 1)
    return float(p), float(math.sqrt(p * (1 - p) / (permutations + 1)))


def holm_two(pvalues: np.ndarray) -> np.ndarray:
    order = np.argsort(pvalues)
    result = np.empty(2, float)
    result[order[0]] = min(1., 2 * pvalues[order[0]])
    result[order[1]] = max(result[order[0]], pvalues[order[1]])
    return result


def analyze(path: Path, bootstrap_draws: int, permutations: int) -> pd.DataFrame:
    scores = pd.read_csv(path)
    expected = pd.MultiIndex.from_product([MODELS, sorted(scores.country.unique()), QUESTIONS],
                                          names=["model", "country", "question_id"])
    if scores.country.nunique() != 64 or len(scores) != len(expected):
        raise ValueError("Expected exactly 64 countries x 6 items x 2 models")
    key = scores.set_index(["model", "country", "question_id"])
    if not key.index.is_unique or set(key.index) != set(expected):
        raise ValueError("Frozen score table lacks complete paired country/item cells")
    for metric in ("w1", "tvd"):
        if not np.isfinite(key[metric].to_numpy(float)).all() or not key[metric].between(0, 1).all():
            raise ValueError(f"Invalid {metric} values")

    indices = np.random.default_rng(SEED).integers(0, 64, size=(bootstrap_draws, 64))
    perm_rng = np.random.default_rng(SEED + 1)
    rows = []
    for scenario, omitted in SCENARIOS:
        retained = tuple(q for q in QUESTIONS if q not in omitted)
        subset = scores[scores.question_id.isin(retained)]
        for metric in ("w1", "tvd"):
            country = subset.pivot_table(index="country", columns="model", values=metric, aggfunc="mean")
            country = country.reindex(columns=MODELS).sort_index()
            if country.shape != (64, 2) or country.isna().any().any():
                raise ValueError(f"Incomplete {scenario} paired observations")
            first, second = (country[model].to_numpy(float) for model in MODELS)
            delta = second - first
            draws = delta[indices].mean(axis=1)
            jackknife = (delta.sum() - delta) / 63
            low, high = bca_interval(draws, float(delta.mean()), jackknife)
            p, mcse = signflip(delta, permutations, perm_rng)
            rows.append({
                "scenario": scenario,
                "retained_items": ",".join(retained),
                "metric": metric.upper(),
                "gpt55_estimate": float(first.mean()),
                "gpt56_estimate": float(second.mean()),
                "delta_56_minus_55": float(delta.mean()),
                "delta_standard_error": float(draws.std(ddof=1)),
                "delta_ci_low_bca": float(low),
                "delta_ci_high_bca": float(high),
                "permutation_p_two_sided": p,
                "permutation_p_mcse": mcse,
                "countries": 64,
                "country_bootstrap_draws": bootstrap_draws,
                "permutations": permutations,
            })
    result = pd.DataFrame(rows)
    for scenario in result.scenario.unique():
        mask = result.scenario == scenario
        result.loc[mask, "holm_p_two_metrics_within_scenario"] = holm_two(
            result.loc[mask, "permutation_p_two_sided"].to_numpy(float))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=HERE / "results")
    parser.add_argument("--bootstrap-draws", type=int, default=20_000)
    parser.add_argument("--permutations", type=int, default=19_999)
    args = parser.parse_args()
    if args.bootstrap_draws < 1_000 or args.permutations < 999:
        parser.error("Release requires >=1,000 draws and >=999 permutations")
    result = analyze(args.results_dir / "country_question_scores.csv", args.bootstrap_draws, args.permutations)
    destination = args.results_dir / "wording_omission_sensitivity.csv"
    result.to_csv(destination, index=False)
    print(result[["scenario", "metric", "delta_56_minus_55", "delta_ci_low_bca",
                  "delta_ci_high_bca", "holm_p_two_metrics_within_scenario"]].to_string(index=False))


if __name__ == "__main__":
    main()
