#!/usr/bin/env python3
"""Original eight-region description of archived country-question losses.

Keep the published WVS/Tao cultural-map labels and the released crosswalk
unchanged. Country means are equally weighted. Exploratory bootstrap intervals
resample countries within each region. The two regions with fewer than five
countries receive point estimates only; do not treat subgroup intervals as
multiplicity-adjusted confirmatory tests.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


HERE = Path(__file__).resolve().parent
MODELS = ("GPT-5.5", "GPT-5.6 Sol")
QUESTIONS = {"Q48", "Q57", "Q106", "Q108", "Q121", "Q159"}
SOURCE_REGIONS = {
    "African-Islamic", "Catholic Europe", "Confucian", "English-Speaking",
    "Latin America", "Orthodox Europe", "Protestant Europe", "West & South Asia",
}
SEED = 20260925


def bca_interval(values: np.ndarray, rng: np.random.Generator, draws: int) -> tuple[float, float]:
    """Country bootstrap BCa CI, consistent with the main paired estimator."""
    n = len(values)
    estimate = float(values.mean())
    replicates = values[rng.integers(n, size=(draws, n))].mean(axis=1)
    prop = (np.sum(replicates < estimate) + 0.5 * np.sum(replicates == estimate)) / draws
    z0 = norm.ppf(np.clip(prop, 1 / (2 * draws), 1 - 1 / (2 * draws)))
    jackknife = (values.sum() - values) / (n - 1)
    residual = jackknife.mean() - jackknife
    denominator = 6 * np.square(residual).sum() ** 1.5
    acceleration = float(np.power(residual, 3).sum() / denominator) if denominator > 0 else 0.0
    probs = []
    for p in (0.025, 0.975):
        z = norm.ppf(p)
        probs.append(norm.cdf(z0 + (z0 + z) / (1 - acceleration * (z0 + z))))
    return tuple(float(x) for x in np.quantile(replicates, np.clip(probs, 0, 1)))


def analyze(path: Path, bootstrap_draws: int = 20_000) -> pd.DataFrame:
    scores = pd.read_csv(path)
    if not {"model", "country", "cultural_region", "question_id", "w1", "tvd"} <= set(scores):
        raise ValueError("Missing required score columns")
    if len(scores) != 64 * len(QUESTIONS) * len(MODELS):
        raise ValueError("Expected complete 64-country, six-item, two-model score table")
    if set(scores.cultural_region) != SOURCE_REGIONS or set(scores.question_id) != QUESTIONS:
        raise ValueError("Source region or question taxonomy has changed")
    if set(scores.model) != set(MODELS) or scores.country.nunique() != 64:
        raise ValueError("Model or country roster has changed")
    if scores.duplicated(["model", "country", "question_id"]).any():
        raise ValueError("Duplicate model-country-question cell")
    by_country = scores.groupby("country", sort=True)
    if not ((by_country.size() == 12).all() and (by_country.cultural_region.nunique() == 1).all()):
        raise ValueError("Incomplete cells or inconsistent country region assignment")
    for metric in ("w1", "tvd"):
        if not scores[metric].between(0, 1).all():
            raise ValueError(f"Invalid {metric} score")
    regions = sorted(scores.cultural_region.unique())
    if len(regions) != 8:
        raise ValueError("Expected eight original cultural-map regions")
    rng = np.random.default_rng(SEED)
    rows = []
    for region in regions:
        part = scores[scores.cultural_region == region]
        for metric in ("w1", "tvd"):
            country = part.pivot_table(index="country", columns="model", values=metric, aggfunc="mean")
            country = country.reindex(columns=MODELS).sort_index()
            if country.isna().any().any() or len(country) != part.country.nunique():
                raise ValueError("Missing paired country score")
            first, second = (country[m].to_numpy(float) for m in MODELS)
            delta = second - first
            # Two- and four-country BCa intervals are too unstable to report.
            lower, upper = (bca_interval(delta, rng, bootstrap_draws)
                            if len(delta) >= 5 else (float("nan"), float("nan")))
            rows.append({
                "cultural_region": region,
                "metric": metric.upper(),
                "countries": len(country),
                "gpt55_estimate": first.mean(),
                "gpt56_estimate": second.mean(),
                "delta_56_minus_55": delta.mean(),
                "delta_ci_low_bca": lower,
                "delta_ci_high_bca": upper,
                "country_bootstrap_draws": bootstrap_draws,
                "bootstrap_seed": SEED,
            })
    result = pd.DataFrame(rows)
    for metric in ("W1", "TVD"):
        rows_for_metric = result[result.metric == metric]
        overall = scores.pivot_table(index="country", columns="model", values=metric.lower(), aggfunc="mean")
        pooled_delta = (overall[MODELS[1]] - overall[MODELS[0]]).mean()
        weighted_delta = np.average(rows_for_metric.delta_56_minus_55, weights=rows_for_metric.countries)
        if not np.isclose(weighted_delta, pooled_delta, atol=1e-12):
            raise ValueError("Regional results fail to reconstruct global contrast")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=HERE / "results")
    parser.add_argument("--bootstrap-draws", type=int, default=20_000)
    args = parser.parse_args()
    if args.bootstrap_draws < 1_000:
        parser.error("Use at least 1,000 country bootstrap draws")
    result = analyze(args.results_dir / "country_question_scores.csv", args.bootstrap_draws)
    destination = args.results_dir / "eight_region_sensitivity.csv"
    result.to_csv(destination, index=False)
    print(result[["cultural_region", "metric", "countries", "delta_56_minus_55", "delta_ci_low_bca", "delta_ci_high_bca"]].to_string(index=False))


if __name__ == "__main__":
    main()
