#!/usr/bin/env python3
"""Distance-kernel spatial-HAC sensitivity for country-level contrasts.

The estimand is the unweighted mean country contrast. Bartlett kernels at
four geographic cutoffs allow residual dependence among nearby countries.
These are cross-sectional spatial robustness estimates, not a temporal panel
and not a causal spatial-lag model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import t

import score_wave1 as core


def conley_intercept(y: np.ndarray, distance: np.ndarray, cutoff_km: float) -> dict[str, float]:
    y = np.asarray(y, float)
    n = len(y)
    estimate = float(y.mean())
    residual = y - estimate
    kernel = np.clip(1.0 - distance / cutoff_km, 0.0, 1.0)
    # Intercept-only sandwich: (X'X)^-1 X' Omega X (X'X)^-1.
    variance = float(residual @ kernel @ residual) / (n * n)
    variance *= n / (n - 1)
    if variance < -1e-14:
        raise ValueError(f"Negative HAC variance ({variance}) at cutoff {cutoff_km}")
    standard_error = float(np.sqrt(max(variance, 0.0)))
    statistic = estimate / standard_error if standard_error > 0 else np.nan
    pvalue = float(2 * t.sf(abs(statistic), df=n - 1)) if np.isfinite(statistic) else np.nan
    critical = float(t.ppf(0.975, df=n - 1))
    return {
        "estimate": estimate,
        "spatial_hac_standard_error": standard_error,
        "t_statistic": statistic,
        "p_value_two_sided": pvalue,
        "ci_low_95": estimate - critical * standard_error,
        "ci_high_95": estimate + critical * standard_error,
    }


def main() -> None:
    outputs = core.validate_frozen_outputs()
    _, scores, human = core.score_outputs(outputs)
    human_wide = core.human_profiles(human)
    profiles = core.model_profiles(scores, human_wide.index)
    scores = core.attach_human_scores(scores, human_wide)
    countries = human_wide.index
    country_meta = scores[["country", "country_code", "cultural_region"]].drop_duplicates().set_index("country").reindex(countries).reset_index()
    coordinates = core.build_coordinates(country_meta).set_index("country").reindex(countries).reset_index()
    distance = core.haversine_matrix(coordinates)

    outcomes: list[tuple[str, str, np.ndarray]] = []
    for metric in ("w1", "tvd"):
        overall = {
            model: scores[scores["model"] == model].groupby("country")[metric].mean().reindex(countries).to_numpy(float)
            for model in core.MODELS
        }
        outcomes.append((metric.upper(), "All six anchors", overall[core.MODELS[1]] - overall[core.MODELS[0]]))
        for domain in core.DOMAIN_ORDER:
            arrays = {
                model: scores[(scores["model"] == model) & (scores["domain"] == domain)].set_index("country")[metric].reindex(countries).to_numpy(float)
                for model in core.MODELS
            }
            outcomes.append((metric.upper(), domain, arrays[core.MODELS[1]] - arrays[core.MODELS[0]]))

    sigma = human_wide.to_numpy(float).std(axis=0, ddof=1)
    crg = {
        model: np.sqrt(np.square((profiles[model].to_numpy(float) - human_wide.to_numpy(float)) / sigma).mean(axis=1))
        for model in core.MODELS
    }
    outcomes.append(("CRG", "All six anchors", crg[core.MODELS[1]] - crg[core.MODELS[0]]))

    rows: list[dict] = []
    for cutoff in (1_000.0, 2_000.0, 3_000.0, 5_000.0):
        cutoff_indices: list[int] = []
        cutoff_pvalues: list[float] = []
        for metric, scope, values in outcomes:
            result = conley_intercept(values, distance, cutoff)
            rows.append({
                "metric": metric,
                "scope": scope,
                "countries": len(countries),
                "cutoff_km": int(cutoff),
                "kernel": "Bartlett triangular distance kernel",
                "estimand": "mean country contrast, GPT-5.6 Sol minus GPT-5.5",
                **result,
            })
            cutoff_indices.append(len(rows) - 1)
            cutoff_pvalues.append(result["p_value_two_sided"])
        adjusted = core.holm_adjust(np.asarray(cutoff_pvalues))
        for index, value in zip(cutoff_indices, adjusted, strict=True):
            rows[index]["holm_p_fifteen_outcomes_within_cutoff"] = value
        for metric in ("W1", "TVD"):
            metric_indices = [index for index in cutoff_indices if rows[index]["metric"] == metric]
            metric_adjusted = core.holm_adjust(
                np.asarray([rows[index]["p_value_two_sided"] for index in metric_indices])
            )
            for index, value in zip(metric_indices, metric_adjusted, strict=True):
                rows[index]["holm_p_seven_outcomes_within_metric_cutoff"] = value
                if metric == "W1":
                    rows[index]["holm_p_eight_outcomes_within_cutoff"] = value
    result = pd.DataFrame(rows)
    result.to_csv(core.RESULTS / "spatial_hac_contrasts.csv", index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
